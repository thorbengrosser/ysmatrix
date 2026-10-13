# Contributing

Thanks for helping! Every kind of contribution is welcome: a short issue saying "works on my
panel", a bug report, a docs fix, or a pull request with a new feature.

## Reporting a device or a bug

Open an issue and include:

- the output of `ysmatrix info` (model, firmware, size)
- what you ran, what you expected and what happened
- for bugs: the output with `-vv`, which shows every frame in hex

## Pull requests

1. `python -m venv .venv && .venv/bin/pip install -e '.[dev]'`
2. Make your change; keep the style of the surrounding code.
3. `.venv/bin/pytest` must pass. The tests replay frames captured from the official app, so a
   protocol change that breaks byte-for-byte compatibility shows up immediately.
4. If you learned something about the protocol, update [docs/status.md](docs/status.md) (what is
   verified, inferred or unknown) and [docs/protocol.md](docs/protocol.md).

Small pull requests are fine; you don't need to open an issue first.

## Evidence, not artifacts

New protocol knowledge is the most valuable contribution. Describe what you observed (frames in
hex, what the panel did) rather than attaching files. **Do not add** the vendor's apps,
decompiled or extracted code, raw Bluetooth captures or vendor media to the repository. See
[how this was reverse-engineered](docs/reverse_engineering.md) for capturing tips.

## Safety

Please don't add commands that can lock users out (firmware update, password, renaming) without
clear evidence they are safe, and mark anything untested as such in `docs/status.md`.
