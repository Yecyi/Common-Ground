# Your own artwork

Put hand-made PNG files in `assets/custom/sprites/` and the game uses them instead of the art it draws in code. You do not need to edit any Python and you do not need to rebuild the executable: start the game again and your art is there. Anything missing, unreadable or misnamed falls back to the built-in art, so you can replace the sprites one at a time.

This folder is separate from `assets/sprites/` on purpose. `assets/sprites/` holds reference copies of the built-in art and is rewritten whenever `python tools/generate_assets.py` runs, so edits made there would be lost and would never reach the game.

## How to replace a sprite

1. Copy a reference file from `assets/sprites/` into `assets/custom/sprites/`.
2. Edit it in any pixel-art editor, keeping the file name.
3. Start the game.

## File names

| What | Name | Notes |
| --- | --- | --- |
| Any sprite | `<name>_polluted.png` and `<name>_restored.png` | For example `tree_polluted.png`, `pump_restored.png`. The two states are the struggling and the recovering village. |
| Ground tiles | `tile_<grass\|path\|water\|bridge>_<polluted\|restored>.png` | 32 by 32 pixels. Other sizes are scaled to fit. |
| A resident, before and after you listen | `mira_polluted.png` and `mira_restored.png` (also `rowan`, `amani`, `theo`, `kit`, `odile`, `noor`) | `polluted` is how they look before you have listened, `restored` is after. |
| The player | `player_polluted.png` | One picture used for every direction and step. |
| One walking frame | `player_<down\|up\|left\|right>_<0\|1\|2>_polluted.png` | Step 0 stands, steps 1 and 2 are the two walking frames. These override the single picture. Reference copies of all twelve are in `assets/sprites/`. |

Sprites are anchored at the bottom centre, so the feet stay where the code expects them whatever the size. Keep a transparent background. People are 24 by 36 pixels and trees are 64 by 80; matching the reference sizes avoids surprises, but other sizes work.

Names for every sprite are listed in `Art.NAMES` in `game/art.py`; the reference sheet `assets/sprites/original_sprite_sheet.png` shows them all.
