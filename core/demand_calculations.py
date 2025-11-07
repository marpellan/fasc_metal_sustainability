import pandas as pd

def disaggregate_capacity(df, mapping_dict,
                                           tech_col="Variable",
                                           cap_col="Value",
                                           new_col="Associated_MI"):
    """
    Expand capacity data by linking each CER technology to one or more MI sub-technologies.

    Keeps the original Variable column unchanged and adds a new column for the associated MI.
    The capacity is split across sub-technologies according to the specified shares.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe (e.g., ELEC_CAP_TECH).
    mapping_dict : dict
        { main_tech : [(mi_tech, share), ...] } mapping.
    tech_col : str
        Column containing CER technology names.
    cap_col : str
        Column with capacity values (GW).
    new_col : str
        New column name to store the associated MI bucket.

    Returns
    -------
    pd.DataFrame
        Disaggregated dataframe with added Associated_MI and scaled capacity values.
    """
    rows = []
    for _, row in df.iterrows():
        tech = row[tech_col]
        if tech in mapping_dict:
            for mi_tech, share in mapping_dict[tech]:
                new_row = row.copy()
                new_row[new_col] = mi_tech
                new_row[cap_col] = row[cap_col] * share
                rows.append(new_row)
        else:
            # Keep row unchanged but mark as unmapped
            new_row = row.copy()
            new_row[new_col] = tech  # or could be None
            rows.append(new_row)
    expanded_df = pd.DataFrame(rows)
    return expanded_df


def calculate_metal_demand(disagg_df, mi_df):
    """
    Merge energy capacity scenarios with metal intensity data and compute metal demand.
    Handles duplicates and missing data based on fiability ranking.

    Parameters
    ----------
    disagg_df : pd.DataFrame
        Must contain ['Scenario','Region','Variable','Year','Value','Unit','Associated_MI'].
        'Associated_MI' = "Technology, Sub-technology".
    mi_df : pd.DataFrame
        Must contain ['Technology','Sub-technology','Metal','Metal intensity','Fiability of the data'].

    Returns
    -------
    pd.DataFrame
        Combined dataset with metal demand in tonnes per scenario/year/metal.
    """

    df = disagg_df.copy()

    # Split technology and sub-tech
    tech_split = df["Associated_MI"].str.split(",", n=1, expand=True)
    df["Technology"] = tech_split[0].str.strip()
    df["Sub-technology"] = tech_split[1].str.strip().fillna("Aggregated")

    # Prepare metal intensity table
    mi = mi_df.copy()
    mi["Metal intensity"] = pd.to_numeric(mi["Metal intensity"], errors="coerce")

    # Define fiability ranking
    fiability_rank = {
        "Small variability in data": 1,
        "Variability in data": 2,
        "Important variability of data": 3,
        "No comparison": 4
    }
    mi["fiability_rank"] = mi["Fiability of the data"].map(fiability_rank).fillna(5)

    # Aggregate properly
    selected_rows = []
    for (tech, subtech, metal), group in mi.groupby(["Technology", "Sub-technology", "Metal"]):
        group = group.dropna(subset=["Metal intensity"])
        if group.empty:
            continue  # skip invalid entries

        best_rank = group["fiability_rank"].min()
        best_group = group[group["fiability_rank"] == best_rank]

        if best_group.empty:
            continue

        if len(best_group) > 1:
            avg_intensity = best_group["Metal intensity"].mean()
            comment = f"mean of {best_group.iloc[0]['Fiability of the data']}"
        else:
            avg_intensity = best_group["Metal intensity"].iloc[0]
            comment = best_group["Comment"].iloc[0] if pd.notna(best_group["Comment"].iloc[0]) else None

        selected_rows.append({
            "Technology": tech,
            "Sub-technology": subtech,
            "Metal": metal,
            "Metal intensity (t/GW)": avg_intensity,
            "Fiability_used": best_group.iloc[0]["Fiability of the data"],
            "Comment": comment
        })

    mi_clean = pd.DataFrame(selected_rows)

    # Merge
    merged = df.merge(mi_clean, on=["Technology", "Sub-technology"], how="left")

    # Compute metal demand
    merged["Metal_demand_t"] = merged["Value"] * merged["Metal intensity (t/GW)"]

    # Final clean-up
    merged = merged[
        ["Scenario", "Region", "Year", "Variable", "Metal",
         "Metal intensity (t/GW)", "Metal_demand_t", "Fiability_used", "Comment"]
    ]

    return merged


# Compute growth for each scenario per year, assuming 2024 value is the base
def compute_ev_growth(ev_df, base_year=2024):
    ev_growth_df = ev_df.copy()
    for scenario in ev_growth_df['Scenario'].unique():
        base_value = ev_growth_df[(ev_growth_df['Scenario'] == scenario) & (ev_growth_df['Year'] == base_year)]['Value'].values[0]
        ev_growth_df.loc[ev_growth_df['Scenario'] == scenario, 'Growth_Factor'] = ev_growth_df.loc[ev_growth_df['Scenario'] == scenario, 'Value'] / base_value
    return ev_growth_df[['Scenario', 'Year', 'Growth_Factor']]


# Multiple ev_df with growth factors for each scenario and year
# Create function to apply growth factor to 2024 EV sales across scenarios and years
def project_ev_sales(ev_df, ev_growth_df):
    # Filter the base year (2024) data
    base_year_df = ev_df[ev_df["Year"] == 2024].copy()

    # Prepare to store results
    projections = []

    # Loop through each scenario
    for scenario in ev_growth_df["Scenario"].unique():
        scenario_growth = ev_growth_df[ev_growth_df["Scenario"] == scenario]

        for _, growth_row in scenario_growth.iterrows():
            year = growth_row["Year"]
            factor = growth_row["Growth_Factor"]

            # Apply the growth factor to the base EV sales data
            projected = base_year_df.copy()
            projected["Scenario"] = scenario
            projected["Year"] = year
            projected["Value"] = projected["Value"] * factor

            projections.append(projected)

    # Combine all projections into a single DataFrame
    result_df = pd.concat(projections, ignore_index=True)
    return result_df

