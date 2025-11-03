import pandas as pd
import brightway2 as bw
import bw2analyzer as ba
import bw2calc as bc
import bw2data as bd
import bw2io as bi
import brightway2 as bw
import pandas as pd

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


def first_tier_contributions(activity, commodity_label, method_id,
                                     amount=1, threshold=0.01):
    """
    Builds a DataFrame of direct (first‑tier) technosphere contributions
    for one commodity, filtered by a percentage cutoff of total endpoint impact.

    Parameters
    ----------
    activity : brightway2 Activity
        The target activity.
    commodity_label : str
        Name of the commodity (for the 'Commodity' column).
    method_id : tuple or str
        The LCIA method identifier (e.g., a triple for IW+ endpoint).
    amount : float
        Functional unit for the target activity.
    threshold : float (0-1)
        Fraction of total impact; only include providers with share >= threshold.

    Returns
    -------
    pd.DataFrame with columns:
      - Commodity     (str)
      - Activity      (provider name)
      - Product       (provider reference product)
      - Location      (provider location)
      - Impact_score  (absolute contribution to endpoint)
      - Share_%       (percentage of total endpoint impact)
    """
    # 1) compute total endpoint impact of the main activity
    lca_main = bw.LCA({activity.key: amount})
    lca_main.lci()
    lca_main.switch_method(method_id)
    lca_main.lcia()
    total_score = lca_main.score or 1e-30

    rows = []
    # 2) loop direct technosphere inputs
    for exc in activity.technosphere():
        provider = exc.input
        unit_amt = getattr(exc, "amount", exc.get("amount", 1))

        # 3) pull provider details
        name     = provider.get("name", "<unknown>")
        product  = provider.get("reference product", "<unknown>")
        location = provider.get("location", "<unknown>")

        # 4) run LCA on provider to get its unit CF
        lca_p = bw.LCA({provider.key: 1})
        lca_p.lci()
        lca_p.switch_method(method_id)
        lca_p.lcia()
        cf_unit = lca_p.score

        # 5) compute contribution & share
        contr = cf_unit * unit_amt * amount
        share_frac = contr / total_score  # fraction of total
        share_pct = share_frac * 100      # percent

        if share_frac >= threshold:
            rows.append({
                "Commodity":     commodity_label,
                "Activity":      name,
                "Product":       product,
                "Location":      location,
                "Impact_score":  contr,
                "Share_%":       share_pct
            })

    # 6) assemble and sort
    df = pd.DataFrame(rows)
    return df.sort_values("Share_%", ascending=False).reset_index(drop=True)