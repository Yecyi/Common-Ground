# Verification record

Verified on 22 October 2026 on Windows 11 with Python 3.14.4 and pygame-ce 2.5.7. This record covers the build after Hillside, the three new neighbours, the river survey and Part Two: Storm Season were added (see `EXPANSION.md`).

The source and the packaged Windows executable (last rebuilt at 23:40 the same day, 37,124,092 bytes, including the background music) both passed the rendered end-to-end playthrough. The packaged executable exited with code 0 after writing all 36 expected screenshots and its verification report, 21 named checks in all, and reported that the background music was loaded. The playthrough asserts the active screen before each capture and uses temporary saves.

## Automated tests

All 195 automated tests passed, in these files:

| File | Tests | What it covers |
| --- | --- | --- |
| `test_state.py` | 13 | The original rules: completion, finite supplies, one-time rewards, decisions and recovery, save validation |
| `test_later_scenes.py` | 33 | The four residents' later chapters, the circle dispute, garden plots, hints, save versions 1 to 2, growth |
| `test_expansion.py` | 46 | The new neighbours, the river survey, bonds, Part Two's rules, its saves, the lookout |
| `test_app.py` | 12 | The application: saving, backups, endings |
| `test_experience.py` | 54 | Guidance, controls, settings, custom art, the living world, sound, music and every original screen |
| `test_hillside.py` | 37 | Hillside, the weather, Part Two in the application, the map, the journal pages, saves on Hillside, the rain |

The checks that matter most:

- The base rule checks still exercise 243 combinations of NPC responses and resource decisions, plus 1,080 task-order and decision scenarios. Alternative initial choices retain a recovery path.
- With every optional chapter added, pressuring responses in every scene, the dispute and the plots all still leave a route to the ending on all nine factory and allocation routes. No optional chapter costs supplies, and none of Part Two touches supplies.
- A bot that only follows "A thread to follow" reaches the first ending on all nine routes, and a second one follows the suggestions through Part Two to its end. Each suggestion it follows was accepted by the game rather than refused.
- **Every possible plan for the storm day** (every set of jobs that fits in six hours, over a hundred) leads through the night and recovery to the closing screen, and each ends in a save that round-trips. **Every route through the night** (all 81 combinations of responses, with three different plans) does too.
- The hours stay put: waiting an hour of play time changes nothing, and a job that does not fit is refused with nothing spent. Jobs involving neighbours you have not met are not offered.
- What was prepared changes what the night does. A prepared Hall reaches more people in the bed outcome panel; clearing the drains keeps Riverside dry; sandbags save one home; a neighbour left alone is remembered. The tolls and recovery keep every value between 0 and 100.
- Saves: a version 1 or 2 save upgrades on load without changing the caller's data; garden and orchard growth survive; a save at every stage of Part Two round-trips; more than two dozen kinds of malformed or inconsistent data are rejected, including chapters that skip their conditions, more than six hours of jobs, scenes out of order, and recovery before the night ends. A save from a future version is refused.
- **A fix to an older bug.** A saved ending used to require the three values to still be at their goals. A pressuring reply after the ending, or the storm, could lower one and make the journey unloadable. The check now only requires the milestones, and there is a regression test. The same bug exists in the build that was first pushed to GitHub.
- The "nearest place" rule holds on Hillside too: standing at the front, side or back of any visible place, in both resident layouts, pressing E would act on that place. A regression test checks this for all of them.
- Screens: every conversation, outcome panel, quiet place, the map (including clicking a numbered marker), all three journal pages, and both endings render inside the window at default, larger text and higher contrast, and scroll to show everything.
- Weather: every phase draws with and without reduced motion and high contrast; the windows are lit only during the night; cots and sandbags appear with the matching jobs; the orchard appears when planted and grows.
- Sound: rain follows the weather and has its own channel; the storm silences the birds, raises the wind and sits the music back; every level stays in range; muting silences every layer.
- Background music: the loop is trimmed and its edges softened without changing the source file; it ducks under tension, swells after a supportive choice and softens in quiet places; a missing or corrupt track falls back to the generated music.

### Without the music track

The supplied track is not in the GitHub repository. With it removed from `assets/music/`, the whole suite runs 195 tests and passes with 5 skipped (the tests that are about the track itself), and the source playthrough passes with `background_music` false, on the generated music. With the track present, none are skipped.

## Rendered playthrough

- All 35 interaction points were reachable on foot from spawn across 4,220 walkable grid positions, including every place on Hillside, the three sampling posts and the Part Two places.
- The playthrough walks the real routes, with real keyboard and click input, through both parts: the original conversations, both resource dilemmas, collection and restoration, all four residents' later chapters, the circle dispute (including taking a side and repairing it), garden plots, three quiet places; then Hillside, meeting Noor, Kit and Odile, three river readings, further chapters, the lookout, the journal's three pages and the map; then Part Two, reading the forecast, planning the day at the Hall (including a job that does not fit), the whole storm night, the morning after, recovery and the closing screen and its scrolled recap.
- Save checks covered round-trips, Continue, blocked-position recovery (including on Hillside), malformed saves, valid and unreadable-save backups, backup failure, and closing title-screen Settings or Help without overwriting progress. The save written at the end of Part Two was loaded and compared with the live state.
- Default and larger-text screens were inspected as rendered images. Dialogue, result text, journal pages and the endings can scroll. Essential information remains available while muted.
- A smaller window was rendered with letterboxing and mouse-coordinate mapping. Fullscreen has a keyboard toggle.

Two Part One routes are recorded. They differ only by the optional chapters.

- **Base cooperative route** (no optional chapters): environment 86, equity 84 and resilience 86, with five supplies remaining. This is asserted in `tests/test_state.py`.
- **All Part One chapters taken**: environment 88, equity 100 and resilience 100, with five supplies remaining. Values are capped at 100.

The first ending also requires the community milestones; high scores alone cannot end the story.

## Speed

Measured headless under SDL's dummy video driver, so a real display adds its own cost. Updating and drawing a frame took 2.2 ms in Willowmere in clear weather, 1.6 ms on Hillside, and 2.4 ms on Hillside in the storm (150 rain lines and the tint), against 16.7 ms for 60 frames per second. Scaling a frame into a hidden window took about 1.1 ms. Starting the game, including building both 1,760-pixel-wide village backgrounds, took 0.12 s.

## Not verified

- **Players.** No player has used any of this yet: Hillside, the neighbours, the survey, the bonds, or Part Two. Whether the new scenes feel respectful, whether the storm day feels like a real choice, and whether the recaps prompt reflection need the feedback process in `CAS_GUIDE.md`.
- **Part Two in a real window.** Nobody has played Part Two interactively. The playthrough drives the real screens and input headlessly, but whether the hours feel like a choice, whether the night reads well, and whether the pacing works are untested by a person. The packaged executable was only run through its smoke test.
- **The people the scenes portray.** The scenes about a nurse, a teenager and an elder were written without input from anyone like them, and have not been reviewed by a nurse, a counsellor or a young person. `CAS_GUIDE.md` has prompts for that review.
- **Gamepad hardware.** The gamepad was tested only with synthetic events and fake devices. Button numbers on real controllers, especially non-Xbox ones, can differ from the mapping used here (A=0, B=1, X=2, Y=3, Start=7).
- **Sound by ear.** Levels were computed and sound was exercised under the dummy audio driver. Nobody has listened to the rain, the storm mix, the background music or how well it loops, so loudness and balance on real speakers or headphones remain untested. The music's volume (0.30 of full scale, because the track is mastered loudly) was chosen from measured loudness, not by ear.
- **Rights to the music.** The creator and licence of `Video Game BGM.mp3` are not known, so nothing here establishes that it can be shared or published. See `SOURCES.md`.
- **Custom artwork in the packaged executable.** Custom PNG loading was tested from source only. The executable looks for `assets/custom/sprites/` beside itself, which was not exercised inside the frozen build.
- **A real display.** Fullscreen on different monitors and the real cost of presenting frames still need a physical check.

Re-run `python -m unittest discover -s tests -v` and `python main.py --smoke-test` after changes. To check the packaged app itself, run `Common Ground.exe --smoke-test --capture-dir work/packaged-check` from a terminal. Use the player checklist and actual feedback for CAS impact evidence.
