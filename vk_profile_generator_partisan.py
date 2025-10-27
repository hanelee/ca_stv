from glob import glob
from votekit.ballot_generator import (
    BlocSlateConfig,
    slate_pl_profile_generator,
    slate_bt_profile_generator,
    cambridge_profile_generator,
)
from joblib import Parallel, delayed
from joblib_progress import joblib_progress
import json
from pathlib import Path
import random
import numpy as np
import os

random.seed(42)
np.random.seed(42)

if os.environ.get("PYTHONHASHSEED") != "0":
    raise ValueError(
        "You must set the PYTHONHASHSEED environment variable to 0 for "
        "reproducibility. If using UV, you may then rerun this script "
    )


generator_name_to_function = {
    "slate_pl": slate_pl_profile_generator,
    "slate_bt": slate_bt_profile_generator,
    "cambridge": cambridge_profile_generator,
}


def process_settings_file(settings_file, profile_folder, mode, duplicate_indx):
    with open(settings_file, "r") as f:
        settings = json.load(f)

    config = BlocSlateConfig(
        n_voters=100_000,
        slate_to_candidates=settings["slate_to_candidates"],
        bloc_proportions=settings["bloc_proportions"],
        cohesion_mapping=settings["cohesion_parameters"],
    )

    config.set_dirichlet_alphas(settings["alphas"])
    setting_file_stem = Path(settings_file).stem

    output_file = (
        profile_folder
        / f"{setting_file_stem.replace('sample_settings', 'profile')}_v{duplicate_indx}.csv"
    )
    profile = generator_name_to_function[mode](config)
    profile.to_csv(output_file)


if __name__ == "__main__":
## generate 100 profiles for each district
    for duplicate_indx in range(100):
        district_nums = [8, 10, 16, 20, 40, 80]
        for district_num in district_nums:
            for mode in ["slate_pl", "slate_bt", "cambridge"]:
                settings_folder = Path(f"./vk_run_settings_partisan/{district_num}")
                profile_folder = Path(f"./vk_voter_profiles_partisan/{mode}/{district_num}")
                profile_folder.mkdir(exist_ok=True, parents=True)

                all_settings_files = glob(f"{settings_folder}/*.json")

                all_settings_files = all_settings_files

                with joblib_progress(
                    description=f"Generating VK profiles for {district_num:02d} districts and voter model {mode}",
                    total=len(all_settings_files),
                ):
                    Parallel(n_jobs=-1)(
                        delayed(process_settings_file)(settings_file, profile_folder, mode, duplicate_indx)
                        for settings_file in all_settings_files
                    )
