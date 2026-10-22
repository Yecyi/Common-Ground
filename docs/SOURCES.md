# Sources and credits

## Project source

The design brief is the user-supplied **Game design PLAN.docx** from the Downloads folder. It specifies a non-combat top-down RPG, mental protection, equity, environmental protection, dynamic color, symbolic community indicators, reactive sound, quiet zones, accessible controls, and a balance-based ending.

The brief includes both Pygame and Unreal Engine 5. This implementation chooses Pygame, consistent with its overview and Python programming tasks. Its narrative and setting are an interpretation of the brief rather than a transcript of a supplied story.

## Research inspiration

World Health Organization, War Trauma Foundation, and World Vision International. *Psychological first aid: Guide for field workers* (2011). [WHO publication page](https://www.who.int/publications-detail-redirect/9789241548205).

The guide informs the dialogue's emphasis on respectful, practical support, listening without pressure, and attention to the person's own priorities. The later resident scenes and the de-escalation scene follow the same principles (offering choices, acknowledging feelings, not pressing for details); their wording is original. The game does not reproduce a clinical assessment or psychological first aid training program. Its fictional community values are gameplay abstractions.

WHO Regional Office for Europe. *Urban green spaces and health* (2016). [WHO publication page](https://www.who.int/europe/publications/i/item/WHO-EURO-2016-3352-43111-60341).

The report informs the relationship between shared natural spaces, environmental conditions, and well-being. Restoration effects and thresholds in the game are invented for progression; they are not empirical estimates of health benefits.

## Background music

The background music is `assets/music/Video Game BGM.mp3`, a 54-second track supplied by the project team from the Downloads folder on 22 October 2026. **Its creator, original source and licence are not recorded in the project and have not been checked.** It was not made by this project's tools, and it should not be credited to a named student or described as original work.

Before the game is shared outside the team, shown publicly, or uploaded anywhere, find out who made the track and what licence it has, add a credit here, and replace it if the licence does not allow this use. The track is also packed inside `Common Ground.exe`, so anyone who receives the executable receives the music.

The game plays whichever music file is in `assets/music/` (the first by name, among `.mp3`, `.ogg`, `.wav` and `.flac`), so replacing the track means swapping that file. If the folder is empty or the file cannot be read, the game falls back to the generated harmony, drone and melody layers in `game/audio.py`. The track is deliberately left out of the GitHub repository; the built executable in it still contains the track. The file itself is never modified; the game trims the silence at the end of the track in memory so it repeats without a gap.

## Implementation and assets

The code, narrative, procedural pixel artwork, and synthesized ambient sound for this build were generated with coding assistance for the requested project. They are supplied as editable material. No supplied team art was available inside the source document, and these assets should not be credited as work completed by the named students.

The runtime dependency is [Pygame Community Edition](https://pyga.me/), pinned in `requirements.txt`. Its [documentation](https://pyga.me/docs/) describes the display, drawing, event, font, and audio APIs used by the game. Pygame and its bundled components retain their own upstream licenses.

The generated art and ambient sound do not require third-party asset downloads or an online service during play. The background music is a supplied recording, described below. System or bundled runtime fonts may be used by the renderer; any redistributed fonts remain subject to their included license.
