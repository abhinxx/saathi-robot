# Hardware bring-up — SO-101 on MakerMods Lab

What actually worked, on a MacBook Pro M4 (Apple Silicon), Himalaya Robotics Hack 2026.
Written down because most of it is not in the upstream docs and cost hours to find.

## The rig

| Piece | Value |
|---|---|
| Stack | [`makermodslab`](https://github.com/makermods-robotics/makermodslab) — LeRobot in a browser tab, API + UI on `:8000` |
| Arms | SO-101 leader/follower, Feetech STS3215 servos |
| Robot record | `saathi` |
| Camera | KD-USB, `front`, 640×480 @ 30 |
| Compute | `mps` (the app auto-selects Apple GPU even when a checkpoint says `cuda`) |

## Identify the arms by voltage, not by port order

Port names reshuffle across replugs. Voltage does not:

```bash
curl -s -G localhost:8000/supply-voltage --data-urlencode "port=/dev/tty.usbmodemXXXX"
```

- **~12.4 V → follower** (the robot, black gripper jaws)
- **~7.3 V → leader** (the teleoperator you hold)

Getting this backwards means the wrong calibration is applied and teleop runs
backwards with the arm in your hand energized. The app has an EEPROM identity
guard for exactly this, but voltage is the cheaper check and it never lies.

## The auto-calibration hang

Auto-calibration wedges on a port that has already been opened by a previous
session. It dies here, in
`makermodslab/vendor/feetech_autocal/auto_calibrate_script.py`:

```python
bus.connect(handshake=False)
print("Clearing residual servo state...")   # last line ever printed
for _ in range(3):
    bus.sync_write("Goal_Velocity", all_zero)   # blocks forever
```

Symptoms, all together:

- log stops at `Clearing residual servo state...` (2 log lines, then nothing)
- process CPU time frozen (`0:00.7x`) while wall time climbs
- process state `U` — uninterruptible kernel wait
- **survives `SIGKILL`**; the server logs `Auto-calibration process survived SIGKILL`
- that port's `/supply-voltage` times out from then on

It hangs on the **first write to the servo bus**, before any motion command —
which is why the arm never moves. It is not slow, it is dead.

**Fix: physically unplug that arm's USB and plug it back in.** No amount of
process killing or server restarting clears it; the wedge is below userspace.
Auto-calibration then completes in ~50 s (~187 log lines).

**Do not re-run auto-calibration on an arm that already has a calibration
file.** That is what poisons the port. Calibrate once, then leave it alone.

## Recording silently discards timed-out episodes

The trap that costs you a dataset:

```
⏰ RECORDING PHASE COMPLETED DUE TO TIMEOUT - triggering re-record
```

If an episode reaches `episode_time_s`, it is **thrown away and re-recorded** —
`saved_episodes` stays at 0 while the UI looks busy and healthy. An episode is
only committed if it ends early:

```bash
curl -s -X POST localhost:8000/recording-exit-early
```

Drive each episode for ~14 s, then call that. Five episodes, five saves.

## Policy refs

`/start-inference` rejects a bare model id:

```
{"detail":"Unrecognised policy ref: 'KaiZehaoGe/act_so101_handshake_merged_139'"}
```

It takes a Hub ref or an **absolute local directory**:

```
~/.cache/huggingface/lerobot/makermodslab_models/KaiZehaoGe/act_so101_handshake_merged_139
```

## Camera viewpoint decides whether a policy works

`act_so101_handshake_merged_139` expects `observation.images.front` at
3×480×640. Feeding it the right resolution is not enough — the *viewpoint* has
to match the training data, because ACT does not resize or re-frame anything at
inference.

Pull the real training frames and look at them before guessing:

```bash
curl -sL -o train.mp4 \
  "https://huggingface.co/datasets/KaiZehaoGe/so101_handshake_merged_139/resolve/main/videos/observation.images.front/chunk-000/file-000.mp4"
ffmpeg -i train.mp4 -vf "select='eq(n\,400)'" -vsync 0 -frames:v 1 frame.jpg
```

Those frames show an **arm-mounted** camera: the robot body sits fixed at the
right edge of every frame, and a human hand fills a third of the view at
20–40 cm. A fixed camera watching the table from a metre away — mostly empty
tabletop — is a different distribution, and the policy thrashes on it.

## Serial-port contention

Teleop, recording, and inference each need the follower's serial port
exclusively. Stop one before starting another. A `supply-voltage` read against a
port teleop is holding returns a *motor check failed* error rather than timing
out — that error means the port is alive and busy, which is a healthy sign, not
a fault.

## Frame rate

With two cameras configured the record loop ran at 16–28 Hz against a 30 Hz
target and logged a warning every few seconds. Dropping to the single camera the
policy actually consumes keeps it closer to target. Frames are dropped
otherwise, and the motion gets jerkier.

## Useful endpoints

```bash
curl -s localhost:8000/health
curl -s localhost:8000/available-ports
curl -s localhost:8000/available-cameras
curl -s localhost:8000/robots/saathi
curl -s localhost:8000/calibration-configs/robot     # follower configs
curl -s localhost:8000/calibration-configs/teleop    # leader configs
curl -s localhost:8000/recording-status
curl -s localhost:8000/recording-log
curl -s localhost:8000/inference-status
curl -s localhost:8000/inference-log
```

`is_clean: true` and `follower_ready: true` on the robot record mean every
referenced calibration file exists on disk. If the UI shows *"references a
calibration file that no longer exists"*, the record names a config that was
never written — compare `follower_config` against
`/calibration-configs/robot` and recalibrate or clear the field.
