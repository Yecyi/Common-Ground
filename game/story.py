"""Original Common Ground dialogue data and presentation-only value objects.

The supportive dialogue follows the principles of listening without pressure,
asking what people need, and connecting people with practical support. It is a
fictional story, not a clinical assessment or a model of recovery.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Choice:
    id: str
    label: str
    hint: str = ""


@dataclass(frozen=True)
class Conversation:
    speaker: str
    role: str
    text: str
    choices: list[Choice] = field(default_factory=list)
    # 0 is calm and 1 is the most strained moment; the soundtrack follows it.
    tension: float = 0.0


@dataclass(frozen=True)
class Result:
    ok: bool
    title: str
    text: str
    # Pairs of (group, level 0-3) shown as an outcome panel after a dilemma.
    outcome: tuple = ()
    outcome_title: str = ""
    # True after a supportive or de-escalating choice, so the music can settle.
    resolved: bool = False


@dataclass(frozen=True)
class Option:
    id: str
    label: str
    hint: str
    title: str
    text: str
    effects: tuple = ()
    good: bool = True


@dataclass(frozen=True)
class Beat:
    """An optional later scene in a resident's story. Beats never cost supplies."""
    id: str
    person: str
    intro: dict
    options: tuple
    needs_completed: tuple = ()
    needs_flags: tuple = ()
    min_tasks: int = 0
    variant_key: str = ""

    def intro_for(self, choices) -> str:
        return self.intro.get(choices.get(self.variant_key), self.intro["default"])


NPCS = {
    "mira": ("Mira", "Community organiser"),
    "rowan": ("Rowan", "Riverside gardener"),
    "amani": ("Amani", "Riverside resident and advocate"),
    "theo": ("Theo", "Former factory technician"),
    "council": ("The neighbourhood circle", "A shared decision"),
    "dispute": ("Neighbours at the circle", "A tense moment"),
    "plots": ("The garden sign-up board", "A shared decision"),
}

INTRO = (
    "The factory closed after its leaking outflow made the river unsafe. "
    "Jobs disappeared, the public pump failed, and a first-come supply queue "
    "left Riverside residents behind. People have been carrying too much alone. "
    "You have come back to help the neighbourhood decide what comes next."
)

LORE = (
    "An old photograph shows neighbours swimming beside the mill. A notice below "
    "it records years of unanswered reports about the leaking outflow. The plant "
    "eventually closed, but nobody funded the cleanup. A newer notice reads: "
    "'Relief parcels available at the square from 8 a.m.' Someone has added: "
    "'What about people working shifts, people who cannot queue, or Riverside?' "
    "The crisis was shaped by decisions. Different decisions can change it."
)

ROWAN_START = (
    "I used to bring seedlings here before my shift. Now the river smells wrong "
    "and I cannot sleep when the pipes rattle. Everyone keeps telling me to "
    "cheer up. I don't have much energy for another conversation."
)
AMANI_START = (
    "The square gets deliveries first. Our road floods, and the queue opens "
    "while I am working. 'Everyone can line up' sounds equal, but it isn't "
    "equal access. Will Riverside get a say this time?"
)
MIRA_START = (
    "We have a few supplies and very different needs. I keep making lists "
    "without asking who is missing from the room. We need clean water, a place "
    "to rest, and a way for neighbours to make decisions together. Where do we start?"
)
THEO_START = (
    "I maintained the old factory. The leak reports were ignored; workers "
    "didn't choose that. Some neighbours want the line restarted for jobs. "
    "We could instead turn the sound equipment into a small community repair "
    "workshop, with shared training and safe water handling. It costs more now."
)

# Later scenes in each resident's story. Each has at least two supportive
# responses; a few have one pressuring response that can be repaired.
BEATS = (
    Beat(
        "rowan_2", "rowan",
        {"default": "The pipes have stopped rattling. Rowan says the nights are still difficult, just differently, and the quiet feels odd after so many bad ones. They stand at the edge of the garden, not sure whether to go in."},
        (
            Option("own_role", "Ask which job, if any, feels manageable today.", "Let them choose the size of the task.",
                   "Rowan picks a small job", "Rowan says watering one bed is enough for now, and that they will tell you if that changes. You agree to check in only when they ask.",
                   (("resilience", 6), ("equity", 2))),
            Option("company", "Offer to sit nearby while they decide.", "Company without pressure.",
                   "Company without questions", "You sit on the low wall. After a while Rowan stands, picks up a watering can and fills it. Nobody comments. The offer stays open for tomorrow too.",
                   (("resilience", 5), ("environment", 2))),
            Option("push", "Say the garden needs them back by the weekend.", "Urgency can make it harder to ask for help.",
                   "Too much, too soon", "Rowan's shoulders tighten. 'I'll see,' they say, and step back from the gate. They have not said no for good. You can return and ask what they would like instead.",
                   (("resilience", -3),), good=False),
        ),
        needs_completed=("support_rowan",), needs_flags=("source_repaired",),
    ),
    Beat(
        "rowan_3", "rowan",
        {"default": "All three beds are planted. Rowan has been watering one of them. They would like to talk about how the care rota should work."},
        (
            Option("share_rota", "Suggest sharing each bed between neighbours, so no one carries it alone.", "A rota that does not depend on one person.",
                   "Shared beds", "Rowan likes the idea that nobody's absence leaves a bed dry. Two neighbours sign up beside them. Rowan writes their own name in pencil: 'Changeable.'",
                   (("resilience", 4), ("environment", 3))),
            Option("own_bed", "Let Rowan keep a bed of their own and tend it when they choose.", "One place that is theirs.",
                   "A bed of their own", "Rowan says one place that is theirs helps on days when everything else feels too loud. The rota lists the bed as 'Rowan, when able.'",
                   (("resilience", 5), ("environment", 2))),
        ),
        needs_completed=("beat_rowan_2",), needs_flags=("garden_open",),
    ),
    Beat(
        "mira_2", "mira",
        {"default": "Mira has a list for her list. She is carrying the inventory, the pump rota and the garden schedule, and she looks tired. 'If I stop, it all stops,' she says."},
        (
            Option("hand_off", "Offer to split her tasks across the care rota, with names beside each one.", "Share the work; keep the record public.",
                   "Work shared out", "Mira reads the list aloud and neighbours volunteer for the lines they can take. She keeps three tasks and crosses off the rest with visible relief.",
                   (("resilience", 5), ("equity", 2))),
            Option("rest", "Offer to cover the inventory table while she takes a proper break.", "Rest is part of the plan.",
                   "A proper break", "Mira hesitates, then sits. You keep the inventory open and public while she eats lunch away from the table. She returns clearer-headed, with a shorter list.",
                   (("resilience", 5), ("equity", 1))),
            Option("more", "Ask her to take on the garden schedule as well. She is good at it.", "Being good at something can become a trap.",
                   "One more thing", "Mira nods and writes it down. She does not mention how tired she is. The list is longer than before. You can return and ask what she needs to drop.",
                   (("resilience", -3), ("equity", -2)), good=False),
        ),
        needs_completed=("support_mira",), min_tasks=3,
    ),
    Beat(
        "mira_3", "mira",
        {"default": "The circle has met. Mira says the care rota only lasts if the plan is easy for anyone to read and change."},
        (
            Option("publish", "Publish the rota so anyone can see it and swap a shift.", "Make the plan readable.",
                   "A rota anyone can read", "The rota goes up beside the noticeboard with a pencil on a string. Within a day it has four new names and two swaps.",
                   (("equity", 4), ("resilience", 3))),
            Option("rotate", "Rotate who coordinates every month.", "Leadership that moves around.",
                   "Coordination that rotates", "Mira writes the months on the wall and puts someone else's name beside the next one. 'Good,' she says. 'I'll still help. I just won't be the whole system.'",
                   (("equity", 3), ("resilience", 4))),
        ),
        needs_completed=("beat_mira_2",), needs_flags=("council_held",),
    ),
    Beat(
        "amani_2", "amani",
        {
            "default": "Did the plan reach Riverside? I want to know how long it lasts, and who decides next time.",
            "needs": "Deliveries reached my street this time, and I didn't have to explain myself in public. I want to know how long that lasts, and who decides next time.",
            "equal": "Everyone got the same share, and I understand why. But my neighbour on the ground floor still can't get to the collection point. Equal isn't the same as reachable.",
            "queue": "The queue left half of Riverside behind again. You listened to us, and then it went the same way anyway. What changes now?",
        },
        (
            Option("listen_back", "Ask where the plan is still failing, and write it down together.", "Let residents name the gaps.",
                   "A list of what is missing", "Amani names three gaps: step-free collection, delivery windows for shift workers, and a private way to ask. Each goes in the circle's notes with a name beside it.",
                   (("equity", 4), ("resilience", 2))),
            Option("join_oversight", "Invite Riverside to co-chair the oversight group.", "Share the decision, not only the benefit.",
                   "Riverside at the head of the table", "Amani accepts, on condition that the group meets where Riverside can reach it. The next meeting is moved to the shelter by the bridge.",
                   (("equity", 5), ("resilience", 1))),
            Option("defend", "Explain that the plan already helps most households.", "'Most' can still leave people out.",
                   "Most is not everyone", "Amani's expression closes. 'Most,' she repeats. The conversation ends politely and nothing is settled. You can return and ask who is still missing.",
                   (("equity", -3), ("resilience", -2)), good=False),
        ),
        needs_completed=("support_amani",), needs_flags=("council_held",), variant_key="allocation",
    ),
    Beat(
        "amani_3", "amani",
        {
            "default": "The circle hasn't formally reviewed who was missed. I'll keep asking until it does.",
            "review": "The review added an appeal route and shared oversight. I want to test whether it works in practice before I trust it.",
        },
        (
            Option("appeal_route", "Walk through how a neighbour would actually make an appeal.", "Test the route, not just the promise.",
                   "A route that works", "You trace an appeal from the first form to the final answer and fix two places where a person could get stuck. Amani adds a private option for people who don't want to explain in public.",
                   (("equity", 4), ("resilience", 2))),
            Option("open_meetings", "Move the circle's meetings to a time and place Riverside can reach.", "Access includes when and where.",
                   "Meetings that can be reached", "The meetings move to evenings at the shelter by the bridge. Shift workers can come, and a ramp is added at the door.",
                   (("equity", 4), ("resilience", 2))),
        ),
        needs_completed=("beat_amani_2",), variant_key="council_review",
    ),
    Beat(
        "theo_2", "theo",
        {
            "default": "Some of the old crew are unhappy with the plan, and Theo is caught in the middle.",
            "workshop": "Some of the old crew say a workshop can't replace the wages they lost. They are angry, and Theo is caught between friends and a plan he believes in.",
            "restart": "The line is running again. Riverside neighbours have started leaving angry notes about the water. Theo is caught between wages and what he sees in the river.",
            "reserve": "Some of the crew are waiting on the supplies we held back, and not everyone is patient. Theo hears it every day.",
        },
        (
            Option("listen_crew", "Invite the crew to say what they need from the work, and share what the river needs.", "Put both lists on one table.",
                   "Both lists on one table", "The crew's list: wages, training, dignity. The river's list: safe water handling, monitoring, repairs. Theo notices how much overlaps, and says so.",
                   (("equity", 3), ("resilience", 3))),
            Option("training_plan", "Sketch a training and hiring plan together.", "Make the plan concrete.",
                   "A plan with names", "Theo and three former workers draft who could train whom, and what the first month of paid work might look like. It is not finished, but it is theirs.",
                   (("equity", 3), ("resilience", 3))),
            Option("blame", "Say the crew should have spoken up about the leaks sooner.", "Blame closes conversations.",
                   "A hard thing to hear", "Theo goes quiet. 'We did,' he says. 'Nobody listened.' The talk ends there. You can return and ask what he would like the crew to hear instead.",
                   (("equity", -2), ("resilience", -3)), good=False),
        ),
        needs_completed=("support_theo",), variant_key="theo",
    ),
    Beat(
        "theo_3", "theo",
        {
            "default": "Theo looks at the old mill. 'Every choice here had a price. I'd like us to say so out loud.'",
            "workshop": "Theo looks at the workshop. 'It cost more than we wanted, and some jobs didn't come back. I still think it was the right decision, and I think it's okay to say it had a price.'",
            "restart": "Theo looks at the line. 'It brought wages back. It also put the river at risk, and I'd rather fix that than defend it.'",
            "reserve": "Theo looks at the quiet machines. 'Waiting protected the supplies. It didn't help anyone with rent, though. Waiting is a choice too.'",
        },
        (
            Option("acknowledge", "Acknowledge what the choice cost, and who paid for it.", "Name the price honestly.",
                   "Naming the cost", "Theo nods slowly. The cost goes into the circle's notes next to the benefits, so the next decision starts with both.",
                   (("equity", 2), ("resilience", 3))),
            Option("look_ahead", "Ask what he would want the next meeting to decide.", "Turn reflection into an agenda.",
                   "A question for the next meeting", "Theo says he wants the crew and Riverside in the same room, with the factory plan open. He writes it on the agenda himself.",
                   (("equity", 3), ("resilience", 2))),
        ),
        needs_completed=("beat_theo_2",), variant_key="theo",
    ),
)
BEAT_BY_ID = {beat.id: beat for beat in BEATS}

DISPUTE_INTRO = {
    "default": "Two neighbours stand either side of the circle's table, voices rising. A former mill worker says the line should restart this week. A Riverside resident says the river cannot take it. Each is looking at you.",
    "restart": "The line is running again. A Riverside resident says her children cannot use the water. A former mill worker says he cannot pay rent without these wages. Voices are rising, and each is looking at you.",
    "workshop": "The workshop is open, but a former mill worker says it hired five people where the mill once employed sixty. A Riverside resident says that is still better than the river. Voices are rising.",
    "reserve": "The supplies have been held back while a plan is made. A former mill worker says waiting costs him rent. A Riverside resident says restarting costs her the river. Voices are rising.",
}
DISPUTE_OPTIONS = (
    Option("acknowledge", "Acknowledge both fears: lost wages, and a river that isn't safe.", "Name what each person is afraid of, without ranking them.",
           "Both fears are real", "You say the worker's worry about rent out loud, then the resident's worry about the water. The shouting drops. Neither has won, but both have been heard.",
           (("resilience", 6), ("equity", 4))),
    Option("shared_need", "Point to what they share: safe work and safe water.", "Look for the shared need, not a winner.",
           "Safe work, safe water", "'You both want a future here,' you say. They look at each other. The worker offers to help test the river. The resident offers to help write the training plan.",
           (("equity", 6), ("resilience", 4), ("environment", 2))),
    Option("pause", "Suggest a pause, and set a time to continue with Theo and Amani there.", "A pause is not a verdict.",
           "Time to cool down", "You ask for ten minutes and a time to talk again, with Theo and Amani present. People breathe out. A date goes on the noticeboard.",
           (("resilience", 4), ("equity", 2))),
    Option("blame", "Say whoever wanted the line restarted caused this mess.", "Taking a side can escalate a dispute.",
           "Sides, not solutions", "The worker steps back and the resident is not satisfied either. Voices get louder before neighbours step between them. The argument has not ended, and you can return to calm it.",
           (("equity", -3), ("resilience", -4)), good=False),
)
DISPUTE_CALM = (
    "The two neighbours are sharing a bench, working out a rota for river testing. "
    "The argument has not vanished; it has become a conversation."
)

PLOTS_INTRO = (
    "Three beds have room for only a few household plots, and more than twice as many "
    "households have asked. Some live in flats with no yard. Some work shifts and cannot "
    "reach a weekday sign-up. A few were first to help with the cleanup. There is no "
    "supply cost, but there is a choice about whose need counts. How should the plots be shared?"
)
PLOTS_OPTIONS = (
    Option("needs_first", "Offer plots first to households with no garden space, many in Riverside.", "No supplies. Priority goes to those with the least access.",
           "Plots for those with least space", "Households without a yard are invited first, and the sign-up is moved to evenings and weekends so shift workers can reach it. Some early helpers wait for a later round.",
           (("equity", 8), ("resilience", 3))),
    Option("lottery", "Draw lots, so every household has an equal chance.", "No supplies. Clear and equal; luck decides.",
           "Plots by lottery", "Names are drawn in public. The process is simple and nobody can claim a favour, but households with the least space have no better odds than anyone else.",
           (("equity", 5), ("resilience", 2))),
    Option("helpers", "Give plots to those who helped the most.", "No supplies. Rewards effort; can leave out people who could not help.",
           "Plots for the busiest helpers", "The plots go to the people who gave the most hours. The garden is quickly tended, but shift workers, carers and Riverside households who could not volunteer are left off the list.",
           (("equity", 1), ("environment", 2))),
)
PLOTS_REVIEW = Option(
    "review", "Reopen the sign-up with shared plots and a waiting list.", "No supplies. Widen access after the first round.",
    "A second round", "Neighbours add shared plots, a waiting list and an evening sign-up. The first decision stands in the record, and the second round reaches people it missed.",
    (("equity", 8), ("resilience", 2)),
)
PLOTS_AFTER = {
    "needs_first": "The first plots have gone to households with the least space. Early helpers have been asked to wait for a later round, and some are not happy about it.",
    "lottery": "The plots were drawn by lot. People accept the fairness of the draw, but not everyone who needed a plot most got one.",
    "helpers": "The plots went to the people who gave the most hours. The garden is busy, and some neighbours feel the list was closed before they could join it.",
}

OUTCOME_WORDS = ("None", "Some", "Most", "All")
OUTCOMES = {
    "allocation": {
        "needs": (("The square", 3), ("Riverside", 3), ("Shift workers", 2), ("People who can't queue", 3)),
        "equal": (("The square", 3), ("Riverside", 2), ("Shift workers", 2), ("People who can't queue", 1)),
        "queue": (("The square", 3), ("Riverside", 1), ("Shift workers", 1), ("People who can't queue", 0)),
    },
    "plots": {
        "needs_first": (("Flat-dwellers", 3), ("Riverside homes", 3), ("Shift workers and carers", 2), ("Early volunteers", 2)),
        "lottery": (("Flat-dwellers", 2), ("Riverside homes", 2), ("Shift workers and carers", 2), ("Early volunteers", 2)),
        "helpers": (("Flat-dwellers", 1), ("Riverside homes", 1), ("Shift workers and carers", 0), ("Early volunteers", 3)),
    },
    "factory": {
        "workshop": (("Wages now", 1), ("River safety", 3), ("A shared say", 3)),
        "restart": (("Wages now", 3), ("River safety", 0), ("A shared say", 1)),
        "reserve": (("Wages now", 0), ("River safety", 2), ("A shared say", 2)),
        "retrofit": (("Wages now", 2), ("River safety", 3), ("A shared say", 3)),
    },
}
OUTCOME_TITLES = {
    "allocation": "Who the supplies reached",
    "plots": "Who the plots reached",
    "factory": "What this choice means for",
}

# What each decision meant, for the end-of-game recap and the epilogue.
RECAP = {
    "allocation": {
        "label": "Six supplies at the circle",
        "values": {
            "needs": ("Prioritised urgent needs, with accessible delivery.", "Households who described urgent needs, Riverside, and people who cannot queue.", "People who prefer not to share their circumstances; a needs check can feel intrusive."),
            "equal": ("Gave every household the same share.", "Everyone received something, and the rule was simple to understand.", "Households with greater needs, or no way to collect their share."),
            "queue": ("Let the first people in the queue collect first.", "People who could wait in line at the square during the day.", "Shift workers, people who cannot queue, and several Riverside homes."),
        },
        "question": "Who gets to say what counts as need, and who checks?",
    },
    "factory": {
        "label": "The old factory",
        "values": {
            "workshop": ("Built a shared repair workshop.", "Residents, trainees and the river.", "Workers who needed wages quickly; not every lost job came back."),
            "restart": ("Restarted the old line.", "Workers who regained wages sooner.", "The river and Riverside, which carry the pollution risk."),
            "reserve": ("Kept the supplies while a safer plan was made.", "The public store, and people who wanted to be consulted.", "Workers who needed income in the meantime."),
        },
        "question": "How do you weigh jobs now against the river over many years?",
    },
    "plots": {
        "label": "Garden plots",
        "values": {
            "needs_first": ("Offered plots first to households with no garden space.", "Flat-dwellers and many Riverside households.", "Early helpers, who had to wait for a later round."),
            "lottery": ("Drew lots for the plots.", "Everyone had the same chance, in a process anyone could watch.", "Households with the greatest need, who had no better odds than anyone."),
            "helpers": ("Gave plots to those who helped most.", "Volunteers who had the time to help.", "Shift workers, carers and anyone who could not volunteer."),
        },
        "question": "Is helping the most the same as deserving the most?",
    },
    "dispute": {
        "label": "Raised voices at the circle",
        "values": {
            "acknowledge": ("Acknowledged both fears.", "Both neighbours, who felt heard.", "The question underneath, which is still open."),
            "shared_need": ("Pointed to the need they share.", "Both neighbours, who found something to work on together.", "The question underneath, which is still open."),
            "pause": ("Suggested a pause and a time to continue.", "Both neighbours, who had room to cool down.", "The question underneath, which waits for the next meeting."),
        },
        "question": "What helps people disagree and keep talking?",
    },
}
RECAP_PEOPLE = {
    "rowan": ("Rowan", {"listen": "Offered company without pressure.", "space": "Gave space and offered practical help."}),
    "amani": ("Amani", {"listen": "Asked what would make the plan accessible.", "deliver": "Offered to arrange deliveries together."}),
    "mira": ("Mira", {"listen": "Asked who had been missing from the decisions.", "coordinate": "Proposed a shared care rota and a public inventory."}),
}
RECAP_PEOPLE_MISSED = "Listening helps, but it does not repair a river, a supply system or a lost job on its own. Those needed practical action too."

EPILOGUE_BASE = (
    "The river runs clearer, the garden is shared, and people who were left outside the "
    "decisions now have a place at the table. Willowmere has a plan it can keep working on together."
)
EPILOGUE_ALLOCATION = {
    "needs": "Deliveries follow what neighbours said they needed. People still have to trust the check-ins, so the circle keeps them private and open to challenge.",
    "equal": "Every household got the same share. It was easy to explain, and the circle learned that an equal share is not always a reachable one.",
    "queue": "The first round of supplies went to whoever could wait in line. Neighbours remember who was missed, and that memory is part of why the plan changed.",
}
EPILOGUE_REVIEW = " Because the circle reviewed it, there are now deliveries, shared oversight and an appeal route."
EPILOGUE_FACTORY = {
    "workshop": "The old mill is a repair workshop. It did not replace every job, but safe water is part of the work.",
    "restart": "The old line still runs. Theo and the neighbours watch the river together and talk about changing the process.",
    "reserve": "The factory question is still open. Nobody was hurried, and nobody was paid yet.",
}
EPILOGUE_RETROFIT = "After the decision was revisited, the old mill is being retrofitted as a shared workshop. Not every job returns, but oversight is shared."
EPILOGUE_PLOTS = {
    "needs_first": "The garden plots went first to households with no space of their own, many of them in Riverside.",
    "lottery": "The garden plots were drawn by lot, so everyone had the same chance.",
    "helpers": "The garden plots went to the people who helped most, which left out people who could not volunteer.",
}
EPILOGUE_PLOTS_REVIEW = " A waiting list and shared plots now widen access."
EPILOGUE_DISPUTE = "At a tense moment, a worker and a Riverside neighbour found something they both wanted. An argument became a conversation."
EPILOGUE_ARCS = {
    "rowan": "Rowan keeps a bed on the rota marked 'when able'. Hard days still come, but they do not come alone.",
    "mira": "Mira's name is no longer on every task. The care rota works because it does not depend on her.",
    "amani": "Riverside helps run the circle now, and appeals have a clear route.",
    "theo": "Theo's crew and Riverside meet in the same room, with the factory plan on the table.",
}
EPILOGUE_NO_ARCS = "The neighbours' stories are still unfolding. There are conversations left to have."
