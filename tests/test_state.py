"""Run with ``python -m unittest discover -s tests -v``; no display needed."""

from copy import deepcopy
from itertools import permutations, product
import math
import unittest

from game.state import GameState


class StoryRulesTests(unittest.TestCase):
    def gather(self, state):
        for action in [*(f"litter_{i}" for i in range(1, 7)), *(f"crate_{i}" for i in range(1, 4))]:
            self.assertTrue(state.perform(action).ok)

    def restore(self, state):
        self.assertTrue(state.perform("pump").ok)
        for i in range(1, 4):
            self.assertTrue(state.perform(f"garden_{i}").ok)
        self.assertTrue(state.perform("quiet").ok)

    def preferred_path(self):
        state = GameState()
        self.gather(state)
        self.restore(state)
        for person in ("mira", "rowan", "amani"):
            self.assertTrue(state.choose(person, "listen").ok)
        self.assertTrue(state.choose("theo", "workshop").ok)
        self.assertTrue(state.choose("council", "needs").ok)
        return state

    def test_complete_path_requires_cooperation_and_a_deliberate_ending(self):
        state = self.preferred_path()
        self.assertTrue(state.can_finish)
        self.assertNotIn("balanced", state.flags)
        self.assertEqual(state.metrics, {"environment": 86, "equity": 84, "resilience": 86})
        self.assertEqual(state.resources, {"supplies": 5, "seeds": 0})
        self.assertTrue(state.choose("council", "finish").ok)
        self.assertIn("balanced", state.flags)
        self.assertIn("finish", state.completed)

    def test_every_branch_can_recover_with_finite_supplies(self):
        """243 branch combinations include initial dismissals and both dilemmas."""
        for rowan, amani, mira, factory, allocation in product(
            ("listen", "space", "rush"),
            ("listen", "deliver", "dismiss"),
            ("listen", "coordinate", "command"),
            ("workshop", "restart", "reserve"),
            ("needs", "equal", "queue"),
        ):
            with self.subTest(rowan=rowan, amani=amani, mira=mira, factory=factory, allocation=allocation):
                state = GameState()
                self.gather(state)
                self.restore(state)
                for person, choice, adverse, repair in (
                    ("rowan", rowan, "rush", "space"),
                    ("amani", amani, "dismiss", "deliver"),
                    ("mira", mira, "command", "coordinate"),
                ):
                    self.assertTrue(state.choose(person, choice).ok)
                    if choice == adverse:
                        self.assertTrue(state.choose(person, repair).ok)
                self.assertTrue(state.choose("theo", factory).ok)
                self.assertTrue(state.choose("council", allocation).ok)
                if factory != "workshop":
                    self.assertTrue(state.choose("theo", "retrofit").ok)
                self.assertTrue(state.choose("council", "review").ok)
                self.assertTrue(state.can_finish, state.objectives())
                self.assertGreaterEqual(state.resources["supplies"], 0)
                self.assertTrue(state.perform("finish").ok)
                self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())

    def test_cannot_win_by_only_cleaning_or_by_scores_alone(self):
        state = GameState()
        self.gather(state)
        self.assertFalse(state.can_finish)
        state.metrics = {key: 100 for key in state.metrics}
        self.assertFalse(state.can_finish)
        before = state.to_dict()
        self.assertFalse(state.perform("finish").ok)
        self.assertEqual(state.to_dict(), before)

    def test_resources_are_not_spent_when_an_action_is_unaffordable(self):
        state = GameState()
        self.assertTrue(state.perform("pump").ok)
        before = state.to_dict()
        self.assertFalse(state.choose("council", "needs").ok)
        self.assertEqual(state.to_dict(), before)
        self.assertFalse(state.choose("theo", "workshop").ok)
        self.assertEqual(state.to_dict(), before)
        self.gather(state)
        self.assertTrue(state.choose("council", "needs").ok)

    def test_repeated_interactions_do_not_farm_rewards_or_journal_entries(self):
        state = self.preferred_path()
        state.perform("noticeboard")
        state.perform("finish")
        before = state.to_dict()
        for action in ("litter_1", "crate_1", "garden_1", "pump", "quiet", "noticeboard", "finish"):
            for _ in range(3):
                self.assertTrue(state.perform(action).ok)
        for person in ("rowan", "mira", "amani", "theo"):
            self.assertTrue(state.choose(person, "reflect").ok)
            self.assertFalse(state.choose(person, "listen").ok)
        self.assertEqual(state.to_dict(), before)

    def test_dilemma_choices_have_different_consequences(self):
        states = []
        for choice in ("needs", "equal", "queue"):
            state = GameState()
            state.choose("council", choice)
            states.append(state)
        self.assertEqual([s.resources["supplies"] for s in states], [0, 0, 0])
        self.assertEqual([s.metrics["equity"] for s in states], [52, 42, 32])
        self.assertEqual([s.choices["allocation"] for s in states], ["needs", "equal", "queue"])
        for state in states:
            self.assertTrue(state.choose("council", "review").ok)
            before = state.to_dict()
            self.assertFalse(state.choose("council", "review").ok)
            self.assertEqual(state.to_dict(), before)

    def test_restart_has_an_environment_cost_and_can_be_revisited(self):
        state = GameState()
        self.assertTrue(state.choose("theo", "restart").ok)
        self.assertEqual(state.metrics["environment"], 18)
        self.assertEqual(state.resources["supplies"], 4)
        self.assertTrue(state.choose("theo", "retrofit").ok)
        self.assertIn("factory_shared", state.flags)
        self.assertEqual(state.resources["supplies"], 1)
        self.assertEqual(state.metrics["environment"], 28)

    def test_pressure_is_recoverable_and_cannot_be_repeated(self):
        state = GameState()
        self.assertTrue(state.choose("rowan", "rush").ok)
        self.assertNotIn("support_rowan", state.completed)
        before = state.to_dict()
        self.assertFalse(state.choose("rowan", "rush").ok)
        self.assertEqual(state.to_dict(), before)
        self.assertTrue(state.choose("rowan", "listen").ok)
        self.assertIn("support_rowan", state.completed)
        self.assertTrue(state.perform("pump").ok)
        self.assertIn("difficult", state.dialogue("rowan").text)

    def test_nonlinear_order_and_optional_lore(self):
        state = GameState()
        self.assertTrue(state.choose("council", "needs").ok)
        self.assertEqual(state.resources["supplies"], 0)
        self.assertFalse(state.perform("garden_1").ok)
        self.gather(state)
        self.restore(state)
        for person in ("amani", "rowan", "mira"):
            state.choose(person, "listen")
        state.choose("theo", "workshop")
        self.assertNotIn("noticeboard", state.completed)
        self.assertTrue(state.can_finish)

    def test_quest_orders_cannot_exhaust_or_double_spend_critical_resources(self):
        """1,080 orders/decision pairs begin with only six supplies, then recover."""
        for order, factory, allocation in product(
            permutations(("pump", "gardens", "factory", "council", "quiet")),
            ("workshop", "restart", "reserve"),
            ("needs", "equal", "queue"),
        ):
            with self.subTest(order=order, factory=factory, allocation=allocation):
                state = GameState()
                for person in ("mira", "rowan", "amani"):
                    state.choose(person, "listen")

                def attempt(task):
                    if task == "gardens":
                        actions = [f"garden_{i}" for i in range(1, 4)]
                    else:
                        actions = [task]
                    for action in actions:
                        if action in state.completed:
                            continue
                        before = state.to_dict()
                        if action == "factory":
                            result = state.choose("theo", factory)
                        elif action == "council":
                            result = state.choose("council", allocation)
                        else:
                            result = state.perform(action)
                        if not result.ok:
                            self.assertEqual(state.to_dict(), before)

                for task in order:
                    attempt(task)
                self.gather(state)
                for task in order:
                    attempt(task)
                if factory != "workshop":
                    self.assertTrue(state.choose("theo", "retrofit").ok)
                self.assertTrue(state.choose("council", "review").ok)
                self.assertTrue(state.can_finish, state.objectives())
                self.assertEqual(GameState.from_dict(state.to_dict()).to_dict(), state.to_dict())

    def test_save_roundtrip_is_detached_and_preserves_story(self):
        state = self.preferred_path()
        state.play_seconds = 128.75
        encoded = state.to_dict()
        restored = GameState.from_dict(encoded)
        self.assertEqual(restored.to_dict(), encoded)
        encoded["metrics"]["equity"] = 0
        encoded["journal"][0]["body"] = "changed"
        self.assertNotEqual(restored.metrics["equity"], 0)
        self.assertNotEqual(restored.journal[0]["body"], "changed")

    def test_invalid_save_values_are_rejected(self):
        base = GameState().to_dict()
        mutations = [
            lambda d: d.update(version=99),
            lambda d: d.update(version=True),
            lambda d: d.pop("choices"),
            lambda d: d.update(unexpected=True),
            lambda d: d["metrics"].update(environment=-1),
            lambda d: d["metrics"].update(environment=101),
            lambda d: d["metrics"].update(equity=True),
            lambda d: d["resources"].update(supplies=-1),
            lambda d: d["resources"].update(seeds=4),
            lambda d: d["resources"].update(supplies="6"),
            lambda d: d["resources"].update(supplies=7),
            lambda d: d.update(completed=["unknown"]),
            lambda d: d.update(completed=["quiet", "quiet"]),
            lambda d: d.update(completed=["support_rowan"]),
            lambda d: d.update(flags=["arbitrary"]),
            lambda d: d.update(flags=["balanced"]),
            lambda d: d.update(choices={"allocation": "cheat"}),
            lambda d: d.update(choices={"allocation": "needs"}),
            lambda d: d.update(journal=[]),
            lambda d: d.update(journal=[{"title": "t"}]),
            lambda d: d.update(journal=[{"title": "t", "body": ""}]),
            lambda d: d.update(play_seconds=math.inf),
            lambda d: d.update(play_seconds=math.nan),
            lambda d: d.update(play_seconds=True),
            lambda d: d.update(play_seconds=-1),
            lambda d: d.update(play_seconds=10**1000),
        ]
        for mutate in mutations:
            data = deepcopy(base)
            mutate(data)
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    GameState.from_dict(data)

    def test_save_flag_consistency_and_unknown_actions(self):
        state = GameState()
        before = state.to_dict()
        self.assertFalse(state.perform("unknown").ok)
        self.assertFalse(state.choose("unknown", "unknown").ok)
        self.assertEqual(state.to_dict(), before)
        data = deepcopy(before)
        data["completed"] = ["pump"]
        with self.assertRaises(ValueError):
            GameState.from_dict(data)
        data = deepcopy(before)
        data["resources"]["seeds"] = 2
        with self.assertRaises(ValueError):
            GameState.from_dict(data)


if __name__ == "__main__":
    unittest.main()
