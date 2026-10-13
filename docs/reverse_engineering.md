# How this was reverse-engineered

There is no public documentation for these panels. The protocol was worked out for
interoperability, in three steps, and each claim in [status.md](status.md) says which kind of
evidence backs it.

1. **Bluetooth captures.** The official iOS app was used normally (power, brightness, uploading
   pictures and a GIF, switching slots) while Apple's *PacketLogger* recorded the Bluetooth traffic.
   Decoding those captures gave the frame format, the checksum and the exact upload sequence.
   ysmatrix's tests rebuild those frames byte for byte.
2. **Studying the official app.** The app is a hybrid web app, so its logic could be read to learn
   which commands exist and how their parameters are laid out. This pointed at text, clock,
   drawing, games, rotation and the time command, none of which were in the captures.
3. **Testing on hardware.** Every feature was then tried on a real panel, with the results
   recorded (including the ones that failed).

## What is *not* in this repository

No copy of the vendor's app, no decompiled or extracted code, no raw capture files and no vendor
media. The documentation and code are original. The test vectors in `tests/vectors.py` are a
handful of protocol frames and a home-made 64×64 test picture, kept small on purpose.
`.gitignore` blocks app packages and capture files so they are not committed by accident.

## Helping out

Useful contributions are new evidence: a capture of the app doing something not yet covered, or a
test on a different panel.

**iOS:** install Apple's Bluetooth logging profile on the phone, record with *PacketLogger* (from
Xcode's Additional Tools) while using the app, and note what you did and when. Do not attach the
capture to a public issue if it contains anything private; describe the frames instead
(`ysmatrix -vv` prints frames in the same hex format).

**Android:** enable *Bluetooth HCI snoop log* in the developer options, use the app, then pull
`btsnoop_hci.log` from a bug report.

Then compare the frames with [the protocol reference](protocol.md), and report what you found
with the panel model and firmware from `ysmatrix info`.
