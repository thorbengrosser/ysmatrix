# Installation

Requires Python 3.10+ and a computer with Bluetooth LE.

```bash
pip install git+https://github.com/thorbengrosser/ysmatrix
# or, from a checkout:
pip install -e .
```

This installs the `ysmatrix` library and the `ysmatrix` command. Dependencies: [bleak](https://github.com/hbldh/bleak)
(Bluetooth) and [Pillow](https://python-pillow.org) (images).

## Platform notes

| Platform | Notes |
|---|---|
| **macOS** | Run from Terminal, iTerm or another app that has Bluetooth permission (System Settings → Privacy & Security → Bluetooth). Without it the process is killed silently (exit code 134). Addresses are UUIDs, not MAC addresses. |
| **Linux** | Needs BlueZ. Works as a normal user on most distributions. |
| **Windows** | Should work through bleak; untested. `ysmatrix game` needs a Unix terminal. |

## Check it works

1. Switch the panel on and make sure the phone app is **not** connected (a connected panel stops advertising).
2. Run:
```bash
ysmatrix scan
ysmatrix info
```
