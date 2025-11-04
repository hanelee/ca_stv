from glob import glob
from votekit.elections import FastSTV as STV, Plurality
from votekit import RankProfile
from joblib import Parallel, delayed
from joblib_progress import joblib_progress
from pathlib import Path
import json
import random
import numpy as np

# random.seed(42)
# np.random.seed(42)


def process_profile(profile_file, n_seats, election_method):
    profile: RankProfile = RankProfile.from_csv(profile_file)

    if election_method == "STV":
        winner_list = [
            next(iter(winner_singleton))
            for winner_singleton in STV(
                profile, m=n_seats, simultaneous=False, tiebreak="random"
            ).get_elected()
        ]
    elif election_method == "IRV":
        winner_list = [
            next(iter(winner_singleton))
            for winner_singleton in STV(
                profile, m=1, simultaneous=False, tiebreak="random"
            ).get_elected()
        ]
    elif election_method == "Plurality":
        winner_list = [
            next(iter(winner_singleton))
            for winner_singleton in Plurality(
                profile, m=1, tiebreak="random"
            ).get_elected()
        ]
    else:
        raise ValueError(f"Invalid election method: {election_method}")

    return winner_list


if __name__ == "__main__":
    for model in ["slate_pl", "slate_bt", "cambridge"]:
        output_dir = Path(f"./vk_ca_election_model_results_partisan/{model}")
        output_dir.mkdir(exist_ok=True, parents=True)

        district_nums = [8, 10, 16, 20, 40, 80]
        winners_count = [5, 4, 5, 4, 1, 1]
        for district_num, n_seats in zip(district_nums, winners_count):
            profile_folder = Path(f"./vk_voter_profiles_partisan/{model}/")

            # alphabetically sorted
            all_profile_files = sorted(glob(f"{profile_folder}/{district_num}/*.csv"))

            if n_seats > 1:
                election_methods = ["STV"]
            else:
                election_methods = ["IRV", "Plurality"]

            for election_method in election_methods:
                with joblib_progress(
                    description=f"Running elections for {district_num:02d} districts and voter model {model} and election method {election_method}",
                    total=len(all_profile_files),
                ):
                    winners_list = Parallel(n_jobs=-1)(
                        delayed(process_profile)(profile_file, n_seats, election_method)
                        for profile_file in all_profile_files
                    )

                with open(
                    output_dir
                    / f"ca_{district_num}_districts_{n_seats}_{election_method}_partisan_winners_for_voter_model_{model}.json",
                    "w",
                ) as out_file:
                    json.dump(winners_list, out_file, indent=2)
