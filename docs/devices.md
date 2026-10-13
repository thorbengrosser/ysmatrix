# Which devices does this work with?

ysmatrix speaks the same Bluetooth protocol as the **LOY PLAY** app (Android/iOS) and its desktop
sibling **LOY SPACE**. It is independent and unofficial; the app names are used only to say what it
is compatible with. These apps drive a family of cheap Bluetooth RGB LED matrices sold as LED
backpacks, bag panels and similar gadgets.

## Is my device one of them?

Likely yes if:

* the vendor tells you to use **LOY PLAY** or **LOY SPACE**,
* it advertises over Bluetooth as **`YS…`** or **`TL…`** followed by digits, and
* `ysmatrix info` prints a model and firmware.

```bash
ysmatrix scan
ysmatrix info
```

Many unrelated LED gadgets also use Bluetooth service `FFF0` but speak a different protocol
(for example iPixel Color devices; see [pypixelcolor](https://github.com/lucagoc/pypixelcolor)).
If `ysmatrix info` gets no answer, your device is probably one of those.

## Tested

<img src="assets/led_backpack_photo.jpg" width="320" alt="The tested 64x64 LED backpack showing a picture sent with ysmatrix">

| Device | Size | Model | Firmware | Result |
|---|---|---|---|---|
| LED backpack | 64×64 | `EXYB-AS#GGMJXZ180` | `V2.9.1#V16` | Everything marked ✅ in [status.md](status.md) |

## Untested but probably fine

The panel reports its own width and height, and ysmatrix sizes images and drawing to match. Other
sizes and round panels exist in the app, but none have been tried. Some features (mirror,
transitions, effects) are rejected by the tested firmware and may work on others.

If you try another device, please share the output of `ysmatrix info` and what worked.
