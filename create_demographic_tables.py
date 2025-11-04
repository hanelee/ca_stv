import pandas as pd
import json
from pathlib import Path



def avg_prop(dist_res, num_profiles, seats, focal):
    all_entries = [item for unit in dist_res for item in unit]
    # Count how many belong in focal group
    count = sum(1 for item in all_entries if item.startswith(focal))
        
    # Divide by number of profile reps
    prop = count / (num_profiles*seats)
    return(prop)





district_nums = [(8,5), (10,4), (16,5), (20,4), (40,1), (80,1)]
district_mode = ["cambridge", "slate_pl", "slate_bt"]
parties = ["D", "R"]
party_focal = parties[0]
races = ["H", "O"]
race_focal = races[0]
plans = ["000", "200", "400", "600", "800"]
num_profiles_per_district = 100 ### CHANGE

# Might need to run vk_settings_generator again






rows = []

# For each district division x seats per district
for (dn, eln) in district_nums:
    dm = 'cambridge'
    for pn in plans:
        # For each district
        for dist_id in range(dn):
            # Add census demographic info from settings file
            racial_settings_folder = Path(f"./vk_run_settings_racial_turnout/{dn}")
            racial_settings_filename = f"ca_{dn}_vk_sample_settings_district_plan_{pn}_district_{dist_id:02d}.json"
            racial_settings_filepath = racial_settings_folder / racial_settings_filename

            with open(racial_settings_filepath, "r") as g:
                settings_data = json.load(g)
                total_hvap = settings_data.get("total_hvap", None)
                total_vap = settings_data.get("total_vap", None)     

            partisan_settings_folder = Path(f"./vk_run_settings_partisan/{dn}")
            partisan_settings_filename = f"ca_{dn}_vk_sample_settings_partisan_district_plan_{pn}_district_{dist_id:02d}.json"
            partisan_settings_filepath = partisan_settings_folder / partisan_settings_filename

            with open(partisan_settings_filepath, "r") as g:
                settings_data = json.load(g)
                dist_rvap_prop = settings_data.get("bloc_proportions", None)["R"]
                   
            rows.append({"plan": pn,
                        "total_district_num": dn,
                        "dist_num": dist_id,
                        "H_prop_census": total_hvap/total_vap,
                        "total_vap": total_vap,
                        "R_prop_census": dist_rvap_prop})
        

df = pd.DataFrame(rows)
# print(df.head())


# hvap_props = []
# rvap_props = []

for (dn, eln) in district_nums:
# for (dn, eln) in [(8,5)]:
    ## create a 5 * dn table showing the hispanic proportion
    dn_df = df[df['total_district_num'] == dn]
    hvap_prop = pd.DataFrame(index = plans, columns = list(range(dn)))
    rvap_prop = pd.DataFrame(index = plans, columns = list(range(dn)))
    pairs_df = pd.DataFrame(index = plans, columns = list(range(dn)))
    for row in dn_df.iterrows():
        plan_num = row[1]['plan']
        district_num = row[1]['dist_num']
        hvap_prop.at[plan_num, district_num] = round(row[1]["H_prop_census"],4)
        rvap_prop.at[plan_num, district_num] = round(row[1]["R_prop_census"],4)
        pairs_df.at[plan_num, district_num] = (round(row[1]["H_prop_census"],4),round(row[1]["R_prop_census"],4))

    # print(hvap_prop.head())
    # print(rvap_prop.head())
    # hvap_props.append(hvap_prop)
    
    hvap_prop_sorted = hvap_prop.apply(lambda row: row.sort_values(ascending=False).values, axis=1, result_type='expand')
    rvap_prop_sorted = rvap_prop.apply(lambda row: row.sort_values(ascending=False).values, axis=1, result_type='expand')
    pairs_df_sorted = pairs_df.apply(
        lambda row: sorted(row, key=lambda x: x[0], reverse=True),
        axis=1, result_type='expand'
    )
    
    hvap_prop_sorted.to_csv(f'./demo_tables/{dn}_districts_hvap_only.csv')
    rvap_prop_sorted.to_csv(f'./demo_tables/{dn}_districts_rshare_only.csv')
    pairs_df_sorted.to_csv(f'./demo_tables/{dn}_districts_hvap_rshare_pairs.csv')







