"""Headless checks of widget events and playback state."""

import unittest

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backend_bases import KeyEvent, MouseEvent

from app import OrbitalApp, VELOCITY_SCALE
from physics import MIN_DISTANCE


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.app = OrbitalApp()
        self.app.fig.canvas.draw()

    def tearDown(self):
        plt.close(self.app.fig)

    def click_axes_center(self, axes):
        x, y = axes.transAxes.transform((0.5, 0.5))
        for name in ("button_press_event", "button_release_event"):
            event = MouseEvent(name, self.app.fig.canvas, x, y, button=1)
            self.app.fig.canvas.callbacks.process(name, event)

    def test_play_pause_reset_button_events(self):
        self.app.tick(0.1)
        self.assertEqual(self.app.sim.time, 0)
        self.click_axes_center(self.app.play_button.ax)
        self.app.tick(0.1)
        self.assertGreater(self.app.sim.time, 0)
        self.click_axes_center(self.app.play_button.ax)
        stopped_time = self.app.sim.time
        self.app.tick(0.1)
        self.assertEqual(self.app.sim.time, stopped_time)
        self.click_axes_center(self.app.reset_button.ax)
        self.assertEqual(self.app.sim.time, 0)
        self.assertFalse(self.app.running)

    def test_slider_restarts_paused(self):
        self.app.toggle()
        self.app.tick(0.1)
        self.app.speed_slider.set_val(0.75)
        self.assertEqual(self.app.sim.speed_factor, 0.75)
        self.assertEqual(self.app.sim.time, 0)
        self.assertFalse(self.app.running)
        self.assertEqual(len(self.app.sim.trails[1]), 1)

    def test_trails_and_body_selection(self):
        for _ in range(12):
            self.app.sim.step()
        history_length = len(self.app.sim.trails[1])
        self.app.trail_toggle.set_active(0)
        self.assertEqual(len(self.app.lines[1].get_xdata()), 0)
        self.assertEqual(len(self.app.sim.trails[1]), history_length)
        self.app.trail_toggle.set_active(0)
        self.assertEqual(len(self.app.lines[1].get_xdata()), history_length)
        body = self.app.sim.bodies[0]
        x, y = self.app.ax.transData.transform((body.x, body.y))
        event = MouseEvent("button_press_event", self.app.fig.canvas, x, y, button=1)
        self.app.fig.canvas.callbacks.process("button_press_event", event)
        self.assertEqual(self.app.selected, 0)
        self.assertIn("1000.0 M", self.app.info.get_text())

    def test_keyboard_shortcuts(self):
        for key in (" ", "t", "r"):
            event = KeyEvent("key_press_event", self.app.fig.canvas, key=key)
            self.app.fig.canvas.callbacks.process("key_press_event", event)
        self.assertFalse(self.app.running)
        self.assertFalse(self.app.show_trails)
        self.assertEqual(self.app.sim.time, 0)

    def test_frame_cap_and_close_approach_pause(self):
        self.app.toggle()
        self.app.tick(100)
        self.assertLessEqual(self.app.sim.time, 1.21)
        self.app.sim.bodies[0].x = 0
        self.app.sim.bodies[1].x = MIN_DISTANCE
        self.app.sim.bodies[0].y = self.app.sim.bodies[1].y = 0
        self.app.tick(0.1)
        self.assertFalse(self.app.running)
        self.assertIn("Close approach", self.app.message)

    def test_escape_remains_in_view(self):
        self.app.sim.bodies[1].x = 900
        self.app.refresh()
        self.assertGreater(self.app.ax.get_xlim()[1], 900)
        self.app.reset()
        self.assertEqual(self.app.ax.get_xlim(), (-155.0, 155.0))

    def test_velocity_arrow_changes_with_speed_and_tracks_motion(self):
        offset = self.app.velocity_arrow.get_position()
        initial_length = offset[1]
        self.assertEqual(offset[0], 0)
        self.assertGreater(initial_length, 0)
        self.assertEqual(self.app.velocity_label.get_text(), "Initial velocity")
        self.app.speed_slider.set_val(1.5)
        changed = self.app.velocity_arrow.get_position()[1]
        self.assertAlmostEqual(changed / initial_length, 1.5)
        for _ in range(1000):
            self.app.sim.step()
        self.app.refresh()
        planet = self.app.sim.bodies[1]
        offset = self.app.velocity_arrow.get_position()
        self.assertEqual(self.app.velocity_arrow.xy, (planet.x, planet.y))
        self.assertAlmostEqual(offset[0] / VELOCITY_SCALE, planet.vx)
        self.assertAlmostEqual(offset[1] / VELOCITY_SCALE, planet.vy)
        self.assertEqual(self.app.velocity_label.get_text(), "Planet velocity")
        self.app.extent *= 5
        self.app.refresh()
        self.assertEqual(self.app.velocity_arrow.get_position(), offset)
        self.app.reset()
        self.assertEqual(self.app.velocity_label.get_text(), "Initial velocity")


if __name__ == "__main__":
    unittest.main()
