import json
import geopandas as gpd
from pathlib import Path
import jsonlines as jl
from tqdm import tqdm
from gerrychain import Graph
from sbt_cohesion_fpv_utils import slate_BT_fpv_to_coh


if __name__ == "__main__":
    # Just grab the population data
    df = gpd.read_file(
        "./geographic_data/ca_districtr_bg_view_v1.gpkg",
        layer="ca_districtr_bg_view_v1",
    )
    # Just a quick sanity check to make sure the graph and df line up
    bg_graph = Graph.from_json("./geographic_data/CA_bg_2020_dualgraph.json")
    for i, node in enumerate(bg_graph.nodes()):
        if bg_graph.nodes[node]["path"] != df.iloc[i]["path"]:
            raise ValueError(f"Node {i} with id {node} does not align with df!")

    df = df[["total_vap_20", "pres_20_dem", "pres_20_rep"]]

    # ========================================
    #   IMPORTANT PARAMETERS FOR SUBSAMPLING
    # ========================================
    chain_length = 1000
    n_subsamples = 5
    subsample_interval = chain_length // n_subsamples

    district_nums = [8, 10, 16, 20, 40, 80]
    for district_num in district_nums:
        settings_folder = Path(f"./vk_run_settings_partisan/{district_num}")
        settings_folder.mkdir(exist_ok=True, parents=True)

        with jl.open(f"./districting/chain_out/ca_{district_num}_dist.jsonl") as file:
            for sample_idx, sample in tqdm(
                enumerate(file),
                total=chain_length,
                desc=f"Generating VK settings for {district_num:02d} districts",
            ):

                if sample_idx % subsample_interval != 0:
                    continue

                # Will be in the same order as the df since the graph was built from the gpkg
                district_plan = sample["assignment"]

                df["district_plan"] = district_plan
                data_by_district = df.groupby("district_plan").sum()

                for _, row in data_by_district.iterrows():
                    district = row.name
                    dprop = float(
                        row["pres_20_dem"] / (row["pres_20_dem"] + row["pres_20_rep"])
                    )

                    num_r_cands = 5
                    num_d_cands = 5
                    pi_r = 0.85
                    pi_d = 0.85
                    sbt_cohesion_r = round(
                        slate_BT_fpv_to_coh(num_r_cands, num_d_cands, pi_r), 4
                    )
                    sbt_cohesion_d = round(
                        slate_BT_fpv_to_coh(num_d_cands, num_r_cands, pi_d), 4
                    )

                    output_settings = dict(
                        n_voters=10_000,
                        slate_to_candidates={
                            "D": [f"D{i+1}" for i in range(num_d_cands)],
                            "R": [f"R{i+1}" for i in range(num_r_cands)],
                        },
                        bloc_proportions={"D": dprop, "R": 1 - dprop},
                        spl_cs_cohesion_parameters={
                            "D": {"D": pi_d, "R": round(1 - pi_d, 4)},
                            "R": {"D": round(1 - pi_r, 4), "R": pi_r},
                        },
                        sbt_cohesion_parameters={
                            "D": {
                                "D": sbt_cohesion_d,
                                "R": round(1 - sbt_cohesion_d, 4),
                            },
                            "R": {
                                "D": round(1 - sbt_cohesion_r, 4),
                                "R": sbt_cohesion_r,
                            },
                        },
                        # alphas={
                        #     "D": {"D": 0.75, "R": 0.50},
                        #     "R": {"D": 1.0, "R": 0.75},
                        # },
                        alphas={
                            "D": {"D": 1, "R": 1},
                            "R": {"D": 1, "R": 1},
                        },
                    )

                    with open(
                        f"{settings_folder}/ca_{district_num}_vk_sample_settings_partisan_district_plan_{sample_idx:03d}_district_{district:02d}.json",
                        "w",
                    ) as out_file:
                        json.dump(output_settings, out_file, indent=2)
