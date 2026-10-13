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

## Sold under many names

The same kind of panel is sold by many brands, usually as a "LED backpack", "pixel backpack" or
"programmable LED display backpack". What they share is the app the seller tells you to use:
**LOY PLAY** or **LOY SPACE** (some sellers just call it **LOY**).

| Status | Meaning |
|---|---|
| ✅ **Tested** | Used with ysmatrix; see [status.md](status.md) for exactly what works |
| 🟡 **Possibly working** | Sold for use with the LOY PLAY / LOY SPACE apps, but nobody has tried ysmatrix with it yet |
| ❔ **Not covered** | Uses a different app, probably a different protocol |

<img src="assets/led_backpack_photo.jpg" width="320" alt="The tested Urbanfeel LED backpack showing a picture sent with ysmatrix">

| Product | App named by the seller | Screen | Status |
|---|---|---|---|
| [Urbanfeel LED Backpack "Umeko"](https://superskunk.es/tiendasonline/en/urbanfeel/urbanfeel-led-backpack-umeko-light-blue/13425) (light blue; also black and pink) | LOY PLAY | 64×64 | ✅ **Tested**: model `EXYB-AS#GGMJXZ180`, firmware `V2.9.1#V16` |
| [Gelrova LED Backpack](https://www.gelrova.com/products/gelrova-led-backpack-city-series) (City series and others) | "LOY" ([download page](https://www.gelrova.com/pages/app-download)) | | 🟡 Possibly working |
| [Taysem Customizable Smart LED Backpack](https://www.amazon.com/Taysem-Customizable-Smart-LED-Backpack/dp/B0FKN71KFX) (T3) | LOY SPACE / LOY PLAY | 64×64 | 🟡 Possibly working |
| [BIOSLED LOY Customizable LED Display Laptop Backpack](https://www.pbtech.co.nz/product/NBGBSD0001/BIOSLED-LOY-Customizable-LED-Display-Laptop-Backpa) (T3-1) | LOY SPACE | 64×64 | 🟡 Possibly working |
| [LOY Bags T3-HD Backpack](https://www.loybags.com.au/) | LOY SPACE | | 🟡 Possibly working |
| [SASKATE Full Color LED Backpack](https://www.amazon.ca/Color-Backpack-Screen-Customizable-Animation/dp/B0F7J34Y2D) | LOY SPACE | 64×64 | 🟡 Possibly working |
| Kemimoto LED Backpack ([setup video](https://www.youtube.com/watch?v=T7WNSyI1ML4)) | LOY SPACE | | 🟡 Possibly working |
| Unbranded "LOY LED Backpack" listings (e.g. [Curacao](https://icuracao.com/products/loy-led-backpack), [eBay](https://www.ebay.com/itm/235373614884)) | LOY / LOY SPACE | 64×64 (some 48×48) | 🟡 Possibly working |
| "Knight" backpacks with LED eyes (e.g. [LOY Bags Knight](https://www.loybags.com.au/), [KWQ Rainbow Knight](https://www.amazon.com/Smart-Backpack-School-Laptop-Christmas/dp/B0C8K17LP3)) | LOY EYES | eyes only | ❔ Not covered; try [pypixelcolor](https://github.com/lucagoc/pypixelcolor) |
| Backpacks with their own apps (e.g. Divoom, PIX) | own app | | ❔ Not covered |

**Looking for LOY EYES (LED-eyes bags)?** ysmatrix does not speak their protocol. They may be
iPixel-style devices, which [pypixelcolor](https://github.com/lucagoc/pypixelcolor) supports. This
is unconfirmed, but it is the place to look.

The "T3" name turns up under several brands (Taysem, BIOSLED, LOY Bags), so these are probably
the same bag from one factory. Links are to listings found online in October 2026 and may
change. Brand names are only used to identify products; none of these companies are involved
with ysmatrix.

**Tried one?** Please [open a device report](https://github.com/thorbengrosser/ysmatrix/issues/new?template=device_report.md)
with the output of `ysmatrix info`, whether it works or not, so the table can be updated.

## Other sizes and firmware

The panel reports its own width and height, and ysmatrix sizes images and drawing to match.
48×48 versions are sold and round panels exist in the app, but none have been tried. Some features (mirror,
transitions, effects) are rejected by the tested firmware and may work on others.

If you try another device, please share the output of `ysmatrix info` and what worked.
