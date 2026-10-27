"""Newtonian two-body motion in dimensionless units."""

from collections import deque
from dataclasses import dataclass
from math import hypot, isfinite, sqrt

G = 1.0
STAR_MASS = 1000.0
PLANET_MASS = 1.0
INITIAL_DISTANCE = 120.0
TIME_STEP = 0.05
MIN_DISTANCE = 5.0
TRAIL_LIMIT = 2000


@dataclass
class Body:
    """A point mass with position and velocity in the orbital plane."""

    name: str
    mass: float
    x: float
    y: float
    vx: float
    vy: float

    @property
    def speed(self):
        return hypot(self.vx, self.vy)


class CloseApproachError(RuntimeError):
    """Raised before a step enters the unsupported close-approach region."""


class Simulation:
    """Integrate both bodies with fixed-step kick-drift-kick leapfrog."""

    def __init__(self, speed_factor=1.0):
        self.reset(speed_factor)

    def reset(self, speed_factor=None):
        """Rebuild the initial state and clear time and sampled trails."""
        factor = self.speed_factor if speed_factor is None else speed_factor
        if not isfinite(factor) or not 0.6 <= factor <= 1.6:
            raise ValueError("Initial speed must be between 0.60 and 1.60.")
        self.speed_factor = factor
        total_mass = STAR_MASS + PLANET_MASS
        relative_speed = sqrt(G * total_mass / INITIAL_DISTANCE) * factor
        star_fraction = PLANET_MASS / total_mass
        planet_fraction = STAR_MASS / total_mass
        self.bodies = [
            Body("Star", STAR_MASS, -star_fraction * INITIAL_DISTANCE, 0.0,
                 0.0, -star_fraction * relative_speed),
            Body("Planet", PLANET_MASS, planet_fraction * INITIAL_DISTANCE, 0.0,
                 0.0, planet_fraction * relative_speed),
        ]
        self.time = 0.0
        self.steps = 0
        self.trails = [deque(maxlen=TRAIL_LIMIT), deque(maxlen=TRAIL_LIMIT)]
        self._record_trails()

    def _record_trails(self):
        for trail, body in zip(self.trails, self.bodies):
            trail.append((body.x, body.y))

    @property
    def distance(self):
        first, second = self.bodies
        return hypot(second.x - first.x, second.y - first.y)

    def accelerations(self, positions=None):
        """Return accelerations from mutual gravity at supplied positions."""
        if positions is None:
            positions = [(body.x, body.y) for body in self.bodies]
        dx = positions[1][0] - positions[0][0]
        dy = positions[1][1] - positions[0][1]
        distance = hypot(dx, dy)
        if distance <= MIN_DISTANCE:
            raise CloseApproachError("Close approach: reset to continue.")
        scale = G / distance ** 3
        return [
            (scale * self.bodies[1].mass * dx, scale * self.bodies[1].mass * dy),
            (-scale * self.bodies[0].mass * dx, -scale * self.bodies[0].mass * dy),
        ]

    def step(self, dt=TIME_STEP):
        """Advance one step; leave the state untouched if it is unsafe."""
        if not isfinite(dt) or dt <= 0:
            raise ValueError("The time step must be finite and positive.")
        acceleration = self.accelerations()
        half_velocities = [
            (body.vx + ax * dt / 2, body.vy + ay * dt / 2)
            for body, (ax, ay) in zip(self.bodies, acceleration)
        ]
        positions = [
            (body.x + vx * dt, body.y + vy * dt)
            for body, (vx, vy) in zip(self.bodies, half_velocities)
        ]
        next_acceleration = self.accelerations(positions)
        for body, position, velocity, (ax, ay) in zip(
                self.bodies, positions, half_velocities, next_acceleration):
            body.x, body.y = position
            body.vx = velocity[0] + ax * dt / 2
            body.vy = velocity[1] + ay * dt / 2
        self.time += dt
        self.steps += 1
        if self.steps % 4 == 0:
            self._record_trails()

    def energy(self):
        """Return kinetic plus gravitational potential energy for validation."""
        kinetic = sum(0.5 * body.mass * body.speed ** 2 for body in self.bodies)
        potential = -G * self.bodies[0].mass * self.bodies[1].mass / self.distance
        return kinetic + potential
