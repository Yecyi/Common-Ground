# Common Ground design

## Purpose

Common Ground translates the supplied CAS plan into a playable, non-combat 2D RPG. The player helps a village respond to environmental damage, unequal access to resources, and the strain these conditions place on residents. The ending requires progress across all three themes rather than a high score in one area.

The game is a small fictional model. Its community values summarise gameplay state; they do not measure an individual's mental health or predict a real community's recovery.

## Engine decision

The plan names Pygame in its overview, asks the team to set up Python and libraries, and later labels technical development as Unreal Engine 5. This build uses Python and Pygame Community Edition. That choice follows the concrete programming tasks and produces an editable desktop game without a large engine installation.

## Play structure

The player explores a top-down village at their own pace. Conversations, collection, restoration, and reflection can be approached in different orders. There is no combat, damage system, countdown, or reflex challenge.

Mira organises community efforts. Rowan expresses the strain of environmental loss. Amani describes the barriers facing an overlooked neighbourhood. Theo brings a worker's perspective to the future of the former factory. Revisiting people and shared spaces connects individual concerns to community decisions.

Choices are recorded in the journal. Limited supplies give resource decisions consequences, while cleanup and salvage support further work. A less inclusive early decision remains repairable through later participation and practical action.

### Required decisions

The first dilemma distributes six supplies between residents: prioritise different needs, split equally, or retain a first-come queue. The council can later review an exclusionary arrangement. Theo's dilemma weighs a safer community workshop against a faster factory restart or postponement. A later retrofit offers a way to improve the factory choice. These are authored scenarios, not a general rule that one allocation method is always fairest.

The village contains six cleanup locations, three salvage caches, and three garden beds. The complete resource pool is 21 supplies. Source repair costs four, each garden costs one supply and one seed, and council allocation costs six. A shared workshop costs three; restarting costs two, and a later retrofit costs three. These totals leave a route to meet the balance goals after any initial choice. Rewards apply once; revisiting an activity cannot generate unlimited supplies or progress.

### Optional chapters

None of these costs supplies, and none is needed to finish. The supply budget above is unchanged, so every route stays recoverable. Each adds journal entries, small changes to the three values, and a line in the ending.

- **Later chapters for each resident.** Each resident has a second and third scene that opens when the village has changed in a way that matters to them: Rowan after the pump is repaired and again once the garden is planted, Mira once she has helped with three tasks and again after the circle meets, Amani after the allocation and the review, Theo after the factory decision. Most scenes offer two supportive responses and sometimes one that adds pressure. A pressuring response costs a little and can be repaired once by returning and trying again.
- **Raised voices at the circle.** After the circle meets, a former mill worker and a Riverside resident argue about the factory. The player can acknowledge both fears, name the need they share, or suggest a pause. Taking a side escalates the argument, but the scene can still be repaired.
- **Garden plots.** When all three beds are planted, the sign-up board asks who should get the few plots: those with no garden space, a lottery, or those who helped most. The lottery and helper choices can be reviewed later with shared plots and a waiting list.
- **Two more quiet places.** A river bank bench and a garden overlook give one journal reflection each and no rewards. Only the willow refuge counts towards the goal.

Each dilemma shows an outcome panel after the decision. It lists four groups (or three, for the factory) and how many were reached, as words and pips so it never relies on colour alone.

### Guidance

"A thread to follow" suggests one next step from the current state: talk to Mira first, collect supplies when the pump or a garden bed is unaffordable, then people, the circle and the refuge, and finally whatever the three values still need. It never blocks another order of play. "Show the way" places a marker over the suggested place and an arrow at the screen edge when it is out of view. First-time prompts explain moving, talking and the journal once each.

## Theme mechanics

| Plan theme | Game expression | Acceptance check |
| --- | --- | --- |
| Mental protection | Consent-based listening, practical support, residents' own pace, de-escalation, quiet reflection, community resilience | Supportive choices respect a resident's wishes; pressuring responses cost something and can be repaired; reflection has no required timed wait and repeat use cannot farm progress. |
| Equity | Scarce supplies, neighbourhood needs, garden plots, and a decision about shared infrastructure | Different allocations have visible consequences, shown as who was reached; the game permits a route to repair exclusion. |
| Environmental protection | Litter removal, source repair, garden planting, scenery that records the damage and its repair, and a recovering village palette | Tasks change persistent state and appearance; repeating completed actions cannot generate resources. |
| Non-linear narrative | Residents and tasks can be visited in different orders | Necessary story information remains available after revisits and alternative choices. |
| Balance ending | Environment at least 70, equity and resilience at least 65, source repair, three planted gardens, four resident support arcs, reflection, and supply allocation | Completing only cleanup, or only the optional chapters, cannot trigger the ending. |

## Presentation

Original procedural pixel sprites represent residents, buildings, vegetation, resources, polluted water, and restored spaces. The three values are shown as living symbols rather than health bars: a sapling that grows, a ring of seats around a table that fills with people, and a lantern whose light widens. A word for each (Fragile, Mending, Growing, Thriving) is always visible, the lowest value is marked "needs care" when it lags, and hovering shows the exact number and goal.

The village's colour follows an overall balance that is weighted towards the weakest value, so neglecting one theme holds the others back. It moves from a cool grey haze with drifting smog specks to warm light, pollen and the odd butterfly. Residents stoop slightly until you have listened to them; afterwards they stand straighter, smile, and walk to the place they care about: Rowan to the garden, Theo to the pump, Amani to the delivery cart. Planted beds grow through three stages as time passes in the village. The growth is cosmetic and never gates progress.

The environment tells its own story. A grey-green film and foam on the water, a bare tree beside the outflow, flood lines on the Riverside houses, a hand-lettered "What about Riverside?" sign, a queue rope at the square, and a sooty mill chimney each change with the matching decision. Standing near one shows a one-line observation.

The player faces the way they walk and has two walking frames. All motion, particles, idle movement and the fading of the interface in quiet places respect the reduced motion setting.

Menus support keyboard, mouse and a gamepad. The window is resizable, and the settings expose larger text, high contrast, reduced motion, movement speed and the guidance marker. Dialogue waits for a deliberate response. A visible journal and map reduce the need to memorise instructions or locations.

### Sound

The ambient mix follows the village. Machinery hums and thumps near the mill, and softens once the mill becomes a workshop. The river sounds murky until the pump is repaired and clearer afterwards. Birds are louder near trees and as the village recovers. The background music is a supplied track that loops under the ambience. It dips while a conversation is tense (the dilemmas and the argument) and swells gently once a supportive or de-escalating choice settles it. In the quiet places the ambience rises and the music softens. If the track is missing or unreadable, generated harmony, drone and melody layers do the same job: a low drone in tense moments that settles into the harmony, and a melody that joins as balance rises. Audio is supplementary: essential information remains visible when muted.

## Persistence and architecture

The Python state module owns resources, consequences, completed tasks, story flags, and ending eligibility. Rendering and input use those rules rather than maintaining a separate progression system. Saves retain world state, choices, garden growth, and player position locally in `saves/save.json`; settings are separate in `saves/settings.json`. Starting a new journey preserves the previous save as a timestamped backup. Invalid save data leaves the original file intact and disables Continue while allowing a new game.

The save format is version 2. A version 1 save is upgraded when it loads, without changing the file until the next save, and its garden beds appear fully grown. Every later scene is checked against its prerequisites on load, so a hand-edited save cannot skip ahead.

Hand-made artwork can replace any built-in sprite or tile. PNG files placed in `assets/custom/sprites/` are used in preference to the drawn art, and anything missing falls back to it (see `assets/custom/README.md`). This folder is deliberately separate from `assets/sprites/`, which holds reference copies that are regenerated from the code.

Rule tests cover completion, alternative decisions and recovery, finite resources, repeated actions, save round-trips and upgrades, and ending gates. A bot that follows the on-screen suggestions is tested to reach the ending on every route. Further tests cover input, settings, sound levels, world behaviour, and rendering of every screen with larger text and higher contrast. Runtime checks should also cover collision, map accessibility, dialogue layout, mute, settings, and resizing; these cannot be established by rule tests alone.

## Plan coverage

| Plan task | Where it lives |
| --- | --- |
| 1.1 Character arcs | Three scenes per resident, plus the de-escalation scene (`game/story.py`, `game/state.py`) |
| 1.3 Dilemma points | Supply allocation, factory, garden plots, each with a review route |
| 1.4 Environmental storytelling | Water film, bare tree, flood lines, sign and cart, queue rope, chimney (`game/world.py`, `game/art.py`) |
| 2.1 Colour psychology | Balance-driven palette, colour grade, particles (`game/world.py`) |
| 2.2 Symbolic HUD | Living symbols and words (`game/ui.py`, `game/app.py`) |
| 2.3 Custom 2D assets | Procedural art plus a custom PNG folder and walking frames (`game/art.py`) |
| 3.1 Top-down mechanics | Movement, click-to-walk, collision, facing and gamepad |
| 3.2 Non-combat loops | Residents who help in the world, growing gardens, optional chapters |
| 3.3 Resource distribution | Outcome panels for allocation, plots and the factory |
| 4.1 Soundscape | Positional machinery, river and birds (`game/audio.py`) |
| 4.2 Reactive soundtrack | The supplied track ducks in tense conversations and swells after a supportive choice; generated drone, harmony and melody layers remain as the fallback |
| 4.3 Quiet zones | Willow refuge, river bank bench, garden overlook |
| 5.1 Intuitive controls | Context-aware suggestion, guidance marker, first-time prompts, gamepad |
| 5.2 Ethical review | End-of-game recap of each decision, and the checklist in `CAS_GUIDE.md` |
| 5.3 Victory verification | Epilogue that follows the choices, and tests that the ending needs balance and the circle |

## Plan boundaries

The plan refers to team-created art, due dates, hours, and completed subtasks. This build does not verify those records. Its generated assets are supplied as editable project material, and the documentation does not attribute their creation to a named student. Player impact and CAS learning outcomes require actual participation, observation, and reflection; a finished program alone cannot establish them.
