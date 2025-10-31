
def avg_prop(dist_res, num_profiles, seats, focal):
    all_entries = [item for unit in dist_res for item in unit]
    # Count how many belong in focal group
    count = sum(1 for item in all_entries if item.startswith(focal))
        
    # Divide by number of profile reps
    prop = count / (num_profiles*seats)
    return(prop)


def count_focal_winners(rep_res, focal):
    # Count how many belong in focal group
    all_entries = [item for unit in rep_res for item in unit]
    count = sum(1 for item in all_entries if item.startswith(focal))
    return(count)