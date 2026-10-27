"""Matplotlib controls and drawing for the orbital sandbox preview."""

from math import hypot
from time import perf_counter

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, CheckButtons, RadioButtons, Slider

from physics import CloseApproachError, Simulation, TIME_STEP

BG = "#202020"
TEXT = "#dedede"
MUTED = "#a0a0a0"
BLUE = "#8aafcc"
GOLD = "#d6b36f"
SIMULATION_RATE = 12.0
VELOCITY_SCALE = 12.0


class OrbitalApp:
    """Own the display and playback state; keep physics in Simulation."""

    def __init__(self, speed_factor=1.0):
        self.sim = Simulation(speed_factor)
        self.running = False
        self.selected = 1
        self.show_trails = True
        self.accumulator = 0.0
        self.extent = 155.0
        self.message = ""
        self.last_frame = perf_counter()
        self.animation = None
        with plt.rc_context({"toolbar": "None"}):
            self.fig = plt.figure(figsize=(11, 7), facecolor=BG)
        self.fig.canvas.manager.set_window_title("Orbital Sandbox")
        self.ax = self.fig.add_axes([0.055, 0.09, 0.64, 0.86], facecolor=BG)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.tick_params(colors=MUTED, labelsize=8, length=3)
        self.ax.set_xlabel("x [L]", color=MUTED, fontsize=9)
        self.ax.set_ylabel("y [L]", color=MUTED, fontsize=9)
        for spine in self.ax.spines.values():
            spine.set_color("#444444")
        self.ax.grid(color="#353535", linewidth=0.5)
        self.lines = [self.ax.plot([], [], color=color, alpha=0.65, lw=1.1)[0]
                      for color in (GOLD, BLUE)]
        self.markers = [self.ax.plot([], [], "o", color=color, markersize=size,
                                    markeredgecolor=TEXT, markeredgewidth=0.8)[0]
                        for color, size in ((GOLD, 13), (BLUE, 8))]
        self.halo, = self.ax.plot([], [], "o", markersize=20, markerfacecolor="none",
                                  markeredgecolor=MUTED, markeredgewidth=0.7)
        self.velocity_arrow = self.ax.annotate(
            "", xy=(0, 0), xytext=(0, 0), textcoords="offset points",
            arrowprops={"arrowstyle": "<-", "color": BLUE, "lw": 1.4,
                        "mutation_scale": 13, "shrinkA": 0, "shrinkB": 6})
        self.velocity_label = self.ax.annotate(
            "Initial velocity", xy=(0, 0), xytext=(-8, 4), textcoords="offset points",
            ha="right", va="bottom", color=TEXT, fontsize=9)
        self.status = self.fig.text(0.72, 0.13, "", color="#db9d91", fontsize=9)
        self._build_controls()
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.refresh()

    def _label(self, y, text, size=10, color=MUTED, weight="normal"):
        return self.fig.text(0.72, y, text, fontsize=size, color=color, weight=weight)

    def _button(self, rect, label, callback):
        axes = self.fig.add_axes(rect)
        button = Button(axes, label, color="#303030", hovercolor="#414141")
        for spine in axes.spines.values():
            spine.set_color("#555555")
        button.label.set_color(TEXT)
        button.label.set_fontsize(10)
        button.on_clicked(callback)
        return button

    def _build_controls(self):
        self.play_button = self._button([0.72, 0.88, 0.11, 0.05], "Play", self.toggle)
        self.reset_button = self._button([0.848, 0.88, 0.11, 0.05], "Reset", self.reset)
        self.time_label = self._label(0.837, "", size=9)
        self._label(0.76, "Initial speed", color=TEXT)
        slider_axes = self.fig.add_axes([0.725, 0.701, 0.192, 0.022], facecolor=BG)
        self.speed_slider = Slider(slider_axes, "", 0.6, 1.6,
                                   valinit=self.sim.speed_factor, valstep=0.01,
                                   valfmt="%1.2fx", color=BLUE, track_color="#484848",
                                   handle_style={"facecolor": TEXT, "edgecolor": TEXT,
                                                 "size": 7})
        self.speed_slider.valtext.set_color(TEXT)
        self.speed_slider.valtext.set_fontsize(10)
        self.speed_slider.on_changed(self.change_speed)
        self._label(0.658, "1x = circular. Changes restart the orbit.", size=8)
        trail_axes = self.fig.add_axes([0.715, 0.566, 0.24, 0.05], facecolor=BG)
        self.trail_toggle = CheckButtons(trail_axes, ["Trails"], [True],
                                        label_props={"color": [TEXT], "fontsize": [10]},
                                        frame_props={"edgecolor": [MUTED]},
                                        check_props={"facecolor": [TEXT]})
        trail_axes.set_axis_off()
        self.trail_toggle.on_clicked(self.toggle_trails)
        self._label(0.51, "Body", color=TEXT)
        radio_axes = self.fig.add_axes([0.715, 0.41, 0.24, 0.085], facecolor=BG)
        self.body_selector = RadioButtons(radio_axes, ("Star", "Planet"), active=1,
                                          activecolor=BLUE,
                                          radio_props={"edgecolor": [MUTED, MUTED]},
                                          label_props={"color": [TEXT, TEXT],
                                                       "fontsize": [10, 10]})
        radio_axes.set_axis_off()
        self.body_selector.on_clicked(self.select_body)
        self.info = self._label(0.374, "", size=9)
        self.info.set_fontfamily("DejaVu Sans Mono")
        self.info.set_verticalalignment("top")
        self.info.set_linespacing(1.65)

    def toggle(self, event=None):
        """Toggle playback without advancing time while paused."""
        self.running = not self.running
        self.accumulator = 0.0
        self.last_frame = perf_counter()
        self.message = ""
        self.refresh()

    def reset(self, event=None):
        """Restore the chosen starting speed and clear elapsed time and trails."""
        self.sim.reset(self.speed_slider.val)
        self.running = False
        self.accumulator = 0.0
        self.extent = 155.0
        self.last_frame = perf_counter()
        self.message = ""
        self.refresh()

    def change_speed(self, value):
        """The slider changes initial conditions, not an in-flight velocity."""
        self.reset()

    def toggle_trails(self, label=None):
        self.show_trails = self.trail_toggle.get_status()[0]
        self.refresh()

    def select_body(self, label):
        self.selected = 0 if label == "Star" else 1
        self.refresh()

    def _on_key(self, event):
        if event.key == " ":
            self.toggle()
        elif event.key in ("r", "R"):
            self.reset()
        elif event.key in ("t", "T"):
            self.trail_toggle.set_active(0)

    def _on_click(self, event):
        if event.inaxes != self.ax or event.x is None or event.y is None:
            return
        pixels = [self.ax.transData.transform((body.x, body.y)) for body in self.sim.bodies]
        distances = [hypot(x - event.x, y - event.y) for x, y in pixels]
        nearest = min(range(2), key=distances.__getitem__)
        if distances[nearest] <= 20:
            self.body_selector.set_active(nearest)

    def tick(self, elapsed):
        """Consume real time using fixed physics steps; cap delayed frames."""
        if not self.running:
            return
        self.accumulator += max(0.0, min(elapsed, 0.1)) * SIMULATION_RATE
        while self.accumulator >= TIME_STEP:
            try:
                self.sim.step()
            except CloseApproachError as error:
                self.running = False
                self.accumulator = 0.0
                self.message = str(error)
                break
            self.accumulator -= TIME_STEP

    def _update_velocity_arrow(self):
        """Draw velocity in screen points so zooming does not hide the arrow."""
        planet = self.sim.bodies[1]
        start = (planet.x, planet.y)
        offset = (planet.vx * VELOCITY_SCALE, planet.vy * VELOCITY_SCALE)
        self.velocity_arrow.xy = start
        self.velocity_arrow.set_position(offset)
        self.velocity_label.xy = start
        self.velocity_label.set_position((offset[0] - 8, offset[1] + 4))
        self.velocity_label.set_text("Initial velocity" if self.sim.steps == 0
                                     else "Planet velocity")

    def refresh(self):
        """Update artists and the information panel from the current model."""
        for body, marker, line, trail in zip(
                self.sim.bodies, self.markers, self.lines, self.sim.trails):
            marker.set_data([body.x], [body.y])
            if self.show_trails:
                line.set_data([p[0] for p in trail], [p[1] for p in trail])
            else:
                line.set_data([], [])
        body = self.sim.bodies[self.selected]
        self.halo.set_data([body.x], [body.y])
        # Expand only when needed, so an escaping body remains visible.
        self.extent = max(self.extent, *(1.18 * max(abs(b.x), abs(b.y))
                                       for b in self.sim.bodies))
        self.ax.set_xlim(-self.extent, self.extent)
        self.ax.set_ylim(-self.extent, self.extent)
        self._update_velocity_arrow()
        self.info.set_text(
            f"Mass           {body.mass:.1f} M\n"
            f"Position x     {body.x:+.2f} L\n"
            f"Position y     {body.y:+.2f} L\n"
            f"Velocity x     {body.vx:+.3f} L/T\n"
            f"Velocity y     {body.vy:+.3f} L/T\n"
            f"Speed          {body.speed:.3f} L/T\n"
            f"Separation     {self.sim.distance:.2f} L")
        self.time_label.set_text(f"Time: {self.sim.time:.2f} T")
        self.play_button.label.set_text("Pause" if self.running else "Play")
        self.status.set_text(self.message)
        self.fig.canvas.draw_idle()

    def _on_frame(self, frame):
        now = perf_counter()
        elapsed = now - self.last_frame
        self.last_frame = now
        self.tick(elapsed)
        self.refresh()

    def run(self):
        """Start the desktop animation and keep its timer alive."""
        self.last_frame = perf_counter()
        self.animation = FuncAnimation(self.fig, self._on_frame, interval=33,
                                        cache_frame_data=False)
        plt.show()
