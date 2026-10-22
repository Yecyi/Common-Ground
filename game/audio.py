"""Quiet synthesized ambience under a supplied background track, with a safe silent-device fallback.

The wind, river, machinery and bird layers are generated here. The background
music is whatever track sits in ``assets/music``; if there is none, or it cannot
be read, the game falls back to the generated harmony, drone and melody layers.
"""
from __future__ import annotations

from array import array
import math
from pathlib import Path
import random
import sys
import wave

import pygame


ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "audio"
MUSIC_DIR = ASSET_DIR.parent / "music"
MUSIC_TYPES = (".mp3", ".ogg", ".wav", ".flac")
RATE = 22050
# The mixer runs at CD rate so a music track keeps its top end; the generated sounds are resampled.
MIXER_RATE = 44100
TRACKS = ("wind", "harmony", "birds", "chime", "machinery", "river_murky", "river_clear", "drone", "melody", "rain")
# Channel 3 is reserved for the short acknowledgement chime.
LAYER_CHANNELS = {"wind": 0, "harmony": 1, "birds": 2, "machinery": 4,
                  "river_murky": 5, "river_clear": 6, "drone": 7, "melody": 8, "rain": 10}
CHIME_CHANNEL = 3
BGM_CHANNEL = 9
# The supplied track is mastered loudly (RMS about 0.18), so it plays well below full volume.
BGM_VOLUME = .30
BGM_FADE_IN_MS = 3000
# Anything quieter than this (about -40 dB) at the end of a track counts as silence when looping.
BGM_SILENCE = .01


def _track(name, seconds=4.0):
    """Generate mono signed 16-bit PCM; all tones are deliberately low-volume."""
    count = int(RATE * seconds)
    out = array("h")
    rng = random.Random(80)
    smooth = 0.0
    fast = slow = 0.0
    tau = math.tau
    for i in range(count):
        t = i / RATE
        if name == "wind":
            smooth = smooth * .94 + rng.uniform(-1, 1) * .06
            v = smooth * .17 + .009 * math.sin(tau * 55 * t) + .006 * math.sin(tau * 82.5 * t)
            v *= .7 + .3 * math.sin(tau * .25 * t) ** 2
        elif name == "harmony":
            v = (.017 * math.sin(tau * 130.75 * t) +
                 .014 * math.sin(tau * 164.75 * t) +
                 .010 * math.sin(tau * 196 * t) +
                 .006 * math.sin(tau * 261.5 * t))
            v *= .75 + .25 * math.sin(tau * .25 * t) ** 2
        elif name == "birds":
            phase = (t + .23) % 1.0
            chirp = max(0.0, 1 - abs(phase - .35) / .14) ** 2
            v = .013 * chirp * math.sin(tau * (1250 * t + 22 * math.sin(tau * 5 * t)))
            v += .003 * math.sin(tau * 440 * t)
        elif name == "machinery":
            # A low hum with a slow mechanical thump every second; the loop is a whole number of beats.
            beat = t % 1.0
            thump = math.exp(-beat * 13) * math.sin(tau * 70 * beat) * .085
            rattle = rng.uniform(-1, 1) * .010 * (.5 + .5 * math.sin(tau * .5 * t))
            v = .018 * math.sin(tau * 55 * t) + .010 * math.sin(tau * 110 * t) + .007 * math.sin(tau * 82.5 * t) + thump + rattle
        elif name == "river_murky":
            smooth = smooth * .985 + rng.uniform(-1, 1) * .015
            v = smooth * .55 * (.8 + .2 * math.sin(tau * .25 * t))
        elif name == "river_clear":
            noise = rng.uniform(-1, 1)
            fast = fast * .78 + noise * .22
            slow = slow * .965 + noise * .035
            bubble = .010 * math.sin(tau * (600 + 150 * math.sin(tau * 3 * t)) * t) * max(0.0, math.sin(tau * 2 * t)) ** 8
            v = (fast - slow) * .32 + bubble
        elif name == "rain":
            # Rain on roofs and leaves: bright hiss with the low rumble taken out, and the odd heavier drop.
            noise = rng.uniform(-1, 1)
            fast = fast * .55 + noise * .45
            slow = slow * .93 + noise * .07
            drops = .02 * max(0.0, math.sin(tau * 7.3 * t + 3 * math.sin(tau * 1.1 * t))) ** 12 * rng.uniform(-1, 1)
            v = (fast - slow) * .30 + drops
        elif name == "drone":
            # A soft low beating pair; whole-number frequencies keep the four-second loop seamless.
            v = (.030 * math.sin(tau * 98 * t) + .024 * math.sin(tau * 103 * t) + .014 * math.sin(tau * 146.5 * t))
            v *= .85 + .15 * math.sin(tau * .5 * t)
        elif name == "melody":
            # A slow pentatonic phrase: each note fades to silence before the next begins.
            slot = int(t)
            freq = (392.0, 440.0, 523.25, 587.33)[slot % 4]
            envelope = math.sin(math.pi * (t - slot)) ** 2
            v = .045 * envelope * (math.sin(tau * freq * t) + .4 * math.sin(tau * 2 * freq * t))
        else:
            # One little rising acknowledgement, no competitive victory fanfare.
            envelope = math.sin(math.pi * min(1, t / seconds)) ** 2
            v = .045 * envelope * (math.sin(tau * 523.25 * t) + .5 * math.sin(tau * 659.25 * t))
        # Soft edges prevent loop clicks, including noise and non-integral pitches.
        edge = min(1, t / .05, (seconds - t) / .05)
        out.append(int(max(-1, min(1, v * edge)) * 32767))
    if sys.byteorder != "little":
        out.byteswap()
    return out.tobytes()


def export_audio(folder=ASSET_DIR):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name in TRACKS:
        target = folder / f"{name}.wav"
        with wave.open(str(target), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(RATE)
            f.writeframes(_track(name, .5 if name == "chime" else 4))


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def find_bgm(folder=MUSIC_DIR):
    """The background track: the first music file, by name, in the folder."""
    try:
        files = sorted(p for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() in MUSIC_TYPES)
    except OSError:
        return None
    return files[0] if files else None


def prepare_loop(raw, channels, rate):
    """Make a track repeat cleanly: drop trailing silence and soften both edges.

    ``raw`` is interleaved signed 16-bit PCM. A song that ends in a long quiet
    tail would otherwise leave a gap before every repeat, and a hard cut would
    click. The last fifty milliseconds of the tail are kept and faded out, and
    the start fades in over ten. The file itself is never changed.
    """
    samples = array("h")
    samples.frombytes(raw[:len(raw) - len(raw) % (2 * channels)])
    floor = int(BGM_SILENCE * 32768)
    end = len(samples)
    while end > 0 and abs(samples[end - 1]) < floor:
        end -= 1
    if end == 0:
        return samples.tobytes()
    end = min(len(samples), end + int(.05 * rate) * channels)
    end -= end % channels
    del samples[end:]
    frames = len(samples) // channels
    fade_in, fade_out = min(frames, int(.01 * rate)), min(frames, int(.05 * rate))
    for frame in range(fade_in):
        for c in range(channels):
            samples[frame * channels + c] = int(samples[frame * channels + c] * frame / fade_in)
    for frame in range(fade_out):
        for c in range(channels):
            index = (frames - 1 - frame) * channels + c
            samples[index] = int(samples[index] * frame / fade_out)
    return samples.tobytes()


class Audio:
    def __init__(self, bgm_file="auto"):
        """``bgm_file`` is a path to the background track, ``None`` for none, or "auto" to use assets/music."""
        self.available = False
        self.bgm_active = False
        self.muted = False
        self.mix = 0.0
        self.tension = 0.0
        self.settle = 0.0
        self.river_clear = 0.0
        self.sounds = {}
        self.channels = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=MIXER_RATE, size=-16, channels=2, buffer=1024)
            pygame.mixer.set_num_channels(max(12, pygame.mixer.get_num_channels()))
            if not all((ASSET_DIR / f"{n}.wav").exists() for n in TRACKS):
                export_audio()
            self.sounds = {name: pygame.mixer.Sound(str(ASSET_DIR / f"{name}.wav")) for name in TRACKS}
            self.channels = {name: pygame.mixer.Channel(index) for name, index in LAYER_CHANNELS.items()}
            for name, channel in self.channels.items():
                channel.set_volume(0)
                channel.play(self.sounds[name], loops=-1)
            self.available = True
            self.start_bgm(find_bgm() if bgm_file == "auto" else bgm_file)
        except (pygame.error, OSError, ValueError):
            # The complete story remains playable without speakers or a device.
            self.available = False

    def start_bgm(self, path):
        """Play the background track on a loop. If it cannot be read, the generated music stays."""
        if not path:
            return
        try:
            rate, _, channels = pygame.mixer.get_init()
            loop = pygame.mixer.Sound(buffer=prepare_loop(pygame.mixer.Sound(str(path)).get_raw(), channels, rate))
            channel = pygame.mixer.Channel(BGM_CHANNEL)
            channel.set_volume(0)
            channel.play(loop, loops=-1, fade_ms=BGM_FADE_IN_MS)
        except (pygame.error, OSError, ValueError, MemoryError):
            return
        self.sounds["bgm"], self.channels["bgm"] = loop, channel
        self.bgm_active = True

    def set_muted(self, value: bool):
        self.muted = bool(value)
        if self.available and self.muted:
            for channel in self.channels.values():
                channel.set_volume(0)
            pygame.mixer.Channel(CHIME_CHANNEL).stop()

    def resolve(self):
        """After a supportive choice the music swells gently for a while as the tension eases."""
        self.settle = 1.0

    def levels(self, health, quiet=False, tension=0.0, zones=None, mill_shared=False, weather="clear"):
        """Target volume for every layer. Quiet places raise the ambience and soften the music.

        With a background track, it carries the music: it ducks while a conversation is tense
        and swells slightly once a supportive choice settles it. Without one, the generated
        harmony, drone and melody layers do the same job.
        """
        zones = zones or {}
        ambient = 1.25 if quiet else 1.0
        music = .4 if quiet else 1.0
        synthesized = not self.bgm_active
        storm = weather == "storm"
        # Weather: steady rain in the storm, a light patter before it and drips after it.
        rain = {"storm": .55, "overcast": .14, "aftermath": .12}.get(weather, 0.0) * ambient
        return {
            "wind": min(1.0, (1 - self.mix) * .42 * ambient + (.28 if storm else 0.0)),
            "harmony": (.15 + self.mix * .60 + .35 * self.settle) * music if synthesized else 0.0,
            "birds": 0.0 if storm else self.mix * .5 * ambient * (.35 + .65 * zones.get("trees", .5)),
            "rain": rain,
            "machinery": .45 * zones.get("mill", 0) * (.4 if mill_shared else 1.0) * ambient,
            "river_murky": .42 * zones.get("river", 0) * (1 - self.river_clear) * ambient,
            "river_clear": .42 * zones.get("river", 0) * self.river_clear * ambient,
            "drone": .34 * self.tension * music if synthesized else 0.0,
            "melody": .40 * clamp((health - .55) / .30) * music if synthesized else 0.0,
            "bgm": 0.0 if synthesized else BGM_VOLUME * (.45 if quiet else 1.0) * (.75 if storm else 1.0) * (1 - .4 * self.tension) + .08 * self.settle,
        }

    def update(self, dt, health, quiet=False, tension=0.0, zones=None, repaired=False, mill_shared=False, weather="clear"):
        if not self.available:
            return
        dt = max(0.0, dt)
        self.mix += (clamp(health) - self.mix) * min(1.0, dt * .65)
        self.tension += (clamp(tension) - self.tension) * min(1.0, dt * 1.2)
        self.settle = max(0.0, self.settle - dt / 6)
        self.river_clear += ((1.0 if repaired else 0.0) - self.river_clear) * min(1.0, dt * .4)
        levels = self.levels(health, quiet, tension, zones, mill_shared, weather)
        for name, channel in self.channels.items():
            channel.set_volume(0 if self.muted else clamp(levels[name]))

    def chime(self):
        if self.available and not self.muted:
            channel = pygame.mixer.Channel(CHIME_CHANNEL)
            channel.set_volume(.32)
            channel.play(self.sounds["chime"])

    def close(self):
        if self.available:
            for channel in self.channels.values():
                channel.stop()
            pygame.mixer.Channel(CHIME_CHANNEL).stop()
