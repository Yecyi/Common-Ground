"""Run Common Ground, or use --smoke-test for a headless rendered check."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description="Common Ground | A CAS community RPG")
    parser.add_argument("--smoke-test",action="store_true",help="render and validate the game without opening a window")
    parser.add_argument("--capture-dir",type=Path,default=Path("work/screenshots"))
    args=parser.parse_args()
    if args.smoke_test:
        os.environ["SDL_VIDEODRIVER"]="dummy"
        os.environ["SDL_AUDIODRIVER"]="dummy"
        from tools.smoke_test import run
        run(args.capture_dir)
        return
    from game.app import App
    App().run()


if __name__=="__main__":
    main()
