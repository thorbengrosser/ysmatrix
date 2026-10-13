# Command line: `ysmatrix`

Every command connects to the first panel it finds. With several panels, pick one by its
advertised name (`-n YS525228813`) or its address (`-a <address>`); `ysmatrix scan` lists both.
Use `-v` for progress and `-vv` to see every frame in hex.

```bash
ysmatrix scan
# YS525228813    88308711-0726-77B0-B9BF-23BBC07AE466
ysmatrix -n YS525228813 text "left backpack"
ysmatrix -a 88308711-0726-77B0-B9BF-23BBC07AE466 text "right backpack"
```

```bash
ysmatrix scan                         # list panels
ysmatrix info                         # model, firmware, size, settings, stored slots
```

## Settings

```bash
ysmatrix power off                   # display dark; content stays stored
ysmatrix power on                    # showing content (image, text, play, loop) also switches it on
ysmatrix brightness 8                 # 1-15
ysmatrix rotate                       # show the current rotation
ysmatrix rotate 2                     # n x 90 degrees clockwise; stored on the panel
ysmatrix sync-time                    # set the panel clock to this computer's time (it resets on power-off)
```

## Content

Content goes into one of 60 slots (0-59) and stays there after power-off. Uploading to a slot replaces it.

```bash
ysmatrix image cat.png --slot 1                   # fit, fill or stretch with --resize
ysmatrix image party.gif --slot 2                 # animated GIFs work too
ysmatrix text "Hello world" --slot 3 -c green     # scrolling text
ysmatrix text "Hi" --static --size 8 -c "#ff8000"
ysmatrix clock --slot 4                           # live hh:mm:ss
ysmatrix clock "{DD}.{MM} {hh}:{mm}" --size 8
ysmatrix builtin-clock                            # the panel's own clock face
```

Colours: a name (`red`, `green`, `blue`, `white`, `yellow`, `cyan`, `magenta`, `orange`, `purple`, `pink`),
`#rrggbb` or `r,g,b`.

## Playback

```bash
ysmatrix play 1                       # show slot 1
ysmatrix loop 1 2 3                   # cycle through slots 1, 2, 3
ysmatrix slots                        # what is stored
ysmatrix delete 3
```

## Live drawing and games

```bash
ysmatrix fill 8 8 55 55 orange        # draws immediately; press Enter to leave drawing mode
ysmatrix game tetris                  # arrows move, s start, p pause, q quit
ysmatrix game snake
```

## Exploring

`raw` sends any payload in hex; see [the protocol reference](../protocol.md).

```bash
ysmatrix raw 06 02 00 0f              # brightness 15
ysmatrix raw 0a00 --query             # device info, raw
```
