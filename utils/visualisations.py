def plot_metal_demand_stackplots(
    df,
    metal_colors,
    tech_colors,
    figsize=(8, 12),
    dpi=350,
    ncol_legend=4,
    threshold=0.01,  # percentage threshold (e.g. 0.01 = 1%)
    savepath=None,
):
    """
    Plot two stacked area charts:
    (1) total metal demand by technology (Variable)
    (2) total metal demand by metal (Metal)
    Small categories (< threshold of total) are grouped as 'Other'.
    """
    import matplotlib.pyplot as plt
    import pandas as pd

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

    # ---- Prepare data ----
    data_var = df.pivot_table(
        index="Year", columns="Variable", values="Metal_demand_t",
        aggfunc="sum", fill_value=0
    )
    data_met = df.pivot_table(
        index="Year", columns="Metal", values="Metal_demand_t",
        aggfunc="sum", fill_value=0
    )

    # ---- Apply grouping ----
    data_var = group_small_categories(data_var, threshold)
    data_met = group_small_categories(data_met, threshold)

    # ---- Figure ----
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, dpi=dpi, sharex=True)

    # ---- 1️⃣ By Variable ----
    colors_var = [tech_colors.get(v, "#cccccc") for v in data_var.columns]
    if "Other" in data_var.columns:
        colors_var[data_var.columns.get_loc("Other")] = "#999999"

    ax1.stackplot(data_var.index, data_var.T, labels=data_var.columns, colors=colors_var)
    ax1.set_title("Total metal demand by technology", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Metal demand (t)")

    ax1.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        ncol=ncol_legend,
        frameon=False,
        fontsize=10,
    )

    # ---- 2️⃣ By Metal ----
    colors_met = [metal_colors.get(m, "#cccccc") for m in data_met.columns]
    if "Other" in data_met.columns:
        colors_met[data_met.columns.get_loc("Other")] = "#999999"

    ax2.stackplot(data_met.index, data_met.T, labels=data_met.columns, colors=colors_met)
    ax2.set_title("Total metal demand by metal", fontsize=12, fontweight="bold")
    #ax2.set_xlabel("Year")
    ax2.set_ylabel("Metal demand (t)")

    ax2.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        ncol=ncol_legend,
        frameon=False,
        fontsize=10,
    )

    # ---- Layout ----
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.subplots_adjust(hspace=0.5)

    # ---- Save ----
    if savepath:
        fig.savefig(f"{savepath}.png", bbox_inches="tight")
        fig.savefig(f"{savepath}.svg", bbox_inches="tight")
        print(f"✅ Figure saved to {savepath}.png and .svg")

    plt.show()
