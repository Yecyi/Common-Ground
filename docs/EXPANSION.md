# Expansion: Hillside, new neighbours and Storm Season

This records what was added after the refinement plan, why it works the way it does, and how to extend it. The aim was depth, not just more: each addition either asks the player to weigh something, or pays off a decision made earlier.

## What was added

| Addition | What the player does | What it draws on |
| --- | --- | --- |
| Hillside | Walks east past Riverside to a health post, a common hall, a cottage, an orchard slope and a lookout | A wider village (1,760 by 832 pixels), a new zone, new buildings and quiet place |
| Noor, Kit and Odile | Meets three neighbours; each has a first conversation and two later chapters | Earlier decisions: the pump, the garden, the circle and Rowan's trust open their chapters |
| The river survey | Takes readings at three sampling posts and watches them change | Pump repair, riverside litter, the factory choice and the state of nature |
| Bonds and the Neighbours page | Sees every friendship and what comes next | The chapters completed so far |
| Part Two: Storm Season | Spends six hours of daylight, plays a five-part storm night, and recovers | Everything: who was met, what was repaired, which chapters were taken |
| Weather and rain | Sees overcast, storm and the morning after | The phase of Part Two |

## Rules the expansion keeps

These are the same rules the first version kept, and each has a test.

- **Nothing here is combat, and nothing counts down.** Part Two's "hours" are a list of jobs the player has done. They never change with real or play time.
- **Nothing costs supplies.** The 21-supply budget that keeps every Part One route recoverable is untouched. Part Two spends hours and nothing else.
- **Nothing new is required.** The ending of Part One needs the same milestones as before. Neighbours, the survey and Part Two only add to it. A player can finish Part One without ever going east.
- **Every path continues.** Pressuring responses cost a little and can be repaired once. The storm night has no wrong answers and no losing state, and every plan, including doing nothing, leads through the night to recovery.
- **No information is carried by colour or sound alone.** The survey and the Hall panel show words as well as pips. The storm is described in text as well as drawn.
- **Reduced motion and high contrast still work.** Rain, puddles and the weather tint are still or softer under those settings.

## Design decisions

**Part Two comes after the first ending.** The first ending is a balance the player has earned, and it should stay that way. Part Two asks a different question: what happens when the balance is tested. Putting it after the ending also means no existing journey is disturbed, and a player who has finished can return to it.

**Hours are a choice, not a clock.** Scarcity of time is the kind of pressure the game wants: not enough for everything, so who do you put first? A real timer would add urgency without adding meaning, and would penalise slower readers. The hours exist only as the sum of the jobs done, so there is nothing to run out and nothing to watch.

**Earlier choices change the night, not its cost.** A tempting design is to make earlier chapters cheaper discounts. That would make the cost of a job depend on later events, which a saved game cannot represent cleanly. Instead every job has a fixed cost and earlier chapters change how well it works, or what it unlocks. Meeting Odile lets you check on her; Mira's rota changes how tired she is; Amani's appeal route changes how many neighbours turn up to clear drains.

**The night is trade-offs, not tests.** None of the responses is the right one. Each protects some people at the expense of others, and the recap names both. The recap's job is to prompt reflection, so it asks the same three things of every decision: who it helped, who it left out, and what the player would do differently.

**The values can fall.** Until now the three values only rose. The storm lowers them, by an amount that depends on what was done, and recovery restores some of it. The saved ending only checks milestones, so a fall can never make a journey unloadable.

**The new neighbours are not stand-ins.** Each has their own concern: whose evidence counts (Kit), what a place remembers (Odile), and where neighbourly help ends and professional care begins (Noor). None exists to unlock something for the player.

## Save format

Saves are version 3. Version 1 and 2 saves load and are upgraded in memory. Older builds of the game cannot open version 3 saves. See `docs/DESIGN.md` for what is validated.

A fix shipped with this version: a saved ending used to require the three values to still be at their goals. A pressuring reply after the ending could lower one and make that journey unloadable. The same fix applies to builds made before this one.

## Extending it

- **A new neighbour**: add a `Beat` for each chapter to `NEIGHBOUR_BEATS` in `game/story.py`, with `grants_support=True` on the first. Add the person to `NPCS`, `NEIGHBOURS` in `game/state.py`, a sprite in `game/art.py`, a `Place` in `game/world.py`, an after-conversation line in `_neighbour_dialogue`, and a row in `RECAP_PEOPLE`. The save format, the journal cards and the bond count pick them up from the data.
- **A new storm job**: add an entry to `PREP` in `game/storm.py` with its cost, label, hint and what it needs, a result in `PREP_RESULTS`, and a line in `PREP_BENEFIT`, `PREP_SHORT`. Then make some scene text depend on `self.prepared(...)`.
- **A new storm scene**: add its id to `SCENES`, its choices to `SCENE_CHOICES` and `SCENE_OPTIONS`, a `_text_<scene>` and `_resolve_<scene>` method, and a recap entry. The save check and the tests that walk every route need the new ids.

## Content to review

This expansion deals with illness, loneliness, ageing and a disaster. `docs/CAS_GUIDE.md` has review prompts for the scenes in this version, including the bed decision, how Noor's scenes treat the line between neighbours and professionals, and how Kit and Odile are portrayed. They are prompts for the team and for the people who play the game; they are not a substitute for talking to the people the characters are meant to respect.
