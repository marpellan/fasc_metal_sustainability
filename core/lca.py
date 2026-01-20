import brightway2 as bw
import pandas as pd
from brightway2 import Database
from brightway2 import LCA
import numpy as np


# ======================================================
# LCA stuff
# ======================================================

def get_inventory_dataset(inventories, database_names):
    """
    Function from Istrate et al (2024) to find the dataset in the specified databases.

    :param inventories: dict in the format (mineral name: activity name, reference product, location)
    :param database_names: must be a list
    :return df:
    """
    inventory_ds = {}
    for rm_name, (activity_name, ref_product, location) in inventories.items():
        match_found = False

        # Iterate over the list of database names
        for database_name in database_names:
            db = bw.Database(database_name)
            matches = [ds for ds in db if ds["name"] == activity_name
                       and ds["reference product"] == ref_product
                       and ds["location"] == location]

            if matches:
                inventory_ds[rm_name] = matches[0]
                match_found = True
                break  # Stop searching once a match is found

        if not match_found:
            print(f"No match found for {rm_name} in provided databases")
    return inventory_ds


def run_lca(inventories, amount, lcia_methods):
    """
    Compute LCA scores for multiple inventories and multiple methods.

    Returns a DataFrame indexed by inventory label, columns = "Impact name (unit)".
    """
    # canonicalize methods dict
    if isinstance(lcia_methods, list):
        # expect tuples like (method_id, ..., label)
        lcia_methods = {tpl[2]: tpl[0] for tpl in lcia_methods}
    if not isinstance(lcia_methods, dict):
        raise TypeError("lcia_methods must be dict or list of tuples")

    results = {}
    for label, activity in inventories.items():
        # one LCA object per activity
        lca = bw.LCA({activity.key: amount})
        lca.lci()
        row = {}
        for imp_label, method_id in lcia_methods.items():
            lca.switch_method(method_id)
            lca.lcia()
            unit = bw.Method(method_id).metadata.get("unit", "")
            row[f"{imp_label} ({unit})"] = lca.score
        results[label] = row

    df = pd.DataFrame.from_dict(results, orient="index")
    df.index.name = "Commodity"
    return df.reset_index()


def compute_midpoint_contributions(
    inventories,
    amount=1,
    damage_version="IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10"
):
    """
    For each activity in `inventories`, computes midpoint→endpoint damage shares
    for IW+ 2.1 Human health and Ecosystem quality.

    Returns
    -------
    df_hh : pd.DataFrame
        rows = Commodity, columns = each Human health midpoint, values = share of total HH damage
    df_eq : pd.DataFrame
        rows = Commodity, columns = each Ecosystem quality midpoint, values = share of total EQ damage
    """
    # 1) grab all triples for that damage version
    all_damage = [m for m in bw.methods if m[0] == damage_version]

    # 2) identify endpoint / midpoint lists per category
    categories = ["Human health", "Ecosystem quality"]
    endpoints = {
        cat: next(
            m for m in all_damage
            if m[1] == cat and m[2].lower().startswith("total")
        )
        for cat in categories
    }
    midpoints = {
        cat: [
            m for m in all_damage
            if m[1] == cat and not m[2].lower().startswith("total")
        ]
        for cat in categories
    }

    # 3) loop over inventories, fill dicts
    hh_shares = {}
    eq_shares = {}

    for comm, activity in inventories.items():
        lca = bw.LCA({activity.key: amount})
        lca.lci()

        # temporary storage per commodity
        tmp = {}

        for cat in categories:
            # compute total
            lca.switch_method(endpoints[cat])
            lca.lcia()
            total = lca.score or 1e-30

            # compute each midpoint share
            shares = {}
            for mid in midpoints[cat]:
                lca.switch_method(mid)
                lca.lcia()
                shares[mid[2]] = lca.score / total

            tmp[cat] = shares

        hh_shares[comm] = tmp["Human health"]
        eq_shares[comm] = tmp["Ecosystem quality"]

    # 4) build DataFrames
    df_hh = pd.DataFrame.from_dict(hh_shares, orient="index")\
             .reset_index()\
             .rename(columns={"index": "Commodity"})

    df_eq = pd.DataFrame.from_dict(eq_shares, orient="index")\
             .reset_index()\
             .rename(columns={"index": "Commodity"})

    return df_hh, df_eq


def setup_activities(lci_df):
    """
    Map (Scenario, Year, Metal) -> Brightway activity based on:
        DB_to_map, Activity, Reference Product, Location
    """

    activities_dict = {}

    for idx, row in lci_df.iterrows():
        scenario = row["Scenario"]
        year = str(row["Year"])
        metal = row["Metal"]

        db_name = row["DB_to_map"]
        act_name = row["Activity"]
        ref_product = row["Reference Product"]
        location = row["Location"]

        key = (scenario, year, metal)

        try:
            db = Database(db_name)

            # --- 1) Match exact name ---
            candidates = [
                act for act in db
                if act["name"] == act_name
            ]

            # --- 2) Match reference product ---
            candidates = [
                act for act in candidates
                if act.get("reference product", None) == ref_product
            ]

            # --- 3) Match location ---
            candidates = [
                act for act in candidates
                if act.get("location", None) == location
            ]

            activities_dict[key] = candidates[0] if candidates else None

        except Exception:
            activities_dict[key] = None

    return activities_dict


def run_scenario_lca(df_demand_agg, activities_dict, lcia_methods):
    """
    Compute scaled LCA results for each row in df_demand_agg.
    df_demand_agg must contain:
        scenario, year, metal, metal_demand_kg
    """

    results = []

    for idx, row in df_demand_agg.iterrows():
        scenario = row["Scenario"]
        year = str(row["Year"])
        metal = row["Metal"]
        qty = float(row["Metal_demand_kg"])

        key = (scenario, year, metal)
        activity = activities_dict.get(key, None)

        impact_results = {}

        if activity is None:
            for m in lcia_methods:
                impact_results[m[2]] = np.nan

        else:
            try:
                lca = LCA({activity: qty}, lcia_methods[0])
                lca.lci()

                for method in lcia_methods:
                    lca.switch_method(method)
                    lca.lcia()
                    impact_results[method[2]] = lca.score

            except:
                for m in lcia_methods:
                    impact_results[m[2]] = np.nan

        results.append({
            "Scenario": scenario,
            "Year": year,
            "Metal": metal,
            "Demand_kg": qty,
            **impact_results
        })

    return pd.DataFrame(results)