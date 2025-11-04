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

    df = df[["total_vap_20", "hvap_20"]]

    # ========================================
    #   IMPORTANT PARAMETERS FOR SUBSAMPLING
    # ========================================
    chain_length = 1000
    n_subsamples = 5
    subsample_interval = chain_length // n_subsamples

    district_nums = [8, 10, 16, 20, 40, 80]
    for district_num in district_nums:
        settings_folder = Path(f"./vk_run_settings_racial/{district_num}")
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
                    hprop = float(row["hvap_20"] / row["total_vap_20"])
                    turnout = {"H": 0.4, "O": 1}
                    adjusted_hprop = (
                        hprop
                        * turnout["H"]
                        / (hprop * turnout["H"] + (1 - hprop) * turnout["O"])
                    )

                    num_h_cands = 4
                    num_o_cands = 6
                    pi_h = 0.75
                    pi_o = 0.80
                    sbt_cohesion_h = round(
                        slate_BT_fpv_to_coh(num_h_cands, num_o_cands, pi_h), 4
                    )
                    sbt_cohesion_o = round(
                        slate_BT_fpv_to_coh(num_o_cands, num_h_cands, pi_o), 4
                    )

                    output_settings = dict(
                        n_voters=10_000,
                        slate_to_candidates={
                            "H": [f"H{i+1}" for i in range(num_h_cands)],
                            "O": [f"O{i+1}" for i in range(num_o_cands)],
                        },
                        bloc_proportions={"H": adjusted_hprop, "O": 1 - adjusted_hprop},
                        spl_cs_cohesion_parameters={
                            "H": {"H": pi_h, "O": round(1 - pi_h, 4)},
                            "O": {"H": round(1 - pi_o, 4), "O": pi_o},
                        },
                        sbt_cohesion_parameters={
                            "H": {
                                "H": sbt_cohesion_h,
                                "O": round(1 - sbt_cohesion_h, 4),
                            },
                            "O": {
                                "H": round(1 - sbt_cohesion_o, 4),
                                "O": sbt_cohesion_o,
                            },
                        },
                        # alphas={
                        #     "H": {"H": 1.25, "O": 0.75},
                        #     "O": {"H": 0.6, "O": 0.50},
                        # },
                        alphas={
                            "H": {"H": 1, "O": 1},
                            "O": {"H": 1, "O": 1},
                        },
                        total_hvap=row["hvap_20"],
                        total_vap=row["total_vap_20"],
                    )

                    with open(
                        f"{settings_folder}/ca_{district_num}_vk_sample_settings_district_plan_{sample_idx:03d}_district_{district:02d}.json",
                        "w",
                    ) as out_file:
                        json.dump(output_settings, out_file, indent=2)
