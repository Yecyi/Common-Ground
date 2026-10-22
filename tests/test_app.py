"""Headless integration regressions for real screens, persistence and endings."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame

from game.app import App
from game.state import GameState
from game.storage import load_game, save_game


class AppIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="common-ground-test-")
        self.folder = Path(self.temp.name)
        self.app = App(save_dir=self.folder, window=False, audio=False)

    def tearDown(self):
        self.app.close()
        self.temp.cleanup()

    def seed_journey(self):
        state = GameState()
        state.perform("litter_1")
        state.choose("rowan", "listen")
        state.play_seconds = 45.25
        save_game(self.app.slot, state, (480, 500))
        self.app.check_save()
        self.assertTrue(self.app.save_valid)
        return self.app.slot.read_bytes()

    def close_window(self):
        self.app.handle(pygame.event.Event(pygame.QUIT))
        self.assertFalse(self.app.running)

    def test_closing_title_settings_preserves_an_existing_journey(self):
        original = self.seed_journey()
        self.app.action("settings")
        self.app.draw()
        self.close_window()
        self.assertEqual(self.app.slot.read_bytes(), original)

    def test_closing_title_help_preserves_an_existing_journey(self):
        original = self.seed_journey()
        self.app.action("help")
        self.app.draw()
        self.close_window()
        self.assertEqual(self.app.slot.read_bytes(), original)

    def test_closing_title_settings_does_not_create_a_journey(self):
        self.app.action("settings")
        self.app.action("setting:muted")
        self.close_window()
        self.assertFalse(self.app.slot.exists())
        self.assertTrue((self.folder / "settings.json").exists())

    def test_new_journey_backs_up_valid_progress_before_replacing_it(self):
        original = self.seed_journey()
        self.app.action("new")
        self.assertEqual(self.app.mode, "confirm")
        self.assertEqual(self.app.slot.read_bytes(), original)
        self.app.action("confirm_new")
        self.assertEqual(self.app.mode, "intro")
        backups = list(self.folder.glob("previous-journey-*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)
        self.assertEqual(self.app.slot.read_bytes(), original)
        self.app.action("begin")
        state, _ = load_game(self.app.slot)
        self.assertEqual(state.completed, set())
        self.assertEqual(backups[0].read_bytes(), original)

    def test_new_journey_also_preserves_unreadable_save_bytes(self):
        original = b'{"broken": invalid json\n'
        self.app.slot.write_bytes(original)
        self.app.check_save()
        self.assertFalse(self.app.save_valid)
        self.app.action("new")
        self.assertEqual(self.app.mode, "confirm")
        self.app.action("confirm_new")
        backups = list(self.folder.glob("previous-journey-*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)
        self.app.action("begin")
        self.assertEqual(load_game(self.app.slot)[0].completed, set())
        self.assertEqual(backups[0].read_bytes(), original)

    def test_cancelling_new_journey_keeps_existing_progress(self):
        original = self.seed_journey()
        self.app.action("new")
        self.app.action("cancel_new")
        self.assertEqual(self.app.mode, "title")
        self.assertEqual(self.app.slot.read_bytes(), original)
        self.assertEqual(list(self.folder.glob("previous-journey-*.json")), [])

    def test_backup_failure_cancels_replacement(self):
        original = self.seed_journey()
        self.app.action("new")
        with patch.object(Path, "write_bytes", side_effect=OSError("not writable")):
            self.app.action("confirm_new")
        self.assertEqual(self.app.mode, "title")
        self.assertFalse(self.app.active_session)
        self.assertEqual(self.app.slot.read_bytes(), original)

    def test_closing_in_game_settings_still_saves_current_progress(self):
        self.seed_journey()
        self.app.action("continue")
        self.assertTrue(self.app.active_session)
        self.app.state.perform("litter_2")
        self.app.action("settings")
        self.close_window()
        state, _ = load_game(self.app.slot)
        self.assertIn("litter_1", state.completed)
        self.assertIn("litter_2", state.completed)
        self.assertIn("support_rowan", state.completed)
        self.assertEqual(state.play_seconds, 45.25)

    def test_council_finish_reaches_the_ending_screen_and_persists(self):
        self.app.new_game()
        self.app.action("begin")
        for action in [
            *(f"litter_{i}" for i in range(1, 7)),
            *(f"crate_{i}" for i in range(1, 4)),
            *(f"garden_{i}" for i in range(1, 4)),
            "pump", "quiet",
        ]:
            self.app.state.perform(action)
        for person in ("mira", "rowan", "amani"):
            self.app.state.choose(person, "listen")
        self.app.state.choose("theo", "workshop")
        self.app.state.choose("council", "needs")
        self.app.talking_to = "council"
        self.app.action("choice:finish")
        self.assertEqual(self.app.mode, "ending")
        self.assertIn("balanced", self.app.state.flags)
        self.app.draw()
        state, _ = load_game(self.app.slot)
        self.assertIn("balanced", state.flags)

    def test_early_council_finish_shows_remaining_goals(self):
        self.app.new_game()
        self.app.action("begin")
        self.app.state.choose("council", "needs")
        self.app.talking_to = "council"
        self.app.action("choice:finish")
        self.assertEqual(self.app.mode, "result")
        self.assertFalse(self.app.result.ok)
        self.assertNotIn("balanced", self.app.state.flags)
        self.app.draw()

    def test_unaffordable_npc_decisions_remain_available_after_more_salvage(self):
        self.app.new_game()
        self.app.action("begin")
        for person, choice, milestone in (("theo", "workshop", "factory"), ("council", "needs", "council")):
            with self.subTest(person=person):
                self.app.state = GameState()
                self.app.state.perform("pump")
                before = self.app.state.to_dict()
                self.app.talking_to = person
                self.app.action("choice:" + choice)
                self.assertFalse(self.app.result.ok)
                self.assertEqual(self.app.state.to_dict(), before)
                self.assertEqual(load_game(self.app.slot)[0].to_dict(), before)
                self.assertIn(choice, [c.id for c in self.app.state.dialogue(person).choices])
                for i in range(1, 4):
                    self.app.state.perform(f"crate_{i}")
                self.app.action("choice:" + choice)
                self.assertTrue(self.app.result.ok)
                self.assertIn(milestone, self.app.state.completed)

    def test_continue_moves_a_blocked_saved_position_to_safe_spawn(self):
        state = GameState()
        save_game(self.app.slot, state, (480, 200))
        self.assertFalse(self.app.world.walkable((480, 200)))
        self.app.action("continue")
        self.assertEqual(tuple(self.app.world.player), (480, 500))
        self.assertTrue(self.app.world.walkable(self.app.world.player))


if __name__ == "__main__":
    unittest.main()
