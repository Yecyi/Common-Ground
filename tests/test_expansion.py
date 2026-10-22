"""Rules for the neighbours beyond Riverside, the river survey, bonds and Part Two: Storm Season."""

from copy import deepcopy
from itertools import combinations, product
import unittest

from game.state import GameState, GROWTH_IDS, SAMPLE_IDS
from game.storm import HOURS_TOTAL, PREP, PREP_ORDER, RECOVER, SCENES, SCENE_CHOICES
from game.story import BEATS, NPCS

LITTER = [f"litter_{i}" for i in range(1, 7)]
CRATES = [f"crate_{i}" for i in range(1, 4)]
NEW = ("kit", "odile", "noor")
FIRST_GOOD = {"kit": "kit_1:read", "odile": "odile_1:sit", "noor": "noor_1:ask_need"}


def gather(state):
    for action in (*LITTER, *CRATES):
        state.perform(action)


def act_one(finish=True):
    state = GameState()
    gather(state)
    state.perform("pump")
    for i in range(1, 4):
        state.perform(f"garden_{i}")
    state.perform("quiet")
    for person in ("mira", "rowan", "amani"):
        assert state.choose(person, "listen").ok
    assert state.choose("theo", "workshop").ok
    assert state.choose("council", "needs").ok
    if finish:
        assert state.choose("council", "finish").ok
    return state


def meet_all(state):
    for person in NEW:
        assert state.choose(person, FIRST_GOOD[person]).ok
    return state


def take_samples(state):
    for site in sorted(SAMPLE_IDS):
        assert state.perform(site).ok


def full_state():
    return meet_all(act_one())


def run_storm(state, tasks=(), path=("doors", "elders_first", "clinic", "sit")):
    assert state.choose("council", "storm_forecast").ok
    for task in tasks:
        result = state.choose("storm", task)
        assert result.ok, (task, result)
    assert state.choose("storm", "begin").ok
    for choice in (*path, "dawn"):
        assert state.storm_scene_pending()
        result = state.choose("storm", choice)
        assert result.ok, (choice, result)
    for task in RECOVER:
        assert state.perform(task).ok
    assert state.choose("council", "storm_close").ok
    return state


def valid_plans(state):
    """Every subset of preparations that fits in the day."""
    plans = []
    for size in range(len(PREP_ORDER) + 1):
        for subset in combinations(PREP_ORDER, size):
            if sum(PREP[t]["cost"] for t in subset) <= HOURS_TOTAL:
                plans.append(subset)
    return plans


class NewNeighbourTests(unittest.TestCase):
    def test_first_meetings_are_free_and_open_from_the_start(self):
        for person in NEW:
            state = GameState()
            supplies = state.resources["supplies"]
            self.assertEqual(state.available_beat(person).id, f"{person}_1")
            self.assertNotIn("reflect", [c.id for c in state.dialogue(person).choices], "nothing to reflect on yet")
            self.assertTrue(state.choose(person, FIRST_GOOD[person]).ok)
            self.assertIn(f"support_{person}", state.completed)
            self.assertEqual(state.resources["supplies"], supplies)
            self.assertEqual(state.bond(person), 1)
            self.assertIn("reflect", [c.id for c in state.dialogue(person).choices])

    def test_every_first_meeting_has_a_response_that_listens_and_one_that_closes_the_door(self):
        for person in NEW:
            beat = state_beat = GameState().available_beat(person)
            self.assertEqual(sum(1 for o in beat.options if o.good), 2)
            self.assertEqual(sum(1 for o in beat.options if not o.good), 1)

    def test_pressure_on_a_first_meeting_is_recoverable_and_is_not_repeated(self):
        for person in NEW:
            with self.subTest(person=person):
                state = GameState()
                bad = next(o for o in state.available_beat(person).options if not o.good)
                before = dict(state.metrics)
                self.assertTrue(state.choose(person, f"{person}_1:{bad.id}").ok)
                self.assertNotIn(f"support_{person}", state.completed)
                self.assertIn(f"rejected_{person}_1", state.completed)
                for metric, amount in bad.effects:
                    self.assertEqual(state.metrics[metric], max(0, before[metric] + amount))
                self.assertNotIn(bad.id, [c.id.split(":")[-1] for c in state.dialogue(person).choices])
                self.assertFalse(state.choose(person, f"{person}_1:{bad.id}").ok)
                self.assertTrue(state.choose(person, FIRST_GOOD[person]).ok)
                self.assertIn(f"support_{person}", state.completed)
                self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())

    def test_later_chapters_wait_for_their_conditions(self):
        state = GameState()
        meet_all(state)
        self.assertIsNone(state.available_beat("kit"), "needs all three river readings")
        take_samples(state)
        self.assertEqual(state.available_beat("kit").id, "kit_2")
        self.assertIsNone(state.available_beat("odile"), "needs the river repaired")
        self.assertIsNone(state.available_beat("noor"), "needs Rowan's trust")
        gather(state)
        state.perform("pump")
        self.assertEqual(state.available_beat("odile").id, "odile_2")
        state.choose("rowan", "listen")
        self.assertEqual(state.available_beat("noor").id, "noor_2")

    def test_the_third_chapters_need_the_circle_or_the_garden(self):
        state = act_one(finish=False)
        meet_all(state)
        take_samples(state)
        for person in NEW:
            while state.available_beat(person) and state.available_beat(person).id.split("_")[1] != "3":
                beat = state.available_beat(person)
                self.assertTrue(state.choose(person, f"{beat.id}:{next(o.id for o in beat.options if o.good)}").ok)
        self.assertEqual({p: state.available_beat(p).id for p in NEW}, {"kit": "kit_3", "odile": "odile_3", "noor": "noor_3"})
        fresh = GameState()
        meet_all(fresh)
        take_samples(fresh)
        fresh.perform("pump")
        self.assertEqual(fresh.available_beat("odile").id, "odile_2")

    def test_every_chapter_can_be_taken_and_none_costs_supplies(self):
        state = act_one(finish=False)
        meet_all(state)
        take_samples(state)
        supplies = state.resources["supplies"]
        for _ in range(3):
            for person in NEW:
                beat = state.available_beat(person)
                if beat:
                    self.assertTrue(state.choose(person, f"{beat.id}:{next(o.id for o in beat.options if o.good)}").ok)
        for person in NEW:
            self.assertEqual(state.bond(person), 3)
            self.assertIsNone(state.available_beat(person))
        self.assertEqual(state.resources["supplies"], supplies)
        for value in state.metrics.values():
            self.assertTrue(0 <= value <= 100)
        self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())

    def test_either_way_of_honouring_odile_plants_the_orchard_and_it_grows(self):
        for option in ("plant_here", "record"):
            state = GameState()
            gather(state)
            state.perform("pump")
            state.choose("odile", FIRST_GOOD["odile"])
            self.assertTrue(state.choose("odile", f"odile_2:{option}").ok)
            self.assertIn("memory_tree", state.completed)
            self.assertIn("memory_tree", state.planted_at)
            self.assertEqual(state.garden_stage("memory_tree"), 1)
            state.play_seconds += 200
            self.assertEqual(state.garden_stage("memory_tree"), 3)
            self.assertTrue("memory_tree" in GROWTH_IDS)
            self.assertEqual(GameState.from_dict(state.to_dict()).planted_at, state.planted_at)

    def test_the_new_chapters_alone_cannot_unlock_the_ending(self):
        state = GameState()
        meet_all(state)
        take_samples(state)
        self.assertFalse(state.can_finish)
        self.assertFalse(state.perform("finish").ok)

    def test_saves_reject_new_chapters_that_skip_their_conditions(self):
        state = GameState()
        meet_all(state)
        base = state.to_dict()
        cases = {
            "support without the first meeting": lambda d: d["completed"].remove("beat_kit_1"),
            "first meeting without support": lambda d: d["completed"].remove("support_noor"),
            "orchard without the chapter": lambda d: (d["completed"].append("memory_tree"), d["planted_at"].update(memory_tree=0.0)),
            "orchard without a growth record": lambda d: d["completed"].append("memory_tree"),
            "readings without Kit": lambda d: (d["completed"].remove("support_kit"), d["completed"].remove("beat_kit_1"), d["choices"].pop("kit_1"), d["completed"].append("sample_up")),
            "a later chapter too early": lambda d: (d["completed"].append("beat_kit_2"), d["choices"].update(kit_2="teach")),
            "an unknown chapter": lambda d: d["completed"].append("beat_kit_9"),
        }
        for name, mutate in cases.items():
            data = deepcopy(base)
            mutate(data)
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    GameState.from_dict(data)

    def test_a_bond_counts_the_first_conversation_and_two_later_chapters(self):
        state = act_one(finish=False)
        self.assertEqual({p: state.bond(p) for p in ("mira", "rowan", "amani", "theo")}, {"mira": 1, "rowan": 1, "amani": 1, "theo": 1})
        self.assertEqual({p: state.bond(p) for p in NEW}, {"kit": 0, "odile": 0, "noor": 0})
        beat = state.available_beat("rowan")
        state.choose("rowan", f"{beat.id}:{beat.options[0].id}")
        self.assertEqual(state.bond("rowan"), 2)

    def test_the_neighbour_cards_say_who_is_where_and_what_is_next(self):
        state = GameState()
        cards = {c["id"]: c for c in state.neighbour_cards()}
        self.assertEqual(list(cards), ["mira", "rowan", "amani", "theo", "noor", "kit", "odile"])
        self.assertFalse(cards["kit"]["met"])
        self.assertIn("east bank", cards["kit"]["note"])
        self.assertIn("health post", cards["noor"]["note"])
        self.assertIn("porch", cards["odile"]["note"])
        state.choose("kit", "kit_1:leave")
        self.assertIn("willing to talk again", {c["id"]: c for c in state.neighbour_cards()}["kit"]["note"])
        state.choose("kit", FIRST_GOOD["kit"])
        card = {c["id"]: c for c in state.neighbour_cards()}["kit"]
        self.assertTrue(card["met"])
        self.assertEqual(card["bond"], 1)
        self.assertIn("river readings", card["note"])
        for card in state.neighbour_cards():
            self.assertTrue(card["note"] and card["name"] and card["role"])

    def test_suggestions_point_at_the_neighbours_and_then_the_survey(self):
        state = GameState()
        text, target = state._neighbour_step()
        self.assertEqual(target, "noor")
        meet_all(state)
        text, target = state._neighbour_step()
        self.assertEqual(target, "sample_up", "the first unread post")
        take_samples(state)
        self.assertIn(state._neighbour_step()[1], ("kit",))
        gather(state)
        state.perform("pump")
        state.choose("kit", "kit_2:teach")
        self.assertIn(state._neighbour_step()[1], ("odile", "noor", "kit"))


class RiverSurveyTests(unittest.TestCase):
    def test_a_reading_needs_kit_and_shows_three_measures(self):
        state = GameState()
        self.assertFalse(state.perform("sample_out").ok)
        state.choose("kit", FIRST_GOOD["kit"])
        result = state.perform("sample_out")
        self.assertTrue(result.ok)
        self.assertEqual([name for name, _ in result.outcome], ["Clarity", "River life", "Safe to drink"])
        self.assertTrue(all(0 <= level <= 3 for _, level in result.outcome))
        self.assertIn("when the village began", result.text)

    def test_the_first_reading_is_a_journal_entry_and_repeats_are_not(self):
        state = GameState()
        state.choose("kit", FIRST_GOOD["kit"])
        entries = len(state.journal)
        state.perform("sample_up")
        self.assertEqual(len(state.journal), entries + 1)
        for _ in range(3):
            self.assertTrue(state.perform("sample_up").ok)
        self.assertEqual(len(state.journal), entries + 1)
        self.assertEqual(state.metrics["environment"], GameState().metrics["environment"] + 2, "only the first meeting moved a value")

    def test_readings_improve_as_the_village_restores_the_river_and_upstream_stays_the_reference(self):
        state = GameState()
        start = {site: state.river_reading(site) for site in ("up", "out", "down")}
        self.assertEqual(start["out"], (0, 0, 0))
        self.assertEqual(start["up"], (3, 3, 3))
        last = sum(start["out"]) + sum(start["down"])
        gather(state)
        for step in ("pump", "workshop", "garden", "quiet"):
            if step == "pump":
                state.perform("pump")
            elif step == "workshop":
                state.choose("theo", "workshop")
            elif step == "garden":
                for i in range(1, 4):
                    state.perform(f"garden_{i}")
            else:
                state.perform("quiet")
            now = sum(state.river_reading("out")) + sum(state.river_reading("down"))
            self.assertGreaterEqual(now, last, step)
            last = now
            self.assertEqual(state.river_reading("up"), start["up"])
        self.assertEqual(state.river_reading("out"), (3, 3, 3))
        for site in ("out", "down"):
            self.assertTrue(all(a <= b for a, b in zip(state.river_reading(site), state.river_reading("up"))))

    def test_restarting_the_line_makes_the_water_worse(self):
        calm, risky = GameState(), GameState()
        for state in (calm, risky):
            gather(state)
            state.perform("pump")
        calm.choose("theo", "reserve")
        risky.choose("theo", "restart")
        self.assertLess(sum(risky.river_reading("out")), sum(calm.river_reading("out")))

    def test_a_storm_muddies_the_water_for_a_while(self):
        state = full_state()
        clear = state.river_reading("out")
        state.choose("council", "storm_forecast")
        state.choose("storm", "begin")
        for choice in ("doors", "elders_first", "clinic", "sit", "dawn"):
            state.choose("storm", choice)
        self.assertLess(state.river_reading("out")[0], clear[0])
        for task in RECOVER:
            state.perform(task)
        state.choose("council", "storm_close")
        self.assertEqual(state.river_reading("out"), clear)


class PartTwoRulesTests(unittest.TestCase):
    def test_part_two_waits_for_the_first_ending(self):
        state = act_one(finish=False)
        self.assertEqual(state.storm_phase(), "none")
        self.assertEqual(state.weather(), "clear")
        self.assertNotIn("storm_forecast", [c.id for c in state.dialogue("council").choices])
        self.assertFalse(state.choose("council", "storm_forecast").ok)
        self.assertFalse(state.choose("storm", "begin").ok)
        state.choose("council", "finish")
        self.assertEqual(state.storm_phase(), "invited")
        self.assertIn("storm_forecast", [c.id for c in state.dialogue("council").choices])

    def test_the_phases_and_weather_follow_the_story(self):
        state = act_one()
        seen = [(state.storm_phase(), state.weather())]
        state.choose("council", "storm_forecast")
        seen.append((state.storm_phase(), state.weather()))
        state.choose("storm", "begin")
        seen.append((state.storm_phase(), state.weather()))
        for choice in ("doors", "elders_first", "clinic", "sit"):
            state.choose("storm", choice)
        self.assertEqual(state.storm_phase(), "night")
        state.choose("storm", "dawn")
        seen.append((state.storm_phase(), state.weather()))
        for task in RECOVER:
            state.perform(task)
        state.choose("council", "storm_close")
        seen.append((state.storm_phase(), state.weather()))
        self.assertEqual(seen, [("invited", "clear"), ("forecast", "overcast"), ("night", "storm"), ("aftermath", "aftermath"), ("done", "clear")])

    def test_the_day_has_six_hours_and_each_task_spends_its_own(self):
        state = full_state()
        state.choose("council", "storm_forecast")
        self.assertEqual(state.prep_hours_left(), HOURS_TOTAL)
        state.choose("storm", "prep_hall")
        self.assertEqual(state.prep_hours_left(), HOURS_TOTAL - 2)
        state.choose("storm", "prep_rowan")
        self.assertEqual(state.prep_hours_left(), HOURS_TOTAL - 3)
        self.assertNotIn("prep_hall", [c.id for c in state.dialogue("storm").choices], "a task is done once")

    def test_a_task_that_does_not_fit_spends_nothing(self):
        state = full_state()
        state.choose("council", "storm_forecast")
        for task in ("prep_hall", "prep_drains", "prep_rowan", "prep_odile"):
            self.assertTrue(state.choose("storm", task).ok)
        self.assertEqual(state.prep_hours_left(), 0)
        before = state.to_dict()
        result = state.choose("storm", "prep_gauge")
        self.assertFalse(result.ok)
        self.assertIn("daylight", result.title.lower())
        self.assertEqual(state.to_dict(), before)

    def test_tasks_involving_people_you_have_not_met_are_not_offered(self):
        state = act_one()
        state.choose("council", "storm_forecast")
        offered = [c.id for c in state.dialogue("storm").choices]
        for task in ("prep_clinic", "prep_odile", "prep_gauge"):
            self.assertNotIn(task, offered)
        for task in ("prep_hall", "prep_drains", "prep_rowan", "prep_pump"):
            self.assertIn(task, offered)
        self.assertIn("not met", state.dialogue("storm").text)
        meet_all(state)
        self.assertEqual({"prep_clinic", "prep_odile", "prep_gauge"} - set(c.id for c in state.dialogue("storm").choices), set())

    def test_the_hours_never_cover_everything_so_the_choice_is_real(self):
        self.assertGreater(sum(task["cost"] for task in PREP.values()), HOURS_TOTAL)
        plans = valid_plans(full_state())
        self.assertGreater(len(plans), 20)
        self.assertTrue(all(sum(PREP[t]["cost"] for t in plan) <= HOURS_TOTAL for plan in plans))

    def test_every_possible_plan_leads_through_the_night_and_recovery_to_the_end(self):
        for plan in valid_plans(full_state()):
            with self.subTest(plan=plan):
                state = run_storm(full_state(), plan)
                self.assertEqual(state.storm_phase(), "done")
                self.assertEqual(state.resources["supplies"], full_state().resources["supplies"], "Part Two never touches supplies")
                for value in state.metrics.values():
                    self.assertTrue(0 <= value <= 100)
                self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())

    def test_every_choice_on_the_night_is_available_and_survivable(self):
        orders = list(product(*(sorted(SCENE_CHOICES[s]) for s in SCENES[:4])))
        self.assertEqual(len(orders), 81)
        for plan in ((), ("prep_hall", "prep_drains"), ("prep_rowan", "prep_odile", "prep_clinic", "prep_pump")):
            for path in orders:
                state = run_storm(full_state(), plan, path)
                self.assertEqual(state.storm_phase(), "done", (plan, path))
        state = full_state()
        state.choose("council", "storm_forecast")
        state.choose("storm", "begin")
        for scene in SCENES[:4]:
            self.assertEqual({c.id for c in state.dialogue("storm").choices}, SCENE_CHOICES[scene])
            state.choose("storm", sorted(SCENE_CHOICES[scene])[0])

    def test_the_night_goes_in_order_and_each_part_happens_once(self):
        state = full_state()
        state.choose("council", "storm_forecast")
        state.choose("storm", "begin")
        self.assertFalse(state.choose("storm", "elders_first").ok, "scene two is not open yet")
        self.assertTrue(state.choose("storm", "doors").ok)
        before = state.to_dict()
        self.assertFalse(state.choose("storm", "doors").ok)
        self.assertEqual(state.to_dict(), before)
        self.assertEqual(state.dialogue("storm").tension, 0.75)
        self.assertEqual(state.next_scene(), "storm_s2")

    def test_nothing_can_be_prepared_once_the_storm_begins(self):
        state = full_state()
        state.choose("council", "storm_forecast")
        state.choose("storm", "begin")
        self.assertFalse(state.choose("storm", "prep_hall").ok)
        self.assertNotIn("prep_hall", state.completed)

    def test_what_you_prepared_changes_what_the_night_does(self):
        def toll(plan, path=("doors", "elders_first", "clinic", "sit")):
            state = full_state()
            state.choose("council", "storm_forecast")
            for task in plan:
                state.choose("storm", task)
            state.choose("storm", "begin")
            for choice in path:
                state.choose("storm", choice)
            return state
        bare, ready = toll(()), toll(("prep_drains", "prep_pump", "prep_hall"))
        self.assertEqual(bare.homes_flooded(), 2)
        self.assertEqual(ready.homes_flooded(), 0)
        self.assertGreater(len(bare.storm_toll()), 0)
        bare_total = sum(-amount for _, amount in bare.storm_toll())
        ready_total = sum(-amount for _, amount in ready.storm_toll())
        self.assertGreater(bare_total, ready_total)
        self.assertNotEqual(bare.dialogue("storm").text, GameState().dialogue("storm").text)
        sandbagged = toll((), ("sandbags", "share", "homes", "sit"))
        self.assertEqual(sandbagged.homes_flooded(), 1)

    def test_a_neighbour_left_alone_is_remembered(self):
        def alone(plan, choice):
            state = full_state()
            state.choose("council", "storm_forecast")
            for task in plan:
                state.choose("storm", task)
            state.choose("storm", "begin")
            for step in ("doors", "elders_first", choice, "sit"):
                state.choose("storm", step)
            return state
        self.assertTrue(alone((), "door").odile_alone())
        self.assertFalse(alone((), "homes").odile_alone(), "you found her")
        self.assertFalse(alone(("prep_odile",), "door").odile_alone(), "she was already safe")
        self.assertFalse(GameState().odile_alone())

    def test_the_hall_outcome_panel_shows_who_got_a_bed(self):
        panels = {}
        for prepared in (False, True):
            for choice in ("elders_first", "families_first", "share"):
                state = full_state()
                state.choose("council", "storm_forecast")
                if prepared:
                    state.choose("storm", "prep_hall")
                state.choose("storm", "begin")
                state.choose("storm", "doors")
                result = state.choose("storm", choice)
                self.assertEqual([g for g, _ in result.outcome], ["Elders", "Families with children", "Riverside households", "Late arrivals"])
                panels[(prepared, choice)] = [level for _, level in result.outcome]
        for choice in ("elders_first", "families_first", "share"):
            self.assertGreater(sum(panels[(True, choice)]), sum(panels[(False, choice)]), "a prepared Hall reaches more people")
        self.assertGreater(panels[(True, "elders_first")][0], panels[(True, "families_first")][0])
        self.assertGreater(panels[(True, "families_first")][1], panels[(True, "elders_first")][1])

    def test_calling_everyone_to_the_hall_early_fills_it(self):
        def late_arrivals(first):
            state = full_state()
            state.choose("council", "storm_forecast")
            state.choose("storm", "prep_hall")
            state.choose("storm", "begin")
            state.choose("storm", first)
            return state.choose("storm", "share").outcome[3][1]
        self.assertLess(late_arrivals("hall_now"), late_arrivals("doors"))

    def test_recovery_comes_after_the_night_and_restores_what_it_cost(self):
        state = full_state()
        state.choose("council", "storm_forecast")
        self.assertFalse(state.perform("recover_streets").ok, "nothing to clear yet")
        state.choose("storm", "begin")
        for choice in ("doors", "elders_first", "clinic", "sit", "dawn"):
            state.choose("storm", choice)
        low = dict(state.metrics)
        for task in RECOVER:
            self.assertTrue(state.perform(task).ok)
        for key in low:
            self.assertGreaterEqual(state.metrics[key], low[key])
        self.assertNotIn("storm_done", state.completed)
        self.assertEqual(state.recovery_remaining(), [])
        before = state.to_dict()
        for task in RECOVER:
            self.assertTrue(state.perform(task).ok)
        self.assertEqual(state.to_dict(), before, "recovery cannot be repeated for rewards")

    def test_the_circle_only_closes_storm_season_once_recovery_is_done(self):
        state = full_state()
        state.choose("council", "storm_forecast")
        state.choose("storm", "begin")
        for choice in ("doors", "elders_first", "clinic", "sit", "dawn"):
            state.choose("storm", choice)
        self.assertNotIn("storm_close", [c.id for c in state.dialogue("council").choices])
        state.perform("recover_streets")
        self.assertFalse(state.choose("council", "storm_close").ok)
        state.perform("recover_homes")
        state.perform("recover_hall")
        self.assertIn("storm_close", [c.id for c in state.dialogue("council").choices])
        self.assertTrue(state.choose("council", "storm_close").ok)
        self.assertNotIn("storm_close", [c.id for c in state.dialogue("council").choices])

    def test_the_recap_and_epilogue_follow_what_happened(self):
        plans = [(), ("prep_hall", "prep_drains"), ("prep_rowan", "prep_odile", "prep_clinic", "prep_gauge")]
        epilogues = set()
        for plan in plans:
            state = run_storm(full_state(), plan)
            rows = state.storm_recap()
            self.assertEqual(rows[0]["label"], "Six hours of daylight")
            self.assertEqual(len(rows), 6)
            for row in rows:
                self.assertEqual(set(row), {"label", "chosen", "benefited", "missed", "revisited", "question"})
                self.assertTrue(all(row.values()))
            epilogues.add(tuple(state.storm_epilogue()))
        self.assertEqual(len(epilogues), 3)
        none = run_storm(full_state(), ())
        self.assertIn("no hours", none.storm_recap()[0]["chosen"].lower())
        self.assertIn("Not reached", none.storm_recap()[0]["missed"])

    def test_the_recap_names_neighbours_who_were_never_met(self):
        state = run_storm(act_one(), ("prep_hall",))
        self.assertIn("never met", state.storm_recap()[0]["missed"])

    def test_suggestions_lead_from_the_invitation_through_to_the_end(self):
        state = act_one()
        seen = []
        for _ in range(60):
            text, target = state.next_step()
            self.assertTrue(text)
            seen.append(state.storm_phase())
            phase = state.storm_phase()
            if target == "council" and phase == "invited":
                self.assertTrue(state.choose("council", "storm_forecast").ok)
            elif target == "storm" and phase == "forecast":
                options = [c.id for c in state.dialogue("storm").choices if c.id.startswith("prep_")]
                self.assertTrue(state.choose("storm", options[0] if options and state.prep_hours_left() > 0 else "begin").ok)
            elif target == "storm":
                scene = state.next_scene()
                self.assertTrue(state.choose("storm", sorted(SCENE_CHOICES[scene])[0]).ok)
            elif target in RECOVER:
                self.assertTrue(state.perform(target).ok)
            elif target == "council":
                self.assertTrue(state.choose("council", "storm_close").ok)
            else:
                break
        self.assertEqual(state.storm_phase(), "done")
        for phase in ("invited", "forecast", "night", "aftermath"):
            self.assertIn(phase, seen)

    def test_the_hours_are_a_choice_not_a_clock(self):
        """Nothing here is timed: the hours only change when the player acts."""
        state = full_state()
        state.choose("council", "storm_forecast")
        before = state.to_dict()
        state.play_seconds += 3600
        self.assertEqual(state.prep_hours_left(), HOURS_TOTAL)
        self.assertEqual(state.storm_phase(), "forecast")
        self.assertEqual({k: v for k, v in state.to_dict().items() if k != "play_seconds"}, {k: v for k, v in before.items() if k != "play_seconds"})


class PartTwoSaveTests(unittest.TestCase):
    def test_a_save_at_every_stage_round_trips(self):
        state = full_state()
        self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())
        state.choose("council", "storm_forecast")
        state.choose("storm", "prep_hall")
        self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())
        state.choose("storm", "begin")
        for choice in ("doors", "elders_first", "clinic", "sit"):
            state.choose("storm", choice)
            self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())
        state.choose("storm", "dawn")
        state.perform("recover_hall")
        self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())

    def test_invalid_part_two_data_is_rejected(self):
        state = full_state()
        state.choose("council", "storm_forecast")
        state.choose("storm", "prep_hall")
        state.choose("storm", "begin")
        state.choose("storm", "doors")
        base = state.to_dict()
        cases = {
            "a scene without a choice": lambda d: d["choices"].pop("storm_s1"),
            "a choice without a scene": lambda d: d["choices"].update(storm_s2="share"),
            "a scene out of order": lambda d: (d["completed"].append("storm_s3"), d["choices"].update(storm_s3="clinic")),
            "an invalid scene choice": lambda d: d["choices"].update(storm_s1="swim"),
            "too many hours": lambda d: d["completed"].extend(["prep_drains", "prep_rowan", "prep_odile", "prep_clinic"]),
            "recovery before the night ends": lambda d: d["completed"].append("recover_hall"),
            "ending Part Two before recovery": lambda d: d["completed"].append("storm_done"),
            "a preparation that was not possible": lambda d: d["completed"].remove("support_odile") or d["completed"].extend(["prep_odile"]) or d["completed"].remove("beat_odile_1") or d["choices"].pop("odile_1"),
            "the storm without the first ending": lambda d: (d["completed"].remove("finish"), d["flags"].remove("balanced")),
            "the night without the forecast": lambda d: d["completed"].remove("storm_forecast"),
        }
        for name, mutate in cases.items():
            data = deepcopy(base)
            mutate(data)
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    GameState.from_dict(data)

    def test_the_ending_still_loads_after_a_value_drops_below_its_goal(self):
        """Regression: a pressuring reply or the storm can lower a value after the ending was reached."""
        state = act_one()
        state.metrics["resilience"] = 20
        state.metrics["equity"] = 10
        self.assertFalse(state.can_finish)
        loaded = GameState.from_dict(state.to_dict())
        self.assertEqual(loaded.metrics, state.metrics)
        self.assertIn("balanced", loaded.flags)
        stormed = run_storm(full_state())
        self.assertEqual(GameState.from_dict(stormed.to_dict()).to_dict(), stormed.to_dict())

    def test_the_ending_still_needs_its_milestones(self):
        data = act_one().to_dict()
        data["completed"].remove("quiet")
        data["flags"].remove("quiet_reflected")
        with self.assertRaises(ValueError):
            GameState.from_dict(data)

    def test_version_two_saves_load_into_version_three(self):
        state = act_one()
        data = state.to_dict()
        data["version"] = 2
        loaded = GameState.from_dict(data)
        self.assertEqual(loaded.to_dict()["version"], 3)
        self.assertEqual(loaded.completed, state.completed)
        self.assertEqual(loaded.storm_phase(), "invited", "a finished journey is invited to Part Two")
        self.assertEqual(data["version"], 2, "the caller's data is untouched")

    def test_a_save_from_a_future_version_is_refused(self):
        data = GameState().to_dict()
        data["version"] = 4
        with self.assertRaises(ValueError):
            GameState.from_dict(data)

    def test_the_new_places_story_ids_are_all_known_to_the_save_format(self):
        from game.state import KNOWN_COMPLETED, CHOICE_VALUES
        for ident in (*SAMPLE_IDS, "memory_tree", "storm_forecast", "storm_begin", "storm_done", *PREP, *SCENES, *RECOVER, "quiet_lookout"):
            self.assertIn(ident, KNOWN_COMPLETED)
        for scene in SCENES:
            self.assertEqual(CHOICE_VALUES[scene], SCENE_CHOICES[scene])
        self.assertTrue(set(NPCS) >= {"kit", "odile", "noor", "storm"})


class LookoutTests(unittest.TestCase):
    def test_the_lookout_gives_one_reflection_that_follows_the_village(self):
        plain, changed = GameState(), act_one()
        first = plain.perform("quiet_lookout")
        self.assertTrue(first.ok)
        entries = len(plain.journal)
        plain.perform("quiet_lookout")
        self.assertEqual(len(plain.journal), entries)
        self.assertNotEqual(first.text, changed.perform("quiet_lookout").text)
        before = GameState()
        before.perform("quiet_lookout")
        self.assertEqual(before.metrics, GameState().metrics, "no rewards")


class AllNewBeatsTests(unittest.TestCase):
    def test_every_new_chapter_has_written_text_and_effects_in_range(self):
        for beat in (b for b in BEATS if b.person in NEW):
            self.assertTrue(beat.intro["default"])
            self.assertGreaterEqual(len([o for o in beat.options if o.good]), 2 if beat.id.endswith("_1") or beat.id.endswith("_2") else 2)
            for option in beat.options:
                self.assertTrue(option.label and option.hint and option.title and option.text)
                self.assertTrue(all(abs(amount) <= 6 for _, amount in option.effects), option.id)


if __name__ == "__main__":
    unittest.main()
