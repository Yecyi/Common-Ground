# Verification record

Verified on 22 October 2026 on Windows 11 with Python 3.14.4 and pygame-ce 2.5.7. This record covers the build after the refinement against `docs/REFINEMENT_PLAN.md`.

The source and the packaged Windows executable (last rebuilt at 22:46 the same day, 36,879,892 bytes, including the background music) both passed the rendered end-to-end smoke playthrough. The packaged executable exited with code 0 after writing all 21 expected screenshots and its verification report. The smoke harness asserts the active screen before each capture and uses temporary saves.

## Automated tests

All 112 automated tests passed: 13 base rule tests, 33 tests for the later chapters, 12 application integration tests and 54 tests for guidance, controls, the living world, sound, music and every screen.

- The base rule checks still exercise 243 combinations of NPC responses and resource decisions, plus 1,080 task-order and decision scenarios. Alternative initial choices retain a recovery path.
- With every optional chapter added, pressuring responses in every scene, the dispute and the plots all still leave a route to the ending on all nine factory and allocation routes. No optional chapter costs supplies.
- A bot that only follows "A thread to follow" reaches the ending on all nine routes. Each suggestion it follows was accepted by the game rather than refused.
- Optional chapters alone cannot unlock the ending, and their prerequisites, repeats and pressuring-response repair are each tested.
- Saves: a version 1 save upgrades on load without changing the caller's data and is written back as version 2; more than a dozen kinds of malformed or inconsistent later-chapter and growth data are rejected; and garden growth survives a save and Continue. The existing `saves/save.json` (format 1) also loaded under the new rules.
- A regression test stands at the front, left, right and back approach of every visible place, with residents at home and at their posts, and checks that pressing E or A would act on that place. It found two cases of my own making during review (Rowan beside the third garden bed and Theo beside the pump), and it fails when the old position is restored. Neighbouring garden beds share their side approaches by design and are excluded.
- Screens: every conversation, outcome panel, quiet place, the map, the ending and its recap render inside the window and keep their buttons on screen at default, larger text and higher contrast. The ending scrolls to show the whole recap.
- Controls and settings: synthesised gamepad events drive the whole interface, a resting stick does not move the character, a failing gamepad is ignored, first-time prompts appear once and are remembered, and every setting fits on its screen.
- Sound: layer volumes were checked as numbers. Machinery follows the mill, the river changes with the repair, tension builds and settles, the melody follows balance, quiet places raise the ambience, and muting silences every layer.
- Background music: trimming the silent tail and softening the edges is tested on synthetic tracks (stereo, mono, odd byte counts, silent and gap-free input) and never changes the source file. With the supplied track, the loop is 46.9 seconds against the file's 53.7, starts and ends at silence so it cannot click, ducks under tension, swells after a supportive choice, softens in quiet places and goes silent when muted. A missing or corrupt file falls back to the generated music layers instead of failing. The packaged executable's smoke test confirms the track loads and plays inside the executable.
- Custom artwork: replacement sprites and tiles load, walking frames can be replaced, and missing, unreadable or absent files fall back to the drawn art.

## Rendered playthrough

- All 24 interaction points were reachable from spawn across 2,513 walkable grid positions. Automated movement followed real routes to all four residents and the quiet places, including the Riverside bridge.
- The complete playthrough covered initial guidance, conversations, both resource dilemmas with their outcome panels, collection, restoration, all four resident scenes, the de-escalation scene (including taking a side and repairing it), the garden plot dilemma, three quiet places, residents walking to their posts, journal, map, hover values at the top of the screen, accessibility settings, the scrolled ending recap, and the deliberate council ending.
- Save checks covered round-trips, Continue, blocked-position recovery, malformed saves, valid and unreadable-save backups, backup failure, and closing title-screen Settings or Help without overwriting progress.
- Default and larger-text screens were inspected as rendered images. Dialogue, result text, journal logs and the ending can scroll. Essential information remains available while muted.
- A smaller window was rendered with letterboxing and mouse-coordinate mapping. Fullscreen has a keyboard toggle.
- Headless drawing and update took about 2.4 ms per frame on the development machine, well within the 16.7 ms budget for 60 frames per second.

Two routes are recorded. They differ only by the optional chapters.

- **Base cooperative route** (no optional chapters): environment 86, equity 84 and resilience 86, with five supplies remaining. This is asserted in `tests/test_state.py`.
- **All chapters taken**: environment 88, equity 100 and resilience 100, with five supplies remaining. Values are capped at 100.

The ending also requires the community milestones; high scores alone cannot end the story.

## Not verified

- **Gamepad hardware.** The gamepad was tested only with synthetic events and fake devices. Button numbers on real controllers, especially non-Xbox ones, can differ from the mapping used here (A=0, B=1, X=2, Y=3, Start=7).
- **Sound by ear.** Levels were computed and sound was exercised under the dummy audio driver. Nobody has listened to the mix or the background music, so loudness, how well the track loops, and the balance against the ambience on real speakers or headphones remain untested. The music's volume (0.30 of full scale, because the track is mastered loudly) was chosen from measured loudness, not by ear.
- **Rights to the music.** The creator and licence of `Video Game BGM.mp3` are not known, so nothing here establishes that it can be shared or published. See `SOURCES.md`.
- **Custom artwork in the packaged executable.** Custom PNG loading was tested from source only. The executable looks for `assets/custom/sprites/` beside itself, which was not exercised inside the frozen build.
- **An interactive window.** The packaged executable was run headless through its smoke test; nobody played it in an open window. Real-display behaviour, such as fullscreen on different monitors, still needs a physical check.
- **Players.** No player has yet used the guidance, the new scenes or the recap. Whether the suggestions are clear, the scenes feel respectful, or the recap prompts reflection needs the feedback process in `CAS_GUIDE.md`.

Re-run `python -m unittest discover -s tests -v` and `python main.py --smoke-test` after changes. To check the packaged app itself, run `Common Ground.exe --smoke-test --capture-dir work/packaged-check` from a terminal. Use the player checklist and actual feedback for CAS impact evidence.
