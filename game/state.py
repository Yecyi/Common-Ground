"""Deterministic, display-independent rules for Common Ground.

Finite supplies, one-time rewards, revisitable decisions, and a validated save
format make the narrative rules independently testable.
"""

import math
from typing import Any

from .story import (
    AMANI_START,
    BEAT_BY_ID,
    BEATS,
    DISPUTE_CALM,
    DISPUTE_INTRO,
    DISPUTE_OPTIONS,
    EPILOGUE_ALLOCATION,
    EPILOGUE_ARCS,
    EPILOGUE_BASE,
    EPILOGUE_DISPUTE,
    EPILOGUE_FACTORY,
    EPILOGUE_NO_ARCS,
    EPILOGUE_PLOTS,
    EPILOGUE_PLOTS_REVIEW,
    EPILOGUE_RETROFIT,
    EPILOGUE_REVIEW,
    INTRO,
    LORE,
    MIRA_START,
    NPCS,
    OUTCOME_TITLES,
    OUTCOMES,
    PLOTS_AFTER,
    PLOTS_INTRO,
    PLOTS_OPTIONS,
    PLOTS_REVIEW,
    RECAP,
    RECAP_PEOPLE,
    RECAP_PEOPLE_MISSED,
    ROWAN_START,
    THEO_START,
    Choice,
    Conversation,
    Result,
)


LITTER_IDS = {f"litter_{i}" for i in range(1, 7)}
CRATE_IDS = {f"crate_{i}" for i in range(1, 4)}
GARDEN_IDS = {f"garden_{i}" for i in range(1, 4)}
PEOPLE = {"mira", "rowan", "amani", "theo"}
TASK_IDS = LITTER_IDS | CRATE_IDS | GARDEN_IDS | {"pump", "quiet"}
QUIET_SPOTS = ("quiet_river", "quiet_garden")
DISPUTE_GOOD = {o.id for o in DISPUTE_OPTIONS if o.good}
DISPUTE_BAD = {o.id for o in DISPUTE_OPTIONS if not o.good}
KNOWN_COMPLETED = (
    LITTER_IDS | CRATE_IDS | GARDEN_IDS
    | {f"support_{person}" for person in PEOPLE}
    | {f"rejected_{person}" for person in PEOPLE}
    | {f"beat_{beat.id}" for beat in BEATS}
    | {f"rejected_{beat.id}" for beat in BEATS if any(not o.good for o in beat.options)}
    | {"pump", "quiet", "noticeboard", "council", "council_review", "factory", "factory_retrofit", "finish",
       "dispute", "rejected_dispute", "plots", "plots_review", *QUIET_SPOTS}
)
KNOWN_FLAGS = {
    "source_repaired", "garden_open", "support_network", "quiet_reflected",
    "council_held", "factory_shared", "balanced",
}
CHOICE_VALUES = {
    "rowan": {"listen", "space", "rush"},
    "amani": {"listen", "deliver", "dismiss"},
    "mira": {"listen", "coordinate", "command"},
    "theo": {"workshop", "restart", "reserve"},
    "allocation": {"needs", "equal", "queue"},
    "council_review": {"review"},
    "factory_retrofit": {"retrofit"},
    "plots": {o.id for o in PLOTS_OPTIONS},
    "plots_review": {"review"},
    "dispute": DISPUTE_GOOD | DISPUTE_BAD,
    **{beat.id: {o.id for o in beat.options} for beat in BEATS},
}
METRIC_WORDS = {"environment": "nature", "equity": "fair access", "resilience": "resilience"}
TENSION_FIRST_MEETING = 0.5


def effects_text(effects) -> str:
    return "  " + ", ".join(f"{amount:+d} {METRIC_WORDS[metric]}" for metric, amount in effects) + "." if effects else ""


def bump(outcome):
    """A review improves each group that was not already fully reached."""
    return tuple((label, min(3, level + 1)) for label, level in outcome)


class GameState:
    SAVE_VERSION = 2

    def __init__(self) -> None:
        self.metrics = {"environment": 24, "equity": 28, "resilience": 30}
        self.resources = {"supplies": 6, "seeds": 3}
        self.completed: set[str] = set()
        self.flags: set[str] = set()
        self.choices: dict[str, str] = {}
        self.journal = [{"title": "A town built around the river", "body": INTRO}]
        self.play_seconds = 0.0
        self.planted_at: dict[str, float] = {}

    def _change(self, **changes: int) -> None:
        for metric, amount in changes.items():
            self.metrics[metric] = max(0, min(100, self.metrics[metric] + amount))

    def _apply(self, effects) -> None:
        for metric, amount in effects:
            self._change(**{metric: amount})

    def _record(self, title: str, text: str, **extra: Any) -> Result:
        self.journal.append({"title": title, "body": text})
        return Result(True, title, text, **extra)

    def _spend(self, supplies: int = 0, seeds: int = 0) -> bool:
        if self.resources["supplies"] < supplies or self.resources["seeds"] < seeds:
            return False
        self.resources["supplies"] -= supplies
        self.resources["seeds"] -= seeds
        return True

    def _shortage(self, supplies: int = 0, seeds: int = 0) -> Result:
        needed = f"{supplies} supplies"
        if seeds:
            needed += f" and {seeds} seed"
        return Result(False, "Gather a little more", f"This needs {needed}. Clear litter and open the three salvage crates for supplies. Nothing has been spent.")

    def _support(self, person: str) -> None:
        self.completed.add(f"support_{person}")
        if all(f"support_{p}" in self.completed for p in PEOPLE):
            self.flags.add("support_network")

    @property
    def balance(self) -> float:
        """Overall health of the village, 0 to 1, weighted towards its weakest value."""
        values = list(self.metrics.values())
        return (0.5 * sum(values) / len(values) + 0.5 * min(values)) / 100

    def task_count(self) -> int:
        return len(self.completed & TASK_IDS)

    def garden_stage(self, garden_id: str) -> int:
        """0 unplanted, then 1-3 as the bed grows with time spent in the village."""
        if garden_id not in self.completed:
            return 0
        age = max(0.0, self.play_seconds - self.planted_at.get(garden_id, 0.0))
        return 1 if age < 45 else 2 if age < 120 else 3

    def objectives(self) -> list[tuple[str, bool]]:
        return [
            ("Repair the river pump (4 supplies)", "source_repaired" in self.flags),
            ("Restore all three garden beds (1 supply + 1 seed each)", "garden_open" in self.flags),
            ("Listen and work with Mira, Rowan, Amani and Theo", "support_network" in self.flags),
            ("Share six supplies at the neighbourhood circle", "council_held" in self.flags),
            ("Spend a quiet moment in the willow refuge", "quiet_reflected" in self.flags),
            ("Restore nature to at least 70", self.metrics["environment"] >= 70),
            ("Build fair access to at least 65", self.metrics["equity"] >= 65),
            ("Build community resilience to at least 65", self.metrics["resilience"] >= 65),
        ]

    @property
    def can_finish(self) -> bool:
        return all(done for _, done in self.objectives())

    # ----------------------------------------------------------------- guidance
    def next_step(self) -> tuple[str, str | None]:
        """A gentle, context-aware suggestion and the place id it points to.

        "collect" means the nearest remaining litter or salvage crate; the
        world resolves it. The suggestion never blocks any other order of play.
        """
        c, supplies = self.completed, self.resources["supplies"]
        if "support_mira" not in c:
            text = "Mira is willing to try again. Return and listen this time." if "rejected_mira" in c else "Talk to Mira near the crossroads. Walk close and press E."
            return text, "mira"
        if "pump" not in c:
            if supplies < 4:
                return "Collect supplies: clear litter or open a salvage crate. The pump needs 4.", "collect"
            return "Repair the river pump (4 supplies) to stop the leak.", "pump"
        if not GARDEN_IDS <= c:
            if supplies < 1:
                return "Collect a supply: each garden bed needs 1 supply and 1 seed.", "collect"
            return "Plant the community garden: each bed takes 1 supply and 1 seed.", "garden"
        for person in ("rowan", "amani"):
            if f"support_{person}" not in c:
                name = NPCS[person][0]
                again = f" {name} is willing to try again. Return and listen this time." if f"rejected_{person}" in c else ""
                return f"Listen to {name}.{again or ' Ask what would help; there is no single right answer.'}", person
        if "factory" not in c:
            if supplies < 3:
                return "Visit Theo near the old mill. His workshop plan costs 3 supplies; waiting costs nothing.", "theo"
            return "Visit Theo near the old mill. He has a decision to share.", "theo"
        if "council" not in c:
            if supplies < 6:
                return "Gather more supplies: the neighbourhood circle shares six.", "collect"
            return "Share six supplies at the neighbourhood circle.", "council"
        if "quiet" not in c:
            return "Spend a quiet moment in the willow refuge.", "quiet"
        if not self.can_finish:
            if self.metrics["environment"] < 70:
                if (LITTER_IDS | CRATE_IDS) - c:
                    return "Nature still needs care. Clear the remaining litter.", "collect"
                if "factory_shared" not in self.flags and supplies >= 3:
                    return "Nature still needs care. Theo would like to revisit the factory decision.", "theo"
            if self.metrics["equity"] < 65 and "council_review" not in c:
                return "Fair access still needs care. Review who was missed at the neighbourhood circle.", "council"
            for person in ("amani", "mira", "theo", "rowan"):
                if self.available_beat(person):
                    return f"{NPCS[person][0]} has more to say. Another conversation may help.", person
            if "garden_open" in self.flags and "plots" not in c:
                return "The garden sign-up board needs a decision about who gets a plot.", "plots"
            if "council" in c and "dispute" not in c:
                return "Voices are raised at the neighbourhood circle. Someone could help.", "dispute"
            return "Keep caring for the village: revisit neighbours and earlier decisions.", None
        return "Return to the neighbourhood circle to agree on the town's future.", "council"

    # ------------------------------------------------------------------- actions
    def perform(self, action_id: str) -> Result:
        if action_id == "finish":
            return self._finish()
        if action_id == "council":
            return Result(True, "The neighbourhood circle", self.dialogue("council").text)
        if action_id in self.completed:
            repeats = {
                "quiet": ("A place to pause", "The bench is here whenever you need it. There is no timer and nothing to earn. Listen to the river or simply sit for a while."),
                "noticeboard": ("The neighbourhood noticeboard", LORE),
                "pump": ("Clean water returns", "The patched outflow is holding. Neighbours will share regular maintenance instead of leaving it to one person."),
            }
            for spot in QUIET_SPOTS:
                repeats[spot] = repeats["quiet"]
            title, text = repeats.get(action_id, ("Already cared for", "This place has already been restored. Your work here is part of a lasting change; there is no need to repeat it."))
            return Result(True, title, text)
        if action_id in LITTER_IDS:
            self.completed.add(action_id)
            self.resources["supplies"] += 1
            self._change(environment=4)
            return self._record("A little breathing room", "You separate the waste and recover one reusable supply. The path is clearer. Cleanup helps today; repairing the outflow prevents new pollution.  +1 supply, +4 nature.")
        if action_id in CRATE_IDS:
            self.completed.add(action_id)
            self.resources["supplies"] += 3
            return self._record("Shared salvage", "Three usable supplies were tucked beneath the broken equipment. The inventory is public: these belong to the neighbourhood.  +3 supplies.")
        if action_id in GARDEN_IDS:
            if not self._spend(supplies=1, seeds=1):
                return self._shortage(1, 1)
            self.completed.add(action_id)
            self.planted_at[action_id] = self.play_seconds
            self._change(environment=6, resilience=2)
            if GARDEN_IDS <= self.completed:
                self.flags.add("garden_open")
            return self._record("Roots for tomorrow", "You plant a seedling and leave water nearby. The garden will take time and shared care to grow. Its care rota is open to everyone.  -1 supply, -1 seed; +6 nature, +2 resilience.")
        if action_id == "pump":
            if not self._spend(supplies=4):
                return self._shortage(4)
            self.completed.add("pump")
            self.flags.add("source_repaired")
            self._change(environment=16)
            return self._record("Fixing the source", "You patch the broken outflow and replace the pump filter. The leak stops. A public maintenance rota makes the repair a shared responsibility.  -4 supplies, +16 nature.")
        if action_id == "quiet":
            self.completed.add("quiet")
            self.flags.add("quiet_reflected")
            self._change(resilience=10)
            return self._record("Room to pause", "You settle beside the river. There is no demand to feel better. You notice the breeze, the ground, and the small work already done. A quiet place is one kind of support; people still need safe homes, care, and one another.  +10 resilience.")
        if action_id in QUIET_SPOTS:
            self.completed.add(action_id)
            return self._record(*self._quiet_spot(action_id))
        if action_id == "noticeboard":
            self.completed.add("noticeboard")
            return self._record("How the river changed", LORE)
        return Result(False, "Nothing to do here", "Explore the neighbourhood and talk to the people beside the paths.")

    def _quiet_spot(self, spot: str) -> tuple[str, str]:
        """Optional reflections: a journal entry once, and no rewards."""
        if spot == "quiet_river":
            if "source_repaired" in self.flags:
                return "Beside the water", "The river sounds different from here now: a steady, clear voice rather than a murmur. You watch it pass. Nobody asks anything of you, and nothing is earned by sitting."
            return "Beside the water", "The river moves slowly past, still carrying a faint film from the mill. You sit with that for a while. A place can be unfinished and still be a good place to rest."
        planted = len(GARDEN_IDS & self.completed)
        if planted == 3:
            body = "All three beds are planted. From here the rows look like a small, deliberate promise. You do not need to do anything about it today."
        elif planted:
            body = "Some beds are planted and some are still bare. From a distance you can see how little needs doing right now."
        else:
            body = "The beds are bare, but you can see where they will be. Nothing needs to happen yet."
        return "Above the garden", body

    # ----------------------------------------------------------------- dialogue
    def available_beat(self, person: str):
        """The next later scene for a resident, if its conditions are met."""
        for beat in BEATS:
            if beat.person == person and f"beat_{beat.id}" not in self.completed:
                return beat if self._beat_ready(beat) else None
        return None

    def _beat_ready(self, beat) -> bool:
        return (all(item in self.completed for item in beat.needs_completed)
                and all(flag in self.flags for flag in beat.needs_flags)
                and self.task_count() >= beat.min_tasks)

    def _beat_choices(self, beat) -> list[Choice]:
        hide_bad = f"rejected_{beat.id}" in self.completed
        return [Choice(f"{beat.id}:{o.id}", o.label, o.hint) for o in beat.options if o.good or not hide_bad]

    def _beat_text(self, beat) -> str:
        text = beat.intro_for(self.choices)
        if f"rejected_{beat.id}" in self.completed:
            text += " You can start again, if you're willing to listen this time."
        return text

    def dialogue(self, npc_id: str) -> Conversation:
        if npc_id not in NPCS:
            return Conversation("A neighbour", "Common Ground", "There is no conversation here yet.")
        name, role = NPCS[npc_id]
        if npc_id == "council":
            return self._council_dialogue()
        if npc_id == "theo":
            return self._theo_dialogue()
        if npc_id == "dispute":
            return self._dispute_dialogue()
        if npc_id == "plots":
            return self._plots_dialogue()
        supported = f"support_{npc_id}" in self.completed
        rejected = f"rejected_{npc_id}" in self.completed
        reflect = Choice("reflect", "What should we remember?", "Hear their reflection.")
        if supported:
            beat = self.available_beat(npc_id)
            if beat:
                return Conversation(name, role, self._beat_text(beat), [*self._beat_choices(beat), reflect], tension=0.35)
            after = {
                "mira": "We are keeping a public record of decisions now. The council still needs a real distribution plan. Check the journal if you're unsure what the neighbourhood needs next.",
                "rowan": ("The water smells different. I'm still having difficult nights, but I don't have to carry this alone. I signed up to water one bed; I can choose how much I take on." if "source_repaired" in self.flags else "Thank you for not asking me to explain everything. I might visit the quiet bench later. Stopping the leak would help make this place feel safer."),
                "amani": ("People are arranging deliveries instead of making everyone queue. Riverside helped write the plan. Being included changes who gets to shape the future." if "council_held" in self.flags else "Thank you for asking us. Bring what you've heard to the circle: check needs, arrange deliveries, and let people appeal a decision. Access is more than an open door."),
            }
            return Conversation(name, role, after[npc_id], [reflect])
        opening = {"rowan": ROWAN_START, "amani": AMANI_START, "mira": MIRA_START}[npc_id]
        if rejected:
            opening += " We can start again, if you're willing to listen this time."
        options = {
            "rowan": [
                Choice("listen", "Would you like company? We can talk or sit quietly.", "Offer choice and listen without pressure."),
                Choice("space", "I'll give you space and help make the garden safer.", "Respect boundaries and offer practical support."),
                Choice("rush", "Try to cheer up. We need you to keep working.", "Pressure can make it harder to ask for help."),
            ],
            "amani": [
                Choice("listen", "What would make the supply plan accessible for you?", "Let residents define what access means."),
                Choice("deliver", "Let's arrange deliveries with Riverside residents.", "Share practical work and decision-making."),
                Choice("dismiss", "The queue is the same for everyone. Isn't that fair?", "Equal rules can preserve unequal access."),
            ],
            "mira": [
                Choice("listen", "Let's ask who has been missing from these decisions.", "Make room for different needs and voices."),
                Choice("coordinate", "Let's build a shared care rota and a public inventory.", "Cooperate instead of relying on one helper."),
                Choice("command", "I'll decide what everyone gets. It will be quicker.", "Speed without participation can cost trust."),
            ],
        }[npc_id]
        if rejected:
            bad_id = {"rowan": "rush", "amani": "dismiss", "mira": "command"}[npc_id]
            options = [option for option in options if option.id != bad_id]
        return Conversation(name, role, opening, options, tension=0.35 if rejected else TENSION_FIRST_MEETING)

    def _theo_dialogue(self) -> Conversation:
        role = NPCS["theo"][1]
        if "factory" not in self.completed:
            return Conversation("Theo", role, THEO_START, [
                Choice("workshop", "Build the shared repair workshop.", "3 supplies. Safer work, shared training and cleaner water."),
                Choice("restart", "Restart the old line to bring jobs back sooner.", "2 supplies. Quick work, but the pollution risk remains."),
                Choice("reserve", "Keep the supplies while we make a safer plan.", "No cost now. Work and cleanup are still unresolved."),
            ], tension=0.6)
        choices: list[Choice] = []
        beat = self.available_beat("theo")
        if beat:
            text, tension = self._beat_text(beat), 0.35
            choices += self._beat_choices(beat)
        elif "factory_shared" in self.flags:
            text, tension = "We built a small workshop from the old equipment. It cannot replace every job. But trainees share decisions, and water safety is part of the work, not something to ignore. The neighbourhood has a practical place to learn and repair.", 0.0
        else:
            text, tension = "We still need a plan that protects both livelihoods and the river. A small shared retrofit could move us toward safe repair work, with residents and former workers deciding together.", 0.0
        if "factory_shared" not in self.flags:
            choices.append(Choice("retrofit", "Revisit the decision and fund the shared retrofit.", "3 supplies. Improve water safety and shared access."))
        choices.append(Choice("reflect", "What did this choice ask of us?" if "factory_shared" in self.flags else "Talk about the trade-off first.", "Hear Theo's reflection." if "factory_shared" in self.flags else "You can return when you're ready."))
        return Conversation("Theo", role, text, choices, tension=tension)

    def _council_dialogue(self) -> Conversation:
        if "council" not in self.completed:
            return Conversation("The neighbourhood circle", "Dilemma: six supplies, different needs", "Six supplies are ready to share. Some neighbours cannot stand in a queue; Riverside was missed by earlier deliveries. There is no perfect plan. What will you prioritise, and who will be involved in reviewing it?", [
                Choice("needs", "Prioritise urgent needs and arrange accessible delivery.", "6 supplies. Check needs with residents; keep the decision open to review."),
                Choice("equal", "Give every household the same share.", "6 supplies. A clear equal split; some barriers remain."),
                Choice("queue", "Let the first people in the queue collect first.", "6 supplies. Quick to organise; shift workers and remote homes may miss out."),
            ], tension=0.7)
        options = []
        if "council_review" not in self.completed:
            options.append(Choice("review", "Review who was missed and share the decisions.", "No supplies needed. Add delivery, representation and an appeal route."))
        options.append(Choice("finish", "Gather everyone and agree the next chapter.", "Finish when every balance goal in your journal is met."))
        options.append(Choice("reflect", "Reflect on what the neighbourhood still needs.", "See the remaining goals."))
        decision = {"needs": "The first deliveries followed the needs people described.", "equal": "Every household received the same share, but equal amounts did not remove every barrier.", "queue": "The queue moved quickly; several Riverside households and shift workers were missed."}[self.choices["allocation"]]
        if "council_review" in self.completed:
            decision += " Residents have now added accessible delivery, shared oversight and a way to challenge decisions."
        return Conversation("The neighbourhood circle", "A plan people can change", decision + " Balance means nature, fair access, and resilience improving together. The journal shows what still needs care.", options, tension=0.2)

    def _dispute_dialogue(self) -> Conversation:
        name, role = NPCS["dispute"]
        if "council" not in self.completed:
            return Conversation(name, role, "The circle has not met yet. There is nothing to settle here.")
        if "dispute" in self.completed:
            return Conversation(name, "A calmer table", DISPUTE_CALM, [Choice("reflect", "What helped?", "Hear a reflection.")])
        rejected = "rejected_dispute" in self.completed
        text = DISPUTE_INTRO.get(self.choices.get("theo"), DISPUTE_INTRO["default"])
        if rejected:
            text += " The shouting has dropped, but the tension has not gone. You can try again, and listen to both sides this time."
        options = [Choice(o.id, o.label, o.hint) for o in DISPUTE_OPTIONS if o.good or not rejected]
        return Conversation(name, role, text, options, tension=0.6 if rejected else 0.9)

    def _plots_dialogue(self) -> Conversation:
        name, role = NPCS["plots"]
        if "garden_open" not in self.flags:
            return Conversation(name, role, "The sign-up list is blank. Plant all three beds before neighbours choose plots.")
        if "plots" not in self.completed:
            return Conversation(name, role, PLOTS_INTRO, [Choice(o.id, o.label, o.hint) for o in PLOTS_OPTIONS], tension=0.5)
        choice = self.choices["plots"]
        text = PLOTS_AFTER[choice]
        if "plots_review" in self.completed:
            text += " A second round has widened access."
        options = []
        if "plots_review" not in self.completed and choice != "needs_first":
            options.append(Choice("review", PLOTS_REVIEW.label, PLOTS_REVIEW.hint))
        options.append(Choice("reflect", "Reflect on how the plots were shared.", "Hear a reflection."))
        return Conversation(name, "A decision you can revisit", text, options, tension=0.15)

    # ------------------------------------------------------------------ choices
    def choose(self, npc_id: str, choice_id: str) -> Result:
        legal = {choice.id for choice in self.dialogue(npc_id).choices}
        if choice_id not in legal:
            return Result(False, "Choose an available response", "This conversation has changed. Talk again to see the current choices.")
        if choice_id == "reflect":
            reflections = {
                "mira": "No single volunteer can carry a whole neighbourhood. Public decisions, shared care and a way to disagree make cooperation more durable.",
                "rowan": "Being heard helped me feel less alone. Recovery has its own pace, and a cleaner river cannot solve everything. Asking what someone wants matters more than finding the perfect words.",
                "amani": "Fairness includes who can arrive, who can speak, and who can change the plan. Keep checking who is missing.",
                "theo": "Work and a healthy river are both needs. A short-term choice can have costs; being willing to revisit it is part of responsibility.",
                "council": "Still to care for: " + "; ".join(label for label, done in self.objectives() if not done) if not self.can_finish else "The balance goals are ready. Gather the neighbourhood when you are ready to agree the next chapter.",
                "dispute": "A pause, a name for each fear and a shared need turned an argument into a conversation. People are rarely persuaded while they feel unheard.",
                "plots": "Who gets a place is a decision about whose time, space and access count. A fair process can still leave someone out, so it helps to keep the door open.",
            }
            return Result(True, "A moment to reflect", reflections[npc_id])
        if ":" in choice_id:
            return self._choose_beat(npc_id, choice_id)
        if npc_id == "council":
            return self._choose_council(choice_id)
        if npc_id == "theo":
            return self._choose_theo(choice_id)
        if npc_id == "dispute":
            return self._choose_dispute(choice_id)
        if npc_id == "plots":
            return self._choose_plots(choice_id)
        bad_choices = {"rowan": "rush", "amani": "dismiss", "mira": "command"}
        if choice_id == bad_choices[npc_id]:
            self.completed.add(f"rejected_{npc_id}")
            self.choices[npc_id] = choice_id
            self._change(equity=-3, resilience=-3)
            return self._record("A conversation worth revisiting", "Your neighbour steps back. The response did not leave much room for their experience or choices. You can return, acknowledge that, and ask what support they would prefer.  -3 fair access, -3 resilience.")
        self._support(npc_id)
        self.choices[npc_id] = choice_id
        if npc_id == "rowan":
            self._change(resilience=14 if choice_id == "listen" else 10, equity=4)
            return self._record("Rowan chooses their pace", "Rowan asks for a little company without questions, then offers to water a bed when they feel able. You agree to check in rather than assume. Their difficulties have not disappeared; they have more choice and support.", resolved=True)
        if npc_id == "amani":
            self._change(equity=14 if choice_id == "listen" else 12, resilience=6)
            return self._record("Riverside has a voice", "Amani explains the access barriers and joins the planning circle. Residents propose deliveries around shifts, step-free collection, and a way to request help privately. The council can now turn listening into a fairer system.", resolved=True)
        self._change(equity=6 if choice_id == "listen" else 4, resilience=6)
        return self._record("A shared way to care", "Mira opens the inventory and invites residents to share planning and maintenance. She sets a limit on her own hours. A care rota, rather than one tireless helper, will keep the work going.", resolved=True)

    def _choose_beat(self, npc_id: str, choice_id: str) -> Result:
        beat_id, option_id = choice_id.split(":", 1)
        beat = BEAT_BY_ID[beat_id]
        option = next(o for o in beat.options if o.id == option_id)
        self.choices[beat.id] = option.id
        self._apply(option.effects)
        self.completed.add(f"beat_{beat.id}" if option.good else f"rejected_{beat.id}")
        return self._record(option.title, option.text + effects_text(option.effects), resolved=option.good)

    def _choose_dispute(self, choice_id: str) -> Result:
        option = next(o for o in DISPUTE_OPTIONS if o.id == choice_id)
        self.choices["dispute"] = option.id
        self._apply(option.effects)
        self.completed.add("dispute" if option.good else "rejected_dispute")
        return self._record(option.title, option.text + effects_text(option.effects), resolved=option.good)

    def _choose_plots(self, choice_id: str) -> Result:
        if choice_id == "review":
            option = PLOTS_REVIEW
            self.completed.add("plots_review")
            self.choices["plots_review"] = "review"
            outcome = bump(OUTCOMES["plots"][self.choices["plots"]])
        else:
            option = next(o for o in PLOTS_OPTIONS if o.id == choice_id)
            self.completed.add("plots")
            self.choices["plots"] = option.id
            outcome = OUTCOMES["plots"][option.id]
        self._apply(option.effects)
        return self._record(option.title, option.text + effects_text(option.effects), outcome=outcome, outcome_title=OUTCOME_TITLES["plots"], resolved=True)

    def _choose_theo(self, choice_id: str) -> Result:
        if choice_id == "retrofit":
            if not self._spend(supplies=3):
                return self._shortage(3)
            self.completed.add("factory_retrofit")
            self.flags.add("factory_shared")
            self.choices["factory_retrofit"] = "retrofit"
            self._change(environment=10, equity=10, resilience=6)
            return self._record("A decision can change", "Workers and residents reshape the plan into a safe shared repair workshop. Not every lost job returns, but training and oversight are open to the neighbourhood.  -3 supplies; +10 nature, +10 fair access, +6 resilience.",
                                outcome=OUTCOMES["factory"]["retrofit"], outcome_title=OUTCOME_TITLES["factory"], resolved=True)
        cost = {"workshop": 3, "restart": 2, "reserve": 0}[choice_id]
        if not self._spend(supplies=cost):
            return self._shortage(cost)
        self.completed.add("factory")
        self._support("theo")
        self.choices["theo"] = choice_id
        extra = dict(outcome=OUTCOMES["factory"][choice_id], outcome_title=OUTCOME_TITLES["factory"], resolved=True)
        if choice_id == "workshop":
            self.flags.add("factory_shared")
            self._change(environment=4, equity=8, resilience=8)
            return self._record("Work that protects the river", "The old equipment becomes a community repair workshop. Workers share skills and residents share oversight. It costs more now and cannot replace every job, but water safety is built into the plan.  -3 supplies; +4 nature, +8 fair access, +8 resilience.", **extra)
        if choice_id == "restart":
            self._change(environment=-6, equity=2, resilience=2)
            return self._record("Work returns, with a cost", "A small line restarts and some wages return. The old process still risks the river. Theo wants a safer retrofit when supplies allow. You can revisit this decision.  -2 supplies; -6 nature, +2 fair access, +2 resilience.", **extra)
        self._change(resilience=2)
        return self._record("Space to make a better plan", "The supplies stay in the public store. People appreciate being consulted, but safer livelihoods still need a plan. Theo will help retrofit the workshop if the neighbourhood funds it later.  +2 resilience.", **extra)

    def _choose_council(self, choice_id: str) -> Result:
        if choice_id == "finish":
            return self._finish()
        if choice_id == "review":
            self.completed.add("council_review")
            self.choices["council_review"] = "review"
            self._change(equity=24, resilience=4)
            return self._record("Fairness is an ongoing practice", "Neighbours identify who was missed, organise deliveries of already allocated parcels, share oversight with Riverside, and add an appeal route. Revising access uses cooperation, not another pile of supplies.  +24 fair access, +4 resilience.",
                                outcome=bump(OUTCOMES["allocation"][self.choices["allocation"]]), outcome_title=OUTCOME_TITLES["allocation"], resolved=True)
        if not self._spend(supplies=6):
            return self._shortage(6)
        self.completed.add("council")
        self.flags.add("council_held")
        self.choices["allocation"] = choice_id
        gain, resilience, message = {
            "needs": (24, 6, "Residents describe urgent needs without having to share their stories publicly. Supplies reach people through accessible collection and deliveries. The plan remains open to review."),
            "equal": (14, 3, "Every household receives the same share. The rule is clear, but some households have greater needs and still face transport or mobility barriers. The circle can review who was missed."),
            "queue": (4, 0, "The queue moves quickly, but shift workers and several Riverside households miss collection. Neighbours ask to review delivery and representation. The plan can still change."),
        }[choice_id]
        self._change(equity=gain, resilience=resilience)
        return self._record("Six supplies, a shared responsibility", message + f"  -6 supplies; +{gain} fair access" + (f", +{resilience} resilience." if resilience else "."),
                            outcome=OUTCOMES["allocation"][choice_id], outcome_title=OUTCOME_TITLES["allocation"], resolved=True)

    def _finish(self) -> Result:
        if "finish" in self.completed:
            return Result(True, "Common Ground", "The neighbourhood's next chapter is already agreed. You can keep exploring, reading reflections, and visiting the people who will care for this place.")
        if not self.can_finish:
            missing = "; ".join(label for label, done in self.objectives() if not done)
            return Result(False, "There is still care to share", "Before the circle can agree its next chapter: " + missing + ".")
        self.completed.add("finish")
        self.flags.add("balanced")
        extra = " Workers and residents will share the workshop's next decisions." if "factory_shared" in self.flags else " Safer livelihoods remain an open question for the next meeting."
        return self._record("Common Ground", "The river runs clearer. Riverside has a voice. The garden and quiet bench are places people can use at their own pace. Rowan's difficult days have not vanished, and the neighbourhood still has work to do. But care no longer belongs to one person, and people can question and change the plan." + extra + " You have reached a balance of nature, fair access, and resilience. This is a beginning the neighbourhood can sustain together.")

    # ------------------------------------------------------- ending and review
    def recap(self) -> list[dict[str, str]]:
        """One row per decision, for the ethical review at the end of the story."""
        rows = []

        def row(label, chosen, benefited, missed, revisited, question):
            rows.append({"label": label, "chosen": chosen, "benefited": benefited, "missed": missed, "revisited": revisited, "question": question})

        questions = {
            "rowan": "What does support look like when someone says what they need?",
            "amani": "Who is missing from the decisions that affect them?",
            "mira": "How do you share a load that one person has been carrying?",
        }
        for person, (name, chosen_by_choice) in RECAP_PEOPLE.items():
            response = self.choices.get(person)
            if response in chosen_by_choice:
                again = f"rejected_{person}" in self.completed
                row(f"Talking with {name}", chosen_by_choice[response], f"{name}, who was asked rather than told.", RECAP_PEOPLE_MISSED,
                    "Revisited: a first response closed the door, and you came back." if again else "Their wishes came first from the start.", questions[person])
        factory = self.choices.get("theo")
        if factory:
            chosen, benefited, missed = RECAP["factory"]["values"][factory]
            revisited = "Revisited: you funded the shared retrofit." if "factory_retrofit" in self.completed else "Not revisited."
            row(RECAP["factory"]["label"], chosen, benefited, missed, revisited, RECAP["factory"]["question"])
        allocation = self.choices.get("allocation")
        if allocation:
            chosen, benefited, missed = RECAP["allocation"]["values"][allocation]
            revisited = "Revisited: the circle reviewed who was missed." if "council_review" in self.completed else "Not revisited."
            row(RECAP["allocation"]["label"], chosen, benefited, missed, revisited, RECAP["allocation"]["question"])
        plots = self.choices.get("plots")
        if plots:
            chosen, benefited, missed = RECAP["plots"]["values"][plots]
            if plots == "needs_first":
                revisited = "Not revisited."
            else:
                revisited = "Revisited: a second round widened access." if "plots_review" in self.completed else "Not revisited."
            row(RECAP["plots"]["label"], chosen, benefited, missed, revisited, RECAP["plots"]["question"])
        dispute = self.choices.get("dispute")
        if "dispute" in self.completed and dispute in DISPUTE_GOOD:
            chosen, benefited, missed = RECAP["dispute"]["values"][dispute]
            again = "rejected_dispute" in self.completed
            row(RECAP["dispute"]["label"], chosen, benefited, missed,
                "Revisited: a first response made the argument louder, and you returned." if again else "Calmed on the first attempt.", RECAP["dispute"]["question"])
        return rows

    def epilogue(self) -> list[str]:
        """The closing paragraphs, shaped by the decisions the player actually made."""
        paragraphs = [EPILOGUE_BASE]
        allocation = self.choices.get("allocation")
        if allocation:
            paragraphs.append(EPILOGUE_ALLOCATION[allocation] + (EPILOGUE_REVIEW if "council_review" in self.completed else ""))
        factory = self.choices.get("theo")
        if factory:
            paragraphs.append(EPILOGUE_RETROFIT if "factory_retrofit" in self.completed else EPILOGUE_FACTORY[factory])
        plots = self.choices.get("plots")
        if plots:
            paragraphs.append(EPILOGUE_PLOTS[plots] + (EPILOGUE_PLOTS_REVIEW if "plots_review" in self.completed else ""))
        if "dispute" in self.completed:
            paragraphs.append(EPILOGUE_DISPUTE)
        arcs = [EPILOGUE_ARCS[person] for person in ("rowan", "mira", "amani", "theo") if f"beat_{person}_3" in self.completed]
        paragraphs.append(" ".join(arcs) if arcs else EPILOGUE_NO_ARCS)
        return paragraphs

    # ------------------------------------------------------------------- saving
    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.SAVE_VERSION,
            "metrics": dict(self.metrics),
            "resources": dict(self.resources),
            "completed": sorted(self.completed),
            "flags": sorted(self.flags),
            "choices": dict(self.choices),
            "journal": [dict(entry) for entry in self.journal],
            "play_seconds": self.play_seconds,
            "planted_at": {key: self.planted_at[key] for key in sorted(self.planted_at)},
        }

    @classmethod
    def migrate(cls, data: Any) -> Any:
        """Upgrade older saves to the current layout without changing the original.

        Version 1 had no garden growth record. Beds from a version 1 save are
        treated as planted at the very start, so they appear fully grown.
        """
        if not isinstance(data, dict) or type(data.get("version")) is not int:
            raise ValueError("Unsupported or missing save version")
        if data["version"] == 1:
            data = dict(data)
            completed = data.get("completed")
            beds = sorted(GARDEN_IDS & set(completed)) if isinstance(completed, list) and all(isinstance(x, str) for x in completed) else []
            data["version"] = 2
            data["planted_at"] = {bed: 0.0 for bed in beds}
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        """Reject malformed saves without partially applying untrusted values."""
        data = cls.migrate(data)
        if data["version"] != cls.SAVE_VERSION:
            raise ValueError("Unsupported or missing save version")
        required = {"version", "metrics", "resources", "completed", "flags", "choices", "journal", "play_seconds", "planted_at"}
        if set(data) != required:
            raise ValueError("Save fields are missing or unexpected")
        for field, expected, maximum in (("metrics", {"environment", "equity", "resilience"}, 100), ("resources", {"supplies", "seeds"}, 99)):
            values = data[field]
            if not isinstance(values, dict) or set(values) != expected:
                raise ValueError(f"Invalid {field}")
            if any(type(value) is not int or not 0 <= value <= maximum for value in values.values()):
                raise ValueError(f"Invalid {field} values")
        if data["resources"]["seeds"] > 3:
            raise ValueError("Invalid seed inventory")
        for field, known in (("completed", KNOWN_COMPLETED), ("flags", KNOWN_FLAGS)):
            items = data[field]
            if not isinstance(items, list) or len(items) > len(known) or any(not isinstance(item, str) or item not in known for item in items) or len(set(items)) != len(items):
                raise ValueError(f"Invalid {field}")
        choices = data["choices"]
        if not isinstance(choices, dict) or any(key not in CHOICE_VALUES or not isinstance(value, str) or value not in CHOICE_VALUES[key] for key, value in choices.items()):
            raise ValueError("Invalid story choices")
        entries = data["journal"]
        if not isinstance(entries, list) or not 1 <= len(entries) <= 200:
            raise ValueError("Invalid journal")
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"title", "body"}:
                raise ValueError("Invalid journal entry")
            if not isinstance(entry["title"], str) or not 1 <= len(entry["title"]) <= 120 or not isinstance(entry["body"], str) or not 1 <= len(entry["body"]) <= 4000:
                raise ValueError("Invalid journal text")
        seconds = data["play_seconds"]
        if type(seconds) not in (int, float) or not 0 <= seconds <= 1_000_000_000 or not math.isfinite(seconds):
            raise ValueError("Invalid elapsed time")
        completed = set(data["completed"])
        flags = set(data["flags"])
        planted = data["planted_at"]
        if not isinstance(planted, dict) or set(planted) != GARDEN_IDS & completed:
            raise ValueError("Invalid garden growth record")
        if any(type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1_000_000_000 for value in planted.values()):
            raise ValueError("Invalid garden growth times")
        relations = {
            "source_repaired": "pump" in completed,
            "garden_open": GARDEN_IDS <= completed,
            "support_network": all(f"support_{p}" in completed for p in PEOPLE),
            "quiet_reflected": "quiet" in completed,
            "council_held": "council" in completed,
            "factory_shared": choices.get("theo") == "workshop" or "factory_retrofit" in completed,
            "balanced": "finish" in completed,
        }
        if any((flag in flags) != expected for flag, expected in relations.items()):
            raise ValueError("Inconsistent story flags")
        if ("council" in completed) != ("allocation" in choices) or ("factory" in completed) != ("theo" in choices):
            raise ValueError("Inconsistent story decisions")
        if ("council_review" in completed) != ("council_review" in choices) or ("factory_retrofit" in completed) != ("factory_retrofit" in choices):
            raise ValueError("Inconsistent reviewed decisions")
        if "council_review" in completed and "council" not in completed or "factory_retrofit" in completed and "factory" not in completed:
            raise ValueError("A decision cannot be reviewed before it is made")
        if data["resources"]["seeds"] != 3 - len(GARDEN_IDS & completed):
            raise ValueError("Inconsistent seed inventory")
        for person, good, bad in (
            ("rowan", {"listen", "space"}, "rush"),
            ("amani", {"listen", "deliver"}, "dismiss"),
            ("mira", {"listen", "coordinate"}, "command"),
        ):
            response = choices.get(person)
            if (f"support_{person}" in completed) != (response in good):
                raise ValueError("Inconsistent support conversation")
            if response == bad and f"rejected_{person}" not in completed:
                raise ValueError("Inconsistent conversation history")
            if f"rejected_{person}" in completed and response is None:
                raise ValueError("Missing conversation history")
        if ("support_theo" in completed) != ("factory" in completed):
            raise ValueError("Inconsistent factory conversation")
        cls._validate_later_scenes(completed, flags, choices)
        expected_supplies = (
            6 + len(LITTER_IDS & completed) + 3 * len(CRATE_IDS & completed)
            - len(GARDEN_IDS & completed)
            - 4 * ("pump" in completed)
            - 6 * ("council" in completed)
            - {"workshop": 3, "restart": 2, "reserve": 0}.get(choices.get("theo"), 0)
            - 3 * ("factory_retrofit" in completed)
        )
        if data["resources"]["supplies"] != expected_supplies:
            raise ValueError("Inconsistent supply inventory")
        state = cls()
        state.metrics = dict(data["metrics"])
        state.resources = dict(data["resources"])
        state.completed = completed
        state.flags = flags
        state.choices = dict(choices)
        state.journal = [dict(entry) for entry in entries]
        state.play_seconds = float(seconds)
        state.planted_at = {key: float(value) for key, value in planted.items()}
        if "finish" in completed and not state.can_finish:
            raise ValueError("The saved ending does not meet the balance goals")
        return state

    @staticmethod
    def _validate_later_scenes(completed: set[str], flags: set[str], choices: dict[str, str]) -> None:
        """Resident scenes, the garden plots and the circle dispute follow their own prerequisites."""
        tasks = len(completed & TASK_IDS)
        for beat in BEATS:
            good = {o.id for o in beat.options if o.good}
            bad = {o.id for o in beat.options if not o.good}
            done, rejected = f"beat_{beat.id}" in completed, f"rejected_{beat.id}" in completed
            response = choices.get(beat.id)
            if done != (response in good) or (response in bad and not rejected) or (rejected and response is None):
                raise ValueError("Inconsistent resident scene")
            if (done or rejected) and not (
                all(item in completed for item in beat.needs_completed)
                and all(flag in flags for flag in beat.needs_flags)
                and tasks >= beat.min_tasks
            ):
                raise ValueError("A resident scene was completed before its conditions")
        response = choices.get("dispute")
        done, rejected = "dispute" in completed, "rejected_dispute" in completed
        if done != (response in DISPUTE_GOOD) or (response in DISPUTE_BAD and not rejected) or (rejected and response is None):
            raise ValueError("Inconsistent circle dispute")
        if (done or rejected) and "council" not in completed:
            raise ValueError("The dispute cannot happen before the circle meets")
        if ("plots" in completed) != ("plots" in choices) or ("plots_review" in completed) != ("plots_review" in choices):
            raise ValueError("Inconsistent garden plots")
        if "plots" in completed and not GARDEN_IDS <= completed:
            raise ValueError("Plots cannot be shared before the beds are planted")
        if "plots_review" in completed and ("plots" not in completed or choices.get("plots") == "needs_first"):
            raise ValueError("A plots decision cannot be reviewed before it is made")
