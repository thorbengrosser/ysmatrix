# What we know, and what we don't

Everything in ysmatrix was worked out without vendor documentation. This page is the honest
ledger: what has been proven on real hardware, what is only inferred, and what is still unknown.

**Test panel:** 64×64 RGB LED backpack, advertised as `YS…`, model `EXYB-AS#GGMJXZ180`,
firmware `V2.9.1#V16`, controlled by the *LOY PLAY* app. Other panels and firmware may differ.

## Legend

| Mark | Meaning |
|---|---|
| ✅ **Verified** | Works on the test panel. "Byte-identical" means our frames equal the official app's captured frames. |
| 🟡 **Inferred** | Accepted by the panel and visibly works, but parameter meanings are only partly known. |
| ❌ **Unsupported** | The test panel rejects it (ack error 3) or accepts it with no visible effect. |
| ❔ **Unknown** | Exists in the official app but was never tried, or results were inconclusive. |

## Features

| Feature | Status | Notes |
|---|---|---|
| Power on/off | ✅ byte-identical | |
| Brightness 1–15 | ✅ byte-identical | |
| Still image upload | ✅ byte-identical | Palette-indexed `YSTP01` format; stored in a slot; survives power cycles |
| Animated GIF upload | ✅ byte-identical | Sent as the GIF file; the panel decodes it. 284 KB / 155 frames tested |
| Show one slot | ✅ byte-identical | |
| Loop through slots | ✅ byte-identical | Each slot shows for its own play time (3 s for stills by default) |
| List stored slots | ✅ | Empty slots report zeros |
| Device info, panel size | ✅ | |
| Read power/brightness/rotation | ✅ | |
| Rotation | ✅ | Absolute value n×90° clockwise, stored on the panel; the test panel's upright is `2` |
| Set/read clock | ✅ | |
| Scrolling and static text | ✅ | Rendered by the panel's own font; colours correct; sizes 8 and 16 tested |
| Live clock (text with time fields) | ✅ | The panel keeps it ticking |
| Live drawing (rectangles, pixels, 1-bit bitmaps) | ✅ | Only renders immediately in drawing mode (game 16); ~30 fps fire-and-forget |
| Built-in games: Tetris (0), Snake (1) | ✅ | Arrow keys, start, pause, exit work |
| Built-in clock face | 🟡 | A digital face appears; style ids not mapped |
| Text scroll speed | 🟡 | Default byte 9 = the app's default; scale/direction not measured |
| Delete a slot | 🟡 | The app sends it at the start of every upload; never sent alone |
| Mirror | ❌ | Error 3 |
| Transitions between programs | ❌ | Error 3 |
| Built-in light effects | ❌ | Acked, nothing visible |
| Game ids 2–20 | ❌ | Nothing shown |
| Tetris rotation key | ❔ | `up` does not rotate; raw codes 11–43 tried without luck |
| RGB channel order | ❔ | Untested on purpose: may change colours persistently |
| Non-ASCII text | ❔ | Encoded as GB18030 like the app; which glyphs the panel has is unknown |
| Other text animations, font sizes, alignment | ❔ | Parameters exist; only left/top, scroll and static tested |
| Countdown timer | ❔ | The app has one (built-in content type 1); start sequence not worked out |
| Schedules (by date/weekday/time), brightness and power schedules | ❔ | Present in the app; not implemented |
| Several regions per program, borders | ❔ | Present in the app; not implemented |
| Weather/temperature text | ❔ | Present in the app; not implemented |
| Firmware update, password, device rename | ⛔ | Deliberately not implemented: risk of locking yourself out |

## Open protocol questions

- **Content key.** Every upload ends with a 16-byte key. The official app computes it as an MD5
  over its *source* image; we do not have that source, so we write an MD5 of what we send. The
  panel stores the key but never checks it. Side effect: the phone app may treat slots written by
  ysmatrix as "changed".
- **Time year encoding.** A clock set by us reads back as `26` for 2026; a never-set panel read
  back `2000`. Both are handled, but the second form is unexplained.
- **Error codes.** Only `0` (ok) and `3` (not supported) have been seen.
- **Other panel sizes.** Uploads use the size the panel reports, but only 64×64 was tested.

Found something out? Please open an issue or pull request; see
[how this was reverse-engineered](reverse_engineering.md) for how to capture evidence.
