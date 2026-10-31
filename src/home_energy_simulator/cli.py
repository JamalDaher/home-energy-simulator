"""Command-line interface for the simulator."""
import argparse
import json
from .model import SystemConfig, demo_profiles, simulate, totals

def main():
    parser = argparse.ArgumentParser(description="Simulate household energy use")
    parser.add_argument("--solar-kw", type=float, default=4.8)
    parser.add_argument("--battery-kwh", type=float, default=14.0)
    parser.add_argument("--generator-kw", type=float, default=0)
    parser.add_argument("--generator", action="store_true")
    parser.add_argument("--grid", action="store_true")
    args = parser.parse_args()
    config = SystemConfig(solar_kw=args.solar_kw, battery_kwh=args.battery_kwh,
                          generator_kw=args.generator_kw,
                          generator_enabled=args.generator, grid_available=args.grid)
    rows = simulate(config, *demo_profiles())
    print(json.dumps(totals(rows), indent=2))

if __name__ == "__main__":
    main()
