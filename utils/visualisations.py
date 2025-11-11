import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
import pandas as pd
import seaborn as sns


def plot_metal_demand_facets(
    df,
    variable_col="Variable",   # Column for technology breakdown (e.g. "Battery_type", "Mode")
    tech_colors=None,
    threshold=0.01,            # group techs < 1% within each metal into "Other"
    ncols=6,
    figsize=(14, 10),
    dpi=350,
    savepath=None,
    add_total_line=False,
):
    """
    Compact grid of stacked-bar subplots.
    One subplot per Metal, stacked by variable_col (e.g., technology, battery type, mode).
    Groups small categories below threshold into "Other".
    Generates unique pastel colors if tech_colors not provided.
    """

    # ---- Helper: unique color generator ----
    def generate_unique_colors(n):
        """Generate n visually distinct pastel colors."""
        hsv = [(i / n, 0.4 + 0.3*np.random.rand(), 0.9) for i in range(n)]
        rgb = [mcolors.hsv_to_rgb(h) for h in hsv]
        return [mcolors.to_hex(c) for c in rgb]

    # ---- Clean & guard ----
    d0 = df.copy()
    if variable_col not in d0.columns:
        raise KeyError(f"❌ Column '{variable_col}' not found in dataframe.")

    d0 = d0[d0["Metal"].notna() & d0[variable_col].notna()]
    d0["Metal"] = d0["Metal"].astype(str).str.strip()
    d0[variable_col] = d0[variable_col].astype(str).str.strip()
    d0["Year"] = d0["Year"].astype(int)

    # ---- Generate unique colors if none provided ----
    if tech_colors is None:
        unique_vars = sorted(d0[variable_col].unique())
        color_list = generate_unique_colors(len(unique_vars))
        tech_colors = dict(zip(unique_vars, color_list))
        if "Other" in tech_colors:
            tech_colors["Other"] = "#999999"

    # ---- Grid setup ----
    metals = sorted(d0["Metal"].unique().tolist())
    n_metals = len(metals)
    nrows = int(np.ceil(n_metals / ncols))

    fig, axes = plt.subplots(
        nrows=nrows, ncols=ncols, figsize=figsize, dpi=dpi, sharex=False, sharey=False
    )
    axes = axes.flatten()

    legend_labels = set()

    for i, metal in enumerate(metals):
        ax = axes[i]
        d_m = d0[d0["Metal"] == metal]

        # ---- Group small categories ----
        totals = d_m.groupby(variable_col)["Metal_demand_t"].sum().sort_values(ascending=False)
        share = totals / totals.sum() if totals.sum() != 0 else totals * 0
        small = share[share < threshold].index.tolist()

        d_m = d_m.copy()
        if len(small) > 0:
            d_m.loc[d_m[variable_col].isin(small), variable_col] = "Other"

        # ---- Pivot ----
        pivot = d_m.pivot_table(index="Year", columns=variable_col, values="Metal_demand_t",
                                aggfunc="sum", fill_value=0).sort_index()

        # ---- Skip empty subplots ----
        if pivot.sum().sum() == 0:
            ax.set_title(metal, fontsize=8, pad=1)
            ax.set_xticks([2020, 2030, 2040, 2050])
            ax.set_xticklabels(["2020", "2030", "2040", "2050"], fontsize=7)
            ax.tick_params(axis="y", labelsize=7)
            ax.grid(False)
            continue

        # ---- Determine colors ----
        cols = pivot.columns.tolist()
        bar_colors = [
            "#999999" if c == "Other" else tech_colors.get(c, "#cccccc") for c in cols
        ]

        # ---- Plot ----
        pivot.plot(kind="bar", stacked=True, ax=ax, color=bar_colors, width=0.9, legend=False)
        legend_labels.update(cols)

        # ---- Format ticks and title ----
        ax.tick_params(axis="x", labelrotation=0, labelsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(
                lambda x, p: f"{x/1e6:.0f}M" if x >= 1e6 else (f"{x/1e3:.0f}k" if x >= 1e3 else f"{int(x)}")
            )
        )
        years = pivot.index.tolist()
        tick_positions = np.arange(len(years))
        tick_labels = [str(y) if (y % 10 == 0) else "" for y in years]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, fontsize=7)
        ax.set_title(metal, fontsize=8, pad=1)
        ax.set_xlabel("")
        ax.set_ylabel("")

        if add_total_line:
            totals_by_year = pivot.sum(axis=1).values
            ax.plot(tick_positions, totals_by_year, linewidth=1.2, color="black", alpha=0.6)

    # ---- Remove unused axes ----
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    # ---- Global legend ----
    labels_sorted = sorted(list(legend_labels), key=lambda x: (x != "Other", x))
    handles = []
    for lab in labels_sorted:
        color = "#999999" if lab == "Other" else tech_colors.get(lab, "#cccccc")
        handles.append(Patch(facecolor=color, edgecolor="none", label=lab))

    if handles:
        fig.legend(
            handles=handles,
            labels=[h.get_label() for h in handles],
            loc="lower center",
            bbox_to_anchor=(0.5, 0.01),
            ncol=min(len(handles), 8),
            fontsize=8,
            frameon=False,
        )

    fig.tight_layout(rect=[0, 0.05, 1, 0.97])
    fig.subplots_adjust(hspace=0.5, wspace=0.2, bottom=0.14)

    if savepath:
        fig.savefig(f"{savepath}.png", bbox_inches="tight")
        fig.savefig(f"{savepath}.svg", bbox_inches="tight")
        print(f"✅ Saved to {savepath}.png / .svg")

    plt.show()



def plot_metal_demand_stackplots(
    df,
    variable_col="Variable",
    metal_colors=None,
    tech_colors=None,
    figsize=(8, 12),
    dpi=350,
    ncol_legend=4,
    threshold=0.01,
    savepath=None,
):
    """
    Plot two stacked area charts:
    (1) total metal demand by variable_col (e.g. technology, mode, battery type)
    (2) total metal demand by metal
    Small categories (< threshold of total) are grouped as 'Other'.
    If color dicts are missing, generate distinct random colors.
    """

    # ---- Helper to group small contributors ----
    def group_small_categories(df_pivot, threshold):
        total_all = df_pivot.sum(axis=1).sum()
        total_per_cat = df_pivot.sum()
        share = total_per_cat / total_all
        small_cats = share[share < threshold].index
        if len(small_cats) > 0:
            df_grouped = df_pivot.copy()
            df_grouped["Other"] = df_pivot[small_cats].sum(axis=1)
            df_grouped = df_grouped.drop(columns=small_cats)
        else:
            df_grouped = df_pivot
        return df_grouped

    # ---- Helper to generate unique random colors ----
    def generate_unique_colors(n):
        """Generate n distinct pastel colors."""
        hsv = [(i / n, 0.5 + 0.3*np.random.rand(), 0.9) for i in range(n)]
        rgb = [mcolors.hsv_to_rgb(h) for h in hsv]
        return [mcolors.to_hex(c) for c in rgb]

    # ---- Guard / Clean ----
    d0 = df.copy()
    d0 = d0[d0["Metal"].notna()]
    if variable_col not in d0.columns:
        raise KeyError(f"❌ Column '{variable_col}' not found in dataframe.")
    d0 = d0[d0[variable_col].notna()]

    # ---- Prepare data ----
    data_var = d0.pivot_table(index="Year", columns=variable_col, values="Metal_demand_t", aggfunc="sum", fill_value=0)
    data_met = d0.pivot_table(index="Year", columns="Metal", values="Metal_demand_t", aggfunc="sum", fill_value=0)

    # ---- Apply grouping ----
    data_var = group_small_categories(data_var, threshold)
    data_met = group_small_categories(data_met, threshold)

    # ---- Generate unique colors ----
    if tech_colors is None:
        color_list = generate_unique_colors(len(data_var.columns))
        tech_colors = dict(zip(data_var.columns, color_list))
        if "Other" in tech_colors:
            tech_colors["Other"] = "#999999"

    if metal_colors is None:
        color_list = generate_unique_colors(len(data_met.columns))
        metal_colors = dict(zip(data_met.columns, color_list))
        if "Other" in metal_colors:
            metal_colors["Other"] = "#999999"

    # ---- Figure ----
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, dpi=dpi, sharex=True)

    # ---- 1️⃣ By Variable ----
    colors_var = [tech_colors.get(v, "#cccccc") for v in data_var.columns]
    ax1.stackplot(data_var.index, data_var.T, labels=data_var.columns, colors=colors_var)
    ax1.set_title(f"Total metal demand by {variable_col}", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Metal demand (t)")
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=ncol_legend, frameon=False, fontsize=9)

    # ---- 2️⃣ By Metal ----
    colors_met = [metal_colors.get(m, "#cccccc") for m in data_met.columns]
    ax2.stackplot(data_met.index, data_met.T, labels=data_met.columns, colors=colors_met)
    ax2.set_title("Total metal demand by metal", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Metal demand (t)")
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=ncol_legend, frameon=False, fontsize=9)

    # ---- Layout ----
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.subplots_adjust(hspace=0.5)

    if savepath:
        fig.savefig(f"{savepath}.png", bbox_inches="tight")
        fig.savefig(f"{savepath}.svg", bbox_inches="tight")
        print(f"✅ Figure saved to {savepath}.png and .svg")

    plt.show()



def plot_masse_stats_per_clas(df, col_clas="CLAS", col_mass="MASSE_NETTE"):
    """
    Compute summary statistics and plot a styled boxplot of mass per CLAS.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing at least columns for class and mass.
    col_clas : str, default="CLAS"
        Column name for the vehicle class.
    col_mass : str, default="MASSE_NETTE"
        Column name for the vehicle mass (numeric).
    """
    # Ensure numeric
    df = df.copy()
    df[col_mass] = pd.to_numeric(df[col_mass], errors="coerce")
    df = df.dropna(subset=[col_clas, col_mass])

    # Summary stats
    summary = df.groupby(col_clas)[col_mass].agg(
        Mean="mean",
        Median="median",
        Min="min",
        Max="max",
        Count="count",
        Q25=lambda x: x.quantile(0.25),
        Q75=lambda x: x.quantile(0.75),
    ).sort_values("Mean", ascending=False)

    # --- Plot ---
    plt.figure(figsize=(12, 10))
    sns.boxplot(x=col_clas, y=col_mass, data=df, showfliers=False, palette="Set3")

    # Add number of samples above each box
    counts = df[col_clas].value_counts()
    positions = range(len(counts))
    for pos, clas in enumerate(counts.index):
        plt.text(pos, df.loc[df[col_clas]==clas, col_mass].max() * 1.02,
                 f"n={counts[clas]}", ha="center", fontsize=9, color="black")

    plt.xticks(rotation=90)
    plt.title("Distribution of Vehicle Mass (MASSE_NETTE) per CLAS")
    plt.xlabel("CLAS")
    plt.ylabel("MASSE_NETTE (kg)")
    plt.tight_layout()
    plt.show()

    return summary