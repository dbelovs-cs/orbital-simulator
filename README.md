# Orbital Sandbox

A small Python desktop program demonstrating two bodies under mutual gravity.
This is the requested first-look slice, not the finished course project.

## Start here

Use **Python 3.11 or 3.12** with desktop GUI support. The tested interpreter is
Python 3.12.14. Extract the ZIP and open a terminal inside the extracted folder
that contains `main.py`. These instructions do not require an online account.

Windows:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

If Python 3.12 is not installed on Windows, install it or replace `py -3.12`
with `py -3.11`. Package installation needs internet access; normal use is local.
Matplotlib needs an interactive graphics backend to open a window. Python from
python.org normally includes Tk on Windows/macOS. Some Linux distributions
package Tk separately (often `python3-tk`). `python -m tkinter` is a useful check
when run with the same interpreter as the application. Run the program from a
desktop terminal, rather than inside a notebook's inline plot output.

## Controls and behaviour

| Control | Result |
| --- | --- |
| Play / Pause or Space | Start or freeze both bodies and the simulation clock. |
| Reset or R | Restore initial positions at the current speed setting; clear trails and time; pause. |
| Initial relative speed slider | 0.60-1.60 times circular speed, in 0.01 steps. Every change resets and pauses. |
| Trails or T | Hide/show recent paths. History continues collecting while hidden. |
| Star / Planet, or click a body | Select the body whose properties appear in the information panel. |
| Window close button | Exit. No state is saved. |

The arrow attached to the planet shows its velocity. At the start it is labelled
**Initial velocity** and points upward (+y). Moving the speed slider changes its
length: longer means faster. The direction is fixed in this two-body setup;
the slider changes speed, not direction. During motion the label changes to
**Planet velocity** and the arrow follows the current velocity. Reset restores
the initial arrow. It is a direction/speed indicator, not a force vector or a
prediction of where the curved orbit will go. Its visual scale is arbitrary
and stays readable when the view zooms out.

The information panel shows mass, x/y position, x/y velocity, speed and the
distance between the two bodies. The units M, L and T mean normalized mass,
distance and simulation time, not kilograms, kilometres or seconds. The view
automatically expands when a body moves away. Reset restores the starting view.
Keep the window close to its starting size (1100 x 700 logical pixels); a very
small window may crowd the labels.

## A short professor demonstration

1. Leave the slider at 1.00x and press Play. The planet follows an approximately
   circular orbit. A complete orbit takes about 22 real seconds on a responsive
   computer. The star also moves, but its displacement is small because it is
   1000 times more massive.
2. Pause and select each body to inspect its position and velocity.
3. Change the slider to 0.75x. Explain that this prepares a new experiment, then
   press Play to show the elliptical path.
4. Toggle the trails, then reset and choose 1.50x. Press Play to demonstrate
   escape and the expanding view.
5. Reset and return the slider to 1.00x.

## Code structure

- `main.py`: command-line arguments, desktop startup and optional PNG rendering.
- `physics.py`: body data, initial conditions, gravity, leapfrog steps and trails.
- `app.py`: drawing, buttons, slider, selection, keyboard events and playback.
- `tests/test_physics.py`: eight checks of the numerical model and its boundaries.
- `tests/test_controls.py`: seven checks of controls, view behaviour and velocity display.
- `screenshots/`: renders of the starting state and circular, elliptical and escape orbits.
- `validation_metrics.json`: measured errors from six initial-speed cases.
- `requirements.txt`: tested Matplotlib and NumPy versions. NumPy is a
  Matplotlib dependency; our physics module uses Python's standard library.

The standard and explained packages have identical Python syntax trees and
behaviour. The explained package adds teaching comments, without changing the
algorithm. Read `physics.py` first, then `app.py`, then `main.py`.

## Model and deliberate limits

G = 1, star mass = 1000, planet mass = 1, initial separation = 120.
The starting relative circular speed is sqrt(G * (1000 + 1) / 120).
Positions and velocities start around the common centre of mass, with zero
total momentum. Both bodies experience equal and opposite gravitational forces.

The integrator uses kick-drift-kick leapfrog with a fixed time step of 0.05 T.
Playback targets 12 T per real second, with about 30 display updates per second.
A delayed frame is capped at 0.1 real second: a slow computer slows playback
rather than taking a dangerously large physics step. The time display remains
the authoritative measure of simulated time. Each trail stores at most 2000
samples, one per four steps, covering about 400 T of recent history.

This is a 2D point-mass model. Marker sizes are symbolic. There are no collisions,
third bodies, body editing, time-speed control, saved sessions, real astronomical
units, relativistic effects or orbit prediction. A separation of 5 L or less
triggers a protective pause; this is a numerical boundary, not a collision model.

## Verification and optional screenshots

After activating your environment, or using its Python path explicitly:

```bash
python -m unittest discover -s tests -v
python main.py --snapshot circular.png --advance 220
python main.py --snapshot ellipse.png --speed 0.75 --advance 135
python main.py --snapshot escape.png --speed 1.5 --advance 300
```

The screenshot mode works without a desktop. `--advance` is simulated time,
rounded to the nearest 0.05 T step; it only works with `--snapshot`.
Screenshot paths supplied on the command line are overwritten if they exist.

Validation: 15 tests passed in Linux with Matplotlib's Agg renderer, including
synthetic mouse and keyboard events. Circular-orbit radius drift over two
periods was below 0.0001%. Windows/macOS desktop operation and live animation
timing have not been manually verified here. Run the app once on the presentation
computer before the professor demonstration.

## Course hand-in

The ZIP contains Python source, tests and pinned requirements. The separate PDF
describes functionality, setup, screenshots, maths, validation and future scope.
Add your actual group member names to the final project document; no names or
repository link have been invented. This preview does not claim to satisfy the
course's requirement for a complete final product. The course brief also asks
you to contact the professor if incorporating previously developed code.
