"""Hillside, the weather, Part Two in the app, the map, the journal pages and the rain."""

from collections import deque
import os
from pathlib import Path
import tempfile
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame

from game.app import App
from game.art import Art
from game.audio import Audio
from game.layout import HEIGHT, RIVERSIDE_EDGE, WIDTH
from game.state import GameState
from game.storage import load_game, save_game
from game.storm import RECOVER
from game.world import LIT_WINDOWS, World

LITTER = [f"litter_{i}" for i in range(1, 7)]
CRATES = [f"crate_{i}" for i in range(1, 4)]
FIRST = {"kit": "kit_1:read", "odile": "odile_1:sit", "noor": "noor_1:ask_need"}
NIGHT = ("doors", "elders_first", "clinic", "sit")


def act_one():
    state = GameState()
    for action in (*LITTER, *CRATES, "pump", "garden_1", "garden_2", "garden_3", "quiet"):
        state.perform(action)
    for person in ("mira", "rowan", "amani"):
        state.choose(person, "listen")
    state.choose("theo", "workshop")
    state.choose("council", "needs")
    state.choose("council", "finish")
    return state


def everyone():
    state = act_one()
    for person, choice in FIRST.items():
        state.choose(person, choice)
    return state


def at_phase(phase):
    state = everyone()
    if phase == "invited":
        return state
    state.choose("council", "storm_forecast")
    if phase == "forecast":
        return state
    state.choose("storm", "prep_hall")
    state.choose("storm", "prep_drains")
    state.choose("storm", "begin")
    if phase == "night":
        return state
    for choice in (*NIGHT, "dawn"):
        state.choose("storm", choice)
    if phase == "aftermath":
        return state
    for task in RECOVER:
        state.perform(task)
    state.choose("council", "storm_close")
    return state


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="common-ground-test-")
        self.folder = Path(self.temp.name)
        self.app = App(save_dir=self.folder, window=False, audio=False)

    def tearDown(self):
        self.app.close()
        self.temp.cleanup()

    def start(self, state=None):
        self.app.new_game()
        self.app.draw()
        self.app.action("begin")
        if state is not None:
            self.app.state = state
        self.app.draw()

    def place(self, ident):
        return next(p for p in self.app.world.places if p.id == ident)

    def key(self, key):
        self.app.draw()
        self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=key))
        self.app.draw()

    def click(self, position):
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=position, button=1))
        self.app.draw()


class ExpandedWorldTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((64, 64), pygame.HIDDEN)
        self.world = World(Art())
        self.keys = pygame.key.get_pressed()

    def place(self, ident):
        return next(p for p in self.world.places if p.id == ident)

    def test_the_village_is_wider_and_the_original_edge_is_remembered(self):
        self.assertGreater(WIDTH, RIVERSIDE_EDGE)
        self.assertEqual((WIDTH, HEIGHT), (1760, 832))
        self.assertEqual(self.world.backgrounds[0].get_size(), (WIDTH, HEIGHT))
        for ident, x in (("clinic", 1240), ("hall", 1450), ("cottage", 1650)):
            self.assertTrue(any(name == ident and px == x for name, px, _ in self.world.decor), ident)

    def test_every_place_including_hillside_can_be_reached_on_foot_from_the_start(self):
        start = (int(self.world.player.x // 16), int(self.world.player.y // 16))
        queue, seen = deque([start]), {start}
        while queue:
            x, y = queue.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nxt = x + dx, y + dy
                if nxt not in seen and self.world.walkable((nxt[0] * 16 + 8, nxt[1] * 16 + 8)):
                    seen.add(nxt)
                    queue.append(nxt)
        self.assertTrue(any(x * 16 > 1600 for x, _ in seen), "the east end of Hillside is open")
        for place in self.world.places:
            self.assertTrue(any((x * 16 + 8 - place.x) ** 2 + (y * 16 + 8 - place.y) ** 2 < 40 ** 2 for x, y in seen), place.id)

    def test_standing_on_hillside_names_the_zone(self):
        self.world.player.update(1300, 420)
        self.assertEqual(self.world.zone(), "HILLSIDE")
        self.world.player.update(1000, 420)
        self.assertEqual(self.world.zone(), "RIVERSIDE")
        self.world.player.update(480, 500)
        self.assertEqual(self.world.zone(), "WILLOWMERE")

    def test_the_new_neighbours_are_always_there_and_stay_at_home(self):
        state = GameState()
        for ident in ("kit", "odile", "noor"):
            place = self.place(ident)
            self.assertFalse(self.world.hidden(place, state))
            self.assertIsNone(place.post)

    def test_places_appear_in_their_own_part_of_the_story(self):
        state = GameState()
        for ident in ("sample_up", "sample_out", "sample_down", "storm", *RECOVER):
            self.assertTrue(self.world.hidden(self.place(ident), state), ident)
        state.choose("kit", "kit_1:read")
        for ident in ("sample_up", "sample_out", "sample_down"):
            self.assertFalse(self.world.hidden(self.place(ident), state))
        phases = {"invited": (False, True), "forecast": (False, True), "night": (False, True), "aftermath": (False, False), "done": (True, True)}
        for phase in ("invited", "forecast", "night", "aftermath", "done"):
            state = at_phase(phase)
            storm_hidden = self.world.hidden(self.place("storm"), state)
            recovery_hidden = [self.world.hidden(self.place(r), state) for r in RECOVER]
            self.assertEqual(storm_hidden, phase == "invited", phase)
            self.assertEqual(all(recovery_hidden), phase != "aftermath", phase)

    def test_the_sample_post_jar_clears_with_the_water(self):
        art = Art()
        state = GameState()
        state.choose("kit", "kit_1:read")
        pump = GameState()
        pump.choose("kit", "kit_1:read")
        pump.perform("pump")
        self.assertLess(state.river_reading("out")[0], 2)
        for ident in ("sample_out",):
            before = self.world.sprite_for(self.place(ident), state)
            after = self.world.sprite_for(self.place(ident), pump)
            self.assertNotEqual(pygame.image.tobytes(before, "RGBA"), pygame.image.tobytes(after, "RGBA"))

    def test_standing_at_anything_on_hillside_selects_it(self):
        """The same rule as the original village: pressing E acts on the place you stand at."""
        state = at_phase("invited")
        state.completed |= {"support_kit", "storm_forecast", "storm_s5"}
        world = World(Art())
        for _ in range(300):
            world.update(1 / 30, self.keys, state)
        approaches = (("front", (0, 29)), ("left", (-30, 8)), ("right", (30, 8)), ("back", (0, -25)))
        for place in world.places:
            if world.hidden(place, state):
                continue
            tested = 0
            for label, (dx, dy) in approaches:
                if place.id.startswith("garden_") and label in ("left", "right"):
                    continue
                spot = (place.x + dx, place.y + dy)
                if not world.walkable(spot):
                    continue
                world.player.update(spot)
                world.update(1 / 60, self.keys, state)
                tested += 1
                self.assertIsNotNone(world.nearest, (place.id, label))
                self.assertEqual(world.nearest.id, place.id, f"{place.id} ({label})")
            self.assertTrue(tested, place.id)

    def test_every_phase_of_the_weather_draws_in_every_motion_and_contrast_mode(self):
        screen = pygame.Surface((1280, 840))
        for phase in ("invited", "forecast", "night", "aftermath", "done"):
            state = at_phase(phase)
            for reduced in (False, True):
                for contrast in (False, True):
                    self.world.player.update(1350, 430)
                    self.world.update(1 / 60, self.keys, state, reduce_motion=reduced)
                    self.world.draw(screen, state, 8.5, reduced, contrast)

    def test_the_weather_changes_what_is_seen_and_clears_afterwards(self):
        def look(phase):
            screen = pygame.Surface((1280, 840))
            state = at_phase(phase)
            self.world.player.update(1350, 430)
            self.world.update(1 / 60, self.keys, state)
            self.world.draw(screen, state, 3.0)
            return pygame.image.tobytes(screen, "RGB"), sum(screen.get_at((x, 300))[1] for x in range(0, 1280, 8))
        clear, clear_green = look("invited")
        night, night_green = look("night")
        done, _ = look("done")
        self.assertFalse(clear == night)
        self.assertLess(night_green, clear_green, "the night is darker")

    def test_the_windows_are_lit_only_during_the_night(self):
        def bright(phase):
            state = at_phase(phase)
            self.world.player.update(1350, 430)
            self.world.update(1 / 60, self.keys, state)
            self.world.draw(pygame.Surface((1280, 840)), state, 1.0, True)
            camera = self.world.camera
            hits = 0
            for x, y, w, h in LIT_WINDOWS[:4]:
                px, py = round(x - camera.x + w / 2), round(y - camera.y + h / 2)
                if 0 <= px < 640 and 0 <= py < 318:
                    r, g, b = self.world.low.get_at((px, py))[:3]
                    hits += r > 235 and g > 215 and b < 215
            return hits
        self.assertGreater(bright("night"), 0)
        self.assertEqual(bright("forecast"), 0)
        self.assertEqual(bright("done"), 0)

    def test_the_storm_scenery_follows_the_preparations(self):
        """Cots appear once the Hall is ready, and sandbags once the drains are cleared."""
        def regions(state):
            self.world.player.update(1230, 430)
            self.world.update(1 / 60, self.keys, state, reduce_motion=True)
            self.world.draw(pygame.Surface((1280, 840)), state, 1.0, True)
            cots = pygame.image.tobytes(self.world.low.subsurface(pygame.Rect(500, 60, 100, 50)), "RGB")
            bags = pygame.image.tobytes(self.world.low.subsurface(pygame.Rect(60, 100, 80, 40)), "RGB")
            return cots, bags
        plain = everyone()
        plain.choose("council", "storm_forecast")
        hall = everyone()
        hall.choose("council", "storm_forecast")
        hall.choose("storm", "prep_hall")
        drains = everyone()
        drains.choose("council", "storm_forecast")
        drains.choose("storm", "prep_drains")
        # The tasks nudge the three values; hold them still so only the scenery can differ.
        hall.metrics = dict(plain.metrics)
        drains.metrics = dict(plain.metrics)
        base, with_hall, with_drains = regions(plain), regions(hall), regions(drains)
        self.assertFalse(base[0] == with_hall[0], "cots appear")
        self.assertTrue(base[1] == with_hall[1], "and nothing else changes")
        self.assertFalse(base[1] == with_drains[1], "sandbags appear")
        self.assertTrue(base[0] == with_drains[0])

    def test_the_orchard_grows_on_the_slope_and_stays_out_of_view_until_planted(self):
        def look(seconds, planted=True):
            state = everyone() if planted else act_one()
            if planted:
                gather = GameState()
            state.choose("odile", "odile_2:plant_here") if planted else None
            state.play_seconds += seconds
            screen = pygame.Surface((1280, 840))
            self.world.player.update(1400, 560)
            self.world.update(1 / 60, self.keys, state, reduce_motion=True)
            self.world.draw(screen, state, 1.0, True)
            return pygame.image.tobytes(self.world.low.subsurface(pygame.Rect(120, 160, 180, 100)), "RGB")
        self.assertFalse(look(0, planted=False) == look(0), "planting shows")
        self.assertFalse(look(0) == look(70), "and it grows")
        self.assertFalse(look(70) == look(300), "and grows again")

    def test_captions_on_hillside_follow_the_story(self):
        state = GameState()
        self.world.player.update(1240, 372)
        self.assertIn("two days a week", self.world.cue_caption(state))
        state.choose("noor", "noor_1:ask_need")
        self.assertIn("propped open", self.world.cue_caption(state))
        self.world.player.update(1450, 372)
        self.assertIsNone(self.world.cue_caption(state))
        forecast = at_phase("forecast")
        self.assertIn("quiet", self.world.cue_caption(forecast))
        forecast.choose("storm", "prep_hall")
        self.assertIn("Cots", self.world.cue_caption(forecast))
        self.assertIn("mud", self.world.cue_caption(at_phase("aftermath")).lower())
        self.world.player.update(1400, 600)
        self.assertIn("Young trees", self.world.cue_caption(self._with_orchard()))

    def _with_orchard(self):
        state = GameState()
        for action in (*LITTER, *CRATES, "pump"):
            state.perform(action)
        state.choose("odile", "odile_1:sit")
        state.choose("odile", "odile_2:plant_here")
        return state


class PartTwoInTheAppTests(AppTestCase):
    def interact(self, ident):
        self.app.interact(self.place(ident))
        self.app.draw()

    def test_the_planning_table_reopens_after_each_task_and_the_night_carries_on_by_itself(self):
        self.start(at_phase("invited"))
        self.interact("council")
        self.app.action("choice:storm_forecast")
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.mode, "play")
        self.interact("storm")
        self.assertEqual(self.app.mode, "dialogue")
        self.app.action("choice:prep_hall")
        self.assertEqual(self.app.mode, "result")
        self.key(pygame.K_RETURN)
        self.assertEqual((self.app.mode, self.app.talking_to), ("dialogue", "storm"), "back at the table")
        self.assertNotIn("prep_hall", [c.id for c in self.app.conversation.choices])
        self.app.action("choice:begin")
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.mode, "dialogue")
        self.assertTrue(self.app.state.storm_scene_pending())
        for choice in (*NIGHT, "dawn"):
            self.app.action("choice:" + choice)
            self.assertTrue(self.app.result.ok, choice)
            self.key(pygame.K_RETURN)
        self.assertEqual(self.app.mode, "play")
        self.assertEqual(self.app.state.storm_phase(), "aftermath")

    def test_a_task_that_does_not_fit_returns_to_the_table(self):
        self.start(at_phase("forecast"))
        for task in ("prep_drains", "prep_rowan", "prep_odile"):
            self.interact("storm")
            self.app.action("choice:" + task)
            self.key(pygame.K_RETURN)
        self.app.action("choice:prep_pump")
        self.assertTrue(self.app.result.ok)

    def test_leaving_the_board_and_doing_something_else_does_not_reopen_it(self):
        self.start(at_phase("forecast"))
        self.interact("storm")
        self.app.action("choice:reflect")
        self.key(pygame.K_RETURN)
        self.assertEqual((self.app.mode, self.app.talking_to), ("dialogue", "storm"), "a reflection returns to the board")
        self.app.action("leave_dialogue")
        self.assertEqual(self.app.mode, "play")
        self.interact("sample_up")
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.mode, "play", "an unrelated result must not pull you back to the board")

    def test_the_daylight_badge_shows_while_planning_and_goes_when_the_night_begins(self):
        self.start(at_phase("forecast"))
        self.app.update(1 / 60)
        self.app.draw()
        planning = pygame.image.tobytes(self.app.surface.subsurface(pygame.Rect(900, 120, 360, 50)), "RGB")
        self.app.state.choose("storm", "begin")
        self.app.draw()
        night = pygame.image.tobytes(self.app.surface.subsurface(pygame.Rect(900, 120, 360, 50)), "RGB")
        self.assertFalse(planning == night)

    def test_the_second_ending_has_its_own_screen_that_scrolls_in_every_accessibility_mode(self):
        self.start(at_phase("aftermath"))
        self.app.talking_to = "council"
        for task in RECOVER:
            self.app.state.perform(task)
        self.app.action("choice:storm_close")
        self.assertEqual((self.app.mode, self.app.ending_part), ("ending", 2))
        for large in (False, True):
            for contrast in (False, True):
                self.app.settings.update(large_text=large, high_contrast=contrast)
                self.app.apply_settings()
                self.app.scroll = 0
                self.app.draw()
                self.assertGreater(self.app.max_scroll, 0)
                first = pygame.image.tobytes(self.app.surface, "RGB")
                self.app.scroll = self.app.max_scroll
                self.app.draw()
                self.assertFalse(first == pygame.image.tobytes(self.app.surface, "RGB"))
                window = pygame.Rect(0, 0, 1280, 840)
                for rect, _, _ in self.app.ui.buttons:
                    self.assertTrue(window.contains(rect))

    def test_the_first_ending_points_to_part_two_until_it_begins(self):
        self.start(act_one())
        self.app.talking_to = "council"
        self.app.state.flags.discard("balanced")
        self.app.ending_part = 1
        self.app.change_mode("ending")
        self.app.draw()
        invited = pygame.image.tobytes(self.app.surface, "RGB")
        self.app.state.choose("council", "storm_forecast")
        self.app.draw()
        self.assertFalse(invited == pygame.image.tobytes(self.app.surface, "RGB"))

    def test_suggestions_are_shown_through_part_two_and_afterwards(self):
        self.start(at_phase("invited"))
        for phase, expect in (("invited", "forecast"), ("forecast", "Hall"), ("night", "storm"), ("aftermath", "storm"), ("done", "Storm Season is over")):
            self.app.state = at_phase(phase)
            self.app.draw()
            text, target = self.app.step
            self.assertTrue(text, phase)
        self.app.state = at_phase("done")
        self.app.draw()
        self.assertIn("Storm Season", self.app.step[0] + "Storm Season")

    def test_part_two_scenes_render_with_larger_text_and_higher_contrast(self):
        for phase in ("forecast", "night"):
            self.start(at_phase(phase))
            for large in (False, True):
                for contrast in (False, True):
                    self.app.settings.update(large_text=large, high_contrast=contrast)
                    self.app.apply_settings()
                    self.interact("storm")
                    self.assertEqual(self.app.mode, "dialogue")
                    window = pygame.Rect(0, 0, 1280, 840)
                    for rect, _, _ in self.app.ui.buttons:
                        # Choices scrolled out of view are clipped to nothing; every visible one must fit.
                        self.assertTrue(rect.width == 0 or window.contains(rect), (phase, rect))
                    self.app.change_mode("play")


class MapAndJournalTests(AppTestCase):
    def test_the_map_shows_hillside_and_a_marker_click_walks_there(self):
        self.start(everyone())
        self.app.change_mode("map")
        self.app.draw()
        labels = [a for _, a, _ in self.app.ui.buttons]
        for ident in ("kit", "noor", "odile", "quiet_lookout"):
            self.assertIn("travel:" + ident, labels)
        self.assertNotIn("travel:storm", labels, "the storm board is not up yet")
        self.assertTrue(self.app.map_markers)
        center, action = next(m for m in self.app.map_markers if m[1] == "travel:noor")
        self.click(center)
        self.assertEqual(self.app.mode, "play")
        self.assertEqual(self.app.pending_interaction.id, "noor")
        self.assertTrue(self.app.world.path)

    def test_the_map_grows_with_the_story(self):
        self.start(at_phase("invited"))
        self.app.change_mode("map")
        self.app.draw()
        before = len(self.app.ui.buttons)
        self.app.state = at_phase("forecast")
        self.app.draw()
        self.assertEqual(len(self.app.ui.buttons), before + 1)
        self.app.state = at_phase("aftermath")
        self.app.draw()
        self.assertGreaterEqual(len(self.app.ui.buttons), before + 3)
        window = pygame.Rect(0, 0, 1280, 840)
        for rect, _, _ in self.app.ui.buttons:
            self.assertTrue(window.contains(rect))

    def test_clicking_empty_map_does_nothing(self):
        self.start(everyone())
        self.app.change_mode("map")
        self.app.draw()
        self.click((150, 200))
        self.assertEqual(self.app.mode, "map")

    def test_the_journal_has_three_pages_switched_by_click_or_arrow_keys(self):
        self.start(everyone())
        self.app.change_mode("journal")
        self.app.draw()
        self.assertEqual(self.app.journal_tab, "story")
        actions = [a for _, a, _ in self.app.ui.buttons]
        for tab in ("tab:story", "tab:people", "tab:river"):
            self.assertIn(tab, actions)
        rect = next(r for r, a, _ in self.app.ui.buttons if a == "tab:people")
        self.click(rect.center)
        self.assertEqual(self.app.journal_tab, "people")
        self.key(pygame.K_RIGHT)
        self.assertEqual(self.app.journal_tab, "river")
        self.key(pygame.K_RIGHT)
        self.assertEqual(self.app.journal_tab, "story")
        self.key(pygame.K_LEFT)
        self.assertEqual(self.app.journal_tab, "river")

    def test_every_journal_page_renders_with_larger_text_and_higher_contrast(self):
        for state in (GameState(), everyone(), at_phase("aftermath")):
            self.start(state)
            self.app.change_mode("journal")
            for tab in ("story", "people", "river"):
                for large in (False, True):
                    for contrast in (False, True):
                        self.app.settings.update(large_text=large, high_contrast=contrast)
                        self.app.apply_settings()
                        self.app.journal_tab = tab
                        self.app.scroll = 0
                        self.app.draw()
                        pygame.image.tobytes(self.app.surface, "RGB")
                        self.app.scroll = self.app.max_scroll
                        self.app.draw()
                        window = pygame.Rect(0, 0, 1280, 840)
                        for rect, _, _ in self.app.ui.buttons:
                            self.assertTrue(window.contains(rect))

    def test_the_river_page_explains_itself_until_kit_is_met_and_then_shows_readings(self):
        self.start(GameState())
        self.app.change_mode("journal")
        self.app.journal_tab = "river"
        self.app.draw()
        before = pygame.image.tobytes(self.app.surface, "RGB")
        self.app.state.choose("kit", "kit_1:read")
        self.app.state.perform("sample_out")
        self.app.draw()
        self.assertFalse(before == pygame.image.tobytes(self.app.surface, "RGB"))

    def test_the_neighbours_page_changes_as_friendships_grow(self):
        self.start(GameState())
        self.app.change_mode("journal")
        self.app.journal_tab = "people"
        self.app.draw()
        before = pygame.image.tobytes(self.app.surface, "RGB")
        self.app.state.choose("kit", "kit_1:read")
        self.app.draw()
        self.assertFalse(before == pygame.image.tobytes(self.app.surface, "RGB"))

    def test_a_first_visit_to_hillside_gets_a_gentle_note_once(self):
        self.start(GameState())
        self.app.settings.update(tip_move=True, tip_talk=True, tip_journal=True)
        self.app.world.player.update(1300, 420)
        self.app.toast_time = 0
        self.app.update(1 / 60)
        self.assertIn("Hillside", self.app.toast)
        self.assertTrue(self.app.settings["tip_hillside"])
        self.app.toast = ""
        self.app.toast_time = 0
        self.app.world.player.update(480, 500)
        self.app.update(1 / 60)
        self.app.world.player.update(1300, 420)
        self.app.update(1 / 60)
        self.assertEqual(self.app.toast, "", "shown only once")


class SavePositionTests(AppTestCase):
    def test_a_journey_saved_on_hillside_continues_there(self):
        state = everyone()
        save_game(self.app.slot, state, (1600, 420))
        loaded, position = load_game(self.app.slot)
        self.assertEqual(position, [1600, 420])
        self.app.action("continue")
        self.assertEqual(tuple(self.app.world.player), (1600, 420))
        self.assertTrue(self.app.world.walkable(self.app.world.player))

    def test_a_position_outside_the_village_is_still_refused(self):
        save_game(self.app.slot, GameState(), (WIDTH + 40, 420))
        with self.assertRaises(ValueError):
            load_game(self.app.slot)
        save_game(self.app.slot, GameState(), (WIDTH - 32, 420))
        load_game(self.app.slot)

    def test_a_blocked_hillside_position_moves_to_the_safe_spawn(self):
        save_game(self.app.slot, GameState(), (1450, 300))
        self.assertFalse(self.app.world.walkable((1450, 300)))
        self.app.action("continue")
        self.assertEqual(tuple(self.app.world.player), (480, 500))

    def test_every_part_two_stage_saves_and_continues(self):
        for phase in ("invited", "forecast", "night", "aftermath", "done"):
            state = at_phase(phase)
            save_game(self.app.slot, state, (480, 500))
            self.app.action("continue")
            self.assertEqual(self.app.state.to_dict(), state.to_dict(), phase)
            self.assertEqual(self.app.state.storm_phase(), phase)
            self.app.change_mode("title")


class RainSoundTests(unittest.TestCase):
    def setUp(self):
        pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.init()
        self.audio = Audio(bgm_file=None)
        if not self.audio.available:
            self.skipTest("no audio device in this environment")
        self.addCleanup(self.audio.close)

    def test_rain_follows_the_weather_and_has_its_own_channel(self):
        self.assertIn("rain", self.audio.channels)
        levels = {w: self.audio.levels(.5, weather=w) for w in ("clear", "overcast", "storm", "aftermath")}
        self.assertEqual(levels["clear"]["rain"], 0)
        self.assertGreater(levels["overcast"]["rain"], 0)
        self.assertGreater(levels["storm"]["rain"], levels["overcast"]["rain"])
        self.assertGreater(levels["aftermath"]["rain"], 0)
        self.assertLess(levels["aftermath"]["rain"], levels["storm"]["rain"])

    def test_the_storm_silences_the_birds_and_raises_the_wind(self):
        self.audio.mix = .8
        calm, storm = self.audio.levels(.8, zones={"trees": 1}), self.audio.levels(.8, zones={"trees": 1}, weather="storm")
        self.assertGreater(calm["birds"], 0)
        self.assertEqual(storm["birds"], 0)
        self.assertGreater(storm["wind"], calm["wind"])

    def test_every_level_stays_in_range_in_every_weather_and_muting_silences_the_rain(self):
        for weather in ("clear", "overcast", "storm", "aftermath"):
            self.audio.set_muted(False)
            self.audio.update(.1, 1.0, tension=1, zones={"mill": 1, "river": 1, "trees": 1}, weather=weather)
            for channel in self.audio.channels.values():
                self.assertTrue(0 <= channel.get_volume() <= 1, weather)
        self.audio.set_muted(True)
        self.audio.update(.1, 1.0, weather="storm")
        self.assertEqual(self.audio.channels["rain"].get_volume(), 0)

    def test_the_music_sits_back_in_the_storm(self):
        track = Path(__file__).resolve().parents[1] / "assets" / "music"
        audio = Audio()
        if not audio.bgm_active:
            audio.close()
            self.skipTest("no background track is installed")
        self.addCleanup(audio.close)
        self.assertLess(audio.levels(.5, weather="storm")["bgm"], audio.levels(.5)["bgm"])


if __name__ == "__main__":
    unittest.main()
