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
You can use download link for «classic» item filters as it is on official pod launcher. But there is a new feature: jinja2-based generator, which you can use to generate item filter rules with loops, conditions and configuration parameters:
```
## configuration part
# set gold_hide_step = 15
# set hp_mp_hide = namespace(
    enabled=true,
    clvls=[12, 18, 30, 40, 0],
    colors={"hp": d2.color.red, "mp": d2.color.blue},
)
# set small_rej_hide_clvl = 40
# set hide_potions = ["stamina", "antidote", "thawing", "rancid_gas", "oil",
                      "choking_gas", "exploding", "strangling_gas", "fulminating"]
# set hide_tp_id_scrolls = true
# set hide_tp_id_books = true
# set hide_key = true
# set hide_gems = namespace(
    enabled=true,
    clvls={
        "chipped": 15,
        "flawed": 20,
        "normal": 40,
    },
)


## implementation part
// hide low gold
# if gold_hide_step:
    # for clvl in range(1, 100):
        ItemDisplay[{{ d2.code.gold }}<{{ (clvl * gold_hide_step)|round|int }} AND CLVL>{{ clvl }}]:
    # endfor
# endif

// runes
# for code in d2.code.rune.by_tier:
    ItemDisplay[{{ code }}]: {{ d2.color.orange }}{{ d2.tag.runename }} Rune [{{ loop.index }}]
# endfor

// hp/mp potions
# if hp_mp_hide
    # for type, color in hp_mp_hide.colors.items():
        # for code in d2.code.potion[type]:
            # set clvl = hp_mp_hide.clvls[loop.index0]
            # if clvl:
                ItemDisplay[{{ code }} CLVL<{{ clvl }}]: {{ color }}!{{ d2.color.white }}{{ type }}
                ItemDisplay[{{ code }} CLVL>{{ clvl - 1 }}]:
            # else
                ItemDisplay[{{ code }}]: {{ color }}!{{ d2.color.white }}{{ type }}
            # endif
        # endfor
    # endfor
# endif

// rejs
# if small_rej_hide_clvl:
    ItemDisplay[{{ d2.code.potion.rejuvenation.small }} CLVL<{{ small_rej_hide_clvl }}]: {{ d2.color.purple }}!{{ d2.color.white }}35%
    ItemDisplay[{{ d2.code.potion.rejuvenation.small }} CLVL>{{ small_rej_hide_clvl - 1 }}]:
# endif
ItemDisplay[{{ d2.code.potion.rejuvenation.big }}]: {{ d2.color.purple }}!{{ d2.color.white }}70%

// hide potions
# if hide_potions
    # for name in hide_potions:
        ItemDisplay[{{ d2.code.potion[name] }}]:
    # endfor
# endif

// hide scrolls
# if hide_tp_id_scrolls
    ItemDisplay[{{ d2.code.scroll.town_portal }}]:
    ItemDisplay[{{ d2.code.scroll.identify }}]:
# endif

// hide books
# if hide_tp_id_books
    ItemDisplay[{{ d2.code.book.town_portal }}]:
    ItemDisplay[{{ d2.code.book.identify }}]:
# endif

// hide key
# if hide_key
    ItemDisplay[{{ d2.code.key }}]:
# endif

// gems
# for name in d2.code.gem:
    # for tier, code in d2.code.gem[name].by_name.items():
        # set clvl = hide_gems.clvls.get(tier)
        # if hide_gems.enabled and clvl:
            ItemDisplay[{{ code }} CLVL<{{ clvl }}]: {{ d2.color.orange }}!{{ d2.color.white }}{{ tier|capitalize }} {{ name|capitalize }}
            ItemDisplay[{{ code }} CLVL>{{ clvl - 1 }}]:
        # else
            ItemDisplay[{{ code }}]: {{ d2.color.orange }}!{{ d2.color.white }}{{ tier|capitalize }} {{ name|capitalize }}
        # endif
    # endfor
# endfor

ItemDisplay[INF !RW !leg]:
```

This will produce about 230 lines of «classic» item filter. Read more on [jinja2 documentation](http://jinja.pocoo.org/docs/2.10/templates/).

`d2` object is straight view/proxy of [this](https://github.com/pohmelie/pypod-launcher/blob/master/pypod_launcher/codes.yaml) yaml file (feel free to make pull requests to add items).
