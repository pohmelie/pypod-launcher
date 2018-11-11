# -*- mode: python -*-

block_cipher = None


a = Analysis(['pypod-launcher.py'],
             pathex=['/home/poh/pro/py/pod/pypod-launcher'],
             binaries=[],
             datas=[('pypod_launcher/main.ui', 'pypod_launcher/'), ('pypod_launcher/icon.ico', 'pypod_launcher/')],
             hiddenimports=['PySide2.QtXml'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='pypod-launcher',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , icon='pypod_launcher/icon.ico')
