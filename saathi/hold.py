"""Force-limited hand hold.

The only motion Saathi performs. Close the gripper until it meets resistance,
then stop and keep holding at that opening. Never squeeze harder than the
configured limit, and let go the moment the person pulls away.

Runs against an SO-101 follower over LeRobot, or with --dry-run against a
simulated hand so the loop can be exercised without hardware.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import Optional, Protocol

# Gripper opening in normalised units, 0 closed and 100 open.
OPEN_POSITION = 60.0
FULLY_CLOSED = 0.0

# Present_Load is reported as tenths of a percent of applied torque, signed.
# A human hand is soft, so contact shows up well below the stall value. This
# threshold is deliberately low: squeezing a hand is a failure, not a success.
CONTACT_LOAD = 60.0

# Once holding, a load reading this far below contact means the hand withdrew.
RELEASE_LOAD = 20.0

CLOSE_STEP = 1.5  # normalised units per tick
TICK_HZ = 30.0

# Consecutive ticks required before a state change is believed. At 30 Hz this
# is ~100 ms, enough to reject single-frame noise on the serial bus without
# making the grip feel laggy to the person being held.
DEBOUNCE_TICKS = 3


class Gripper(Protocol):
    """The two operations this behaviour needs from any arm."""

    def read_load(self) -> float: ...

    def write_position(self, position: float) -> None: ...


@dataclass
class HoldResult:
    contacted: bool
    grip_position: Optional[float]
    hold_seconds: float
    released_by_person: bool


class SimulatedGripper:
    """A hand that is present between two opening values.

    Used by --dry-run and by the self-check. Load rises as the gripper closes
    past the point where it first meets the hand, which is the behaviour the
    controller has to cope with on real hardware.
    """

    def __init__(self, hand_at: float = 30.0, withdraw_after: Optional[float] = None):
        self.hand_at = hand_at
        # Seconds of contact before the hand is pulled away. Measured from
        # first contact, not from startup, so a test can set it without
        # having to know how long the closing sweep takes.
        self.withdraw_after = withdraw_after
        self.position = OPEN_POSITION
        self._contact_seconds = 0.0
        self._touched = False

    def read_load(self) -> float:
        if self.position >= self.hand_at:
            return 0.0
        self._touched = True
        self._contact_seconds += 1.0 / TICK_HZ
        if self.withdraw_after is not None and self._contact_seconds > self.withdraw_after:
            return 0.0
        # Soft tissue: load climbs roughly linearly with how far past contact
        # the gripper has travelled.
        return (self.hand_at - self.position) * 40.0

    def write_position(self, position: float) -> None:
        self.position = position


class LeRobotGripper:
    """Adapter onto a LeRobot follower arm.

    Imported lazily so the module and its self-check stay usable on a machine
    with no robot attached and no lerobot installed.
    """

    def __init__(self, port: str, robot_id: str, robot_type: str = "so101_follower"):
        from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

        config = SO101FollowerConfig(port=port, id=robot_id)
        self._robot = SO101Follower(config=config)
        self._robot.connect(calibrate=False)
        self._bus = self._robot.bus

    def read_load(self) -> float:
        raw = self._bus.read("Present_Load", "gripper", normalize=False)
        # Bit 10 is the direction flag, not part of the magnitude. Without
        # masking it a joint at rest reads 1000 instead of 0.
        return float(int(raw) & 0x3FF)

    def write_position(self, position: float) -> None:
        self._robot.send_action({"gripper.pos": position})

    def close(self) -> None:
        self._robot.disconnect()


def hold_hand(
    gripper: Gripper,
    on_contact=None,
    hold_seconds: float = 20.0,
    contact_load: float = CONTACT_LOAD,
) -> HoldResult:
    """Close until resistance, hold, and release when the person withdraws.

    Returns without ever having commanded a position past the point of
    contact, which is what keeps this safe to put a hand into.
    """
    tick = 1.0 / TICK_HZ
    position = OPEN_POSITION
    contact_streak = 0

    while position > FULLY_CLOSED:
        gripper.write_position(position)
        if gripper.read_load() >= contact_load:
            contact_streak += 1
            if contact_streak >= DEBOUNCE_TICKS:
                break
        else:
            contact_streak = 0
            position -= CLOSE_STEP
        time.sleep(tick)

    if contact_streak < DEBOUNCE_TICKS:
        # Travelled the whole range and never met anything.
        gripper.write_position(OPEN_POSITION)
        return HoldResult(False, None, 0.0, False)

    grip = position
    if on_contact is not None:
        on_contact()

    started = time.monotonic()
    gone_streak = 0
    released = False
    while time.monotonic() - started < hold_seconds:
        gripper.write_position(grip)
        if gripper.read_load() <= RELEASE_LOAD:
            gone_streak += 1
            if gone_streak >= DEBOUNCE_TICKS:
                released = True
                break
        else:
            gone_streak = 0
        time.sleep(tick)

    gripper.write_position(OPEN_POSITION)
    return HoldResult(True, grip, time.monotonic() - started, released)


def _self_check() -> None:
    """Smallest thing that fails if the hold logic breaks."""
    # Finds a hand and never closes past it.
    sim = SimulatedGripper(hand_at=30.0)
    result = hold_hand(sim, hold_seconds=0.2)
    assert result.contacted, "failed to detect a hand that was present"
    assert result.grip_position is not None
    assert result.grip_position >= 30.0 - CLOSE_STEP * DEBOUNCE_TICKS, (
        "closed too far past contact: %s" % result.grip_position
    )

    # Empty gripper: closes fully, reports nothing, returns to open.
    empty = SimulatedGripper(hand_at=-1.0)
    assert not hold_hand(empty, hold_seconds=0.2).contacted, "reported contact on empty air"
    assert empty.position == OPEN_POSITION, "did not reopen after finding nothing"

    # Hand withdrawn while being held: notice and let go.
    leaving = SimulatedGripper(hand_at=30.0, withdraw_after=0.5)
    assert hold_hand(leaving, hold_seconds=10.0).released_by_person, (
        "did not notice the hand withdrawing"
    )

    print("self-check ok")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="simulated hand, no hardware")
    parser.add_argument("--self-check", action="store_true", help="run assertions and exit")
    parser.add_argument("--port", default="/dev/tty.usbmodem58FA0829721")
    parser.add_argument("--id", dest="robot_id", default="saathi")
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--quiet", action="store_true", help="do not speak on contact")
    args = parser.parse_args()

    if args.self_check:
        _self_check()
        return

    speak = None
    if not args.quiet:
        from saathi.voice import Reassurance

        speak = Reassurance().start

    if args.dry_run:
        gripper: Gripper = SimulatedGripper()
        result = hold_hand(gripper, on_contact=speak, hold_seconds=args.seconds)
    else:
        arm = LeRobotGripper(port=args.port, robot_id=args.robot_id)
        try:
            result = hold_hand(arm, on_contact=speak, hold_seconds=args.seconds)
        finally:
            arm.close()

    if not result.contacted:
        print("no hand found")
    else:
        print(
            "held at %.1f for %.1fs%s"
            % (
                result.grip_position,
                result.hold_seconds,
                " (they pulled away)" if result.released_by_person else "",
            )
        )


if __name__ == "__main__":
    main()
