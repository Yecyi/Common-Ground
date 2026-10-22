"""Part Two: Storm Season.

After the first ending the village learns that a storm is coming. There are six
hours of daylight to share between things that all matter, and not enough for all
of them. The night that follows is shaped by what was done, what was left, and
the decisions made on the way. Nothing here costs supplies and nothing is timed:
the hours are a way of choosing, not a clock. Every outcome leads on to recovery.
"""

from .story import NPCS, Choice, Conversation, Result, bump, effects_text

HOURS_TOTAL = 6

# Preparation tasks: cost in hours, a label, a hint, and what has to be true before it is offered.
PREP = {
    "prep_hall": dict(cost=2, label="Open the Common Hall as a shelter.", hint="Beds, water and heat for neighbours who cannot stay home.", needs=()),
    "prep_drains": dict(cost=2, label="Clear the Riverside drains with Amani's neighbours.", hint="Keep water off Riverside's doorsteps.", needs=()),
    "prep_clinic": dict(cost=1, label="Move the health post's medicine and charge its lamps with Noor.", hint="So care can carry on in the dark.", needs=("support_noor",)),
    "prep_odile": dict(cost=1, label="Visit Odile and agree a safe place for the night.", hint="Older neighbours should not be alone in a storm.", needs=("support_odile",)),
    "prep_rowan": dict(cost=1, label="Spend the afternoon with Rowan.", hint="Company, if they want it. Loud nights are hard.", needs=("support_rowan",)),
    "prep_pump": dict(cost=1, label="Reinforce the pump housing with Theo.", hint="Protect the repair that made the river safer.", needs=("source_repaired",)),
    "prep_gauge": dict(cost=1, label="Set a river gauge and flood markers with Kit.", hint="Early warning, with a line at which everyone moves.", needs=("support_kit",)),
}
PREP_ORDER = tuple(PREP)
FLAG_NEEDS = {"source_repaired"}
SCENES = ("storm_s1", "storm_s2", "storm_s3", "storm_s4", "storm_s5")
SCENE_CHOICES = {
    "storm_s1": {"doors", "sandbags", "hall_now"},
    "storm_s2": {"elders_first", "families_first", "share"},
    "storm_s3": {"clinic", "homes", "door"},
    "storm_s4": {"sit", "task", "carers"},
    "storm_s5": {"dawn"},
}
RECOVER = ("recover_streets", "recover_homes", "recover_hall")
PART_TWO_IDS = {"storm_forecast", "storm_begin", "storm_done", *PREP, *SCENES, *RECOVER}
SCENE_TENSION = {"storm_s1": .8, "storm_s2": .75, "storm_s3": .85, "storm_s4": .6, "storm_s5": .2}

HALL_GROUPS = ("Elders", "Families with children", "Riverside households", "Late arrivals")
HALL_LEVELS = {
    True: {"elders_first": (3, 2, 2, 1), "families_first": (2, 3, 2, 1), "share": (2, 2, 2, 2)},
    False: {"elders_first": (2, 1, 1, 0), "families_first": (1, 2, 1, 0), "share": (1, 1, 1, 1)},
}

FORECAST_TEXT = (
    "The forecast pinned beside the minutes gives the storm two days. The river is clearer than it has been in years, "
    "but nobody knows how the village will hold. Mira suggests meeting at the Common Hall on Hillside to plan. "
    "There are six hours of daylight to share between checking on neighbours and preparing the village. "
    "You cannot do everything. Choose who and what matters most, and talk with the people you have met along the way."
)

# What each preparation did, for the journal. Earlier chapters change how well it worked.
PREP_RESULTS = {
    "prep_hall": ("The Hall is ready", "You air out the Common Hall, borrow cots from three households and fill the water tanks. It will not hold everyone, but it will hold a lot.", (("resilience", 2),)),
    "prep_drains": ("The drains run clear", "Amani's neighbours arrive with rakes, gloves and a wheelbarrow, and by dusk the Riverside drains run clear.", (("equity", 2), ("environment", 1))),
    "prep_clinic": ("The post is ready for the dark", "Noor moves the medicine to the high shelf and charges every lamp. 'If the power goes, we still have a clinic,' she says.", (("resilience", 2),)),
    "prep_odile": ("A safe place for Odile", "Odile will not leave her armchair until you promise to carry her stories along too. She agrees to spend the night in the Hall, with her own blanket.", (("resilience", 1), ("equity", 1))),
    "prep_rowan": ("An afternoon with Rowan", "Rowan says a storm is easier to face if they are not at the window alone. You spend the afternoon repotting seedlings and saying very little.", (("resilience", 3),)),
    "prep_pump": ("The pump is strapped down", "Theo helps you strap down the pump housing and tape the filter. 'This pump has been through enough already,' he says.", (("environment", 2),)),
    "prep_gauge": ("Markers on the bridge", "Kit paints flood markers on the bridge post and shows you how to read the gauge. 'At the red line, we move people,' they say.", (("resilience", 1),)),
}
PREP_EXTRA = {
    "prep_drains": ("beat_amani_3", " The appeal route you built means people know who to call, and forty neighbours turn up."),
    "prep_clinic": ("beat_noor_3", " The extended hours mean two volunteers are already trained and ready to stay."),
    "prep_hall": ("beat_mira_3", " Mira's published rota means every shift in the Hall already has a name beside it."),
    "prep_gauge": ("beat_kit_3", " Kit's seat on the circle means the warning goes straight to the people who decide."),
}
# For the recap: who each preparation protected, short.
PREP_BENEFIT = {
    "prep_hall": ("the Hall's guests", "a shelter that could not be set up"),
    "prep_drains": ("Riverside's doorsteps", "Riverside's drains"),
    "prep_clinic": ("patients on the health post's night shift", "the health post's lamps and medicine"),
    "prep_odile": ("Odile", "Odile's safety"),
    "prep_rowan": ("Rowan", "an afternoon with Rowan"),
    "prep_pump": ("the pump and the river", "the pump housing"),
    "prep_gauge": ("early warning on the river", "the river gauge"),
}
PREP_SHORT = {
    "prep_hall": "opened the Hall", "prep_drains": "cleared the drains", "prep_clinic": "readied the health post",
    "prep_odile": "visited Odile", "prep_rowan": "spent the afternoon with Rowan",
    "prep_pump": "reinforced the pump", "prep_gauge": "set the river gauge",
}

SCENE_OPTIONS = {
    "storm_s1": {
        "doors": ("Go door to door in Riverside with Amani, making sure everyone can get out.", "People first; the houses take their chances."),
        "sandbags": ("Use the hour to sandbag the lowest doorways.", "Protect the homes; fewer people are checked on."),
        "hall_now": ("Call everyone at risk to the Common Hall straight away.", "Safe and early, but the Hall fills sooner."),
    },
    "storm_s2": {
        "elders_first": ("Give the beds to elders and anyone with medical needs first.", "Care for the most vulnerable; families wait."),
        "families_first": ("Give the beds to families with small children first.", "Protect the children; elders sit up in chairs."),
        "share": ("Pool the space: everyone gets a little and nobody is turned away.", "Fair shares, but crowded for everyone."),
    },
    "storm_s3": {
        "clinic": ("Go to the health post and help Noor.", "Medicine and light for the patients."),
        "homes": ("Walk the dark streets and check on neighbours who stayed at home.", "Reach the people who did not come."),
        "door": ("Stay at the Hall door and keep the log of who is inside.", "Know who is safe, but you cannot be everywhere."),
    },
    "storm_s4": {
        "sit": ("Sit with whoever is frightened, and do not try to fix anything.", "Presence, not solutions."),
        "task": ("Offer small jobs to anyone who wants one.", "Busy hands help some people and are unwelcome to others."),
        "carers": ("Take over the door so Mira and Noor can sleep for an hour.", "Carers need care too."),
    },
    "storm_s5": {"dawn": ("Step outside into the first light.", "The storm is over. The work of recovery begins.")},
}
SCENE_RECAP = {
    "storm_s1": ("Rising water in Riverside", "Who was checked on, and which homes were protected?",
                 {"doors": ("Went door to door with Amani.", "Riverside households who needed help to move.", "The lowest doorways, which took the water."),
                  "sandbags": ("Sandbagged the lowest doorways.", "Homes at the water's edge.", "Neighbours who needed a hand to move and were not checked on."),
                  "hall_now": ("Called everyone at risk to the Hall.", "Riverside residents, who were out of danger early.", "The Hall, which filled sooner, and the homes left empty.")}),
    "storm_s2": ("The Hall fills", "Whose need should come first when there are not enough beds?",
                 {"elders_first": ("Gave the beds to elders and those with medical needs.", "Elders and people with medical needs.", "Families with children, who made a nest of coats."),
                  "families_first": ("Gave the beds to families with small children.", "Children and their parents.", "Elders, who sat up in chairs."),
                  "share": ("Pooled the space so nobody was turned away.", "Everyone, a little.", "Nobody was fully comfortable, and the late arrivals had the least space.")}),
    "storm_s3": ("Lights out", "When you can only be in one place, who do you leave?",
                 {"clinic": ("Helped Noor at the health post.", "The patients at the post.", "Neighbours who stayed at home, and the Hall door."),
                  "homes": ("Walked the dark streets checking on neighbours.", "People who had not come to the Hall.", "The health post, where Noor managed alone."),
                  "door": ("Kept the log at the Hall door.", "The people inside, who were counted and safe.", "Anyone who stayed home, and the health post.")}),
    "storm_s4": ("The long hours", "How do you look after people, and the people who look after others?",
                 {"sit": ("Sat with whoever was frightened.", "The frightened, who were not left alone with it.", "The door and the tea table, which ran on fewer hands."),
                  "task": ("Offered small jobs to anyone who wanted one.", "People who wanted busy hands.", "People who wanted only to sit, who were gently left alone."),
                  "carers": ("Covered the door so the carers could sleep.", "Mira and Noor, who rested for an hour.", "Anyone who wanted company while you were on the door.")}),
    "storm_s5": ("Dawn", "What did the night show about who the village looked after?", {"dawn": ("Stepped outside into the first light.", "Everyone who made it through the night.", "Whatever the storm cost, which recovery has to answer.")}),
}


class StormMixin:
    """Part Two rules for the game state. Everything here is derived from completed ids and choices."""

    # ------------------------------------------------------------------ phase
    def storm_phase(self) -> str:
        c = self.completed
        if "finish" not in c:
            return "none"
        if "storm_done" in c:
            return "done"
        if "storm_s5" in c:
            return "aftermath"
        if "storm_begin" in c:
            return "night"
        if "storm_forecast" in c:
            return "forecast"
        return "invited"

    def weather(self) -> str:
        return {"forecast": "overcast", "night": "storm", "aftermath": "aftermath"}.get(self.storm_phase(), "clear")

    def prep_hours_left(self) -> int:
        return HOURS_TOTAL - sum(PREP[task]["cost"] for task in PREP if task in self.completed)

    def prep_ready(self, task: str) -> bool:
        """Offered when everything it needs is true and it has not been done."""
        return task not in self.completed and all((item in self.flags if item in FLAG_NEEDS else item in self.completed) for item in PREP[task]["needs"])

    def prep_available(self) -> list[str]:
        return [task for task in PREP_ORDER if self.prep_ready(task)]

    def next_scene(self):
        return next((scene for scene in SCENES if scene not in self.completed), None)

    def storm_scene_pending(self) -> bool:
        return self.storm_phase() == "night" and self.next_scene() is not None

    def recovery_remaining(self) -> list[str]:
        return [task for task in RECOVER if task not in self.completed]

    # ----------------------------------------------------- what the night did
    def prepared(self, task: str) -> bool:
        return task in self.completed

    def homes_flooded(self) -> int:
        """How many Riverside homes took water: none if the drains were cleared; fewer with sandbags."""
        if self.prepared("prep_drains"):
            return 0
        return max(0, 2 - (1 if self.choices.get("storm_s1") == "sandbags" else 0))

    def odile_alone(self) -> bool:
        return "support_odile" in self.completed and not self.prepared("prep_odile") and self.choices.get("storm_s3") != "homes"

    def storm_toll(self) -> tuple:
        env = -(4 if self.prepared("prep_pump") else 8)
        equity = -2 * self.homes_flooded()
        resilience = -(3 + (2 if self.odile_alone() else 0) + (0 if self.prepared("prep_hall") else 2))
        return tuple((metric, amount) for metric, amount in (("environment", env), ("equity", equity), ("resilience", resilience)) if amount)

    # --------------------------------------------------------------- dialogue
    def _storm_dialogue(self) -> Conversation:
        name, role = NPCS["storm"]
        phase = self.storm_phase()
        reflect = Choice("reflect", "Talk about the trade-offs.", "Hear a reflection.")
        if phase in ("none", "invited"):
            return Conversation(name, role, "Nothing has been posted here yet.")
        if phase == "forecast":
            return self._planning_table(name, role, reflect)
        if phase == "night":
            return self._storm_scene(name)
        if phase == "aftermath":
            left = self.recovery_remaining()
            text = "The storm has passed. The board lists what is left to do: " + "; ".join({"recover_streets": "clear the square", "recover_homes": "dry out Riverside's homes", "recover_hall": "close the Hall"}[t] for t in left) + "." if left else "Everything on the board is done. The circle is ready to talk about what the storm showed."
            return Conversation(name, "After the storm", text, [reflect])
        return Conversation(name, "Storm Season", "Storm Season is over. The board is bare except for a note in Mira's handwriting: 'Thank you.'", [reflect])

    def _planning_table(self, name, role, reflect) -> Conversation:
        left = self.prep_hours_left()
        done = [PREP_SHORT[t] for t in PREP_ORDER if t in self.completed]
        text = f"{left} of {HOURS_TOTAL} hours of daylight are left. Each task takes the hours shown, and nothing here has a right answer. You can begin the night whenever you are ready, with hours unspent."
        if done:
            text += " So far you have " + ", ".join(done) + "."
        unmet = [p for p in ("kit", "odile", "noor") if f"support_{p}" not in self.completed]
        if unmet:
            text += " There are neighbours beyond Riverside you have not met, and the people you know best are the ones you can help in time."
        choices = [Choice(task, f"{PREP[task]['label']} ({PREP[task]['cost']} hour{'s' if PREP[task]['cost'] > 1 else ''})", PREP[task]["hint"]) for task in self.prep_available()]
        choices.append(Choice("begin", "Begin the night.", "Unspent hours are kept as rest. Once the storm starts you cannot prepare any more."))
        choices.append(reflect)
        return Conversation(name, role, text, choices, tension=.3)

    def _storm_scene(self, name) -> Conversation:
        scene = self.next_scene()
        number = SCENES.index(scene) + 1
        text = getattr(self, f"_text_{scene}")()
        choices = [Choice(key, label, hint) for key, (label, hint) in SCENE_OPTIONS[scene].items()]
        return Conversation(name, f"Storm night, part {number} of 5", text, choices, tension=SCENE_TENSION[scene])

    # ------------------------------------------------------------ scene texts
    def _text_storm_s1(self) -> str:
        text = "By evening the rain is falling in sheets, and Riverside Road is the first place to feel it."
        text += (" The drains you cleared carry the first surge away, and the road stays passable." if self.prepared("prep_drains")
                 else " The drains are choked with leaves and plastic, and water is already crossing the road and nosing under two front doors.")
        text += (" Kit's gauge on the bridge shows the river a hand's width below the red line, and Kit calls out the number every ten minutes." if self.prepared("prep_gauge")
                 else " Nobody is sure how high the river will climb.")
        return text

    def _text_storm_s2(self) -> str:
        if self.prepared("prep_hall"):
            text = "The Common Hall is warm and lit. Cots line the walls, the water tanks are full, and Mira has a clipboard."
        else:
            text = "The Common Hall is cold and nobody has set up beds. Neighbours arrive soaked and sit on the floor while Mira organises blankets from the coats on the pegs."
        if self.choices.get("storm_s1") == "hall_now":
            text += " Because you called people early, the Hall is already crowded."
        return text + " Forty people have come, and the beds will not stretch to all of them."

    def _text_storm_s3(self) -> str:
        text = ("At eleven the power fails across the valley. The health post is running on the lamps you charged, and the medicine is already on the high shelf." if self.prepared("prep_clinic")
                else "At eleven the power fails across the valley. At the health post Noor is working by phone light, and the medicine fridge has gone quiet.")
        if self.prepared("prep_odile"):
            text += " Odile is in the Hall, wrapped in her blanket and telling the story of the flood of '74 to three children."
        elif "support_odile" in self.completed:
            text += " Odile is still at home in the dark, and Noor says she has not answered the phone."
        else:
            text += " An older neighbour on Orchard Lane has not been seen since the afternoon."
        return text + " You have a pair of hands, and you cannot be everywhere."

    def _text_storm_s4(self) -> str:
        if self.prepared("prep_rowan"):
            text = "Near three in the morning the Hall settles into the hush of tired people. Rowan is handing out blankets. They look worn out, but it is the kind of tired that comes with having a job to do."
        elif "support_rowan" in self.completed:
            text = "Near three in the morning Rowan appears in the doorway, soaked and pale. The pipes have been rattling again, they say, and they could not stay at home alone."
        else:
            text = "Near three in the morning a quiet neighbour appears in the doorway, soaked and pale, and says they could not stay at home alone."
        text += (" Mira's rota means other people have been taking shifts, so she is only tired, not spent." if "beat_mira_2" in self.completed
                 else " Mira has been awake for twenty hours and keeps saying she is fine.")
        return text

    def _text_storm_s5(self) -> str:
        text = "The rain thins at five. By six the river is brown and high but inside its banks."
        text += (" The pump housing held." if self.prepared("prep_pump") else " The pump housing cracked in the night, and for an hour the old outflow channel ran again.")
        flooded = self.homes_flooded()
        text += (f" {flooded} Riverside homes took water." if flooded > 1 else " One Riverside home took water." if flooded == 1 else " Riverside stayed dry.")
        if self.odile_alone():
            text += " Odile spent the night alone at home, cold but safe."
        return text + " The village is still here. What it cost is for you to see."

    # ---------------------------------------------------------------- choices
    def _choose_storm(self, choice_id: str) -> Result:
        phase = self.storm_phase()
        if phase == "forecast":
            if choice_id == "begin":
                return self._begin_storm()
            return self._prepare(choice_id)
        scene = self.next_scene()
        return getattr(self, f"_resolve_{scene}")(choice_id)

    def _prepare(self, task: str) -> Result:
        cost = PREP[task]["cost"]
        if cost > self.prep_hours_left():
            return Result(False, "Not enough daylight", f"This takes {cost} hours and only {self.prep_hours_left()} are left. Nothing has been spent. Choose something shorter, or begin the night.")
        self.completed.add(task)
        title, text, effects = PREP_RESULTS[task]
        extra = PREP_EXTRA.get(task)
        if extra and extra[0] in self.completed:
            text += extra[1]
        self._apply(effects)
        return self._record(title, f"{text}  Hours left: {self.prep_hours_left()}." + effects_text(effects), resolved=True)

    def _begin_storm(self) -> Result:
        self.completed.add("storm_begin")
        used = HOURS_TOTAL - self.prep_hours_left()
        return self._record("The storm arrives", f"You spent {used} of {HOURS_TOTAL} hours preparing. The light goes early, and the first heavy rain hits the Hall roof like gravel. Whatever was not done now has to be faced as it is.")

    def _finish_scene(self, scene: str, choice_id: str, title: str, text: str, effects=(), **extra) -> Result:
        self.completed.add(scene)
        self.choices[scene] = choice_id
        self._apply(effects)
        return self._record(title, text + effects_text(effects), **extra)

    def _resolve_storm_s1(self, choice: str) -> Result:
        drains = self.prepared("prep_drains")
        if choice == "doors":
            text = ("Everyone in Riverside is accounted for within the hour, and a few neighbours join you at the next door." if drains
                    else "You help three households carry what they can upstairs. Two homes still take water, but everyone is accounted for.")
            return self._finish_scene("storm_s1", choice, "Door to door", text, (("equity", 2), ("resilience", 2)), resolved=True)
        if choice == "sandbags":
            text = ("The sandbags are barely needed, but the doorways stay dry and the neighbours are glad of the work." if drains
                    else "The bags hold at three doorways. You learn later that a neighbour at the end of the road needed help to move, and waited alone.")
            return self._finish_scene("storm_s1", choice, "Sandbags", text, (("equity", 1),) if drains else (("equity", 1), ("resilience", -1)), resolved=True)
        return self._finish_scene("storm_s1", choice, "Everyone to the Hall", "Within the hour thirty people are crossing the bridge in raincoats. Riverside is nearly empty, which means nobody is in danger there, and the Hall is going to be full.", (("resilience", 2),), resolved=True)

    def _resolve_storm_s2(self, choice: str) -> Result:
        prepared = self.prepared("prep_hall")
        levels = list(HALL_LEVELS[prepared][choice])
        if self.choices.get("storm_s1") == "hall_now":
            levels[3] = max(0, levels[3] - 1)
        outcome = tuple(zip(HALL_GROUPS, levels))
        titles = {"elders_first": ("Beds for the elders", "Elders and anyone on medication get the beds. Families make a nest of coats near the stove, and some of the children fall asleep sitting up. Nobody complains out loud."),
                  "families_first": ("Beds for the children", "Families with small children get the beds. A few elders sit up in chairs with blankets and say they are fine, in the voice people use when they are not."),
                  "share": ("Everyone a little", "You pool the space: every person gets a share of mattress, a blanket and a square of floor. It is crowded, and warmer than expected, and nobody is turned away.")}
        title, text = titles[choice]
        effects = (("equity", 4), ("resilience", 1 if prepared else -1)) if choice == "share" else (("equity", 3), ("resilience", 1))
        return self._finish_scene("storm_s2", choice, title, text, effects, outcome=outcome, outcome_title="Who got a bed", resolved=True)

    def _resolve_storm_s3(self, choice: str) -> Result:
        if choice == "clinic":
            if self.prepared("prep_clinic"):
                return self._finish_scene("storm_s3", choice, "The lamp and the patients", "Noor needs less than she feared. You hold the lamp while she sees four patients, and talk with two who are frightened.", (("resilience", 2),), resolved=True)
            return self._finish_scene("storm_s3", choice, "Saving the medicine", "You carry the insulin to the Hall's generator before it warms, then hold the lamp while Noor sees patients. 'Thank you,' she says. 'I couldn't have done that and the rest.'", (("resilience", 3), ("equity", 2)), resolved=True)
        if choice == "homes":
            if "support_odile" in self.completed and not self.prepared("prep_odile"):
                return self._finish_scene("storm_s3", choice, "Found by torchlight", "You find Odile by torchlight, cold, calm and delighted to see you. She tells you about the flood of '74 while you walk her to the Hall, and for once nobody hurries her.", (("equity", 2), ("resilience", 3)), resolved=True)
            return self._finish_scene("storm_s3", choice, "The empty streets", "You find a young man on Orchard Lane who had not heard the call, and walk him to the Hall. He had a torch and nowhere to put it.", (("equity", 3), ("resilience", 1)), resolved=True)
        alone = "support_odile" in self.completed and not self.prepared("prep_odile")
        text = "The log fills with names and the count stays honest. " + ("Odile's name is not on it. At dawn you learn she spent the night alone in the dark, cold but safe." if alone else "Everyone you expected is on it.")
        return self._finish_scene("storm_s3", choice, "The log at the door", text, (("equity", 1), ("resilience", -1 if alone else 1)), resolved=not alone)

    def _resolve_storm_s4(self, choice: str) -> Result:
        if choice == "sit":
            return self._finish_scene("storm_s4", choice, "Nothing to fix", "You sit. Someone starts to talk about the last time the river rose, and then someone else does. At some point you notice you have been talking about something else entirely.", (("resilience", 3),), resolved=True)
        if choice == "task":
            text = ("Rowan runs the tea table with quiet pride, and a small queue of tired people thank them by name." if self.prepared("prep_rowan")
                    else "Most people take a job gratefully. A few shake their head and you leave them alone, which turns out to be the right thing to do.")
            return self._finish_scene("storm_s4", choice, "Busy hands", text, (("resilience", 2), ("equity", 1)), resolved=True)
        text = ("Mira goes without argument, which is how you know she trusts the rota. Noor sleeps sitting up." if "beat_mira_2" in self.completed
                else "Mira argues, then falls asleep mid-sentence. Noor does not argue at all.")
        return self._finish_scene("storm_s4", choice, "Looking after the carers", text, (("resilience", 3),), resolved=True)

    def _resolve_storm_s5(self, choice: str) -> Result:
        toll = self.storm_toll()
        text = self._text_storm_s5() + " The night took its toll."
        return self._finish_scene("storm_s5", choice, "Dawn", text, toll)

    # ---------------------------------------------------------------- recovery
    def recover(self, task: str) -> Result:
        """Aftermath tasks: each is done once and restores some of what the night cost."""
        self.completed.add(task)
        flooded = self.homes_flooded()
        if task == "recover_streets":
            effects = (("environment", 6),)
            text = "Neighbours with brooms, wheelbarrows and flasks of tea clear the fallen branches and silt from the square. By noon the path to the Hall is open."
            title = "Clearing the square"
        elif task == "recover_homes":
            effects = (("equity", 2 + 2 * flooded), ("resilience", 1))
            text = ("Neighbours carry out ruined carpets and carry in borrowed heaters. Amani keeps a list of what each household lost, so the circle can answer it properly." if flooded
                    else "Riverside is dry, so the neighbours bring tea and tools to help anyone who needs a hand. Mostly they sit in the sun and talk.")
            title = "Drying out Riverside"
        else:
            effects = (("resilience", 6),)
            text = "The Hall is swept, the cots are stacked and the lamps refilled. Someone pins a list of the people who helped to the door, and the list is longer than anyone expected."
            title = "Closing the Hall"
        self._apply(effects)
        return self._record(title, text + effects_text(effects), resolved=True)

    def storm_close(self) -> Result:
        """The circle talks over what the night showed, and Part Two ends."""
        self.completed.add("storm_done")
        lines = []
        if self.prepared("prep_drains"):
            lines.append("Clearing the drains kept the water off the doorsteps.")
        elif self.homes_flooded():
            lines.append("Riverside took the water that the drains could not.")
        if self.prepared("prep_hall"):
            lines.append("Opening the Hall meant nobody slept in the rain.")
        else:
            lines.append("The Hall was cold and crowded, and everyone agreed to set it up before the next storm.")
        if self.odile_alone():
            lines.append("Odile spent a night alone, and the circle resolves that no older neighbour will again.")
        lines.append("Nobody could do everything, and nobody was asked to.")
        effects = (("equity", 2), ("resilience", 2), ("environment", 2))
        text = "At the circle, neighbours take turns to say what the night showed them. " + " ".join(lines) + "  A plan for the next storm goes in the minutes, in more than one handwriting."
        self._apply(effects)
        return self._record("What the storm taught us", text + effects_text(effects), resolved=True)

    def read_forecast(self) -> Result:
        self.completed.add("storm_forecast")
        return self._record("A storm is on its way", FORECAST_TEXT)

    # ---------------------------------------------------------- recap/epilogue
    def storm_recap(self) -> list[dict[str, str]]:
        rows = []
        used = HOURS_TOTAL - self.prep_hours_left()
        done = [t for t in PREP_ORDER if t in self.completed]
        undone = [t for t in PREP_ORDER if t not in self.completed]
        unmet = [NPCS[p][0] for p in ("kit", "odile", "noor") if f"support_{p}" not in self.completed]
        missed = "Not reached in time: " + ", ".join(PREP_BENEFIT[t][1] for t in undone) + "." if undone else "Nothing was left undone."
        if unmet:
            missed += " " + ", ".join(unmet) + (" was" if len(unmet) == 1 else " were") + " never met, so they could not be helped in advance."
        rows.append({
            "label": "Six hours of daylight",
            "chosen": (f"You spent {used} of {HOURS_TOTAL} hours: " + ", ".join(PREP_SHORT[t] for t in done) + ".") if done else "You spent no hours and went straight to the night.",
            "benefited": ("Protected: " + ", ".join(PREP_BENEFIT[t][0] for t in done) + ".") if done else "Nobody, in advance.",
            "missed": missed,
            "revisited": f"Hours left unspent: {self.prep_hours_left()}.",
            "question": "Who did you put first when you could not help everyone, and why?",
        })
        for scene in SCENES[:4]:
            title, question, options = SCENE_RECAP[scene]
            choice = self.choices.get(scene)
            if choice in options:
                chosen, benefited, missed_who = options[choice]
                rows.append({"label": title, "chosen": chosen, "benefited": benefited, "missed": missed_who, "revisited": "A decision made in the moment.", "question": question})
        flooded = self.homes_flooded()
        rows.append({
            "label": "The morning after",
            "chosen": "Cleared the square, dried out Riverside and closed the Hall.",
            "benefited": "Everyone who had been through the night, and Riverside most of all." if flooded else "Everyone who had been through the night.",
            "missed": (f"{flooded} homes lost belongings that could not be replaced." if flooded > 1 else "One home lost belongings that could not be replaced.") if flooded else "Nothing was lost that could not be mended.",
            "revisited": "The circle agreed a plan for the next storm.",
            "question": "What would you do before the next storm, if you could start earlier?",
        })
        return rows

    def storm_epilogue(self) -> list[str]:
        paragraphs = ["The storm passed, and the village was still there. Nobody had done everything, and everybody had done something."]
        if self.prepared("prep_drains") and self.prepared("prep_hall"):
            paragraphs.append("Because the drains were clear and the Hall was ready, the night was frightening but not cruel.")
        elif self.homes_flooded():
            paragraphs.append("Riverside took the water, and Riverside took the work of drying out. The circle remembers that it was asked to prepare for this earlier than it did.")
        else:
            paragraphs.append("The Hall was not what it could have been, but the drains held, and Riverside stayed dry enough to sleep in.")
        if self.odile_alone():
            paragraphs.append("Odile spent the night alone, and the village decided that would not happen again.")
        elif self.prepared("prep_odile") or self.choices.get("storm_s3") == "homes":
            paragraphs.append("Odile told the flood of '74 to a Hall full of people who had never heard it, and nobody hurried her.")
        if self.prepared("prep_rowan"):
            paragraphs.append("Rowan ran the tea table, and was seen to smile.")
        elif "support_rowan" in self.completed:
            paragraphs.append("Rowan came to the Hall at three in the morning, and was met at the door. That is what the door was for.")
        paragraphs.append("There will be another storm. This time the village knows who to call, who to check on, and where the cots are.")
        return paragraphs
