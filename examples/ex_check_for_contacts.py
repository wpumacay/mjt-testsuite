import argparse
from pathlib import Path


SIM_DT = 0.002
SIM_DURATION = 2.0
NUM_RUNS = 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="Path to the mjcf file to be loaded for testing",
    )
    parser.add_argument(
        "--vis",
        action="store_true",
        help="Flag to whether or not to visualize the simulation",
    )

    args = parser.parse_args()

    if args.model == "":
        print("Must provide mjcf by using --model with this script")
        return 1

    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Given model `{model_path.as_posix()}` doesn't exist")
        return 1
    if not model_path.is_file():
        print(f"Given model `{model_path.as_posix()}` is not a single file")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
