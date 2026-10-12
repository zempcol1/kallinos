"""Sound effects and music, synthesized in code (no audio files).

Effects are short and rendered at startup. Music tracks are longer loops
rendered in a background thread and turned into sounds on the main thread
(``update``), then played on a reserved channel; a track asked for before
it is ready starts as soon as it is. Instruments: a plucked lyre
(Karplus-Strong), a soft drone, a breathy flute, frame drum and tambourine.
The title uses D Dorian, the battle E Phrygian; the garden and village
are in bright G major.

If no audio device is available, everything here quietly does nothing.
"""

from __future__ import annotations

import math
import operator
import random
import threading
from array import array

import pygame

import settings as s

RATE = s.AUDIO_RATE
_MAX = 32000
_NOTE_NAMES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8,
               "A": 9, "A#": 10, "B": 11}


def _freq(note: str) -> float:
    """'A4' → 440.0; sharps as 'C#5'."""
    name, octave = note[:-1], int(note[-1])
    midi = 12 * (octave + 1) + _NOTE_NAMES[name]
    return 440.0 * 2 ** ((midi - 69) / 12)


# ── Synthesis ────────────────────────────────────────────────────────────────

def _env(n: int, attack: float, decay: float) -> list[float]:
    """Attack (s) then exponential decay with time constant ``decay`` (s)."""
    a = max(1, int(attack * RATE))
    out = []
    for i in range(n):
        t = i / RATE
        level = min(1.0, i / a) * math.exp(-max(0.0, t - attack) / decay)
        out.append(level)
    return out


def _tone(freq: float, seconds: float, wave: str = "sine", attack: float = 0.005,
          decay: float = 0.1, glide: float = 0.0, vibrato: float = 0.0) -> list[float]:
    """An oscillator with an envelope; ``glide`` bends pitch by that factor over the note."""
    n = int(seconds * RATE)
    env = _env(n, attack, decay)
    out, phase = [], 0.0
    for i in range(n):
        t = i / n
        f = freq * (1 + glide * t) * (1 + vibrato * math.sin(i / RATE * math.tau * 6))
        phase = (phase + f / RATE) % 1.0
        if wave == "sine":
            v = math.sin(phase * math.tau)
        elif wave == "triangle":
            v = 4 * abs(phase - 0.5) - 1
        else:  # soft square
            v = math.tanh(math.sin(phase * math.tau) * 3)
        out.append(v * env[i])
    return out


def _drone(freq: float, seconds: float, fade: float) -> list[float]:
    """A steady soft tone ``seconds`` long plus a ``fade`` tail; the tail ramps
    down while the start ramps up, so mixing with wrap crossfades the loop seam."""
    n, f = int(seconds * RATE), int(fade * RATE)
    out = []
    for i in range(n + f):
        level = min(1.0, i / f) if i < n else 1 - (i - n) / f
        phase = (i * freq / RATE) % 1.0
        out.append((4 * abs(phase - 0.5) - 1) * level)
    return out


def _noise(seconds: float, decay: float, smooth: float = 0.5, seed: str = "noise") -> list[float]:
    """Filtered noise; higher ``smooth`` = darker (one-pole low-pass)."""
    rng = random.Random(seed)
    n = int(seconds * RATE)
    env = _env(n, 0.002, decay)
    out, last = [], 0.0
    for i in range(n):
        last = last * smooth + rng.uniform(-1, 1) * (1 - smooth)
        out.append(last * env[i])
    return out


def _pluck(freq: float, seconds: float, damping: float = 0.996, dark: float = 0.5,
           seed: str = "pluck") -> list[float]:
    """Karplus-Strong plucked string: the lyre.

    Each pass averages a sample with its successor, which shortens the loop
    by half a sample, and the delay line only holds whole samples; a
    first-order allpass supplies the fractional rest. Without it, high notes
    come out tens of cents sharp.
    """
    rng = random.Random(f"{seed}{freq:.1f}")
    exact = RATE / freq + 0.5
    period = int(exact)
    frac = exact - period
    if frac < 0.1:                       # keep the allpass well-behaved
        period -= 1
        frac += 1
    c = (1 - frac) / (1 + frac)
    buf, last = [], 0.0
    for _ in range(period):              # a darker pluck: low-passed noise
        last = last * dark + rng.uniform(-1, 1) * (1 - dark)
        buf.append(last)
    out = []
    x1 = y1 = 0.0
    i = 0
    for _ in range(int(seconds * RATE)):
        j = (i + 1) % period
        value = buf[i]
        averaged = (value + buf[j]) * 0.5 * damping
        y = c * averaged + x1 - c * y1
        x1, y1 = averaged, y
        buf[i] = y
        out.append(value)
        i = j
    return out


def _mix_into(target: list[float], part: list[float], start: int, volume: float,
              wrap: bool = False) -> None:
    """Add ``part`` into ``target`` at ``start``; with ``wrap`` the tail loops to the front."""
    n = len(target)
    part = [v * volume for v in part]
    end = min(n, start + len(part))
    target[start:end] = map(operator.add, target[start:end], part[:end - start])
    rest = part[end - start:]
    if wrap and rest:
        k = min(n, len(rest))
        target[:k] = map(operator.add, target[:k], rest[:k])


def _concat(*parts: tuple[list[float], float]) -> list[float]:
    """Sequence parts with given start offsets in seconds."""
    length = max(int(off * RATE) + len(p) for p, off in parts)
    out = [0.0] * length
    for p, off in parts:
        _mix_into(out, p, int(off * RATE), 1.0)
    return out


def _to_bytes(samples: list[float], volume: float = 1.0) -> bytes:
    """Normalize the peak to ``volume`` of full scale and pack as 16-bit signed mono."""
    peak = max((abs(v) for v in samples), default=0.0) or 1.0
    k = _MAX * volume / peak
    return array("h", (int(v * k) for v in samples)).tobytes()


# ── Effects ──────────────────────────────────────────────────────────────────

def _effects() -> dict[str, tuple[list[float], float]]:
    """name → (samples, volume)."""
    croak = []
    for burst in range(2):                         # ribbit: two throaty pulses
        croak += _tone(118 - burst * 14, 0.13, "square", 0.01, 0.07, glide=-0.25,
                       vibrato=0.06) + [0.0] * int(0.04 * RATE)
    victory = _concat(*[(_pluck(_freq(n), 0.9, 0.997), i * 0.11)
                        for i, n in enumerate(("D4", "F#4", "A4", "D5"))],
                      *[(_pluck(_freq(n), 1.6, 0.998), 0.5) for n in ("D4", "F#4", "A4", "D5")])
    defeat = _concat(*[(_pluck(_freq(n), 1.3, 0.997, 0.7), i * 0.38)
                       for i, n in enumerate(("A3", "F3", "D3"))])
    chime = _concat(*[(_tone(_freq(n), 1.6, "sine", 0.004, 0.7), i * 0.16)
                      for i, n in enumerate(("A5", "C#6", "E6", "A6"))])
    return {
        "menu_move": (_tone(1400, 0.04, "square", 0.002, 0.012), 0.18),
        "menu_select": (_concat((_tone(880, 0.07, "triangle", 0.003, 0.04), 0),
                                (_tone(1320, 0.1, "triangle", 0.003, 0.05), 0.06)), 0.3),
        "deny": (_concat((_tone(220, 0.08, "square", 0.002, 0.05), 0),
                         (_tone(180, 0.1, "square", 0.002, 0.06), 0.08)), 0.22),
        "blip": (_tone(760, 0.03, "square", 0.002, 0.01), 0.1),
        "blip_low": (_tone(520, 0.035, "square", 0.002, 0.012), 0.1),
        "blip_high": (_tone(1040, 0.028, "square", 0.002, 0.009), 0.09),
        "blip_soft": (_tone(640, 0.03, "triangle", 0.002, 0.012), 0.08),
        "step": (_noise(0.05, 0.018, 0.75, "step"), 0.16),
        "step_alt": (_noise(0.05, 0.016, 0.8, "step_alt"), 0.14),
        "pickup": (_concat(*[(_tone(f, 0.12, "triangle", 0.003, 0.06), i * 0.06)
                             for i, f in enumerate((1047, 1319, 1568))]), 0.3),
        "harvest": (_concat((_noise(0.12, 0.05, 0.4, "rustle"), 0),
                            (_tone(600, 0.1, "sine", 0.002, 0.05, glide=0.5), 0.08)), 0.3),
        "swoosh": (_noise(0.35, 0.15, 0.6, "swoosh"), 0.25),
        "hit": (_concat((_noise(0.09, 0.03, 0.3, "hit"), 0),
                        (_tone(130, 0.14, "sine", 0.002, 0.06, glide=-0.4), 0)), 0.45),
        "hurt": (_concat((_noise(0.07, 0.03, 0.5, "hurt"), 0),
                         (_tone(90, 0.16, "square", 0.002, 0.07, glide=-0.3), 0)), 0.4),
        "croak": (croak, 0.32),
        "heal": (_concat(*[(_tone(f, 0.25, "sine", 0.004, 0.12), i * 0.07)
                           for i, f in enumerate((784, 988, 1175, 1568))]), 0.28),
        "thud": (_concat((_tone(80, 0.16, "sine", 0.002, 0.07, glide=-0.3), 0),
                         (_noise(0.06, 0.02, 0.7, "thud"), 0)), 0.4),
        "chime": (chime, 0.26),
        "victory": (victory, 0.42),
        "defeat": (defeat, 0.4),
    }


# ── Music ────────────────────────────────────────────────────────────────────

_DRUM = _concat((_tone(82, 0.22, "sine", 0.002, 0.09, glide=-0.35), 0),   # frame drum
                (_noise(0.04, 0.012, 0.85, "drum"), 0))
_TAMB = _noise(0.08, 0.025, 0.05, "tamb")                                    # tambourine
_DRONE_FADE = 2.0   # seconds of crossfade at the loop seam
_DRONE_VOLUME = 0.05

# Each track: tempo, bars of chords (arpeggiated on the lyre), a melody as
# "note:beats" tokens ("-" is a rest), and options.
_TRACKS = {
    "title": {
        "bpm": 72, "drone": ("D3", "A3"),
        "chords": ["D3 A3 D4 F4", "C3 G3 C4 E4", "G2 D3 G3 B3", "D3 A3 D4 F4",
                   "F2 C3 F3 A3", "C3 G3 C4 E4", "G2 D3 G3 B3", "A2 E3 A3 C#4"],
        "melody": "A4:2 D5:2 E5:1 D5:1 C5:2 D5:3 B4:1 A4:4 "
                  "C5:2 F5:2 E5:1 D5:1 E5:2 D5:2 B4:1 G4:1 E5:2 C#5:2",
        "lead": "lyre",
    },
    "garden": {
        "bpm": 96, "drums": True,
        "chords": ["G2 D3 G3 B3", "C3 G3 C4 E4", "G2 D3 G3 B3", "D3 A3 D4 F#4",
                   "E2 B2 E3 G3", "C3 G3 C4 E4", "D3 A3 D4 F#4", "G2 D3 G3 B3"],
        "melody": "D5:1 G5:0.5 F#5:0.5 G5:1 D5:1 E5:1 G5:0.5 E5:0.5 C5:2 "
                  "B4:0.5 C5:0.5 D5:1 G5:1 D5:1 A4:1 B4:0.5 C5:0.5 D5:2 "
                  "E5:1 G5:0.5 F#5:0.5 E5:1 B4:1 C5:1 E5:0.5 D5:0.5 C5:1 E5:1 "
                  "D5:1 F#5:0.5 E5:0.5 D5:1 A4:1 G5:2 -:1 D5:1",
        "lead": "lyre",
    },
    "village": {
        "bpm": 80,
        "chords": ["G2 D3 G3 B3", "C3 G3 C4 E4", "G2 D3 G3 B3", "D3 A3 D4 F#4",
                   "E2 B2 E3 G3", "C3 G3 C4 E4", "A2 E3 A3 C4", "D3 A3 D4 F#4"],
        "melody": "D5:2 B4:1 G4:1 E5:2 C5:2 D5:3 -:1 A4:2 F#4:2 "
                  "B4:2 G4:1 E4:1 C5:2 E5:2 A4:2 C5:1 B4:1 A4:4",
        "lead": "flute",
    },
    "battle": {
        "bpm": 132, "drums": True, "bass": True,
        "chords": ["E2", "E2", "F2", "E2", "A2", "G2", "F2", "E2"],
        "melody": "B4:0.5 C5:0.5 B4:1 -:1 E4:1 E5:1 D5:0.5 C5:0.5 B4:2 "
                  "F5:1 E5:0.5 D5:0.5 C5:1 B4:1 B4:3 -:1 "
                  "A4:0.5 B4:0.5 C5:1 E5:1 D5:1 G5:1 F5:0.5 E5:0.5 D5:2 "
                  "C5:1 B4:0.5 A4:0.5 F4:1 G4:1 E4:4",
        "lead": "lyre",
    },
}


class _NoteCache:
    """Renders each distinct instrument note once."""

    def __init__(self) -> None:
        self._cache: dict[tuple, list[float]] = {}

    def get(self, instrument: str, note: str, seconds: float) -> list[float]:
        key = (instrument, note, round(seconds, 2))
        if key not in self._cache:
            f = _freq(note)
            if instrument == "lyre":
                part = _pluck(f, seconds + 0.6, 0.997)
            elif instrument == "harp":
                part = _pluck(f, seconds + 0.3, 0.995, 0.65)
            elif instrument == "bass":
                part = _pluck(f, seconds + 0.2, 0.993, 0.8)
            elif instrument == "flute":
                part = _tone(f, seconds + 0.25, "triangle", 0.06, seconds * 0.8 + 0.2,
                             vibrato=0.004)
            else:
                raise ValueError(f"Unknown instrument {instrument!r}")
            self._cache[key] = part
        return self._cache[key]


def _render_track(spec: dict) -> bytes:
    beat = 60 / spec["bpm"]
    bars = len(spec["chords"])
    length = int(bars * 4 * beat * RATE)
    out = [0.0] * length
    notes = _NoteCache()

    def at(beats: float) -> int:
        return int(beats * beat * RATE) % length

    if "drone" in spec:
        for note in spec["drone"]:
            _mix_into(out, _drone(_freq(note), bars * 4 * beat, _DRONE_FADE), 0, _DRONE_VOLUME,
                      wrap=True)
    for bar, chord in enumerate(spec["chords"]):
        tones = chord.split()
        if spec.get("bass"):
            root = tones[0]
            octave_up = root[:-1] + str(int(root[-1]) + 1)
            for i, n in enumerate((root, root, octave_up, root, root, root, octave_up, root)):
                _mix_into(out, notes.get("bass", n, beat / 2), at(bar * 4 + i / 2), 0.32,
                          wrap=True)
        else:
            pattern = (tones + tones[-2:0:-1]) * 3      # up and back down, 8 eighths
            for i, n in enumerate(pattern[:8]):
                _mix_into(out, notes.get("harp", n, beat / 2), at(bar * 4 + i / 2), 0.16,
                          wrap=True)
        if spec.get("drums"):
            for b in (0, 2, 2.5) if spec.get("bass") else (0, 2):
                _mix_into(out, _DRUM, at(bar * 4 + b), 0.3, wrap=True)
            for b in (0.5, 1.5, 2.5, 3.5):
                _mix_into(out, _TAMB, at(bar * 4 + b), 0.07, wrap=True)

    position = 0.0
    for token in spec["melody"].split():
        note, length_beats = token.split(":")
        length_beats = float(length_beats)
        if note != "-":
            volume = 0.5 if spec["lead"] == "lyre" else 0.3
            _mix_into(out, notes.get(spec["lead"], note, length_beats * beat), at(position),
                      volume, wrap=True)
        position += length_beats
    return _to_bytes(out, 0.8)


# ── Playback ─────────────────────────────────────────────────────────────────

class Audio:
    """All game sound: ``play`` for effects, ``play_music`` for looping tracks."""

    MUSIC_FADE_MS = 800

    def __init__(self) -> None:
        self.enabled = pygame.mixer.get_init() is not None
        self.muted = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._tracks: dict[str, pygame.mixer.Sound] = {}
        self._rendered: dict[str, bytes] = {}
        self._wanted: str | None = None
        self._playing: str | None = None
        if not self.enabled:
            return
        try:
            pygame.mixer.set_reserved(1)
            self._music_channel = pygame.mixer.Channel(0)
            for name, (samples, volume) in _effects().items():
                self._sounds[name] = self._make_sound(_to_bytes(samples, volume))
        except pygame.error:
            self.enabled = False
            return
        threading.Thread(target=self._render_music, daemon=True).start()

    @staticmethod
    def _make_sound(mono: bytes) -> pygame.mixer.Sound:
        """A Sound from 16-bit mono samples, matching whatever the mixer runs at."""
        rate, _, channels = pygame.mixer.get_init()
        samples = array("h")
        samples.frombytes(mono)
        if rate != RATE:   # the device refused our rate: resample (nearest)
            step = RATE / rate
            samples = array("h", (samples[int(i * step)]
                                  for i in range(int(len(samples) / step))))
        if channels > 1:
            wide = array("h", bytes(len(samples) * 2 * channels))
            for c in range(channels):
                wide[c::channels] = samples
            samples = wide
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _render_music(self) -> None:
        """Background thread: render every track (raw bytes only, no pygame calls)."""
        order = ["title"] + [name for name in _TRACKS if name != "title"]
        for name in order:
            self._rendered[name] = _render_track(_TRACKS[name])

    def update(self) -> None:
        """Main thread, once per frame: adopt rendered tracks, start wanted music."""
        if not self.enabled:
            return
        for name in list(self._rendered):
            self._tracks[name] = self._make_sound(self._rendered.pop(name))
        if self._wanted and self._wanted != self._playing and self._wanted in self._tracks:
            self._music_channel.play(self._tracks[self._wanted], loops=-1,
                                     fade_ms=self.MUSIC_FADE_MS)
            self._music_channel.set_volume(0 if self.muted else s.MUSIC_VOLUME)
            self._playing = self._wanted

    def play(self, name: str, volume: float = 1.0) -> None:
        """Play a sound effect by name."""
        if not self.enabled or self.muted or name not in self._sounds:
            return
        sound = self._sounds[name]
        sound.set_volume(s.SFX_VOLUME * volume)
        sound.play()

    def play_music(self, name: str | None) -> None:
        """Switch to a looping track (None stops the music). Starts once rendered."""
        if not self.enabled or name == self._wanted:
            return
        self._wanted = name
        if self._playing:
            self._music_channel.fadeout(self.MUSIC_FADE_MS // 2)
            self._playing = None

    def stop_music(self, fade_ms: int = 600) -> None:
        if self.enabled:
            self._wanted = None
            self._playing = None
            self._music_channel.fadeout(fade_ms)

    def toggle_mute(self) -> None:
        if not self.enabled:
            return
        self.muted = not self.muted
        self._music_channel.set_volume(0 if self.muted else s.MUSIC_VOLUME)
