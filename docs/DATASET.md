# Dataset — `saathi_handshake`

Teleoperated handshake episodes recorded on the SO-101 pair during the
Himalaya Robotics Hack, 30 August 2026.

```
abhinxx/saathi_handshake_20260830_182138
```

| | |
|---|---|
| Episodes | 5 |
| Frames | 2,358 |
| FPS | 30 |
| Camera | `observation.images.front`, 640×480 |
| State / action | 6-DOF each |
| Duration | ~79 s of footage |
| Task label | `handshake` |

## What's in this repo

```
dataset/
├── meta/
│   ├── info.json        schema, fps, feature list
│   ├── stats.json       per-feature mean/std/min/max
│   ├── tasks.parquet    task index
│   └── episodes/chunk-000/file-000.parquet
└── data/chunk-000/file-000.parquet    joint states + actions, all 5 episodes
```

The original `videos/` payload is a 114 MB MP4 — over GitHub's 100 MB per-file
limit, so it is **not** committed raw. A compressed copy of the same 2,358
frames is at [`media/teleop_handshake.mp4`](../media/teleop_handshake.mp4)
(3.3 MB, CRF 30, identical framing and length).

To train against this you need the full-resolution video. Re-record it, or ask
for the original.

## Features

| Key | Shape | Meaning |
|---|---|---|
| `action` | 6 | commanded joint positions (from the leader) |
| `observation.state` | 6 | measured follower joint positions |
| `observation.images.front` | 3×480×640 | front camera frame |
| `timestamp`, `frame_index`, `episode_index`, `index`, `task_index` | — | LeRobot bookkeeping |

## How it was recorded

Leader/follower teleoperation — a human drives the leader arm, the follower
mirrors it, and both the camera and joint states are captured at 30 Hz.

```bash
curl -s -X POST localhost:8000/start-recording -H 'Content-Type: application/json' -d '{
  "leader_port":"/dev/tty.usbmodem...", "follower_port":"/dev/tty.usbmodem...",
  "leader_config":"saathi_leader", "follower_config":"saathi_follower",
  "mode":"single", "robot_name":"saathi",
  "dataset_repo_id":"abhinxx/saathi_handshake",
  "single_task":"handshake",
  "num_episodes":5, "episode_time_s":30, "reset_time_s":10, "fps":30
}'
```

**Every episode must be ended early or it is discarded** — see
[HARDWARE.md](HARDWARE.md#recording-silently-discards-timed-out-episodes).

```bash
curl -s -X POST localhost:8000/recording-exit-early
```

## Honest note

These are teleoperated demonstrations, not autonomous behaviour. The arm is
doing exactly what a human hand told it to do through the leader. That is the
point of a demonstration dataset, but it should not be described as the robot
handshaking on its own.
