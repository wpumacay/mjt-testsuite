import argparse
import glob
import re
from pathlib import Path

from pathvalidate import is_valid_filepath, sanitize_filepath
from tqdm import tqdm

CATEGORIES = [
    "Microwave",
    "Fridge",
    "Toaster",
    "Dresser",
    "Light_Switch",
    "Toilet",
    "Book",
    "Shelving_Unit",
    "Side_Table",
    "Coffee_Table",
    "Desk",
    "Laptop",
    "Doorway",
    "Laundry_Hamper",
    "Safe",
    "Box",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--folder",
        type=str,
        default="",
        help="The folder where to search for .obj files recursively",
    )

    args = parser.parse_args()
    if args.folder == "":
        print("Must use --folder to specify root folder for the search")
        return 1

    folder_path = Path(args.folder)
    patterns = {
        category: re.compile(category + r"_\d+") for category in CATEGORIES
    }
    path_candidates = [
        Path(path)
        for path in glob.glob(f"{folder_path}/**/*.obj", recursive=True)
    ]

    print("Starting first preprocessing stage ...")
    paths_first_pass = []
    for path in tqdm(path_candidates):
        if not path.exists() or not path.is_file():
            continue
        for category in CATEGORIES:
            if not patterns[category].match(path.stem):
                continue
            paths_first_pass.append(path)
    print("First preprocessing stage done")

    print("Starting final processing stage ...")
    for path in paths_first_pass:
        valid_in_linux = is_valid_filepath(path, platform="linux")
        valid_in_windows = is_valid_filepath(path, platform="windows")
        if valid_in_linux and not valid_in_windows:
            sanitized_path = sanitize_filepath(path)
            sanitized_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                path.rename(sanitized_path)
            except:
                print(f"Invalid path: {path.as_posix()}")
    print("Final processing stage done")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
