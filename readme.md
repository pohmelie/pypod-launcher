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

## Usage

### Loot filter generator
You can use download link for «classic» item filters as it is on official pod launcher. But there is a new feature: jinja2-based generator, which you can use to generate item filter rules:
```
// hide low gold
# for clvl in range(1, 91):
ItemDisplay[{{ code.gold }}<{{ clvl * 1000 // 90 }} AND CLVL>{{ clvl }}]:
# endfor
ItemDisplay[{{ code.gold }}]: %NAME%

// runes
# for i in range(1, 34):
ItemDisplay[r{{ i }}]: %ORANGE%%NAME%
# endfor

// rejs
ItemDisplay[{{ code.potion.rejuvenation.small }} CLVL<40]: %PURPLE%!%WHITE%35%
ItemDisplay[{{ code.potion.rejuvenation.small }} CLVL>39]:
ItemDisplay[{{ code.potion.rejuvenation.big }}]: %PURPLE%!%WHITE%70%

// gems
# for name in code.gem:
# for code in code.gem[name].by_tier:
ItemDisplay[{{ code }}]: %ORANGE%!%WHITE%%NAME%
# endfor
# endfor
```

This will produce about 170 lines of «classic» item filter. Read more on [jinja2 documentation](http://jinja.pocoo.org/docs/2.10/templates/).

`code` object is straight view/proxy of [this](https://github.com/pohmelie/pypod-launcher/blob/master/pypod_launcher/codes.yaml) yaml file (feel free to make pull requests to add items).
