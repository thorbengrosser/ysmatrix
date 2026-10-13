# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Process exits silently, exit code 134 (macOS) | The app running Python has no Bluetooth permission | Run from Terminal/iTerm and allow Bluetooth when asked, or enable it in System Settings → Privacy & Security → Bluetooth |
| `no panel found` | Panel off, out of range, or connected to the phone app | Close the app on the phone; switch the panel off and on; run `ysmatrix scan` |
| Found once, then not anymore | A previous run ended without disconnecting cleanly; the panel still thinks it is connected | Power-cycle the panel |
| `UnsupportedCommand` (error 3) | This firmware does not implement the command (e.g. mirror) | Nothing to fix; see [status.md](status.md) |
| `NoAck` | Weak signal or panel busy | Move closer; retry |
| Drawings appear only every few seconds | Drawing outside drawing mode | Use `panel.drawing()` (or `ysmatrix fill`) |
| Random pixels when drawing fast | Fire-and-forget frames sent with no pause | Keep the default `unacked_gap` (20 ms) |
| Picture looks rotated | Rotation is a stored setting | `ysmatrix rotate` to see it, `ysmatrix rotate <n>` to fix |
| Display stays dark after `power off` | Power-off is separate from what is shown | Showing anything (`image`, `text`, `play`, `loop`…) switches it back on; or `ysmatrix power on` |
| Clock shows the wrong time after a restart | The panel forgets the time when switched off | `ysmatrix sync-time` (or `panel.set_time()`) after powering on |
| A built-in game shows `START` and nothing happens | It waits for the start key | Press `s` in `ysmatrix game`, or `game_key("start")` |
