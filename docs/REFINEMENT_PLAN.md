# Refinement plan

This plan compares the current build of Common Ground with **Game design PLAN.docx**. That file is identical to the copy in `docs/`. The plan lists what to change next. It follows the design doc's task numbers and owners, so each item maps back to the CAS plan.

When the plan was written, the build was checked on 22 October 2026: all 25 tests passed and the rendered smoke playthrough completed. The gaps below come from reading the source and the smoke-test screenshots of that build.

**Sizes:** S is under 2 hours, M is 2–6 hours, and L is more than 6 hours.

---

## Status: carried out on 22 October 2026

Every item below was implemented, in the suggested order, and verified as recorded in `VERIFICATION.md`. The detail that follows is the plan as it was approved; where the work differs from it, the difference is listed here.

**Differences from the approved plan**

- **Custom artwork lives in `assets/custom/sprites/`, not `assets/sprites/`.** The plan said the game would load a PNG from `assets/sprites/` when one exists. `assets/sprites/` already holds a reference copy of every sprite, and `tools/generate_assets.py` rewrites it, so loading from there would have made stale copies override the art drawn in code, and any edit made there would be overwritten the next time the generator ran. A separate folder keeps hand-made art safe and lets each sprite be replaced one at a time. The naming rules are in `assets/custom/README.md`.
- **The reference PNGs in `assets/sprites/` were regenerated and overwritten.** They now include the new sprites and twelve walking frames for the player, and the sprite sheet was laid out again. If anyone had edited a file there by hand, that edit is gone; nothing in the project said those files were hand-edited.
- **Task 4.2 now uses a supplied background track.** After the plan was carried out, the team asked for `Video Game BGM.mp3` to be the background music. It replaces the generated harmony, drone and melody layers during play. The reactivity is kept by changing the track's volume: it dips in tense conversations, swells after a supportive choice and softens in quiet places. The generated layers remain as the fallback if the file is missing. The track's creator and licence are not recorded; see `SOURCES.md`.
- **The game was expanded afterwards.** Hillside, three new neighbours, the river survey, bonds and Part Two: Storm Season were added after this plan was carried out. They are described in `EXPANSION.md`.
- **The previous executable was kept.** The earlier build (made before this work) was copied to `C:\Users\Administrator\AppData\Local\Temp\claude\C--Users-Administrator-Desktop-CAS-Project---Common-Ground\dfba9899-7321-4488-8f80-c70ad0d2d153\scratchpad\Common Ground (previous build).exe` before the new one replaced it. That folder is temporary and may be cleaned up, so copy the file somewhere permanent if you want to keep it. The source for that build no longer exists separately, because the project is not under version control.
- **Positions of Rowan, Theo, the arguing neighbours and the sign-up board differ from what the plan implied.** A review found that Rowan's and Theo's helper positions sat close enough to a garden bed and the pump that pressing E in front of those would have talked to the resident instead. Rowan's home was already close to the second bed. All four were moved, and a test now checks every place's approach points.

---

## Tier 0: Fix verified defects (do first)

| # | Defect | Evidence | Fix | Size |
| --- | --- | --- | --- | --- |
| D1 | When the "A thread to follow" hint runs to two lines, the text spills out of its box. | The box has a fixed 68 px height (`game/app.py:347-350`). In the restored-village screenshot, "town's future." spills below the box. | Size the box to the measured paragraph height. | S |
| D2 | Residents never change appearance, whatever the player does. | `_make_sprite` returns `_person(name)` and ignores `restored` (`game/art.py:174-176`). The world checks `p.id in state.completed` (`game/world.py:202`), but support is stored as `support_<id>`, so the check never passes. | Add a "supported" variant of each resident: upright posture, a small smile, a brighter coat. Show it when `support_<id>` is completed. | S |
| D3 | The first instructions contradict each other. | The opening toast says "Start with Mira" (`game/app.py:139`). The first objective shown is "Repair the river pump" (`game/state.py:89`). | Replace the first-unfinished-objective rule with a hint that depends on context (see 5.1). | S |
| D4 | The same place has several names, and the spelling is inconsistent. | "Community table" (`game/world.py:38`), "Community council" (`game/app.py:529`), "council table" (`game/app.py:397`) and "The neighborhood circle" (`game/story.py:38`). The text mixes neighbour/neighborhood and colour/color. | Use one name: "Neighbourhood circle" at the "community table". Use one spelling throughout; British English is recommended. | S |
| D5 | The ending screen is cramped with larger text. | The layout uses fixed y positions (`game/app.py:543-555`). With larger text, the scores almost touch the closing question. | Lay the screen out from measured heights, the same way the dialogue and journal screens already do. | S |

---

## Tier 1: Close the gaps against the design doc

### Phase 1: Narrative

**1.1 Thematic character arcs.**
- **Now:** Each resident has one conversation, one choice and a short follow-up line (`game/state.py:150-190`). The doc asks for "complex character arcs" and for scenes about "empathy and de-escalation". It also asks how "environmental stress triggers mental health crises".
- **Change:** Give each resident three beats, unlocked by world state rather than by a fixed order:
  - **Rowan (mental protection):**
    1. Can't sleep while the pipes rattle (existing).
    2. After the pump repair, the quiet unsettles them at first. They choose their own small role in the garden.
    3. They co-lead the garden care rota at their own pace.
  - **Mira (burnout):**
    1. Making lists alone (existing).
    2. After two or more tasks, she is visibly overloaded and trying to do everything. The player helps her hand work to others, or adds to her load.
    3. She sets limits and the care rota works.
  - **Amani (equity):**
    1. Shut out by the queue (existing).
    2. Reacts honestly to the allocation actually chosen at the circle.
    3. Joins oversight, or holds the circle to account if the review hasn't happened.
  - **Theo (livelihood vs. river):**
    1. The workshop dilemma (existing).
    2. Former co-workers press him to restart the line.
    3. He reflects on the choice that was made.
- **Add one de-escalation scene.** After the allocation, a former mill worker and a Riverside resident argue at the circle about restarting the factory. The response options are:
  - Acknowledge both fears.
  - Name the need they share (safe work *and* safe water).
  - Suggest a pause.
  - Take a side or assign blame. This escalates, but the scene can still be recovered.
- **Rules:** The second and third beats are optional and enrich the story. They give small metric gains and journal entries and feed the ending epilogue. They have **no supply costs**, so the economy is unchanged.
- **Files:** `game/story.py`, `game/state.py`, `tests/test_state.py`.
- **Size:** L.

**1.3 Dilemma points.**
- **Now:** There are two dilemmas: the six-supply allocation and the factory.
- **Change:** Add a third dilemma that **costs no supplies**: deciding who gets plots in the community garden. It triggers once all three beds are planted. The options are:
  - Priority for households without yards, many of them in Riverside (equity).
  - An equal lottery.
  - Plots for whoever helped most (merit). This leaves out shift workers and carers, and the circle can review it.
- **Why no supply cost:** This tests distributive fairness without touching the 21-supply budget that keeps every route recoverable.
- **Files:** `game/state.py`, `game/story.py`, tests.
- **Size:** M.

**1.4 Environmental storytelling.**
- **Now:** The backstory is mostly noticeboard text. The river water only follows the overall environment value; it does not change when the pump is repaired.
- **Change:** Add visual cues that switch on specific world events:
  - **Outflow plume and foam:** a discoloured plume and foam on the water downstream of the mill. These clear when `source_repaired` is set.
  - **Dead tree:** a leafless tree beside the outflow, which buds after the repair.
  - **Flood marks:** water-line stains on the Riverside houses.
  - **Protest sign:** a faded "What about Riverside?" sign, replaced by a delivery cart once the allocation is needs-based or has been reviewed.
  - **Queue barrier:** a queue rope at the square while the queue system remains.
  - **Chimney:** the mill chimney is dark. It is cleaned once the workshop route is chosen.

  Each cue has an optional one-line "observe" caption, with no long text.
- **Files:** `game/art.py`, `game/world.py`.
- **Size:** M.

### Phase 2: Visual direction

**2.1 Color psychology** (unassigned).
- **Now:** One overlay blends the polluted and restored backgrounds, driven by environment only (`game/world.py:183-187`). In screenshots, the before and after palettes look very similar. The doc ties color to "healing and equity", not only to nature.
- **Change:**
  - Drive the blend from overall balance: the average of the three values, weighted towards the lowest one.
  - Widen the gap between the two palettes, from a cool grey-green haze to warm golden light.
  - Add a light full-screen color grade.
  - Add drifting smog specks at low balance, and pollen or butterflies at high balance.
  - With reduced motion on, the particles are static and the color grade still applies.
- **Files:** `game/world.py`, `game/art.py`.
- **Size:** M.

**2.2 Symbolic HUD** (Jayden, 5 h).
- **Now:** Each value is shown as a number plus five filled dots (`game/app.py:315-323`). This is still a segmented health bar, which the doc says to replace.
- **Change:** Replace each value with a living symbol:
  - **Environment:** a sapling that grows from a sprout to a flowering tree.
  - **Equity:** a ring of seats around a table that fills with people.
  - **Resilience:** a lantern whose light widens.
- **Balance cue:** A small "balance" mark shows which value is lagging.
- **Accessibility:** The exact numbers stay in the journal and appear when the mouse hovers over a symbol. High-contrast mode keeps its outlines.
- **Files:** `game/ui.py`, `game/app.py`.
- **Size:** M.

**2.3 Custom 2D assets** (Jayden, 20 h).
- **Now:** The runtime draws every sprite from code. The exported PNGs in `assets/sprites/` are only a reference (`assets/README.md`).
- **Change:**
  - **PNG loading:** If a PNG named `assets/sprites/<name>_<polluted|restored>.png` exists, the game uses it. Otherwise it falls back to the sprite drawn in code. Jayden can then replace art one file at a time in any pixel editor, without editing Python.
  - **Animation:** Add a two-frame walk cycle and four facing directions for the player, and a gentle idle animation for residents. These follow the reduced-motion setting.
  - **Docs:** Document the naming and size rules in `assets/README.md`.
- **Files:** `game/art.py`, `assets/README.md`.
- **Size:** M for the loading and animation code. Drawing the art is Jayden's task.

### Phase 3: Gameplay systems

**3.2 Non-combat loops that reward patience and cooperation** (Everyone).
- **Now:** The loop is collect, spend, talk. Restored places stay static.
- **Change:**
  - **Growing gardens:** Planted beds grow through three visual stages while the player explores. The growth is cosmetic and never gates progress or adds a timer.
  - **Visible helpers:** Residents you have supported appear at the sites they care about: Rowan in the garden, Theo at the pump, Amani with the delivery cart. This shows cooperation in the world.
- **Files:** `game/world.py`, `game/state.py` (read-only queries).
- **Size:** M.

**3.3 Resource distribution systems** (Everyone).
- **Now:** The result of an allocation is described only in text.
- **Change:** Show an outcome panel after each distribution decision. It lists four groups (the square, Riverside, shift workers, older residents) and fills or empties their icons. The unequal outcome becomes visible as well as described. This pairs with the 1.3 garden dilemma.
- **Files:** `game/app.py`, `game/state.py`.
- **Size:** M.

### Phase 4: Audio and pacing

**4.1 Atmospheric soundscape** (unassigned).
- **Now:** Three global loops crossfade (`game/audio.py:97-110`). The wind loop contains a faint hum.
- **Change:** Add synthesized loops that depend on position, with volume set by distance:
  - Machinery near the old mill.
  - River water, murky before the repair and clear after.
  - Birds near trees and the garden, scaled by how restored the area is.
- **Files:** `game/audio.py`, `game/app.py`, regenerated `assets/audio/`.
- **Size:** M.

**4.2 Reactive soundtrack** (unassigned).
- **Now:** The mix follows only the average of the metrics (`game/app.py:306`). Nothing responds to narrative tension.
- **Change:** Give each conversation a tension level. Dilemmas, the de-escalation scene and distressed first beats are tense.
  - **During tension:** A low, soft drone fades in.
  - **After a supportive or de-escalating choice:** The drone resolves into the harmony layer.
  - **Melody:** A melody layer unlocks as balance rises.
  - **Text first:** Sound is never the only way information reaches the player.
- **Files:** `game/audio.py`, `game/story.py` (a tension field on `Conversation`), `game/app.py`.
- **Size:** M.

**4.3 Quiet zones** (Eason, 4 h).
- **Now:** There is one refuge (`game/world.py:40`). The doc asks for "quiet zones" in the plural.
- **Change:** Add two more quiet spots: a Riverside jetty bench across the bridge, and an overlook of the garden. Each has its own observation prompt about what has changed there.
- **Inside a quiet zone:**
  - The HUD fades and the camera eases slowly.
  - Ambient sound rises.
  - With reduced motion on, the camera stays still.
- **Rules:** Only the willow refuge counts towards the goal. The extra zones add journal reflections and give no repeatable rewards.
- **Files:** `game/world.py`, `game/state.py`, `game/app.py`.
- **Size:** M.

### Phase 5: Accessibility and impact

**5.1 Intuitive controls** (Oscar, 3 h).
- **Change:**
  - **Context-aware hint (fixes D3):** The hint suggests what to do next. For example, talk to Mira first. If the player can't afford something, it points to the nearest crate or litter.
  - **"Show the way" setting:** An optional gentle marker over the hint's target. It is on by default for new players.
  - **First-time prompts:** Short prompts for moving, talking and opening the journal, shown once each.
- **Optional:** Gamepad support (left stick and A/B) through `pygame.joystick`.
- **Files:** `game/app.py`, `game/state.py`, `game/storage.py` (new setting).
- **Size:** M.

**5.2 Ethical implication review** (Eason, 2 h).
- **Change:** Add a "Your choices" recap to the ending. For each decision it shows:
  - what was chosen
  - who benefited
  - who was missed
  - whether the decision was revisited
  - one reflection question

  Also add a scene-by-scene review checklist to `docs/CAS_GUIDE.md` for Eason to work through. For example: does any resident become just a diagnosis? Does listening alone appear to fix structural problems?
- **Files:** `game/app.py`, `game/state.py`, `docs/CAS_GUIDE.md`.
- **Size:** M.

**5.3 Victory condition verification** (Jayden, 3 h).
- **Change:**
  - **Epilogue:** Make the ending vary with the actual choices: the allocation and whether it was reviewed, the factory route, the garden plots, and the optional arc beats.
  - **New tests:** The new dilemmas and beats cannot unlock the ending on their own. The ending is still reached only through balance and the deliberate council choice. Every new branch remains recoverable.
- **Files:** `game/state.py`, `tests/`.
- **Size:** S–M.

---

## Required alongside any change

1. **Save format v2 with migration.** New completed IDs, flags and choices require updates to `KNOWN_COMPLETED`, `KNOWN_FLAGS`, `CHOICE_VALUES` and the consistency checks in `GameState.from_dict` (`game/state.py:24-46, 326-415`).
   - Bump `SAVE_VERSION` to 2.
   - Upgrade version-1 saves when they load. Without this, the existing `saves/save.json` would be reported as unreadable.
   - Add round-trip and migration tests.
2. **Keep the supply economy.** The 21-supply budget keeps every branch recoverable. None of the additions above cost supplies. Any later costed addition must be rebalanced, and must extend the recovery and quest-order tests in `tests/test_state.py`.
3. **Keep the invariants:**
   - no combat and no countdown
   - every new animation and particle obeys reduced motion
   - high contrast stays legible
   - full keyboard and mouse parity
   - essential information is always shown as text
4. **Verify and ship:**
   - Extend `tools/smoke_test.py` with captures of the new screens.
   - Run the unit tests and the smoke test.
   - Rebuild `Common Ground.exe` with `tools/build_windows.ps1` and run the packaged smoke test. The Play launcher opens the exe first, so a stale exe would hide every change.
   - Update the test counts in `README.md`, and update `docs/DESIGN.md`, `docs/VERIFICATION.md`, `docs/PLAYTEST_CHECKLIST.md` and `assets/README.md`.
5. **Unchanged decisions:** The game stays on Pygame. The Unreal Engine 5 heading is already addressed in `docs/DESIGN.md`. Generated content remains an editable starting point and is not credited to a named student. The owners in the design doc keep ownership of their tasks.

## Suggested order

1. Tier 0 fixes (D1–D5) and the save-v2 groundwork.
2. Story and rules: 1.1, 1.3, 3.3 and 5.3, with tests.
3. World and visuals: 1.4, 2.1, 2.2, 2.3 (PNG loading and animation), 3.2 and the resident variants.
4. Audio and pacing: 4.1, 4.2 and 4.3.
5. Guidance and the ending recap: 5.1 and 5.2.
6. Full verification, exe rebuild and documentation updates.

## Out of scope

- Porting to Unreal Engine 5.
- Separate levels or maps. The single village has distinct zones, which is enough for the doc's "level design" goals at this scale.
- Voice acting.
- Claims about real-world mental-health impact. Player impact needs actual playtesting, as described in `docs/CAS_GUIDE.md`.
