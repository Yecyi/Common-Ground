"""Regenerate the project's editable procedural art and original WAV sounds."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame
from game.art import Art
from game.audio import export_audio

if __name__ == "__main__":
    Art().export_assets(ROOT / "assets" / "sprites")
    export_audio(ROOT / "assets" / "audio")
    print("Original sprites and soundscapes regenerated in assets/.")
