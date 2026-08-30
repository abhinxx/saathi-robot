"""Reassurance while holding.

The robot speaks Nepali, on device, with no network. That is not a preference:
the Bhote Koshi valley has no working connectivity, so a cloud voice assistant
is not a degraded option there, it is a non-functional one.

Playback runs on its own thread so speaking never blocks the hold loop. If the
grip has to react to someone pulling away, it cannot be waiting on audio.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import threading
from pathlib import Path
from typing import List, Optional

PHRASES_DIR = Path(__file__).resolve().parent.parent / "phrases"

# Said on a loop, in order, while contact is held. Short lines, because
# someone under rubble is in pain and frightened and cannot follow sentences.
# Romanised here for the repo; the audio files carry the real Nepali.
LINES: List[str] = [
    ("ma yahaa chu", "I am here."),
    ("uddhaar aayirakheko chha", "Rescue is coming."),
    ("mero haat chhod-nu-hos na", "Do not let go of my hand."),
    ("saas pheri rahanuhos", "Keep breathing."),
    ("timi eklai chhainau", "You are not alone."),
]

GAP_SECONDS = 6.0


def _player() -> Optional[List[str]]:
    """The system audio player, or None if there isn't one."""
    if platform.system() == "Darwin" and shutil.which("afplay"):
        return ["afplay"]
    for candidate in (["paplay"], ["aplay"], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]):
        if shutil.which(candidate[0]):
            return candidate
    return None


class Reassurance:
    """Loops the phrase list until stopped."""

    def __init__(self, phrases_dir: Path = PHRASES_DIR, gap: float = GAP_SECONDS):
        self.phrases_dir = phrases_dir
        self.gap = gap
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _run(self) -> None:
        player = _player()
        index = 0
        while not self._stop.is_set():
            romanised, english = LINES[index % len(LINES)]
            audio = self.phrases_dir / ("%s.wav" % romanised.replace(" ", "_"))
            print("[saathi] %s  (%s)" % (romanised, english))
            if player is not None and audio.exists():
                try:
                    subprocess.run(
                        player + [str(audio)],
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except OSError:
                    pass
            index += 1
            self._stop.wait(self.gap)


def _self_check() -> None:
    """Starting and stopping must not hang or raise, with or without audio files."""
    r = Reassurance(phrases_dir=Path("/nonexistent"), gap=0.05)
    r.start()
    r.start()  # idempotent
    import time

    time.sleep(0.2)
    r.stop()
    assert r._thread is None, "thread was not joined on stop"
    print("self-check ok")


if __name__ == "__main__":
    _self_check()
