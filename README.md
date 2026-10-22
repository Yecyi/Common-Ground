# Common Ground

A small, complete top-down RPG about caring for a community after an industrial spill. Explore the village, listen to its residents, share limited supplies, and restore the places people depend on. Progress comes from cooperation and reflection; there is no combat or time limit.

## Play

Double-click **Common Ground.exe** in this folder to play without installing Python. The game runs offline and stores progress beside the executable.

**Play Common Ground.cmd** opens the executable when it is present. Double-click **Run from source.cmd** to run your edited Python version using the included local environment. If no executable is present, the Play launcher can set up a Python environment and install the single dependency; initial setup may need an internet connection.

To run from a terminal with Python 3.10 or later:

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Controls

| Action | Keyboard and mouse | Gamepad |
| --- | --- | --- |
| Move | WASD or arrow keys | Left stick or d-pad |
| Walk to a visible place | Left-click the ground or an object | |
| Talk or interact | E or Space | A |
| Menu selection or continue | Enter; mouse buttons also work | A (d-pad up and down to choose) |
| Choose a dialogue response | Number keys 1 to 9 or mouse | d-pad, then A |
| Journal and objectives | J | X |
| Village map | Tab | Y |
| Pause or go back | Esc | B or Start |
| Mute | M | |
| Fullscreen | F11 | |
| Scroll dialogue, journal or ending | Mouse wheel or Page Up / Page Down | |

The first few times you play, short prompts explain moving, talking and the journal. Hover over a symbol at the top of the screen to see its exact value and goal.

The settings offer larger text, reduced motion, high contrast, gentler movement, and a "Show the way" marker. The marker is a small diamond (or an arrow at the edge of the screen) over the place that "A thread to follow" suggests. Take as long as you need to read or explore. The quiet places have no required timed wait.

## Your goal

Restore the environment, strengthen community resilience, and improve equity together. Talk to Mira, Rowan, Amani, and Theo, explore the consequences of the supply and workshop decisions, repair the water source, plant all three shared gardens, and visit the willow refuge. The journal tracks remaining work. Return to the neighbourhood circle when the village is ready to agree on its future.

There is more to find than the goal needs. Residents have later chapters that open as the village changes. Raised voices at the circle, a garden plot dilemma, and two more quiet places appear as you progress. None of them costs supplies or is required, but they change the ending. When the story closes, the ending looks back at who your choices helped and who they left out.

The three symbols at the top show the village's state: a sapling for the environment, a ring of seats around a table for equity, and a lantern for resilience. The village's colours, sounds and small details move with them.

The game autosaves locally in `saves/save.json`. **Continue** resumes your progress, including journeys saved by earlier versions of the game. Starting a new game asks first and retains a timestamped backup of the previous journey in `saves/`. Settings are saved in `saves/settings.json`.

## Project files

- `main.py` and `game/`: editable Python source.
- `assets/`: original pixel artwork and synthesized audio, with generation tools where applicable.
- `assets/custom/`: put your own hand-made PNGs here to replace the built-in art without touching the code. See `assets/custom/README.md`.
- `assets/music/`: the background track. Swap the file to change the music. It is a supplied recording whose creator and licence are not recorded; see `docs/SOURCES.md` before sharing the game. The GitHub repository does not include the track (see `assets/music/README.md`); the built `Common Ground.exe` does.
- `docs/DESIGN.md`: design decisions and plan coverage.
- `docs/REFINEMENT_PLAN.md`: the plan this version was refined against, with what was done.
- `docs/CAS_GUIDE.md`: prompts for collecting real CAS evidence and player feedback, and an ethics review checklist.
- `docs/SOURCES.md`: research inspiration and asset provenance.
- `docs/PLAYTEST_CHECKLIST.md`: repeatable checks for the finished game.
- `docs/VERIFICATION.md`: what was checked, and how to repeat it.
- `tests/`: automated checks for the game rules, progression and screens.

Run all 112 tests with `python -m unittest discover -s tests -v`. The rules include 243 dialogue/decision combinations and 1,080 quest-order scenarios, a check that following the on-screen suggestions reaches the ending on all nine decision routes, and checks that every optional chapter stays recoverable. Run a rendered playthrough with `python main.py --smoke-test`; it uses a temporary save and produces screenshots and a verification report under `work/screenshots`.

To rebuild the Windows executable after editing, run `powershell -ExecutionPolicy Bypass -File tools/build_windows.ps1`. The build needs an internet connection for PyInstaller if it is not already installed. Original sprites and audio can be regenerated with `python tools/generate_assets.py`.

This implementation follows the supplied **Game design PLAN.docx**. Pygame was chosen because the overview and programming tasks specify a Python 2D RPG, despite a conflicting Unreal Engine 5 heading later in the plan. The existing desktop project was preserved in its separate folder.
