# Playtest checklist

Record the build, date, starting state, result, and any replay steps for each run. These checks support technical verification; ask actual players separately about clarity and impact using the questions in `CAS_GUIDE.md`.

## Starting and saving

- Launch the executable without a Python terminal. Start a new journey and read the introduction.
- Complete a task, save and quit, reopen, and confirm Continue restores resources, choices, completed work, and position.
- Open Settings and How to play from the title screen, then close the window. Confirm neither operation changes an existing journey.
- Start a new game from an existing save. Check confirmation, cancellation, and the retained previous-journey backup.
- In a disposable copy, supply an invalid save. Confirm the title screen remains usable and the invalid file is retained.

## Exploring and controls

- Move with both WASD and arrows. Confirm diagonal speed is consistent, buildings and river banks block passage, and the bridge is usable.
- Reach all four residents, the council, source pump, quiet bench, noticeboard, all six litter locations, all three crates, and all three garden beds.
- Click a nearby object, a distant object, and open ground. Confirm navigation and interaction; use movement keys to cancel walking.
- Use the journal, map, and pause controls with keyboard and mouse. Travel from the map to each listed destination.
- Resize the window, use fullscreen, and return to windowed mode. Check that mouse targets still match the buttons.
- If you have a gamepad, move with the stick and d-pad, talk with A, open the journal with X and the map with Y, and go back with B. Check that a resting stick does not make the character drift.
- Start a new journey with a fresh `saves/settings.json`. Confirm the first-time prompts for moving, talking and the journal each appear once and are not repeated after restarting.
- Follow "A thread to follow" from the start without any other help. Note where the suggestion is unclear or points somewhere unexpected, and whether the guidance marker helps or distracts. Repeat with "Show the way" off.

## Readability and accessibility

- Check each resident and council conversation with normal and larger text. Read every choice and hint using scrolling when needed.
- Read the entire noticeboard result and an early attempt to finish. Ensure body text does not overlap the footer or Continue button.
- Read every journal objective and the latest and earliest entries. Confirm objectives, values, and Return controls do not overlap.
- Use the game muted. Confirm all essential information remains visible.
- Toggle reduced motion and check water, the player, and the quiet-space circle. Check higher contrast and slower movement.
- Enter each of the three quiet places (willow refuge, river bank bench, garden overlook) and immediately choose Reflect and return. Confirm there is no mandatory timer, the interface fades gently, and only the willow refuge changes a value.
- Turn on reduced motion. Confirm particles, resident idle movement, the walking cycle, smoke and the fading interface are all still.
- Hover over each symbol at the top of the screen. Confirm the exact value and goal appear, and that the words stay readable with larger text and higher contrast.
- Read the one-line observations near the water below the outflow, the bare tree, the Riverside houses, the sign, the queue rope and the mill chimney, before and after the matching decision.

## Consequences and ending

- Play an inclusive route and confirm all three values and required milestones gate the ending.
- Try equal and first-come allocation, revisit the council, and review access. Confirm the new decision is recorded.
- Try the workshop, restart, and reserve routes. Revisit Theo and check retrofit costs and consequences where offered.
- Make a dismissive response, return to that resident, and take a supportive action. Confirm progress remains possible.
- Interact again with completed cleanup, salvage, planting, reflection, and conversation actions. Confirm resources and rewards are not repeated.
- Attempt restoration without enough resources. Confirm costs are not partly deducted.
- Complete only environmental work and attempt to finish. Confirm the missing community work is explained.
- Reach the ending through the council conversation. Keep exploring, reopen the journal, save, and Continue the completed journey.

## Later chapters and the ending

- Listen to each resident, then change the village (repair the pump, plant the garden, hold the circle) and return. Confirm each later scene opens only when its condition is met, and that its text follows your earlier decisions (the allocation for Amani, the factory for Theo).
- Choose a pressuring response in a later scene. Confirm the cost is small, the option disappears for the retry, and a supportive response is still possible.
- Hold the circle, then speak to the arguing neighbours. Try taking a side, then calm them. Confirm the argument can be repaired and the neighbours look calmer afterwards.
- Plant all three beds and use the sign-up board. Try each plot decision and the second round. Confirm no supplies are spent and that the outcome panel explains who was reached.
- Watch the residents you listened to walk to the garden, the pump and the delivery cart. Leave the planted beds for a while and check they grow.
- Finish with and without the optional chapters. Confirm both endings are reachable, the epilogue differs, and the recap lists every decision with who it helped, who it left out, and whether it was revisited. Scroll the recap with larger text.
- Ask someone who has not seen the game to read the recap. Note which decisions they disagree with.

## Hillside and the new neighbours

- Walk east past Riverside to Hillside. Confirm the zone name changes, a short note appears once, and every building and the lookout can be reached on foot.
- Meet Noor, Kit and Odile. Try the response that closes the door with each, confirm a small cost, then return and listen. Confirm the first conversation cannot be repeated for rewards.
- Confirm Kit's second chapter waits for all three river readings, Odile's for the river pump, and Noor's for Rowan's trust. Confirm none costs supplies.
- Plant Odile's orchard. Leave the village a while and confirm the saplings grow, and that the orchard is still there after saving and continuing.
- Open the journal's Neighbours page. Confirm every neighbour is listed with their bond, what is next, and where to find anyone not yet met. Switch pages with the mouse and with the left and right arrow keys.

## The river survey

- Take a reading at each of Kit's three posts. Confirm each shows words as well as pips, and the first reading is a journal entry and later ones are not.
- Repair the pump, take the factory route, and clear the litter by the river. Return to the posts after each and confirm the water reads better. Choose the factory restart and confirm it reads worse.
- Open the journal's River page and confirm it matches the posts.

## Part Two: Storm Season

- Finish Part One. Confirm the forecast is offered at the circle, and that the suggestion points to it.
- At the Hall board, spend the hours on different jobs across several runs. Confirm each job spends its own hours, a job that does not fit is refused with nothing spent, jobs for neighbours you have not met are not offered, and the planning table reopens after each task.
- Wait on the board for a long time before choosing. Confirm the hours do not change.
- Begin the night with some hours unspent, and with none. Confirm the five scenes follow each other, nothing can be prepared afterwards, and the text changes with what you prepared. Try at least three different routes through the night.
- Leave the game mid-night, quit and continue. Confirm you can carry on from the board.
- After dawn, confirm the debris, the puddles and the three recovery tasks, that the journal's goals stay ticked even if a value dipped, and that the circle only closes Storm Season once recovery is done.
- Read the recap. Confirm it names who you reached and who you left out, and notes neighbours you never met.
- Take it to someone who has not played it. Ask them what the night asked of them and which choice they regretted.

## Weather

- Watch the sky through the forecast, the night, the morning after and the clear-up. Confirm the lit windows appear only in the night and the scenery follows what you prepared (cots, sandbags).
- With reduced motion, confirm rain and puddles are still. With high contrast, confirm the storm tint is gentler and the village is still readable.
- Listen to the rain, the wind and the music through the storm with headphones. Confirm the music sits back and the birds are quiet.

## Saves from earlier versions

- Copy a save made by an earlier build into a spare folder and open it. Confirm Continue works, and that a finished journey is invited to Part Two.

## Sound

- Walk from the mill to the river and the trees with headphones. Confirm machinery fades with distance and the river and birds come in.
- Repair the pump and take the workshop route. Confirm the river sounds clearer and the machinery softens.
- Open a tense conversation, then choose supportively. Confirm the music dips and then swells back. Mute with M and confirm no information is lost.
- Let the background music play through at least two repeats. Confirm it returns without a long silence or a click, and that its volume sits comfortably under the ambience and dialogue on your speakers and headphones.
- Move the track out of `assets/music/` and start the game. Confirm the generated music takes over instead of silence or an error, then put it back.

## Your own art

- Copy one reference sprite from `assets/sprites/` into `assets/custom/sprites/`, change it, and start the game. Confirm it appears in the village. Remove it and confirm the built-in art returns.

## Evidence to retain

Keep a short recording or screenshots for a completed route, a revised resource decision, a changed world appearance, and a larger-text screen. Retain failed checks with exact replay steps and rerun those steps after the fix. Separate observed technical behavior from player opinions and untested assumptions.
