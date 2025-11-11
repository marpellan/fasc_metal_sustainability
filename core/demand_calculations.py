import pandas as pd

def disaggregate_nrj_capacity(df, mapping_dict,
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


def apply_chemistry_mix(ev_df, chem_df):
    """
    Expand EV installed capacity data by chemistry mix, keeping all original columns.

    Parameters
    ----------
    ev_df : DataFrame
        Must include at least ['Mode', 'Year', 'Installed_battery_cap'].
    chem_df : DataFrame
        Must include ['Mode', 'Battery_type', year columns (as int)].
        Scenario column is ignored if present.

    Returns
    -------
    DataFrame
        Same columns as ev_df + 'Battery_type' and updated 'Installed_battery_cap'
        values for each chemistry (plus a row 'All' for total).
    """
    df = ev_df.copy()
    chem = chem_df.copy()

    # --- Clean chemistry dataframe ---
    chem.columns = chem.columns.map(str)
    chem = chem.drop(columns=[c for c in chem.columns if c.lower() == "scenario"], errors="ignore")

    # Long format (Mode, Battery_type, Year, Share)
    chem_long = chem.melt(
        id_vars=["Mode", "Battery_type"],
        var_name="Year",
        value_name="Share"
    )
    chem_long["Year"] = chem_long["Year"].astype(int)

    # Interpolate missing years
    all_years = pd.DataFrame({"Year": range(df["Year"].min(), df["Year"].max() + 1)})
    interpolated = []
    for (mode, chem_type), group in chem_long.groupby(["Mode", "Battery_type"]):
        merged = all_years.merge(group, on="Year", how="left")
        merged["Mode"] = mode
        merged["Battery_type"] = chem_type.replace("Gr-", "")
        merged["Share"] = merged["Share"].interpolate(limit_direction="both")
        interpolated.append(merged)

    chem_interp = pd.concat(interpolated, ignore_index=True)

    # Merge EV installed capacity with chemistry shares
    merged = df.merge(chem_interp, on=["Mode", "Year"], how="left")

    # Multiply capacity × share
    merged["Installed_battery_cap"] = merged["Installed_battery_cap"] * merged["Share"]

    # Drop share column
    merged = merged.drop(columns=["Share"])

    # Add the total rows ("All")
    total_rows = df.copy()
    total_rows["Battery_type"] = "All"

    # Combine
    result = pd.concat([total_rows, merged], ignore_index=True)

    # Reorder so Battery_type appears after Mode/Powertrain
    insert_pos = list(result.columns).index("Mode") + 1
    cols = result.columns.tolist()
    cols.remove("Battery_type")
    cols.insert(insert_pos, "Battery_type")
    result = result[cols]

    return result

def calculate_metal_demand_nrj(disagg_df, mi_df):
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


def calculate_metal_demand_ev_battery(ev_df, mi_df, mapping_dict):
    """
    Compute metal demand for each Battery_type in the EV dataset.
    Compatible with mappings like {"LFP": [("Vehicle battery, LFP", 1.0)]}.

    Parameters
    ----------
    ev_df : pd.DataFrame
        Must include ['Battery_type', 'Installed_battery_cap'] (capacity in kWh).
    mi_df : pd.DataFrame
        Must include ['Technology','Sub-technology','Metal','Metal intensity','Fiability of the data'].
    mapping_dict : dict
        Maps Battery_type -> [(Technology, Sub-technology)] or [(single string, weight)].

    Returns
    -------
    pd.DataFrame
        ev_df + metal-specific demand (tonnes) per row, with Fiability_used and Comment columns.
    """
    df = ev_df.copy()
    mi = mi_df.copy()
    mi["Metal intensity"] = pd.to_numeric(mi["Metal intensity"], errors="coerce")

    # --- Fiability ranking ---
    fiability_rank = {
        "Small variability in data": 1,
        "Variability in data": 2,
        "Important variability of data": 3,
        "No comparison": 4
    }
    mi["fiability_rank"] = mi["Fiability of the data"].map(fiability_rank).fillna(5)

    # --- Select best or averaged intensity per Tech/Sub-tech/Metal ---
    selected_rows = []
    for (tech, subtech, metal), group in mi.groupby(["Technology", "Sub-technology", "Metal"]):
        group = group.dropna(subset=["Metal intensity"])
        if group.empty:
            continue
        best_rank = group["fiability_rank"].min()
        best_group = group[group["fiability_rank"] == best_rank]

        if len(best_group) > 1:
            avg_intensity = best_group["Metal intensity"].mean()
            comment = f"mean of {best_group.iloc[0]['Fiability of the data']}"
        else:
            avg_intensity = best_group["Metal intensity"].iloc[0]
            comment = (
                best_group["Comment"].iloc[0]
                if "Comment" in best_group.columns and pd.notna(best_group["Comment"].iloc[0])
                else None
            )

        selected_rows.append({
            "Technology": str(tech),
            "Sub-technology": str(subtech),
            "Metal": metal,
            "Metal intensity (g/kWh)": avg_intensity,
            "Fiability_used": best_group.iloc[0]["Fiability of the data"],
            "Comment": comment
        })

    mi_clean = pd.DataFrame(selected_rows)

    # --- Expand Battery_type mapping ---
    map_rows = []
    for batt_type, mapping_list in mapping_dict.items():
        for tech_entry, weight in mapping_list:
            if "," in tech_entry:
                tech, subtech = [x.strip() for x in tech_entry.split(",", 1)]
            else:
                tech, subtech = tech_entry.strip(), "Aggregated"
            map_rows.append({
                "Battery_type": batt_type,
                "Technology": tech,
                "Sub-technology": subtech,
                "Weight": weight
            })
    map_df = pd.DataFrame(map_rows)

    # --- Merge ---
    merged = df.merge(map_df, on="Battery_type", how="left")

    # Ensure consistent dtype
    for col in ["Technology", "Sub-technology"]:
        merged[col] = merged[col].astype(str)
        mi_clean[col] = mi_clean[col].astype(str)

    merged = merged.merge(mi_clean, on=["Technology", "Sub-technology"], how="left")

    # --- Compute metal demand (convert g/kWh → tonnes) ---
    merged["Metal_demand_t"] = (
        merged["Installed_battery_cap"] * merged["Metal intensity (g/kWh)"] / 1000000
    )

    # --- Final column ordering ---
    cols = list(ev_df.columns) + [
        "Technology", "Sub-technology", "Metal",
        "Metal intensity (g/kWh)", "Metal_demand_t",
        "Fiability_used", "Comment"
    ]
    merged = merged[cols]

    return merged


def calculate_metal_demand_ev_body(ev_sales_df, mi_df, mapping_dict, main_var="Sales"):
    """
    Compute metal demand for each Powertrain (e.g., BEV, PHEV, FCEV) in the EV body dataset.

    Parameters
    ----------
    ev_sales_df : pd.DataFrame
        Must include ['Powertrain', main_var] (number of vehicles or total sales in the unit).
    mi_df : pd.DataFrame
        Must include ['Technology','Sub-technology','Metal','Metal intensity','Fiability of the data','Comment'].
        Metal intensity should be in kg/vehicle (or convertible unit).
    mapping_dict : dict
        Maps Powertrain -> [(Technology, Sub-technology, weight)].
        e.g. {"BEV": [("Vehicle body, BEV", 1.0)], "FCEV": [("Vehicle body, ICEV", 1.0)]}
    main_var : str
        Column containing the number of vehicles (default: 'Sales').

    Returns
    -------
    pd.DataFrame
        ev_sales_df + metal-specific demand (tonnes) per row, with Fiability_used and Comment columns.
    """

    import pandas as pd

    df = ev_sales_df.copy()
    mi = mi_df.copy()
    mi["Metal intensity"] = pd.to_numeric(mi["Metal intensity"], errors="coerce")

    # --- Fiability ranking ---
    fiability_rank = {
        "Small variability in data": 1,
        "Variability in data": 2,
        "Important variability of data": 3,
        "No comparison": 4
    }
    mi["fiability_rank"] = mi["Fiability of the data"].map(fiability_rank).fillna(5)

    # --- Select best/averaged MI ---
    selected_rows = []
    for (tech, subtech, metal), group in mi.groupby(["Technology", "Sub-technology", "Metal"]):
        group = group.dropna(subset=["Metal intensity"])
        if group.empty:
            continue
        best_rank = group["fiability_rank"].min()
        best_group = group[group["fiability_rank"] == best_rank]
        if len(best_group) > 1:
            avg_intensity = best_group["Metal intensity"].mean()
            comment = f"mean of {best_group.iloc[0]['Fiability of the data']}"
        else:
            avg_intensity = best_group["Metal intensity"].iloc[0]
            comment = (
                best_group["Comment"].iloc[0]
                if "Comment" in best_group.columns and pd.notna(best_group["Comment"].iloc[0])
                else None
            )
        selected_rows.append({
            "Technology": str(tech),
            "Sub-technology": str(subtech),
            "Metal": metal,
            "Metal intensity (g/vehicle)": avg_intensity,
            "Fiability_used": best_group.iloc[0]["Fiability of the data"],
            "Comment": comment
        })
    mi_clean = pd.DataFrame(selected_rows)

    # --- Expand Powertrain mapping ---
    map_rows = []
    for pt, mapping_list in mapping_dict.items():
        for tech_entry, weight in mapping_list:
            if "," in tech_entry:
                tech, subtech = [x.strip() for x in tech_entry.split(",", 1)]
            else:
                tech, subtech = tech_entry.strip(), "Aggregated"
            map_rows.append({
                "Powertrain": pt,
                "Technology": tech,
                "Sub-technology": subtech,
                "Weight": weight
            })
    map_df = pd.DataFrame(map_rows)

    # --- Merge ---
    merged = df.merge(map_df, on="Powertrain", how="left")
    merged = merged.merge(mi_clean, on=["Technology", "Sub-technology"], how="left")

    # --- Compute metal demand ---
    merged["Metal_demand_t"] = merged[main_var] * merged['Mass_vehicule'] * merged["Metal intensity (g/vehicle)"] / 1000000

    # --- Column order ---
    cols = list(ev_sales_df.columns) + [
        "Technology", "Sub-technology", "Metal",
        "Metal intensity (g/vehicle)", "Metal_demand_t",
        "Fiability_used", "Comment"
    ]
    merged = merged[cols]

    return merged
