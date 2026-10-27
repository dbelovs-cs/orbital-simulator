"""Launch the preview or render a reproducible PNG without a desktop."""

import argparse
from math import isfinite
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--speed", type=float, default=1.0, help="Initial speed factor, 0.60-1.60")
    parser.add_argument("--snapshot", type=Path, help="Save a PNG instead of opening a window")
    parser.add_argument("--advance", type=float, default=0.0,
                        help="Simulation time units to advance before a snapshot")
    args = parser.parse_args()
    if not isfinite(args.speed) or not 0.6 <= args.speed <= 1.6:
        parser.error("--speed must be between 0.60 and 1.60")
    if not isfinite(args.advance) or not 0 <= args.advance <= 10000:
        parser.error("--advance must be between 0 and 10000")
    if args.advance and not args.snapshot:
        parser.error("--advance requires --snapshot")
    if args.snapshot:
        import matplotlib
        matplotlib.use("Agg")
    from app import OrbitalApp
    from physics import TIME_STEP
    app = OrbitalApp(args.speed)
    if args.snapshot:
        for _ in range(round(args.advance / TIME_STEP)):
            app.sim.step()
        app.refresh()
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        app.fig.savefig(args.snapshot, dpi=150, facecolor=app.fig.get_facecolor())
        print(f"Saved {args.snapshot}")
    else:
        import matplotlib
        if matplotlib.get_backend().lower() == "agg":
            parser.exit(1, "No desktop graphics backend found. Install Python with Tk support, "
                        "or use --snapshot preview.png.\n")
        app.run()


if __name__ == "__main__":
    main()
