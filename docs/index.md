# ysmatrix

<p align="center">
  <img src="assets/all_your_base_demo.gif" width="300" alt="Animated GIF on a 64x64 LED backpack">
  <img src="assets/led_backpack_photo.jpg" width="300" alt="Picture on the same backpack">
</p>

Unofficial Python library and command-line tool for the Bluetooth RGB LED matrix panels that
advertise as `YS…`/`TL…` (64×64 LED backpacks, bag panels), normally used with the LOY PLAY /
LOY SPACE apps.

* [Which devices?](devices.md)
* [Installation](getting_started/installation.md)
* [Command line](getting_started/cli.md)
* [Library](getting_started/library.md)
* [API reference](reference.md)
* [What we know and don't](status.md)
* [Protocol reference](protocol.md)
* [Troubleshooting](troubleshooting.md)
* [How it was reverse-engineered](reverse_engineering.md)

!!! warning "Unofficial and reverse-engineered: use at your own risk"
    ysmatrix is not made, endorsed or supported by the maker of these panels or of the
    LOY PLAY / LOY SPACE apps. The protocol was worked out by observation, and we cannot rule out
    that some command could misbehave or even brick a device, especially on untested panels or
    firmware. Risky commands (firmware update, password, renaming) are deliberately left out and
    nothing has harmed the test panel so far. Start with `ysmatrix info` and be careful with
    `ysmatrix raw`.

Feedback is welcome: open an issue (bugs, questions, "works on my panel") or send a pull request.
