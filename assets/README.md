# Original Common Ground assets

All sprites, tiles, and sounds in this folder were generated specifically for
this project from the source in `game/art.py` and `game/audio.py`.
They do not contain downloaded stock art, sampled music, or third-party assets.
These are code-drawn assets supplied with this implementation, rather than
artwork attributed to any of the named students in the design plan.

Edit colours and shapes in `game/art.py`, or frequencies and envelopes in
`game/audio.py`, then run:

```powershell
python tools/generate_assets.py
```

Sprites have transparent backgrounds and use a bottom-centre anchor. Tiles are
32 by 32 pixels. `sprites/original_sprite_sheet.png` previews both the polluted
and restored palettes. The files in `sprites/` are reference copies, rewritten
every time the generator runs. To use your own artwork, copy a file into
`custom/sprites/` and edit it there; the game then uses it in place of the
drawn art (see `custom/README.md`). Twelve walking frames for the player are
supplied as templates, named like `player_left_1_polluted.png`.

The WAV files are quiet mono 22050 Hz 16-bit PCM and loop seamlessly. Nine are
supplied: `wind`, `harmony`, `birds`, `chime`, `machinery` (heard near the mill),
`river_murky` and `river_clear` (the river, before and after the repair), `drone`
(tense conversations) and `melody` (as balance rises). Quiet places raise the
ambience and soften the music. Sound is optional and never signals information
that is missing from the visual interface.

## Music

`music/` holds the background track. It is a supplied recording, not generated
here; see `docs/SOURCES.md` for what is and is not known about it. The game plays
the first music file by name (`.mp3`, `.ogg`, `.wav` or `.flac`) and loops it,
so swapping the file swaps the music. The generated `harmony`, `drone` and
`melody` sounds above are only used when there is no readable track.
