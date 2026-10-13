# Protocol reference

This describes the Bluetooth protocol in our own words, as observed on the wire and confirmed on
a real panel. Status marks follow [status.md](status.md). The code lives in
`ysmatrix/framing.py` (frames), `ysmatrix/commands.py` (payloads) and `ysmatrix/ystp.py` (images).

## 1. Bluetooth LE

| | |
|---|---|
| Advertised name | `YS` or `TL` followed by digits, e.g. `YS525228813` |
| Service | `0000FFF0-0000-1000-8000-00805F9B34FB` |
| Write | `FFF2` (write without response) |
| Notify | `FFF1` (acks and replies) |
| Pairing | none |

The panel reports `MTU:512`; the official app writes up to 509 bytes per BLE packet. A frame may be
split across several writes; the panel reassembles them by the frame length.

The FFF0 service UUID is shared by many unrelated cheap LED gadgets. The `AA 55` frame below is
what identifies this family.

## 2. Frames

```
AA 55 | FF FF | len u16 | sno u16 | type | class | payload … | checksum u16
```

| Field | Meaning |
|---|---|
| `len` | payload length + 6 |
| `sno` | sequence number, echoed in the ack |
| `type` | `C1` = please acknowledge, `81` = fire and forget (bit 7 = checksum present) |
| `class` | `02` command, `03` query; panel replies use `82`/`84` (ack) and `83` (query answer) |
| `checksum` | 16-bit sum of all preceding bytes |

All integers are little-endian.

**Ack:** `AA55 FFFF 0700 <sno> 81 82 <status> <checksum>`. Status `0` = ok, `3` = not supported.
The app sends one frame and waits for its ack (60–250 ms) before the next.

**Fire and forget:** frames of type `81` get no ack. They are fast, but without a pause between
them the panel's input buffer overflows and draws arrive corrupted. ysmatrix waits 20 ms.

## 3. Payload: TLVs

A payload is one or more `tag, length, value` entries. Length is one byte below 128, `81 nn`
below 256, else `82 lo hi`. Several TLVs may share one frame (this is how a draw batch works).

## 4. Commands

| Tag | Command | Value | Status |
|---|---|---|---|
| `04` | power | `00 on` | ✅ |
| `05` | set clock | `year-2000 u16, month, day, h, m, s, ms u16` | ✅ |
| `06` | brightness | `00 level` (1–15) | ✅ |
| `08` | delete slot | `00 slot` | 🟡 |
| `2F` | rotation | `n` (×90° clockwise, absolute, stored) | ✅ |
| `30` | game | `id+128` to start (0 Tetris, 1 Snake, 16 drawing); key codes below | ✅ |
| `32` | live draw | see §7 | ✅ |
| `33` | built-in content | type 0 = clock face `fmt clock date rgb` | 🟡 |
| `36` | play | `mode index ids…` (§6) | ✅ |
| `38` | transition | | ❌ |
| `39` | channel order | | ❔ |
| `3A` | mirror | | ❌ |

Game keys: left 37, up 38, right 39, down 40, start 115, pause 112, done 100, exit 101.

## 5. Uploading content to a slot

The panel stores up to 60 *programs* in slots 0–59. Each upload is a fixed sequence of acked frames:

1. **Create.** `08 02 00 <slot>` (delete) + `09 01 01` + `0C 01 <slot>` + timing `1C 06 00 00 <loops u16> <seconds u16>` +
   `0D 01 00` + region `1D 09 <x y w h u16> 00`. `seconds` is the program's play time in a loop playlist.
2. **Item header.** `09 01 01 0C 01 <slot> 0D 01 00 0E 01 00` + animation `14 03 <type> <speed> <stay>` + item type `11 …`:
   * image/GIF: `11 04 00 <loops u16> 0A`
   * text: `11 0A 00 <loops u16> 06 01 00 <font height> 00 <gap u16>`
3. **Data chunks.** For each 960-byte piece: same prefix + `12 07 <count u16> <index u16> C0 03 00` + `13 <len> <data>`.
4. **Commit.** `35 19 <slot> <prefix u32> <key 16> <unix time u32>`. `prefix` is `slot+1` written as decimal digits
   and read as hex (slot 9 → `10 00 00 00`). For the key, see [status.md](status.md).

Animation types seen: `01` static (images, static text), `00` scroll left (text).

### Image data: `YSTP01`

```
"YSTP01" | width u16 | height u16 | pages u16 | width u16 | bpp u8 | palette | pixels
```

* `bpp` is 1, 2, 4 or 8 with an RGB palette of 2^bpp entries, or 24 for raw RGB.
* The palette lists colours in the order first seen, scanning top-left to bottom-right.
* Rows are top to bottom, each padded to a whole byte; pixels are packed least-significant-bit first.
* `bpp` grows 1 → 2 → 4 → 8 when more than 2, 4, 16 or 256 colours are used.

### GIF data

Animations are uploaded as the GIF file itself, resized to the panel. The panel decodes it.

### Text data

Inline control codes, then the text:

| Code | Meaning |
|---|---|
| `03 00 v` / `03 01 h` | vertical / horizontal alignment (0 start, 1 centre, 2 end) |
| `00 r g b r g b` | text colour, background colour |
| `01 01 00 height` | font (code page 1, font 0, height in pixels) |
| `06 digits field` | live clock field: 0 year, 1 month, 2 day, 3 hour, 4 minute, 5 second |

## 6. Playback

`36 <len> <mode> <index> <ids…>`

* **Single:** mode `01`, all ids `00…3B`, index = slot to show.
* **Loop:** mode `00`, index `FF`, ids = slots to cycle through.

## 7. Live drawing

Send game `16` first (`30 01 90`); only then do draws show up immediately. Leave with key exit (`30 01 65`).
Outside this mode draws only appear when the running program refreshes (about every 3 s).

* Rectangle: `32 0D 01 <rgb> 00 <x0 y0 x1 y1 u16>` (inclusive)
* Bitmap: `32 <len> 00 <rgb> <x0 y0 x1 y1 u16> <rows, MSB first, each padded to a byte>`

Measured: 8 fps with two acked frames per step, 16 fps with erase+draw in one frame, 32 fps fire-and-forget.

## 8. Queries

Send `<tag> <n> <args…>` with class 3. The reply is a class-`83` frame holding a TLV with the same tag;
an empty payload means "not supported".

| Query | Reply |
|---|---|
| `0A 00` device info | ASCII `serial,model,firmware,capabilities…` |
| `1B 00` panel | `00 width u16 height u16 … ` (byte 7 = colour type, 3 = RGB) |
| `04 00` / `06 00` / `2F 00` | power / brightness / rotation |
| `05 00` clock | same layout as setting it |
| `35 <n> <slots…>` | 21 bytes per slot: `slot prefix u32 key 16` (zeros when empty) |
