import argparse
import json
import sys
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any, List, Optional
from xml.etree import ElementTree as ET

import open3d as o3d
from pathvalidate import is_valid_filepath


class CheckType(IntEnum):
    FILE_PATH_VALID = 0
    FILE_EXISTS = 1
    FILE_XML_CAN_OPEN = 2
    FILE_JSON_CAN_OPEN = 3
    FILE_OBJ_CAN_OPEN = 4
    FILE_MESH_IS_WATERTIGHT = 5
    FILE_MESH_VOLUME_TOO_SMALL = 6


def get_check_type_str(check_type: CheckType) -> str:
    if check_type == CheckType.FILE_PATH_VALID:
        return "file_path_valid"
    elif check_type == CheckType.FILE_EXISTS:
        return "file_exists"
    elif check_type == CheckType.FILE_XML_CAN_OPEN:
        return "file_xml_can_open"
    elif check_type == CheckType.FILE_JSON_CAN_OPEN:
        return "file_json_can_open"
    elif check_type == CheckType.FILE_OBJ_CAN_OPEN:
        return "file_obj_can_open"
    elif check_type == CheckType.FILE_MESH_IS_WATERTIGHT:
        return "file_mesh_is_watertight"
    elif check_type == CheckType.FILE_MESH_VOLUME_TOO_SMALL:
        return "file_mesh_volume_too_small"
    return "undefined"


@dataclass
class CheckInfo:
    check_type: CheckType = CheckType.FILE_PATH_VALID
    passed: bool = False
    message: str = ""
    info_str: str = ""
    filepath_str: str = ""

    def to_json(self) -> Any:
        return {
            "type": get_check_type_str(self.check_type),
            "passed": self.passed,
            "message": self.message,
            "info_str": self.info_str,
            "filepath": self.filepath_str,
        }


class AssetChecker:
    def __init__(self, filepath: Optional[Path] = None):
        self._filepath: Optional[Path] = filepath

        self._checks_info: List[CheckInfo] = []

    @property
    def filepath(self) -> Path:
        return self._filepath

    def update_check(
        self,
        check_type: CheckType,
        passed: bool,
        message: str = "",
        info_str: str = "",
    ) -> None:
        if self._filepath is not None:
            self._checks_info.append(
                CheckInfo(
                    check_type=check_type,
                    passed=passed,
                    message=message,
                    info_str=info_str,
                    filepath_str=self._filepath.as_posix(),
                )
            )

    def run_all_checks(
        self, filepath: Optional[Path] = None, keep_last_info: bool = False
    ) -> None:
        self._filepath = filepath if filepath is not None else self._filepath

        if not keep_last_info:
            self._checks_info.clear()

        self.check_file(self._filepath)

    def check_file(self, filepath: Optional[Path] = None) -> None:
        self._filepath = filepath if filepath is not None else self._filepath

        if self._filepath is None:
            print("Must provide a valid filepath to run the check_file checks")
            return

        if not is_valid_filepath(self._filepath, platform=sys.platform):
            self.update_check(
                CheckType.FILE_PATH_VALID,
                False,
                f"Filepath @ {self._filepath.as_posix()} is not valid",
            )
        else:
            self.update_check(CheckType.FILE_PATH_VALID, True)

        file_exists = self._filepath.exists()
        if not file_exists:
            self.update_check(
                CheckType.FILE_EXISTS,
                False,
                f"File {self._filepath.as_posix()} doesn't exist",
            )
        else:
            self.update_check(CheckType.FILE_EXISTS, True)

        if not file_exists:
            return

        if self._filepath.suffix.lower() == ".xml":
            try:
                ET.parse(self._filepath.as_posix())
                self.update_check(CheckType.FILE_XML_CAN_OPEN, True)
            except ET.ParseError as e:
                self.update_check(
                    CheckType.FILE_XML_CAN_OPEN,
                    False,
                    f"XML file @ {self._filepath.name} can't be parsed",
                    f"Error-msg: {e.msg} \n\r" + f"Position: {e.position}",
                )

        if self._filepath.suffix.lower() == ".json":
            try:
                with open(self._filepath, "r") as fhandle:
                    json.load(fhandle)
                self.update_check(CheckType.FILE_JSON_CAN_OPEN, True)
            except json.JSONDecodeError as e:
                self.update_check(
                    CheckType.FILE_JSON_CAN_OPEN,
                    False,
                    f"JSON file @ {self._filepath.name} can't be parsed",
                    f"Error: {e}",
                )

        if self._filepath.suffix.lower() == ".obj":
            mesh = o3d.io.read_triangle_mesh(self._filepath.as_posix())
            if mesh.is_empty():
                self.update_check(
                    CheckType.FILE_OBJ_CAN_OPEN,
                    False,
                    f"OBJ file @ {self._filepath.name} can't be opened",
                )
            else:
                self.update_check(CheckType.FILE_OBJ_CAN_OPEN, True)
                if mesh.is_watertight():
                    self.update_check(CheckType.FILE_MESH_IS_WATERTIGHT, True)
                    if mesh.get_volume() < 1e-6:
                        self.update_check(
                            CheckType.FILE_MESH_VOLUME_TOO_SMALL,
                            False,
                            f"3d mesh file @ {self._filepath.name} has too small volume",
                        )
                else:
                    self.update_check(
                        CheckType.FILE_MESH_IS_WATERTIGHT,
                        False,
                        f"3d mesh file @ {self._filepath.name} is not watertight",
                    )

    def save_to_json(self, savepath: Path) -> None:
        json_data = {"checks": [info.to_json() for info in self._checks_info]}
        with open(savepath, "w") as fhandle:
            json.dump(json_data, fhandle, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        type=str,
        default="",
        help="The file to test the checks with",
    )

    args = parser.parse_args()
    if args.file == "":
        print("Must provide --file that points to the file to test")
    else:
        filepath = Path(args.file)
        asset_checker = AssetChecker(filepath)
        asset_checker.run_all_checks()
        asset_checker.save_to_json(Path("./checks_results.json"))
