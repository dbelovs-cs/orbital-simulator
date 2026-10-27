"""Numerical checks independent of the graphical interface."""

import math
import unittest

from physics import (G, INITIAL_DISTANCE, MIN_DISTANCE, PLANET_MASS, STAR_MASS,
                     TIME_STEP, TRAIL_LIMIT, CloseApproachError, Simulation)


class PhysicsTests(unittest.TestCase):
    def test_initial_center_and_momentum(self):
        for factor in (0.6, 0.75, 1.0, 1.5, 1.6):
            sim = Simulation(factor)
            for field in ("x", "y", "vx", "vy"):
                total = sum(b.mass * getattr(b, field) for b in sim.bodies)
                self.assertAlmostEqual(total, 0.0, places=10)
            relative = sim.bodies[1].vy - sim.bodies[0].vy
            expected = math.sqrt(G * (STAR_MASS + PLANET_MASS) / INITIAL_DISTANCE)
            self.assertAlmostEqual(relative, expected * factor)

    def test_equal_opposite_force(self):
        sim = Simulation()
        acceleration = sim.accelerations()
        for axis in (0, 1):
            net_force = sum(b.mass * a[axis] for b, a in zip(sim.bodies, acceleration))
            self.assertAlmostEqual(net_force, 0.0, places=14)

    def test_circular_orbit_two_periods(self):
        sim = Simulation()
        initial_energy = sim.energy()
        period = 2 * math.pi * math.sqrt(INITIAL_DISTANCE ** 3 / (G * (STAR_MASS + PLANET_MASS)))
        radius_error = 0.0
        energy_error = 0.0
        for _ in range(round(2 * period / TIME_STEP)):
            sim.step()
            radius_error = max(radius_error, abs(sim.distance / INITIAL_DISTANCE - 1))
            energy_error = max(energy_error, abs(sim.energy() / initial_energy - 1))
        self.assertLess(radius_error, 1e-5)
        self.assertLess(energy_error, 1e-8)
        self.assertLess(abs(sum(b.mass * b.vx for b in sim.bodies)), 1e-10)
        self.assertLess(abs(sum(b.mass * b.vy for b in sim.bodies)), 1e-10)

    def test_ellipse_and_escape(self):
        ellipse, escape = Simulation(0.75), Simulation(1.5)
        self.assertLess(ellipse.energy(), 0)
        self.assertGreater(escape.energy(), 0)
        initial = ellipse.energy()
        closest = ellipse.distance
        for _ in range(6000):
            ellipse.step()
            escape.step()
            closest = min(closest, ellipse.distance)
        self.assertLess(closest, 60)
        self.assertGreater(escape.distance, 600)
        self.assertLess(abs(ellipse.energy() / initial - 1), 1e-4)

    def test_reset_clears_state_but_keeps_speed(self):
        sim = Simulation(0.75)
        for _ in range(20):
            sim.step()
        sim.reset()
        self.assertEqual(sim.time, 0)
        self.assertEqual(sim.steps, 0)
        self.assertEqual(sim.speed_factor, 0.75)
        self.assertAlmostEqual(sim.distance, INITIAL_DISTANCE)
        self.assertEqual([len(t) for t in sim.trails], [1, 1])

    def test_trail_storage_is_bounded(self):
        sim = Simulation()
        for _ in range(4 * (TRAIL_LIMIT + 10)):
            sim.step()
        self.assertEqual([len(t) for t in sim.trails], [TRAIL_LIMIT, TRAIL_LIMIT])

    def test_invalid_input_rejected(self):
        for speed in (0, 2, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                Simulation(speed)
        for dt in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                Simulation().step(dt)

    def test_close_approach_does_not_commit_step(self):
        sim = Simulation()
        sim.bodies[0].x = 0
        sim.bodies[1].x = MIN_DISTANCE + 0.01
        sim.bodies[1].vx = -1
        before = [(b.x, b.y, b.vx, b.vy) for b in sim.bodies]
        with self.assertRaises(CloseApproachError):
            sim.step()
        self.assertEqual(before, [(b.x, b.y, b.vx, b.vy) for b in sim.bodies])
        self.assertEqual(sim.time, 0)


if __name__ == "__main__":
    unittest.main()
