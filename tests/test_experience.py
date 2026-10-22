"""Headless checks for guidance, controls, the living world, sound and every new screen."""

import json
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
from game.audio import BGM_VOLUME, Audio, find_bgm, prepare_loop
from game.state import GameState
from game.storage import load_game, load_settings, save_game
from game.world import World


LITTER = [f"litter_{i}" for i in range(1, 7)]
CRATES = [f"crate_{i}" for i in range(1, 4)]


def finished_state():
    state = GameState()
    for action in (*LITTER, *CRATES, "pump", "garden_1", "garden_2", "garden_3", "quiet"):
        state.perform(action)
    for person in ("mira", "rowan", "amani"):
        state.choose(person, "listen")
    state.choose("theo", "workshop")
    state.choose("council", "needs")
    return state


def story_state(supported):
    """Every optional place is visible; residents are at home or, once supported, at their posts."""
    state = GameState()
    for action in (*LITTER, *CRATES, "garden_1", "garden_2", "garden_3", "pump", "quiet"):
        state.perform(action)
    state.choose("council", "needs")
    if supported:
        for person in ("mira", "rowan", "amani"):
            state.choose(person, "listen")
        state.choose("theo", "reserve")
    return state


APPROACHES = (("front", (0, 29)), ("left", (-30, 8)), ("right", (30, 8)), ("back", (0, -25)))


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="common-ground-test-")
        self.folder = Path(self.temp.name)
        self.app = App(save_dir=self.folder, window=False, audio=False)

    def tearDown(self):
        self.app.close()
        self.temp.cleanup()

    def start(self):
        self.app.new_game()
        self.app.draw()
        self.app.action("begin")
        self.app.draw()

    def pad(self, button):
        self.app.handle(pygame.event.Event(pygame.JOYBUTTONDOWN, button=button, instance_id=0, joy=0))
        self.app.draw()


class GamepadTests(AppTestCase):
    def test_buttons_move_through_the_whole_interface(self):
        self.app.new_game()
        self.app.draw()
        self.assertEqual(self.app.mode, "intro")
        self.pad(0)
        self.assertEqual(self.app.mode, "play")
        self.pad(2)
        self.assertEqual(self.app.mode, "journal")
        self.pad(2)
        self.assertEqual(self.app.mode, "play")
        self.pad(3)
        self.assertEqual(self.app.mode, "map")
        self.pad(1)
        self.assertEqual(self.app.mode, "play")
        self.pad(7)
        self.assertEqual(self.app.mode, "pause")
        self.pad(1)
        self.assertEqual(self.app.mode, "play")

    def test_a_button_talks_to_the_person_beside_you(self):
        self.start()
        mira = next(p for p in self.app.world.places if p.id == "mira")
        self.app.world.player.update(mira.x, mira.y + 29)
        self.app.update(1 / 60)
        self.pad(0)
        self.assertEqual(self.app.mode, "dialogue")
        self.assertEqual(self.app.talking_to, "mira")

    def test_the_d_pad_changes_the_focused_menu_item(self):
        self.start()
        self.app.action("open_pause")
        self.app.draw()
        start = self.app.ui.focus
        self.app.handle(pygame.event.Event(pygame.JOYHATMOTION, value=(0, -1), hat=0, joy=0, instance_id=0))
        self.app.draw()
        self.assertEqual(self.app.ui.focus, start + 1)
        self.app.handle(pygame.event.Event(pygame.JOYHATMOTION, value=(0, 1), hat=0, joy=0, instance_id=0))
        self.assertEqual(self.app.ui.focus, start)

    def test_stick_movement_has_a_dead_zone_and_moves_the_player(self):
        class Pad:
            def __init__(self, x, y, hat=(0, 0)):
                self.x, self.y, self.hat = x, y, hat

            def get_axis(self, axis):
                return (self.x, self.y)[axis]

            def get_numhats(self):
                return 1

            def get_hat(self, index):
                return self.hat

        self.app.pads = {0: Pad(.2, -.1)}
        self.assertEqual(tuple(self.app.read_pad()), (0, 0), "a resting stick must not drift")
        self.app.pads = {0: Pad(1, 0)}
        self.assertAlmostEqual(self.app.read_pad().length(), 1)
        self.app.pads = {0: Pad(0, 0, (0, 1))}
        self.assertLess(self.app.read_pad().y, 0, "d-pad up moves up the screen")
        self.start()
        self.app.pads = {0: Pad(1, 0)}
        before = self.app.world.player.x
        for _ in range(10):
            self.app.update(1 / 60)
        self.assertGreater(self.app.world.player.x, before)
        self.assertEqual(self.app.world.facing, "right")

    def test_a_broken_gamepad_is_ignored(self):
        class Broken:
            def get_axis(self, axis):
                raise pygame.error("unplugged")

            def get_numhats(self):
                return 0

        self.app.pads = {0: Broken()}
        self.assertEqual(tuple(self.app.read_pad()), (0, 0))
        self.assertEqual(self.app.pads, {})


class GuidanceAndSettingsTests(AppTestCase):
    def test_show_the_way_is_on_by_default_and_can_be_turned_off(self):
        self.assertTrue(self.app.settings["show_way"])
        self.start()
        self.app.update(1 / 60)
        marker = self.app.world.hint_place(self.app.state.next_step()[1], self.app.state)
        self.assertEqual(marker.id, "mira")
        self.app.action("setting:show_way")
        self.assertFalse(load_settings(self.folder / "settings.json")["show_way"])
        self.app.draw()

    def test_first_time_prompts_appear_once_and_are_remembered(self):
        self.app.new_game()
        self.app.action("begin")
        self.assertIn("Move with", self.app.toast)
        self.assertTrue(self.app.settings["tip_move"])
        mira = next(p for p in self.app.world.places if p.id == "mira")
        self.app.world.player.update(mira.x, mira.y + 29)
        self.app.toast_time = 0
        self.app.update(1 / 60)
        self.assertIn("Press E", self.app.toast)
        self.assertTrue(self.app.settings["tip_talk"])
        self.app.toast = ""
        self.app.toast_time = 0
        self.app.update(1 / 60)
        self.assertEqual(self.app.toast, "", "a prompt is not repeated")
        self.app.result = self.app.state.perform("litter_1")
        self.app.change_mode("result")
        self.app.action("dismiss")
        self.assertIn("journal", self.app.toast.lower())
        self.assertTrue(self.app.settings["tip_journal"])
        saved = load_settings(self.folder / "settings.json")
        self.assertTrue(saved["tip_move"] and saved["tip_talk"] and saved["tip_journal"])
        self.app.close()
        self.app = App(save_dir=self.folder, window=False, audio=False)
        self.assertTrue(self.app.settings["tip_move"])

    def test_settings_screen_fits_every_option(self):
        self.app.action("settings")
        self.app.draw()
        actions = [a for _, a, _ in self.app.ui.buttons]
        for key in ("muted", "large_text", "reduced_motion", "high_contrast", "slow_walk", "show_way"):
            self.assertIn("setting:" + key, actions)
        for rect, _, _ in self.app.ui.buttons:
            self.assertTrue(pygame.Rect(0, 0, 1280, 840).contains(rect))

    def test_the_hint_box_grows_with_long_suggestions(self):
        self.start()
        self.app.state.choose("mira", "listen")
        self.app.state.perform("pump")
        self.app.update(1 / 60)
        text, _ = self.app.state.next_step()
        self.assertTrue(text)
        self.app.draw()


class CustomArtTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((64, 64), pygame.HIDDEN)
        self.temp = tempfile.TemporaryDirectory(prefix="common-ground-art-")
        self.folder = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_hand_made_pngs_replace_the_drawn_art(self):
        surface = pygame.Surface((10, 12), pygame.SRCALPHA)
        surface.fill((255, 0, 0, 255))
        pygame.image.save(surface, str(self.folder / "tree_restored.png"))
        art = Art(custom_dir=self.folder)
        self.assertEqual(art.sprite("tree", True).get_size(), (10, 12))
        self.assertEqual(art.sprite("tree", False).get_size(), Art().sprite("tree", False).get_size())

    def test_tiles_are_scaled_to_fit_and_people_frames_can_be_replaced(self):
        pygame.image.save(pygame.Surface((8, 8)), str(self.folder / "tile_grass_polluted.png"))
        frame = pygame.Surface((24, 36), pygame.SRCALPHA)
        frame.fill((0, 255, 0, 255))
        pygame.image.save(frame, str(self.folder / "player_left_1_polluted.png"))
        art = Art(custom_dir=self.folder)
        self.assertEqual(art.tile("grass", False).get_size(), (32, 32))
        self.assertEqual(art.person("player", "left", 1).get_at((5, 5))[:3], (0, 255, 0))
        self.assertNotEqual(art.person("player", "left", 2).get_at((5, 5))[:3], (0, 255, 0))

    def test_unreadable_files_fall_back_to_the_drawn_art(self):
        (self.folder / "house_polluted.png").write_bytes(b"not a png")
        art = Art(custom_dir=self.folder)
        self.assertEqual(art.sprite("house", False).get_size(), (128, 112))

    def test_a_missing_folder_is_fine(self):
        art = Art(custom_dir=self.folder / "nowhere")
        self.assertEqual(art.sprite("pump").get_size(), Art().sprite("pump").get_size())

    def test_people_have_every_pose_and_supported_residents_look_different(self):
        art = Art()
        for name in art.PEOPLE:
            for facing in art.FACINGS:
                for step in (0, 1, 2):
                    self.assertEqual(art.person(name, facing, step).get_size(), (24, 36))
        steps = {pygame.image.tobytes(art.person("player", "down", step), "RGBA") for step in (0, 1, 2)}
        self.assertEqual(len(steps), 3, "walking frames differ")
        for name in ("mira", "rowan", "amani", "theo"):
            self.assertNotEqual(pygame.image.tobytes(art.person(name, supported=False), "RGBA"),
                                pygame.image.tobytes(art.person(name, supported=True), "RGBA"))

    def test_every_listed_sprite_exists_in_both_palettes(self):
        art = Art()
        for name in art.NAMES:
            for restored in (False, True):
                self.assertGreater(art.sprite(name, restored).get_width(), 0, name)


class LivingWorldTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((64, 64), pygame.HIDDEN)
        self.world = World(Art())
        self.keys = pygame.key.get_pressed()

    def place(self, ident):
        return next(p for p in self.world.places if p.id == ident)

    def test_places_appear_when_the_story_reaches_them(self):
        state = GameState()
        self.assertTrue(self.world.hidden(self.place("dispute"), state))
        self.assertTrue(self.world.hidden(self.place("plots"), state))
        state = finished_state()
        self.assertFalse(self.world.hidden(self.place("dispute"), state))
        self.assertFalse(self.world.hidden(self.place("plots"), state))

    def test_supported_residents_walk_to_the_places_they_care_about(self):
        state = GameState()
        self.world.update(1 / 60, self.keys, state)
        home = (self.place("rowan").x, self.place("rowan").y)
        state.choose("rowan", "listen")
        self.world.update(1 / 60, self.keys, state)
        moved = (self.place("rowan").x, self.place("rowan").y)
        self.assertNotEqual(moved, (748, 648), "residents walk rather than jump")
        for _ in range(600):
            self.world.update(1 / 30, self.keys, state)
        self.assertEqual((self.place("rowan").x, self.place("rowan").y), (748, 648))
        self.assertNotEqual(home, (748, 648))
        # Loading a different journey puts everyone back where that story has them.
        self.world.update(1 / 30, self.keys, GameState())
        self.assertEqual((self.place("rowan").x, self.place("rowan").y), home)

    def test_reduced_motion_places_helpers_immediately(self):
        state = GameState()
        state.choose("amani", "listen")
        self.world.update(1 / 60, self.keys, state, reduce_motion=True)
        self.assertEqual((self.place("amani").x, self.place("amani").y), (955, 410))

    def test_every_post_and_new_place_can_be_reached_on_foot(self):
        for ident in ("dispute", "plots", "quiet_river", "quiet_garden", "council"):
            place = self.place(ident)
            self.world.player.update(480, 500)
            self.assertTrue(self.world.walk_to((place.x, place.y + 29)) or self.world.walk_to((place.x - 30, place.y + 8)), ident)
        for ident, post in (("rowan", (748, 648)), ("theo", (702, 286)), ("amani", (955, 410))):
            self.world.player.update(480, 500)
            self.assertTrue(any(self.world.walk_to((post[0] + dx, post[1] + dy)) for _, (dx, dy) in APPROACHES), ident)

    def test_standing_at_something_selects_it_whether_residents_are_at_home_or_at_their_posts(self):
        """Pressing E or A must act on the thing you are standing at, not on a neighbour who moved nearby."""
        for supported in (False, True):
            state = story_state(supported)
            world = World(Art())
            for _ in range(900):
                world.update(1 / 30, self.keys, state)
            for place in world.places:
                if world.hidden(place, state):
                    continue
                tested = []
                for label, (dx, dy) in APPROACHES:
                    if place.id.startswith("garden_") and label in ("left", "right"):
                        continue  # neighbouring beds are only 50 pixels apart and share their sides
                    spot = (place.x + dx, place.y + dy)
                    if not world.walkable(spot):
                        continue
                    world.player.update(spot)
                    world.update(1 / 60, self.keys, state)
                    tested.append(label)
                    self.assertIsNotNone(world.nearest, (place.id, label))
                    self.assertEqual(world.nearest.id, place.id, f"{place.id} ({label}), residents {'at posts' if supported else 'at home'}")
                self.assertTrue(tested, f"{place.id} has no walkable approach")

    def test_captions_describe_what_the_player_is_near_and_follow_the_story(self):
        state = GameState()
        self.world.player.update(830, 330)
        before = self.world.cue_caption(state)
        self.assertIn("film", before)
        state.flags.add("source_repaired")
        self.assertNotEqual(self.world.cue_caption(state), before)
        self.world.player.update(480, 620)
        self.assertIsNone(self.world.cue_caption(state))
        self.world.player.update(420, 508)
        self.assertIn("queue", self.world.cue_caption(GameState()))
        self.assertIsNone(self.world.cue_caption(finished_state()), "the queue rope is gone once the circle moved on")

    def test_hint_places_resolve_to_visible_places(self):
        state = GameState()
        self.assertEqual(self.world.hint_place("mira", state).id, "mira")
        self.assertIsNone(self.world.hint_place(None, state))
        self.world.player.update(360, 360)
        self.assertEqual(self.world.hint_place("collect", state).id, "litter_1")
        for action in (*LITTER, *CRATES):
            state.perform(action)
        self.assertIsNone(self.world.hint_place("collect", state))
        self.assertEqual(self.world.hint_place("garden", state).id, "garden_1")
        self.assertIsNone(self.world.hint_place("dispute", state), "hidden places cannot be suggested")

    def test_audio_zones_follow_the_player(self):
        self.world.player.update(665, 200)
        near = self.world.audio_zones()
        self.world.player.update(150, 700)
        far = self.world.audio_zones()
        self.assertGreater(near["mill"], far["mill"])
        self.world.player.update(840, 460)
        self.assertGreater(self.world.audio_zones()["river"], far["river"])
        for value in near.values():
            self.assertTrue(0 <= value <= 1)

    def test_player_faces_the_way_they_walk_and_cycles_through_walking_frames(self):
        state = GameState()
        for vector, facing in (((1, 0), "right"), ((-1, 0), "left"), ((0, 1), "down"), ((0, -1), "up")):
            self.world.move(vector, 1 / 30)
            self.assertEqual(self.world.facing, facing)
        stride = self.world.stride
        self.world.move((0, 1), 1 / 30)
        self.assertGreater(self.world.stride, stride)
        self.world.move((0, 0), 1 / 30)
        self.assertFalse(self.world.walking)

    def test_every_state_draws_in_both_motion_modes(self):
        screen = pygame.Surface((1280, 840))
        states = [GameState(), finished_state()]
        extreme = GameState()
        extreme.metrics = {key: 0 for key in extreme.metrics}
        states.append(extreme)
        thriving = GameState()
        thriving.metrics = {key: 100 for key in thriving.metrics}
        states.append(thriving)
        restart = GameState()
        restart.perform("litter_1")
        restart.choose("theo", "restart")
        states.append(restart)
        for state in states:
            for reduced in (False, True):
                for contrast in (False, True):
                    self.world.draw(screen, state, 12.3, reduced, contrast, (5, 3), self.place("mira"))

    def test_the_off_screen_marker_points_towards_a_distant_place(self):
        screen = pygame.Surface((1280, 840))
        self.world.player.update(150, 700)
        self.world.update(1 / 60, self.keys, GameState())
        self.world.draw(screen, GameState(), 0, False, False, (0, 0), self.place("amani"))

    def test_the_water_film_clears_gradually_once_the_source_is_repaired(self):
        state = GameState()
        self.world.update(1 / 60, self.keys, state)
        self.assertEqual(self.world.plume, 1.0)
        state.flags.add("source_repaired")
        self.world.update(1 / 4, self.keys, state)
        self.assertTrue(0 < self.world.plume < 1)
        for _ in range(300):
            self.world.update(1 / 20, self.keys, state)
        self.assertLess(self.world.plume, .02)
        self.world.update(1 / 60, self.keys, state, reduce_motion=True)
        self.assertEqual(self.world.plume, 0)


class SoundTests(unittest.TestCase):
    def setUp(self):
        pygame.mixer.pre_init(22050, -16, 2, 512)
        pygame.init()
        self.audio = Audio(bgm_file=None)
        if not self.audio.available:
            self.skipTest("no audio device in this environment")

    def tearDown(self):
        self.audio.close()

    def test_machinery_is_heard_near_the_mill_and_softens_once_it_is_a_workshop(self):
        near = self.audio.levels(.5, zones={"mill": 1})
        far = self.audio.levels(.5, zones={"mill": 0})
        shared = self.audio.levels(.5, zones={"mill": 1}, mill_shared=True)
        self.assertGreater(near["machinery"], far["machinery"])
        self.assertEqual(far["machinery"], 0)
        self.assertLess(shared["machinery"], near["machinery"])

    def test_the_river_sounds_clearer_after_the_repair(self):
        zones = {"river": 1}
        self.audio.river_clear = 0
        before = self.audio.levels(.5, zones=zones)
        self.audio.river_clear = 1
        after = self.audio.levels(.5, zones=zones)
        self.assertGreater(before["river_murky"], before["river_clear"])
        self.assertGreater(after["river_clear"], after["river_murky"])

    def test_tension_builds_a_drone_and_a_supportive_choice_settles_it_into_harmony(self):
        calm = self.audio.levels(.5)
        self.audio.tension = 1
        tense = self.audio.levels(.5)
        self.assertEqual(calm["drone"], 0)
        self.assertGreater(tense["drone"], 0)
        harmony = self.audio.levels(.5)["harmony"]
        self.audio.resolve()
        self.assertGreater(self.audio.levels(.5)["harmony"], harmony)
        for _ in range(400):
            self.audio.update(1 / 20, .5)
        self.assertEqual(self.audio.settle, 0)

    def test_the_melody_unlocks_as_balance_rises(self):
        low = self.audio.levels(.3)["melody"]
        high = self.audio.levels(.95)["melody"]
        self.assertEqual(low, 0)
        self.assertGreater(high, 0)

    def test_quiet_places_raise_the_ambience_and_soften_the_music(self):
        self.audio.mix = .5
        normal = self.audio.levels(.8, zones={"river": 1, "trees": 1})
        quiet = self.audio.levels(.8, quiet=True, zones={"river": 1, "trees": 1})
        self.assertGreater(quiet["wind"], normal["wind"])
        self.assertGreater(quiet["birds"], normal["birds"])
        self.assertLess(quiet["harmony"], normal["harmony"])
        self.assertLess(quiet["melody"], normal["melody"])

    def test_muting_silences_every_layer_and_all_levels_stay_in_range(self):
        self.audio.set_muted(True)
        self.audio.update(.1, 1.0, tension=1, zones={"mill": 1, "river": 1, "trees": 1})
        for channel in self.audio.channels.values():
            self.assertEqual(channel.get_volume(), 0)
        self.audio.set_muted(False)
        self.audio.update(.1, 1.0, tension=1, zones={"mill": 1, "river": 1, "trees": 1})
        for channel in self.audio.channels.values():
            self.assertTrue(0 <= channel.get_volume() <= 1)


class BackgroundMusicTests(unittest.TestCase):
    def setUp(self):
        pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.init()
        self.temp = tempfile.TemporaryDirectory(prefix="common-ground-music-")
        self.folder = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def pcm(frames, channels=2, tail_silence=0, amplitude=12000):
        from array import array
        samples = array("h")
        for i in range(frames):
            value = int(amplitude * (1 if (i // 40) % 2 else -1))
            samples.extend([value] * channels)
        samples.extend([0] * (tail_silence * channels))
        return samples.tobytes()

    def test_a_long_silent_tail_is_trimmed_and_the_edges_are_softened(self):
        from array import array
        raw = self.pcm(44100, tail_silence=88200)
        out = array("h")
        out.frombytes(prepare_loop(raw, 2, 44100))
        frames = len(out) // 2
        self.assertEqual(len(out) % 2, 0)
        self.assertLess(frames, 44100 + 44100 // 10, "two seconds of silence are removed")
        self.assertGreaterEqual(frames, 44100)
        self.assertEqual(tuple(out[:2]), (0, 0), "the loop starts from silence, so it cannot click")
        self.assertEqual(tuple(out[-2:]), (0, 0), "and ends at silence")
        self.assertLess(abs(out[2]), abs(out[2000]), "the start fades in")

    def test_the_music_itself_is_left_untouched_by_trimming(self):
        raw = self.pcm(44100, tail_silence=1000)
        original = bytes(raw)
        prepare_loop(raw, 2, 44100)
        self.assertEqual(raw, original)

    def test_a_track_with_no_silence_keeps_its_length_and_a_silent_track_is_returned_unchanged(self):
        from array import array
        out = array("h")
        out.frombytes(prepare_loop(self.pcm(44100), 2, 44100))
        self.assertEqual(len(out) // 2, 44100)
        silent = bytes(4000)
        self.assertEqual(prepare_loop(silent, 2, 44100), silent)

    def test_mono_tracks_and_odd_byte_counts_are_handled(self):
        from array import array
        mono = self.pcm(5000, channels=1, tail_silence=5000)
        out = array("h")
        out.frombytes(prepare_loop(mono + b"", 1, 44100))
        self.assertTrue(0 < len(out) < 10000)

    def test_the_first_music_file_by_name_is_used_and_other_files_are_ignored(self):
        self.assertIsNone(find_bgm(self.folder))
        self.assertIsNone(find_bgm(self.folder / "missing"))
        (self.folder / "notes.txt").write_text("not music")
        (self.folder / "b.ogg").write_bytes(b"x")
        (self.folder / "A.MP3").write_bytes(b"x")
        self.assertEqual(find_bgm(self.folder).name, "A.MP3")

    def test_the_supplied_track_is_in_the_project(self):
        track = find_bgm()
        self.assertIsNotNone(track, "assets/music should hold the background track")
        self.assertGreater(track.stat().st_size, 100_000)

    def test_the_supplied_track_plays_on_a_loop_without_a_gap_and_carries_the_music(self):
        audio = Audio()
        if not audio.available:
            self.skipTest("no audio device in this environment")
        self.addCleanup(audio.close)
        self.assertTrue(audio.bgm_active)
        self.assertIn("bgm", audio.channels)
        self.assertTrue(audio.channels["bgm"].get_busy())
        original = pygame.mixer.Sound(str(find_bgm())).get_length()
        self.assertLess(audio.sounds["bgm"].get_length(), original - 2, "the silent tail is gone")
        levels = audio.levels(.5)
        self.assertEqual((levels["harmony"], levels["drone"], levels["melody"]), (0, 0, 0), "generated music steps aside")
        self.assertAlmostEqual(levels["bgm"], BGM_VOLUME)
        self.assertGreater(levels["wind"], 0, "the ambience stays")

    def test_the_music_ducks_in_tense_moments_swells_after_a_supportive_choice_and_softens_in_quiet_places(self):
        audio = Audio()
        if not audio.available:
            self.skipTest("no audio device in this environment")
        self.addCleanup(audio.close)
        calm = audio.levels(.5)["bgm"]
        audio.tension = 1
        tense = audio.levels(.5)["bgm"]
        self.assertLess(tense, calm)
        self.assertGreater(tense, calm * .5, "ducking never silences the music")
        audio.resolve()
        self.assertGreater(audio.levels(.5)["bgm"], tense)
        audio.tension = 0
        audio.settle = 0
        self.assertLess(audio.levels(.5, quiet=True)["bgm"], calm)

    def test_music_volume_stays_in_range_and_muting_silences_it(self):
        audio = Audio()
        if not audio.available:
            self.skipTest("no audio device in this environment")
        self.addCleanup(audio.close)
        audio.set_muted(True)
        audio.update(.1, 1.0, tension=1, zones={"mill": 1, "river": 1, "trees": 1})
        self.assertEqual(audio.channels["bgm"].get_volume(), 0)
        audio.set_muted(False)
        audio.resolve()
        audio.update(.1, 1.0)
        self.assertTrue(0 < audio.channels["bgm"].get_volume() <= 1)

    def test_a_missing_or_unreadable_track_falls_back_to_the_generated_music(self):
        for path in (None, self.folder / "nowhere.mp3"):
            audio = Audio(bgm_file=path)
            if not audio.available:
                self.skipTest("no audio device in this environment")
            self.addCleanup(audio.close)
            self.assertFalse(audio.bgm_active)
            self.assertNotIn("bgm", audio.channels)
            levels = audio.levels(.95)
            self.assertGreater(levels["harmony"], 0)
            self.assertGreater(levels["melody"], 0)
            self.assertEqual(levels["bgm"], 0)
        broken = self.folder / "broken.mp3"
        broken.write_bytes(b"this is not an mp3 file at all" * 50)
        audio = Audio(bgm_file=broken)
        self.addCleanup(audio.close)
        self.assertFalse(audio.bgm_active)
        self.assertGreater(audio.levels(.5)["harmony"], 0)
        audio.update(.1, .5)


class ScreenTests(AppTestCase):
    """Every screen renders inside the window with every accessibility setting on or off."""

    def each_setting(self):
        for large in (False, True):
            for contrast in (False, True):
                self.app.settings.update(large_text=large, high_contrast=contrast)
                self.app.apply_settings()
                yield large, contrast

    def screen_ok(self):
        self.app.draw()
        window = pygame.Rect(0, 0, 1280, 840)
        for rect, _, _ in self.app.ui.buttons:
            self.assertTrue(window.contains(rect), (self.app.mode, rect))

    def play_through(self):
        self.start()
        self.app.state = finished_state()
        self.app.state.choose("dispute", "blame")
        self.app.state.choose("dispute", "acknowledge")
        self.app.state.choose("plots", "helpers")
        self.app.state.choose("plots", "review")
        for person in ("rowan", "mira", "amani", "theo"):
            while self.app.state.available_beat(person):
                beat = self.app.state.available_beat(person)
                self.app.state.choose(person, f"{beat.id}:{beat.options[0].id}")

    def test_every_conversation_renders_and_every_choice_is_clickable(self):
        self.play_through()
        for large, contrast in self.each_setting():
            for ident in ("mira", "rowan", "amani", "theo", "council", "dispute", "plots"):
                place = next(p for p in self.app.world.places if p.id == ident)
                self.app.interact(place)
                self.screen_ok()
                self.assertTrue(self.app.conversation.choices)
                self.app.change_mode("play")

    def test_outcome_panels_render_for_every_decision(self):
        self.start()
        for choice in ("needs", "equal", "queue"):
            state = GameState()
            for action in (*LITTER, *CRATES):
                state.perform(action)
            self.app.state = state
            self.app.talking_to = "council"
            self.app.action("choice:" + choice)
            self.assertEqual(len(self.app.result.outcome), 4)
            for large, contrast in self.each_setting():
                self.screen_ok()
            self.app.change_mode("play")

    def test_the_ending_scrolls_to_show_the_whole_recap(self):
        self.play_through()
        self.app.talking_to = "council"
        self.app.action("choice:finish")
        self.assertEqual(self.app.mode, "ending")
        for large, contrast in self.each_setting():
            self.app.scroll = 0
            self.screen_ok()
            self.assertGreater(self.app.max_scroll, 0)
            self.app.scroll = self.app.max_scroll
            self.screen_ok()
            self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_PAGEUP))
            self.assertLess(self.app.scroll, self.app.max_scroll)

    def test_the_map_lists_only_places_that_exist_yet_and_travel_works(self):
        self.start()
        self.app.change_mode("map")
        self.screen_ok()
        before = len(self.app.ui.buttons)
        self.play_through()
        self.app.change_mode("map")
        self.screen_ok()
        self.assertGreater(len(self.app.ui.buttons), before)
        self.app.action("travel:plots")
        self.assertEqual(self.app.mode, "play")
        self.assertEqual(self.app.pending_interaction.id, "plots")
        self.assertTrue(self.app.world.path)

    def test_each_quiet_place_has_its_own_prompt_and_reflection(self):
        self.start()
        for ident in ("quiet", "quiet_river", "quiet_garden"):
            place = next(p for p in self.app.world.places if p.id == ident)
            self.app.interact(place)
            self.assertEqual(self.app.mode, "quiet")
            self.app.quiet_time = 5
            for large, contrast in self.each_setting():
                self.screen_ok()
            self.app.action("quiet_reflect")
            self.assertTrue(self.app.result.ok)
            self.assertIn(ident, self.app.state.completed)
            self.app.change_mode("play")
        self.assertEqual(self.app.state.metrics["resilience"], 40, "only the willow refuge adds resilience")

    def test_reduced_motion_makes_the_quiet_interface_settle_at_once(self):
        self.start()
        self.app.settings["reduced_motion"] = True
        place = next(p for p in self.app.world.places if p.id == "quiet")
        self.app.interact(place)
        self.app.draw()
        reduced = pygame.image.tobytes(self.app.surface, "RGB")
        self.app.quiet_time = 100
        self.app.draw()
        self.assertEqual(pygame.image.tobytes(self.app.surface, "RGB"), reduced)

    def test_hud_hover_shows_exact_values_and_goals(self):
        self.start()
        self.app.ui.mouse = (520, 40)
        self.app.draw()
        plain = pygame.image.tobytes(self.app.surface, "RGB")
        self.app.ui.mouse = (-1, -1)
        self.app.draw()
        self.assertNotEqual(pygame.image.tobytes(self.app.surface, "RGB"), plain)

    def test_the_living_symbols_draw_at_every_value(self):
        surface = pygame.Surface((200, 120))
        for kind in ("environment", "equity", "resilience"):
            drawn = set()
            for value in range(0, 101, 10):
                surface.fill((247, 243, 228))
                self.app.ui.surface = surface
                self.app.ui.vital(kind, (100, 60), value, (60, 110, 80))
                drawn.add(pygame.image.tobytes(surface, "RGB"))
            self.app.ui.surface = self.app.surface
            self.assertGreater(len(drawn), 3, f"{kind} should change as the value changes")

    def test_the_marker_is_drawn_only_while_exploring(self):
        self.start()
        self.app.draw()
        self.app.settings["show_way"] = False
        shown = pygame.image.tobytes(self.app.surface, "RGB")
        self.app.draw()
        self.assertNotEqual(pygame.image.tobytes(self.app.surface, "RGB"), shown)


class SaveCompatibilityTests(AppTestCase):
    def test_a_saved_version_one_journey_continues_and_is_saved_as_version_two(self):
        state = finished_state()
        state.play_seconds = 400
        data = state.to_dict()
        data["version"] = 1
        del data["planted_at"]
        path = self.folder / "save.json"
        path.write_text(json.dumps({"format": 1, "state": data, "position": [480, 500]}), encoding="utf-8")
        self.app.check_save()
        self.assertTrue(self.app.save_valid)
        self.app.action("continue")
        self.assertEqual(self.app.mode, "play")
        self.assertEqual(self.app.state.completed, state.completed)
        self.assertTrue(all(self.app.state.garden_stage(f"garden_{i}") == 3 for i in range(1, 4)))
        self.app.action("save")
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["state"]["version"], 2)
        self.assertEqual(set(saved["state"]["planted_at"]), {"garden_1", "garden_2", "garden_3"})
        reloaded, _ = load_game(path)
        self.assertEqual(reloaded.to_dict(), self.app.state.to_dict())

    def test_garden_growth_survives_a_save_and_continue(self):
        state = GameState()
        for action in (*LITTER, *CRATES, "garden_1"):
            state.perform(action)
        state.play_seconds = 100
        state.perform("garden_2")
        state.play_seconds = 140
        save_game(self.app.slot, state, (480, 500))
        self.app.action("continue")
        self.assertEqual(self.app.state.garden_stage("garden_1"), 3)
        self.assertEqual(self.app.state.garden_stage("garden_2"), 1)


if __name__ == "__main__":
    unittest.main()
