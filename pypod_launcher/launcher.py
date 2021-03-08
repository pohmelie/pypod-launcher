import collections
import contextlib
import datetime
import functools
import logging
import logging.handlers
import pathlib
import sys
import tempfile
import zlib
from subprocess import DEVNULL, Popen

import jinja2
import pkg_resources
import requests
import yaml
from lxml import etree
from PySide2 import QtGui, QtUiTools, QtWidgets
from skin import Skin
from sqlitedict import SqliteDict

from . import __version__ as version

logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    "d2_path": pathlib.Path(),
    "window_mode": True,
    "glide_wrapper_only": True,
    "no_fix_aspect": False,
    "skip_to_bnet": True,
    "direct": False,
    "no_sound": False,
    "widescreen": False,
    "check_for_updates": False,
    "loot_filter_url": "http://pathofdiablo.com/item.filter",
    "update_url": "https://raw.githubusercontent.com/GreenDude120/PoD-Launcher/master/files.xml",
}

LAUNCH_KEYS = {
    "window_mode": "-w",
    "glide_wrapper_only": "-3dfx",
    "no_fix_aspect": "-nofixaspect",
    "skip_to_bnet": "-skiptobnet",
    "direct": "-direct",
    "no_sound": "-ns",
    "widescreen": "-widescreen",
}

CHUNK_SIZE = 8192
SOCKET_TIMEOUT = 300
IGNORE_ON_UPDATE = {"item.filter"}


class UiLogger(logging.StreamHandler):

    MAX_LOGGER_LINES = 1000

    def __init__(self, *args, ui, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = ui

    def emit(self, record):
        try:
            self.ui.log.addItem(self.format(record))
            while self.ui.log.count() > self.MAX_LOGGER_LINES:
                self.ui.log.takeItem(0)
            self.ui.log.scrollToBottom()
        except RuntimeError:
            pass
        except Exception:
            self.handleError(record)


class Progress:

    def __init__(self, progress, status):
        self.progress = progress
        self.status = status
        self.current = 0
        self.total = None

    def add(self, value):
        self.current = min(self.total, self.current + value)
        self.progress.setValue(int(self.current / self.total * 100))

    def __call__(self, message, total):
        logger.debug(message)
        self.status.setText(message)
        self.total = total
        return self

    def __enter__(self):
        self.progress.setValue(0)
        self.current = 0
        return self

    def __exit__(self, *exc_info):
        self.progress.setValue(100)


def log_exception(f):

    @functools.wraps(f)
    def sync_wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            logger.exception("critical on %r", f)

    return sync_wrapper


class Launcher:

    def __init__(self, ui):
        self.ui = ui
        self.progress = Progress(self.ui.progress, self.ui.status)
        file_config = SqliteDict("pypod-launcher-settings.sqlite", autocommit=True)
        self.config = collections.ChainMap(file_config, DEFAULT_CONFIG)
        self.load()
        self.bind()
        if self.config["check_for_updates"]:
            self.ui.update_button.clicked.emit()

    def center(self):
        desktop = QtWidgets.QApplication.desktop()
        screen = desktop.screenNumber(desktop.cursor().pos())
        center = desktop.screenGeometry(screen).center()
        frame_geometry = self.ui.frameGeometry()
        frame_geometry.moveCenter(center)
        self.ui.move(frame_geometry.topLeft())

    def load(self):
        for key, value in self.config.items():
            edit = getattr(self.ui, "{}_edit".format(key), None)
            view = getattr(self.ui, "{}_view".format(key), None)
            for w in (view, edit):
                if not w:
                    continue
                if isinstance(w, (QtWidgets.QLabel, QtWidgets.QLineEdit)):
                    w.setText(str(self.config[key]))
                elif isinstance(w, QtWidgets.QCheckBox):
                    w.setChecked(self.config[key])
                else:
                    logger.error("no widgets for %r key in config", key)
                    continue
                break

    def _choose_directory(self, key, view):
        s = QtWidgets.QFileDialog.getExistingDirectory(self.ui, dir=view.text())
        if not s:
            return
        self.config[key] = pathlib.Path(s).resolve()
        view.setText(s)

    def _choose_file(self, key, view):
        s, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui, dir=view.text())
        if not s:
            return
        self.config[key] = pathlib.Path(s).resolve()
        view.setText(s)

    def _checkbox_changed(self, key, edit, *_):
        self.config[key] = edit.isChecked()

    def _line_edit_changed(self, key, edit):
        self.config[key] = edit.text()

    def bind(self):
        for key, value in self.config.items():
            edit = getattr(self.ui, "{}_edit".format(key), None)
            view = getattr(self.ui, "{}_view".format(key), None)
            if isinstance(edit, QtWidgets.QPushButton):
                edit.clicked.connect(functools.partial(self._choose_directory, key, view))
            elif isinstance(edit, QtWidgets.QCheckBox):
                edit.stateChanged.connect(functools.partial(self._checkbox_changed, key, edit))
            elif isinstance(edit, QtWidgets.QLineEdit):
                edit.editingFinished.connect(functools.partial(self._line_edit_changed, key, edit))
            else:
                logger.error("no widgets for %r key in config", key)
        self.ui.launch_button.clicked.connect(self.launch)
        self.ui.generate_loot_filter_button.clicked.connect(self.generate_loot_filter)
        self.ui.update_button.clicked.connect(self.update)
        f = functools.partial(self._choose_file, "loot_filter_url", self.ui.loot_filter_url_edit)
        self.ui.browse_loot_filter_button.clicked.connect(f)

    @property
    def pod_path(self):
        return self.config["d2_path"] / "Path of Diablo"

    def _set_buttons_state(self, state):
        buttons = (self.ui.launch_button, self.ui.generate_loot_filter_button,
                   self.ui.update_button, self.ui.browse_loot_filter_button)
        for b in buttons:
            b.setEnabled(state)

    @contextlib.contextmanager
    def disabled_buttons(self):
        self._set_buttons_state(False)
        try:
            yield
        finally:
            self._set_buttons_state(True)

    @log_exception
    def launch(self):
        with self.disabled_buttons():
            logger.info("launching pod...")
            args = [str(self.pod_path / "Game.exe")]
            for name, key in LAUNCH_KEYS.items():
                if self.config[name]:
                    args.append(key)
            logger.info("launching arguments %r", args)
            try:
                Popen(args, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, cwd=str(self.pod_path))
            except Exception:
                logger.exception("launch went wrong")

    def _download_file(self, urls, target, expected_crc=None):
        logger.debug("downloading %r", urls)
        target.parent.mkdir(parents=True, exist_ok=True)
        for url in urls:
            with target.open(mode="wb") as f:
                try:
                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                    crc = 0
                    for chunk in response.iter_content(2 ** 20):
                        crc = zlib.crc32(chunk, crc)
                        f.write(chunk)
                    calculated_crc = "{:x}".format(crc)
                    if expected_crc is not None and expected_crc != calculated_crc:
                        logger.warning("crc32 for url %s is %r, but expect %r", url, calculated_crc, expected_crc)
                        continue
                    logger.debug("download successful for %r", url)
                    return True
                except Exception:
                    logger.exception("something went wrong with url %s", url)
        logger.error("download failed for %r", urls)
        return False

    def _update_files(self, descriptions):
        need_update = []
        need_check = []
        for desc in descriptions:
            if desc.crc and desc.target.exists():
                need_check.append(desc)
            elif desc.target.name not in IGNORE_ON_UPDATE:
                need_update.append(desc)
        if need_check:
            # crc32 local files
            with self.progress("calculating local crc32...", total=len(need_check)):
                for desc in need_check:
                    logger.debug("calculating crc32 for %r", desc.target)
                    crc = 0
                    with desc.target.open(mode="rb") as f:
                        while True:
                            chunk = f.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            crc = zlib.crc32(chunk, crc)
                    calculated_crc = "{:x}".format(crc)
                    if desc.crc != calculated_crc:
                        need_update.append(desc)
                    self.progress.add(1)
        if not need_update:
            logger.info("everything is up to date")
            return
        with tempfile.TemporaryDirectory(prefix="pod-launcher-") as tmp_dir:
            # download remote
            tmp_path = pathlib.Path(tmp_dir)
            with self.progress("download remote files...", total=len(need_update)):
                for desc in need_update:
                    tmp_file = tmp_path / desc.target.name
                    if not self._download_file(desc.urls, tmp_file, desc.crc):
                        logger.error("update failed on %r", desc)
                        return
                    self.progress.add(1)
            # move passed remote to target
            with self.progress("replacing old files...", total=len(need_update)):
                for desc in need_update:
                    tmp_file = tmp_path / desc.target.name
                    desc.target.parent.mkdir(parents=True, exist_ok=True)
                    tmp_file.replace(desc.target)
                    self.progress.add(1)

    def generate_loot_filter(self):
        with self.disabled_buttons():
            target = self.pod_path / "filter" / "item.filter"
            if target.exists():
                answer = QtWidgets.QMessageBox.question(self.ui, "Confirmation",
                                                        "Are you sure you want to rewrite your 'item.filter'?")
                if answer == QtWidgets.QMessageBox.StandardButton.No:
                    return
            logger.info("generating loot filter...")
            uri = self.config["loot_filter_url"]
            try:
                template = pathlib.Path(uri).read_text()
            except Exception:
                response = requests.get(uri.strip())
                response.raise_for_status()
                template = response.text
            d2 = Skin(yaml.load(pkg_resources.resource_string("pypod_launcher", "d2.yaml")))
            rendered = jinja2.Template(template, line_statement_prefix="#", line_comment_prefix="##").render(d2=d2)
            header = "// Generated with pypod-launcher v{} ({})\n".format(version, datetime.datetime.now())
            target.parent.mkdir(exist_ok=True)
            target.write_text(header + rendered)
            logger.info("generation done")
            self.ui.status.setText("done")

    @log_exception
    def update(self):
        with self.disabled_buttons():
            logger.info("checking for update...")
            url = self.config["update_url"].strip()
            response = requests.get(url)
            response.raise_for_status()
            parsed = etree.fromstring(response.content)
            descriptions = []
            for file_desc in parsed:
                crc = file_desc.get("crc")
                if crc:
                    crc = crc.lower()
                descriptions.append(Skin(dict(
                    urls=[link.text for link in file_desc],
                    target=self.pod_path / file_desc.get("name"),
                    crc=crc,
                )))
            self._update_files(descriptions)
            (self.pod_path / "config").mkdir(parents=True, exist_ok=True)
            logger.debug("update done")
            self.ui.status.setText("done")


def config_logging(ui):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                                  datefmt="[%Y-%m-%d %H:%M:%S]")
    file_handler = logging.handlers.RotatingFileHandler("pypod-launcher.log", maxBytes=2 ** 20,
                                                        backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    ui_handler = UiLogger(ui=ui)
    ui_handler.setFormatter(formatter)
    ui_handler.setLevel(logging.DEBUG)
    logger.addHandler(ui_handler)
    logger.setLevel(logging.DEBUG)
    logger.info("pypod-launcher version: %s", version)


def main():
    app = QtWidgets.QApplication(sys.argv)
    icon_file = pkg_resources.resource_filename("pypod_launcher", "icon.ico")
    app.setWindowIcon(QtGui.QIcon(icon_file))
    ui_file = pkg_resources.resource_filename("pypod_launcher", "main.ui")
    ui = QtUiTools.QUiLoader().load(ui_file)
    ui.setWindowTitle("pypod-launcher [v{}]".format(version))
    config_logging(ui)
    launcher = Launcher(ui)
    launcher.center()
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
