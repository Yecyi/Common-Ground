"""Rules for resident scenes, the circle dispute, garden plots, hints and save version 2."""

from copy import deepcopy
from itertools import product
import unittest

from game.state import GARDEN_IDS, GameState
from game.story import BEATS, NPCS


LITTER = [f"litter_{i}" for i in range(1, 7)]
CRATES = [f"crate_{i}" for i in range(1, 4)]


def gather(state):
    for action in (*LITTER, *CRATES):
        state.perform(action)


def restore(state):
    state.perform("pump")
    for i in range(1, 4):
        state.perform(f"garden_{i}")
    state.perform("quiet")


def preferred(factory="workshop", allocation="needs"):
    state = GameState()
    gather(state)
    restore(state)
    for person in ("mira", "rowan", "amani"):
        assert state.choose(person, "listen").ok
    assert state.choose("theo", factory).ok
    assert state.choose("council", allocation).ok
    return state


def first_good(beat):
    return next(o for o in beat.options if o.good)


def play_all_beats(state):
    """Take the first supportive response in every available resident scene."""
    progressed = True
    while progressed:
        progressed = False
        for person in ("rowan", "mira", "amani", "theo"):
            beat = state.available_beat(person)
            if beat:
                assert state.choose(person, f"{beat.id}:{first_good(beat).id}").ok
                progressed = True


class ResidentSceneTests(unittest.TestCase):
    def test_scenes_wait_for_their_conditions(self):
        state = GameState()
        for person in ("rowan", "mira", "amani", "theo"):
            self.assertIsNone(state.available_beat(person))
        state.choose("rowan", "listen")
        self.assertIsNone(state.available_beat("rowan"), "needs the pump repaired first")
        state.perform("pump")
        self.assertEqual(state.available_beat("rowan").id, "rowan_2")
        state.choose("mira", "listen")
        self.assertIsNone(state.available_beat("mira"), "needs three completed tasks")
        state.perform("litter_1")
        self.assertIsNone(state.available_beat("mira"), "two tasks are not enough")
        state.perform("litter_2")
        self.assertEqual(state.available_beat("mira").id, "mira_2")
        self.assertEqual(state.available_beat("rowan").id, "rowan_2")

    def test_second_and_third_scenes_follow_in_order(self):
        state = preferred()
        self.assertEqual(state.available_beat("rowan").id, "rowan_2")
        for before, after in (("rowan", "rowan_3"), ("mira", "mira_3"), ("amani", "amani_3"), ("theo", "theo_3")):
            beat = state.available_beat(before)
            self.assertTrue(state.choose(before, f"{beat.id}:{first_good(beat).id}").ok)
            self.assertEqual(state.available_beat(before).id, after)
            beat = state.available_beat(before)
            self.assertTrue(state.choose(before, f"{beat.id}:{first_good(beat).id}").ok)
            self.assertIsNone(state.available_beat(before))

    def test_scenes_never_cost_supplies_and_cannot_be_repeated(self):
        state = preferred()
        supplies = state.resources["supplies"]
        play_all_beats(state)
        self.assertEqual(state.resources["supplies"], supplies)
        before = state.to_dict()
        for beat in (b for b in BEATS if b.person in ("rowan", "mira", "amani", "theo")):
            result = state.choose(beat.person, f"{beat.id}:{first_good(beat).id}")
            self.assertFalse(result.ok, beat.id)
        self.assertEqual(state.to_dict(), before)

    def test_pressure_in_a_scene_can_be_repaired_once(self):
        for beat in (b for b in BEATS if any(not o.good for o in b.options)):
            with self.subTest(beat=beat.id):
                state = preferred()
                play_scenes_before(state, beat.id)
                bad = next(o for o in beat.options if not o.good)
                before = dict(state.metrics)
                self.assertTrue(state.choose(beat.person, f"{beat.id}:{bad.id}").ok)
                self.assertIn(f"rejected_{beat.id}", state.completed)
                self.assertNotIn(f"beat_{beat.id}", state.completed)
                for metric, amount in bad.effects:
                    self.assertEqual(state.metrics[metric], max(0, before[metric] + amount))
                self.assertNotIn(bad.id, [c.id.split(":")[-1] for c in state.dialogue(beat.person).choices])
                again = state.choose(beat.person, f"{beat.id}:{bad.id}")
                self.assertFalse(again.ok)
                self.assertTrue(state.choose(beat.person, f"{beat.id}:{first_good(beat).id}").ok)
                self.assertIn(f"beat_{beat.id}", state.completed)
                self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())

    def test_scene_variants_follow_earlier_decisions(self):
        texts = set()
        for allocation in ("needs", "equal", "queue"):
            state = preferred(allocation=allocation)
            texts.add(state.dialogue("amani").text)
        self.assertEqual(len(texts), 3)
        texts = set()
        for factory in ("workshop", "restart", "reserve"):
            state = preferred(factory=factory)
            texts.add(state.dialogue("theo").text)
        self.assertEqual(len(texts), 3)

    def test_reflection_is_still_available_during_a_scene(self):
        state = preferred()
        for person in ("rowan", "mira", "amani", "theo"):
            self.assertIn("reflect", [c.id for c in state.dialogue(person).choices])
            self.assertTrue(state.choose(person, "reflect").ok)


def play_scenes_before(state, beat_id):
    """Complete the same resident's earlier scenes so the named one is available."""
    person = next(b.person for b in BEATS if b.id == beat_id)
    while state.available_beat(person).id != beat_id:
        beat = state.available_beat(person)
        assert state.choose(person, f"{beat.id}:{first_good(beat).id}").ok
    assert state.available_beat(person).id == beat_id


class DisputeAndPlotsTests(unittest.TestCase):
    def test_dispute_waits_for_the_circle_and_can_be_calmed(self):
        state = GameState()
        self.assertFalse(state.choose("dispute", "acknowledge").ok)
        gather(state)
        state.choose("council", "queue")
        self.assertIn("blame", [c.id for c in state.dialogue("dispute").choices])
        self.assertEqual(state.dialogue("dispute").tension, 0.9)
        before = dict(state.metrics)
        self.assertTrue(state.choose("dispute", "blame").ok)
        self.assertEqual(state.metrics["equity"], before["equity"] - 3)
        self.assertEqual(state.metrics["resilience"], before["resilience"] - 4)
        self.assertNotIn("blame", [c.id for c in state.dialogue("dispute").choices])
        self.assertLess(state.dialogue("dispute").tension, 0.9)
        self.assertTrue(state.choose("dispute", "shared_need").ok)
        self.assertIn("dispute", state.completed)
        self.assertFalse(state.choose("dispute", "pause").ok)
        self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())

    def test_each_calming_response_works_and_costs_nothing(self):
        for response in ("acknowledge", "shared_need", "pause"):
            state = preferred()
            supplies = state.resources["supplies"]
            result = state.choose("dispute", response)
            self.assertTrue(result.ok and result.resolved)
            self.assertEqual(state.resources["supplies"], supplies)
            self.assertIn("dispute", state.completed)

    def test_plots_wait_for_the_planted_garden(self):
        state = GameState()
        self.assertFalse(state.choose("plots", "lottery").ok)
        gather(state)
        for i in range(1, 4):
            state.perform(f"garden_{i}")
        self.assertTrue(state.choose("plots", "lottery").ok)

    def test_plots_choices_differ_cost_nothing_and_show_who_was_reached(self):
        results = {}
        for choice in ("needs_first", "lottery", "helpers"):
            state = GameState()
            gather(state)
            for i in range(1, 4):
                state.perform(f"garden_{i}")
            supplies, equity = state.resources["supplies"], state.metrics["equity"]
            result = state.choose("plots", choice)
            self.assertTrue(result.ok)
            self.assertEqual(state.resources["supplies"], supplies)
            self.assertEqual(len(result.outcome), 4)
            self.assertTrue(all(0 <= level <= 3 for _, level in result.outcome))
            results[choice] = state.metrics["equity"] - equity
            ids = [c.id for c in state.dialogue("plots").choices]
            self.assertEqual("review" in ids, choice != "needs_first")
        self.assertGreater(results["needs_first"], results["lottery"])
        self.assertGreater(results["lottery"], results["helpers"])

    def test_plots_review_improves_who_was_reached_and_can_happen_once(self):
        state = GameState()
        gather(state)
        for i in range(1, 4):
            state.perform(f"garden_{i}")
        first = state.choose("plots", "helpers")
        review = state.choose("plots", "review")
        self.assertTrue(review.ok)
        self.assertGreater(sum(level for _, level in review.outcome), sum(level for _, level in first.outcome))
        self.assertFalse(state.choose("plots", "review").ok)
        self.assertFalse(state.choose("plots", "lottery").ok)
        self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())

    def test_every_dilemma_shows_an_outcome_panel(self):
        state = GameState()
        gather(state)
        self.assertTrue(state.choose("council", "queue").outcome)
        self.assertTrue(state.choose("council", "review").outcome)
        self.assertTrue(state.choose("theo", "restart").outcome)
        self.assertTrue(state.choose("theo", "retrofit").outcome)


class EndingGateTests(unittest.TestCase):
    def test_optional_scenes_alone_cannot_unlock_the_ending(self):
        state = GameState()
        gather(state)
        state.choose("council", "needs")
        state.choose("dispute", "acknowledge")
        self.assertFalse(state.can_finish)
        self.assertFalse(state.choose("council", "finish").ok)
        self.assertNotIn("balanced", state.flags)

    def test_all_optional_scenes_add_to_the_ending_without_replacing_it(self):
        state = preferred()
        play_all_beats(state)
        self.assertTrue(state.choose("dispute", "shared_need").ok)
        self.assertTrue(state.choose("plots", "needs_first").ok)
        for spot in ("quiet_river", "quiet_garden"):
            self.assertTrue(state.perform(spot).ok)
        self.assertTrue(state.can_finish)
        self.assertNotIn("balanced", state.flags)
        self.assertTrue(state.choose("council", "finish").ok)
        self.assertIn("balanced", state.flags)
        self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())

    def test_new_scenes_leave_every_branch_recoverable(self):
        """Pressure in every optional scene still leaves a route to the ending."""
        for factory, allocation in product(("workshop", "restart", "reserve"), ("needs", "equal", "queue")):
            with self.subTest(factory=factory, allocation=allocation):
                state = GameState()
                gather(state)
                restore(state)
                for person in ("mira", "rowan", "amani"):
                    state.choose(person, "listen")
                state.choose("theo", factory)
                state.choose("council", allocation)
                for beat in BEATS:
                    bad = next((o for o in beat.options if not o.good), None)
                    if bad and state.available_beat(beat.person) and state.available_beat(beat.person).id == beat.id:
                        state.choose(beat.person, f"{beat.id}:{bad.id}")
                state.choose("dispute", "blame")
                state.choose("plots", "helpers")
                if factory != "workshop":
                    self.assertTrue(state.choose("theo", "retrofit").ok)
                self.assertTrue(state.choose("council", "review").ok)
                play_all_beats(state)
                state.choose("dispute", "pause")
                state.choose("plots", "review")
                self.assertTrue(state.can_finish, (state.metrics, state.objectives()))
                self.assertTrue(state.perform("finish").ok)
                self.assertGreaterEqual(state.resources["supplies"], 0)

    def test_metrics_stay_within_bounds_after_every_option(self):
        state = preferred()
        play_all_beats(state)
        for value in state.metrics.values():
            self.assertTrue(0 <= value <= 100)


class QuietSpotTests(unittest.TestCase):
    def test_extra_quiet_spots_give_one_entry_and_no_rewards(self):
        state = GameState()
        for spot in ("quiet_river", "quiet_garden"):
            before = state.to_dict()
            self.assertTrue(state.perform(spot).ok)
            self.assertEqual(state.metrics, before["metrics"])
            self.assertEqual(state.resources, before["resources"])
            self.assertEqual(len(state.journal), len(before["journal"]) + 1)
            once = state.to_dict()
            for _ in range(3):
                self.assertTrue(state.perform(spot).ok)
            self.assertEqual(state.to_dict(), once)
        self.assertNotIn("quiet_reflected", state.flags)

    def test_quiet_spot_text_reflects_what_has_changed(self):
        before, after = GameState(), GameState()
        gather(after)
        after.perform("pump")
        self.assertNotEqual(before.perform("quiet_river").text, after.perform("quiet_river").text)


class GuidanceTests(unittest.TestCase):
    def test_first_step_matches_the_opening_and_changes_with_state(self):
        state = GameState()
        text, target = state.next_step()
        self.assertEqual(target, "mira")
        self.assertIn("Mira", text)
        state.choose("mira", "listen")
        self.assertEqual(state.next_step()[1], "pump")
        state.perform("pump")
        self.assertEqual(state.next_step()[1], "garden")
        state.perform("garden_1")
        state.perform("garden_2")
        self.assertEqual(state.next_step()[1], "collect", "supplies are short for the last bed")
        state = GameState()
        state.choose("mira", "command")
        self.assertIn("try again", state.next_step()[0])

    def test_following_the_suggestions_always_reaches_the_ending(self):
        for factory, allocation in product(("workshop", "restart", "reserve"), ("needs", "equal", "queue")):
            with self.subTest(factory=factory, allocation=allocation):
                self.follow_hints(factory, allocation)

    def follow_hints(self, factory, allocation):
        state = GameState()
        for _ in range(200):
            text, target = state.next_step()
            self.assertTrue(text)
            if "balanced" in state.flags:
                break
            if target == "collect":
                action = next((a for a in (*LITTER, *CRATES) if a not in state.completed), None)
                self.assertIsNotNone(action, "a gather suggestion must point at something to gather")
                self.assertTrue(state.perform(action).ok)
            elif target == "garden":
                action = next(f"garden_{i}" for i in range(1, 4) if f"garden_{i}" not in state.completed)
                self.assertTrue(state.perform(action).ok)
            elif target in ("pump", "quiet"):
                self.assertTrue(state.perform(target).ok)
            elif target in ("mira", "rowan", "amani", "theo"):
                beat = state.available_beat(target)
                if target == "theo" and "factory" not in state.completed:
                    cost = {"workshop": 3, "restart": 2, "reserve": 0}[factory]
                    for action in (*LITTER, *CRATES):
                        if state.resources["supplies"] >= cost:
                            break
                        state.perform(action)
                    result = state.choose("theo", factory)
                elif beat:
                    result = state.choose(target, f"{beat.id}:{first_good(beat).id}")
                elif target == "theo":
                    result = state.choose("theo", "retrofit")
                else:
                    result = state.choose(target, "listen")
                self.assertTrue(result.ok, (target, text, result))
            elif target == "council":
                if "council" not in state.completed:
                    result = state.choose("council", allocation)
                elif state.can_finish:
                    result = state.choose("council", "finish")
                else:
                    result = state.choose("council", "review")
                self.assertTrue(result.ok, (text, result))
            elif target == "plots":
                self.assertTrue(state.choose("plots", "needs_first").ok)
            elif target == "dispute":
                self.assertTrue(state.choose("dispute", "acknowledge").ok)
            else:
                self.fail(f"The hint has no next action: {text!r} {state.metrics}")
        self.assertIn("balanced", state.flags, state.next_step())

    def test_every_hint_target_is_a_real_place_or_a_known_action(self):
        valid = {None, "collect", "garden", *NPCS, "pump", "quiet"}
        state = GameState()
        seen = set()
        for _ in range(60):
            text, target = state.next_step()
            seen.add(target)
            self.assertIn(target, valid)
            if target == "mira":
                state.choose("mira", "listen")
            elif target == "collect":
                action = next((a for a in (*LITTER, *CRATES) if a not in state.completed), None)
                if action is None:
                    break
                state.perform(action)
            elif target in ("pump", "quiet"):
                state.perform(target)
            elif target == "garden":
                state.perform(next(f"garden_{i}" for i in range(1, 4) if f"garden_{i}" not in state.completed))
            else:
                break
        self.assertTrue({"mira", "pump"} <= seen)


class RecapTests(unittest.TestCase):
    def test_recap_lists_each_decision_with_who_gained_and_who_was_missed(self):
        state = preferred(factory="restart", allocation="queue")
        state.choose("council", "review")
        rows = state.recap()
        labels = [r["label"] for r in rows]
        self.assertIn("Six supplies at the circle", labels)
        self.assertIn("The old factory", labels)
        row = next(r for r in rows if r["label"] == "Six supplies at the circle")
        self.assertIn("Revisited", row["revisited"])
        self.assertIn("Riverside", row["missed"])
        for row in rows:
            self.assertEqual(set(row), {"label", "chosen", "benefited", "missed", "revisited", "question"})
            self.assertTrue(all(row.values()))

    def test_recap_notes_a_resident_conversation_that_was_revisited(self):
        state = GameState()
        state.choose("rowan", "rush")
        state.choose("rowan", "listen")
        row = next(r for r in state.recap() if r["label"] == "Talking with Rowan")
        self.assertIn("came back", row["revisited"])

    def test_epilogue_follows_the_choices(self):
        endings = set()
        for factory, allocation in product(("workshop", "restart", "reserve"), ("needs", "equal", "queue")):
            state = preferred(factory, allocation)
            endings.add(tuple(state.epilogue()))
        self.assertEqual(len(endings), 9)
        state = preferred()
        plain = state.epilogue()
        play_all_beats(state)
        state.choose("plots", "lottery")
        state.choose("dispute", "pause")
        richer = state.epilogue()
        self.assertGreater(len(richer), len(plain))
        self.assertTrue(any("drawn by lot" in p for p in richer))
        self.assertTrue(any("worker" in p and "Riverside" in p for p in richer))
        self.assertTrue(any("when able" in p for p in richer))


class SaveVersionTests(unittest.TestCase):
    def v1(self, state):
        data = state.to_dict()
        data["version"] = 1
        del data["planted_at"]
        return data

    def test_version_one_saves_upgrade_without_losing_progress(self):
        state = preferred()
        state.play_seconds = 300
        data = self.v1(state)
        original = deepcopy(data)
        loaded = GameState.from_dict(data)
        self.assertEqual(data, original, "loading must not modify the caller's data")
        self.assertEqual(loaded.SAVE_VERSION, 3)
        self.assertEqual(loaded.completed, state.completed)
        self.assertEqual(loaded.metrics, state.metrics)
        self.assertEqual(loaded.to_dict()["version"], 3)
        self.assertEqual({g for g in GARDEN_IDS}, set(loaded.planted_at))
        self.assertTrue(all(loaded.garden_stage(g) == 3 for g in GARDEN_IDS))

    def test_a_fresh_version_one_save_upgrades(self):
        data = self.v1(GameState())
        self.assertEqual(GameState.from_dict(data).planted_at, {})

    def test_malformed_version_one_saves_are_still_rejected(self):
        for mutate in (
            lambda d: d.update(completed=["unknown"]),
            lambda d: d.update(completed="pump"),
            lambda d: d.update(completed=[["pump"]]),
            lambda d: d.update(completed=None),
        ):
            data = self.v1(GameState())
            mutate(data)
            with self.assertRaises(ValueError):
                GameState.from_dict(data)

    def test_version_two_round_trip_keeps_growth_and_later_scenes(self):
        state = preferred()
        play_all_beats(state)
        state.choose("dispute", "acknowledge")
        state.choose("plots", "needs_first")
        state.perform("quiet_river")
        state.play_seconds = 500.5
        loaded = GameState.from_dict(state.to_dict())
        self.assertEqual(loaded.to_dict(), state.to_dict())
        self.assertEqual(loaded.planted_at, state.planted_at)

    def test_invalid_later_scene_saves_are_rejected(self):
        state = preferred()
        play_all_beats(state)
        state.choose("dispute", "acknowledge")
        state.choose("plots", "lottery")
        state.choose("plots", "review")
        base = state.to_dict()
        mutations = {
            "unknown scene": lambda d: d["completed"].append("beat_nobody_9"),
            "scene without its choice": lambda d: d["choices"].pop("rowan_2"),
            "scene with a wrong choice": lambda d: d["choices"].update(rowan_2="push"),
            "dispute without circle": lambda d: (d["completed"].remove("council"), d["flags"].remove("council_held"), d["choices"].pop("allocation"), d["resources"].update(supplies=d["resources"]["supplies"] + 6)),
            "plots without a choice": lambda d: d["choices"].pop("plots"),
            "review of the needs-first plan": lambda d: d["choices"].update(plots="needs_first"),
            "invalid dispute choice": lambda d: d["choices"].update(dispute="shout"),
            "missing growth record": lambda d: d["planted_at"].pop("garden_1"),
            "growth for an unplanted bed": lambda d: (d["completed"].remove("garden_1"), d["resources"].update(seeds=d["resources"]["seeds"] + 1, supplies=d["resources"]["supplies"] + 1)),
            "bad growth time": lambda d: d["planted_at"].update(garden_1=float("nan")),
            "negative growth time": lambda d: d["planted_at"].update(garden_1=-1),
            "growth time is not a number": lambda d: d["planted_at"].update(garden_1="soon"),
        }
        for name, mutate in mutations.items():
            data = deepcopy(base)
            mutate(data)
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    GameState.from_dict(data)

    def test_a_scene_completed_before_its_conditions_is_rejected(self):
        state = GameState()
        state.choose("rowan", "listen")
        data = state.to_dict()
        data["completed"].append("beat_rowan_2")
        data["choices"]["rowan_2"] = "own_role"
        with self.assertRaises(ValueError):
            GameState.from_dict(data)


class GardenGrowthTests(unittest.TestCase):
    def test_planted_beds_grow_with_time_in_the_village(self):
        state = GameState()
        gather(state)
        self.assertEqual(state.garden_stage("garden_1"), 0)
        state.perform("garden_1")
        self.assertEqual(state.garden_stage("garden_1"), 1)
        state.play_seconds += 60
        self.assertEqual(state.garden_stage("garden_1"), 2)
        state.play_seconds += 100
        self.assertEqual(state.garden_stage("garden_1"), 3)
        self.assertEqual(state.garden_stage("garden_2"), 0)

    def test_growth_never_changes_progress(self):
        state = GameState()
        gather(state)
        state.perform("garden_1")
        before = (state.metrics, state.resources, state.flags, state.completed)
        state.play_seconds += 1000
        self.assertEqual((state.metrics, state.resources, state.flags, state.completed), before)


class BalanceTests(unittest.TestCase):
    def test_overall_balance_is_weighted_towards_the_weakest_value(self):
        state = GameState()
        state.metrics = {"environment": 90, "equity": 90, "resilience": 90}
        high = state.balance
        state.metrics["equity"] = 10
        self.assertLess(state.balance, high)
        self.assertLess(state.balance, sum(state.metrics.values()) / 300)
        state.metrics = {key: 0 for key in state.metrics}
        self.assertEqual(state.balance, 0)
        state.metrics = {key: 100 for key in state.metrics}
        self.assertEqual(state.balance, 1)


if __name__ == "__main__":
    unittest.main()
