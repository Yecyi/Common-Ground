# Common Ground

A top-down RPG about caring for a community after an industrial spill. Explore the village, listen to its residents, share limited supplies, and restore the places people depend on. Progress comes from cooperation and reflection; there is no combat or time limit.

The game has two parts. **Part One** is the village of Willowmere and its river, and it ends in a balance of nature, fair access and resilience. **Part Two, Storm Season**, begins after that ending, on Hillside, where a storm is coming and there is not enough daylight to prepare for everything.

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
| Journal and objectives | J (Left and Right change page) | X |
| Village map | Tab (click a place or a number to walk there) | Y |
| Pause or go back | Esc | B or Start |
| Mute | M | |
| Fullscreen | F11 | |
| Scroll dialogue, journal or ending | Mouse wheel or Page Up / Page Down | |

The first few times you play, short prompts explain moving, talking and the journal. Hover over a symbol at the top of the screen to see its exact value and goal.

The settings offer larger text, reduced motion, high contrast, gentler movement, and a "Show the way" marker. The marker is a small diamond (or an arrow at the edge of the screen) over the place that "A thread to follow" suggests. Take as long as you need to read or explore. The quiet places have no required timed wait.

## Part One: Willowmere

Restore the environment, strengthen community resilience, and improve equity together. Talk to Mira, Rowan, Amani, and Theo, explore the consequences of the supply and workshop decisions, repair the water source, plant all three shared gardens, and visit the willow refuge. The journal tracks remaining work. Return to the neighbourhood circle when the village is ready to agree on its future.

There is more to find than the goal needs, and none of it costs supplies:

- **Later chapters.** Each of the four residents has more to say as the village changes. Raised voices at the circle and a garden plot dilemma appear as you progress.
- **Hillside.** Walk east past Riverside and the village keeps going: a health post, a common hall, a cottage, an orchard slope and a lookout. Three more neighbours live out here or beside the river, each with three chapters. **Noor** is the community nurse, **Kit** tests the river's water, and **Odile** remembers it before the mill.
- **The river survey.** Kit's three sampling posts show how clear and how safe the river is. The readings change as you decide things, so coming back after a decision tells you what it did to the water.
- **More quiet places**, including a lookout over the whole valley.
- **The journal's other pages.** Besides your choices, the journal lists every neighbour with how far your friendship has grown, and the river readings.

The three symbols at the top show the village's state: a sapling for the environment, a ring of seats around a table for equity, and a lantern for resilience. The village's colours, sounds and small details move with them.

When Part One closes, the ending looks back at who your choices helped and who they left out.

## Part Two: Storm Season

A forecast is pinned at the neighbourhood circle once Part One is complete. A storm is coming, and there are six hours of daylight to share between jobs that all matter: opening the Common Hall as a shelter, clearing Riverside's drains, readying the health post, checking on Odile or Rowan, strapping down the pump, and setting a river gauge with Kit. The jobs add up to more than six hours, so you cannot do everything.

The hours are a choice, not a clock. Nothing counts down, and they only change when you decide something. What you prepared, and which neighbours you have met, shapes the night: who sleeps where, who is found in the dark, which homes take water, and who is left alone. There is no losing. Every route leads through the night to a morning of recovery, and the closing screen looks back at who you reached and who you did not.

## Saves

The game autosaves locally in `saves/save.json`. **Continue** resumes your progress, including journeys saved by earlier versions of the game. Newer saves cannot be opened by older builds. Starting a new game asks first and retains a timestamped backup of the previous journey in `saves/`. Settings are saved in `saves/settings.json`.

## Project files

- `main.py` and `game/`: editable Python source. `game/storm.py` holds Part Two and `game/story.py` the written content.
- `assets/`: original pixel artwork and synthesized audio, with generation tools where applicable.
- `assets/custom/`: put your own hand-made PNGs here to replace the built-in art without touching the code. See `assets/custom/README.md`.
- `assets/music/`: the background track. Swap the file to change the music. It is a supplied recording whose creator and licence are not recorded; see `docs/SOURCES.md` before sharing the game. The GitHub repository does not include the track (see `assets/music/README.md`); the built `Common Ground.exe` does.
- `docs/DESIGN.md`: design decisions and plan coverage.
- `docs/EXPANSION.md`: how Hillside, the new neighbours and Part Two were designed, and the rules they keep.
- `docs/REFINEMENT_PLAN.md`: the plan this version was refined against, with what was done.
- `docs/CAS_GUIDE.md`: prompts for collecting real CAS evidence and player feedback, and an ethics review checklist.
- `docs/SOURCES.md`: research inspiration and asset provenance.
- `docs/PLAYTEST_CHECKLIST.md`: repeatable checks for the finished game.
- `docs/VERIFICATION.md`: what was checked, and how to repeat it.
- `tests/`: automated checks for the game rules, progression and screens.

Run all 195 tests with `python -m unittest discover -s tests -v`. Tests that need the supplied music track skip themselves when it is not installed. The rules include 243 dialogue/decision combinations and 1,080 quest-order scenarios, a check that following the on-screen suggestions reaches both endings on every route, every possible plan for the storm day, and every route through the storm night. Run a rendered playthrough with `python main.py --smoke-test`; it uses a temporary save, walks across the whole village, plays both parts, and produces screenshots and a verification report under `work/screenshots`.

To rebuild the Windows executable after editing, run `powershell -ExecutionPolicy Bypass -File tools/build_windows.ps1`. The build needs an internet connection for PyInstaller if it is not already installed. Original sprites and audio can be regenerated with `python tools/generate_assets.py`.

This implementation follows the supplied **Game design PLAN.docx**. Pygame was chosen because the overview and programming tasks specify a Python 2D RPG, despite a conflicting Unreal Engine 5 heading later in the plan. The existing desktop project was preserved in its separate folder.
