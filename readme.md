# Python Path of Diablo launcher
Wine targeted pod-launcher written in python. Ported from original
[vb](https://github.com/GreenDude120/PoD-Launcher) 🤢
version

![screenshot](https://raw.githubusercontent.com/pohmelie/pypod-launcher/master/screenshot.png)

## Reasons
* Wine friendly
* No dependencies (.NET for example)
* No os restriction (winXP is ok)

## Installation
### From binary
[Windows-wine-friendly binaries](https://github.com/pohmelie/pypod-launcher/releases)
### From source
``` bash
py -m pip install git+https://github.com/pohmelie/pypod-launcher
```

## Requirements
* python 3.5 (python 3.6+ have [unresolved issue under wine](http://wine.1045685.n8.nabble.com/Bug-44999-New-Python-3-6-5-crashes-due-to-unimplemented-function-api-ms-win-core-path-l1-1-0-dll-Pat-td5959543.html))

## License
`pypod-launcher` is offered under the WTFPL license.
