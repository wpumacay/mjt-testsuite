import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import mujoco as mj
from tqdm import tqdm


@dataclass
class TestConfig:
    timestep: float = 0.002
    n_steps: int = 2000
    n_runs: int = 3
    freeze_all: bool = False


@dataclass
class TestRunResults:
    step_time: float = 0.0
    real_time_factor: float = 0.0
    contacts_per_step: int = 0

    def to_json(self) -> Dict[str, Any]:
        return dict(
            step_time=self.step_time,
            real_time_factor=self.real_time_factor,
            contacts_per_step=self.contacts_per_step,
        )


def run_testspeed_single_model(
    filepath: Path, config: TestConfig
) -> List[TestRunResults]:
    model_spec: mj.MjSpec = mj.MjSpec.from_file(filepath.as_posix())
    if config.freeze_all:
        for joint in model_spec.joints:
            if joint.type == mj.mjtJoint.mjJNT_FREE:
                joint.delete()

    model: mj.MjModel = model_spec.compile()
    model.opt.timestep = config.timestep

    results: List[TestRunResults] = []
    for _ in tqdm(range(config.n_runs)):
        data: mj.MjData = mj.MjData(model)
        step_time_buff = []
        contacts_count_buff = []
        for _ in range(config.n_steps):
            t_step_start = time.perf_counter()
            mj.mj_step(model, data)
            t_step_end = time.perf_counter()
            step_time_buff.append(t_step_end - t_step_start)
            contacts_count_buff.append(data.ncon)

        result = TestRunResults()
        result.step_time = sum(step_time_buff) / len(step_time_buff)
        result.contacts_per_step = int(
            sum(contacts_count_buff) / len(contacts_count_buff)
        )
        result.real_time_factor = config.timestep / result.step_time
        results.append(result)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="Path to the mjcf scene to be tested",
    )
    parser.add_argument(
        "--folder",
        type=str,
        default="",
        help="Path to the folder containing the ithor scenes",
    )
    parser.add_argument(
        "--save_results",
        action="store_true",
        help="Whether or not to save the results",
    )

    args = parser.parse_args()

    if args.model != "":
        model_path = Path(args.model)
        test_config = TestConfig()
        results = run_testspeed_single_model(model_path, test_config)
        if args.save_results:
            json_data = {}
            json_data[model_path.stem] = [
                result.to_json() for result in results
            ]
            with open(f"{model_path.stem}_speed_test.json", "w") as fhandle:
                json.dump(json_data, fhandle, indent=4)
    elif args.folder != "":
        folder_path = Path(args.folder)
        test_config = TestConfig()
        # TODO(wilbert): complete my implementation, pls :D
