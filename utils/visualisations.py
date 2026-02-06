import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
import pandas as pd
#import seaborn as sns
from matplotlib.ticker import FuncFormatter, AutoMinorLocator
import plotly.graph_objects as go



def plot_metal_demand_facets(
    df,
    variable_col="Variable",   # Column for technology breakdown (e.g. "Battery_type", "Mode")
    tech_colors=None,
    threshold=None,            # group techs < threshold within each metal into "Other"
    ncols=6,
    figsize=(14, 10),
    dpi=350,
    savepath=None,
    add_total_line=False,
    legend_ncol=4,             # wrap legend to avoid exceeding figure width
    legend_fontsize=14,
    sci_y_threshold=1e3,       # if ymax < this (and >0) -> use scientific notation for that subplot
):
    """
    Publication-ready grid of stacked-bar subplots (one subplot per Metal),
    stacked by variable_col (e.g., technology, battery type, mode).

    Style:
    - NO grid (robustly disabled even after pandas plotting)
    - Black contour (spines) around each subplot
    - Bold titles
    - Hide '0' label on y-axis
    - For small magnitudes (e.g., Yttrium), switch to scientific notation per subplot
    - Global legend wrapped (legend_ncol) to avoid exceeding figure width

    Expected columns in df:
    - Metal
    - Year
    - Metal_demand_t
    - variable_col
    """

    # ---- Helper: unique color generator ----
    def generate_unique_colors(n):

        cmap = plt.get_cmap("tab20")  # 20 couleurs qualitatives distinctes
        colors = [mcolors.to_hex(cmap(i)) for i in range(min(n, 20))]

        # si >20 catégories, on complète avec tab20b/tab20c (rare chez toi)
        if n > 20:
            cmap2 = plt.get_cmap("tab20b")
            colors += [mcolors.to_hex(cmap2(i)) for i in range(min(n - 20, 20))]
        if n > 40:
            cmap3 = plt.get_cmap("tab20c")
            colors += [mcolors.to_hex(cmap3(i)) for i in range(n - 40)]

        return colors[:n]

    # ---- Helper: style each axis (publication) ----
    def style_axis(ax):
        # Remove grids robustly (pandas can re-enable)
        ax.grid(False)
        ax.xaxis.grid(False)
        ax.yaxis.grid(False)

        # Black box around subplot
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color("black")
            spine.set_linewidth(0.8)

        # Ticks style
        ax.tick_params(axis="both", which="major", labelsize=7, length=3, width=0.7)
        ax.tick_params(axis="both", which="minor", length=2, width=0.5)

    # ---- Formatter: hide 0 label + compact units ----
    def y_formatter_no_zero(x, pos):
        if np.isclose(x, 0.0):
            return ""
        if x >= 1e6:
            return f"{x/1e6:.0f}M"
        if x >= 1e3:
            return f"{x/1e3:.0f}k"
        # Keep integers for small values (avoid "0.0")
        if abs(x - int(x)) < 1e-9:
            return f"{int(x)}"
        return f"{x:g}"

    # ---- Clean & guard ----
    d0 = df.copy()
    if variable_col not in d0.columns:
        raise KeyError(f"❌ Column '{variable_col}' not found in dataframe.")
    for col in ["Metal", "Year", "Metal_demand_t"]:
        if col not in d0.columns:
            raise KeyError(f"❌ Missing required column: '{col}'")

    d0 = d0[d0["Metal"].notna() & d0[variable_col].notna()]
    d0["Metal"] = d0["Metal"].astype(str).str.strip()
    d0[variable_col] = d0[variable_col].astype(str).str.strip()
    d0["Year"] = d0["Year"].astype(int)

    # ---- Colors ----
    if tech_colors is None:
        unique_vars = sorted(d0[variable_col].unique())
        tech_colors = dict(zip(unique_vars, generate_unique_colors(len(unique_vars))))
    # Force Other grey if present later
    tech_colors["Other"] = "#000000"

    # ---- Grid setup ----
    metals = sorted(d0["Metal"].unique().tolist())
    n_metals = len(metals)
    nrows = int(np.ceil(n_metals / ncols))

    fig, axes = plt.subplots(
        nrows=nrows, ncols=ncols, figsize=figsize, dpi=dpi,
        sharex=False, sharey=False
    )
    axes = np.array(axes).flatten()

    legend_labels = set()

    for i, metal in enumerate(metals):
        ax = axes[i]
        d_m = d0[d0["Metal"] == metal].copy()

        # ---- Group small categories into Other (within this metal) ----
        totals = d_m.groupby(variable_col)["Metal_demand_t"].sum().sort_values(ascending=False)
        denom = totals.sum()
        if denom > 0 and threshold is not None:
            share = totals / denom
            small = share[share < threshold].index.tolist()
            if small:
                d_m.loc[d_m[variable_col].isin(small), variable_col] = "Other"

        # ---- Pivot ----
        pivot = d_m.pivot_table(
            index="Year", columns=variable_col, values="Metal_demand_t",
            aggfunc="sum", fill_value=0
        ).sort_index()

        # ---- Empty subplot handling ----
        if pivot.to_numpy().sum() == 0:
            ax.set_title(metal, fontsize=8, fontweight="bold", pad=2)
            ax.set_xticks([2020, 2030, 2040, 2050])
            ax.set_xticklabels(["2020", "2030", "2040", "2050"], fontsize=7)
            ax.set_xlabel("")
            ax.set_ylabel("")
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(y_formatter_no_zero))
            style_axis(ax)
            continue

        # ---- Ensure "Other" plotted last if present ----
        if "Other" in pivot.columns:
            cols = [c for c in pivot.columns if c != "Other"] + ["Other"]
            pivot = pivot[cols]

        cols = pivot.columns.tolist()
        legend_labels.update(cols)

        bar_colors = [tech_colors.get(c, "#cccccc") for c in cols]

        # ---- Plot (pandas) ----
        pivot.plot(
            kind="bar",
            stacked=True,
            ax=ax,
            color=bar_colors,
            width=0.9,
            legend=False,
            linewidth=0,          # remove segment borders
            edgecolor="none"
        )

        # ---- Titles bold ----
        ax.set_title(metal, fontsize=8, fontweight="bold", pad=2)

        # ---- X ticks: show decades only ----
        years = pivot.index.tolist()
        tick_positions = np.arange(len(years))
        tick_labels = [str(y) if (y % 10 == 0) else "" for y in years]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, fontsize=7, rotation=0)

        # ---- Y formatting: scientific for very small magnitudes ----
        ymax = float(pivot.to_numpy().max())
        if (ymax > 0) and (ymax < sci_y_threshold):
            ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            ax.yaxis.get_offset_text().set_size(7)
            # hide 0 label even in sci mode
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, p: "" if np.isclose(x, 0.0) else f"{x:g}")
            )
        else:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(y_formatter_no_zero))

        ax.set_xlabel("")
        ax.set_ylabel("")

        # Optional total line
        if add_total_line:
            totals_by_year = pivot.sum(axis=1).values
            ax.plot(tick_positions, totals_by_year, linewidth=1.0, color="black", alpha=0.6)

        # ---- Force style AFTER plotting (kills unwanted grids) ----
        style_axis(ax)

    # ---- Remove unused axes ----
    for j in range(n_metals, len(axes)):
        fig.delaxes(axes[j])

    # ---- Global legend ----
    labels_sorted = sorted(list(legend_labels), key=lambda x: (x == "Other", x))  # Other last
    handles = [
        Patch(facecolor=tech_colors.get(lab, "#cccccc"), edgecolor="none", label=lab)
        for lab in labels_sorted
    ]

    if handles:
        fig.legend(
            handles=handles,
            labels=[h.get_label() for h in handles],
            loc="lower center",
            bbox_to_anchor=(0.5, -0.03),
            ncol=min(len(handles), legend_ncol),
            fontsize=legend_fontsize,
            frameon=False,
            handlelength=1.2,
            columnspacing=0.9,
        )

    # Layout
    fig.tight_layout(rect=[0, 0.06, 1, 0.98])
    fig.subplots_adjust(hspace=0.45, wspace=0.20, bottom=0.14)

    if savepath:
        fig.savefig(f"{savepath}.pdf", bbox_inches="tight")
        print(f"✅ Saved to {savepath}.pdf")


def plot_metal_demand_stackplots(
    df,
    variable_col="Variable",
    metal_colors=None,
    tech_colors=None,
    figsize=(15, 6),
    dpi=600,
    ncol_legend_left=3,
    ncol_legend_right=3,
    threshold_tech=0.05,      # aggregate small tech categories into "Other" (left only)
    threshold_metal=None,     # keep metals separate by default (right)
    savepath=None,
):
    """
    Publication-ready side-by-side stacked area charts:
    (1) total metal demand by variable_col (Technology / Mode / Battery type, etc.)
    (2) total metal demand by metal

    Features:
    - side-by-side layout
    - bold titles
    - black contour (spines) around each subplot
    - no grid
    - remove white seams between stacked areas (edgecolor none)
    - y ticks on both subplots (including right side ticks), but ylabel only on left
    - hide '0' tick label on y-axis
    - optional aggregation into "Other" ONLY for left subplot (threshold_tech)
    - metals kept separate unless threshold_metal is provided

    Expected columns in df:
    - Year
    - Metal
    - Metal_demand_t
    - variable_col (default "Variable")
    """

    # ---- Helper to group small contributors ----
    def group_small_categories(df_pivot, threshold):
        if threshold is None:
            return df_pivot
        total_all = df_pivot.to_numpy().sum()
        if total_all == 0:
            return df_pivot

        total_per_cat = df_pivot.sum(axis=0)
        share = total_per_cat / total_all
        small_cats = share[share < threshold].index

        if len(small_cats) == 0:
            return df_pivot

        df_grouped = df_pivot.copy()
        df_grouped["Other"] = df_pivot[small_cats].sum(axis=1)
        df_grouped = df_grouped.drop(columns=small_cats)
        return df_grouped

    # ---- Helper to generate unique colors ----
    def generate_unique_colors(n):
        """Generate n distinct pastel-ish colors."""
        n = max(int(n), 1)
        hsv = [(i / n, 0.55 + 0.25 * np.random.rand(), 0.92) for i in range(n)]
        rgb = [mcolors.hsv_to_rgb(h) for h in hsv]
        return [mcolors.to_hex(c) for c in rgb]

    # ---- Guard / Clean ----
    d0 = df.copy()
    if "Metal" not in d0.columns or "Year" not in d0.columns or "Metal_demand_t" not in d0.columns:
        raise KeyError("❌ df must contain columns: 'Year', 'Metal', 'Metal_demand_t'.")

    d0 = d0[d0["Metal"].notna()]
    if variable_col not in d0.columns:
        raise KeyError(f"❌ Column '{variable_col}' not found in dataframe.")
    d0 = d0[d0[variable_col].notna()]

    # ---- Prepare data (pivot) ----
    data_var = d0.pivot_table(
        index="Year", columns=variable_col, values="Metal_demand_t",
        aggfunc="sum", fill_value=0
    ).sort_index()

    data_met = d0.pivot_table(
        index="Year", columns="Metal", values="Metal_demand_t",
        aggfunc="sum", fill_value=0
    ).sort_index()

    # ---- Apply grouping (LEFT only by default) ----
    data_var = group_small_categories(data_var, threshold_tech)
    data_met = group_small_categories(data_met, threshold_metal)

    # ---- Keep "Other" last if present ----
    def move_other_last(df_pivot):
        if "Other" in df_pivot.columns:
            cols = [c for c in df_pivot.columns if c != "Other"] + ["Other"]
            return df_pivot[cols]
        return df_pivot

    data_var = move_other_last(data_var)
    data_met = move_other_last(data_met)

    # ---- Colors ----
    if tech_colors is None:
        tech_colors = dict(zip(data_var.columns, generate_unique_colors(len(data_var.columns))))
    if metal_colors is None:
        metal_colors = dict(zip(data_met.columns, generate_unique_colors(len(data_met.columns))))

    # Force "Other" to grey if present
    if "Other" in data_var.columns:
        tech_colors["Other"] = "#999999"
    if "Other" in data_met.columns:
        metal_colors["Other"] = "#999999"

    # ---- Formatter: hide 0 label on y-axis ----
    def hide_zero_formatter(x, pos):
        return "" if np.isclose(x, 0.0) else f"{x:g}"
    yfmt = FuncFormatter(hide_zero_formatter)

    # ---- Axis styling ----
    def style_axis(ax, show_ylabel=False):
        ax.grid(False)

        # black contour around each subplot
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.9)
            spine.set_color("black")

        # ticks (major + minor), and show ticks on the right side too
        ax.minorticks_on()
        ax.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax.tick_params(axis="both", labelsize=12)
        ax.tick_params(axis="y", which="major", length=4, width=0.8, left=True, right=False)
        ax.tick_params(axis="y", which="minor", length=2, width=0.6, left=True, right=False)

        ax.yaxis.set_major_formatter(yfmt)

        if show_ylabel:
            ax.set_ylabel("tonnes", fontsize=14)
        else:
            ax.set_ylabel("")

    # ---- Figure ----
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=figsize, dpi=dpi, sharex=True, sharey=True
    )

    # ---- 1) By variable (Technology) ----
    colors_var = [tech_colors.get(v, "#cccccc") for v in data_var.columns]
    ax1.stackplot(
        data_var.index, data_var.T,
        labels=data_var.columns,
        colors=colors_var,
        edgecolor="none", linewidth=0, antialiased=True,   # remove white seams
    )
    #ax1.set_title(f"Total metal demand by {variable_col}", fontsize=11, fontweight="bold", pad=8)
    style_axis(ax1, show_ylabel=True)

    ax1.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=ncol_legend_left,
        frameon=False,
        fontsize=14,
        handlelength=1.2,
        columnspacing=1.0,
        borderaxespad=0.0,
    )

    # ---- 2) By metal ----
    colors_met = [metal_colors.get(m, "#cccccc") for m in data_met.columns]
    ax2.stackplot(
        data_met.index, data_met.T,
        labels=data_met.columns,
        colors=colors_met,
        edgecolor="none", linewidth=0, antialiased=True,   # remove white seams
    )
    #ax2.set_title("Total metal demand by metal", fontsize=11, fontweight="bold", pad=8)
    style_axis(ax2, show_ylabel=False)

    ax2.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=ncol_legend_right,
        frameon=False,
        fontsize=14,
        handlelength=1.2,
        columnspacing=1.0,
        borderaxespad=0.0,
    )

    # ---- Layout: reserve bottom space for legends ----
    fig.subplots_adjust(wspace=0.05, bottom=0.28, top=0.90)

    if savepath:
        #fig.savefig(f"{savepath}.png", bbox_inches="tight")
        #fig.savefig(f"{savepath}.svg", bbox_inches="tight")
        fig.savefig(f"{savepath}.pdf", bbox_inches="tight")
        print(f"✅ Figure saved to {savepath}.png, .svg and .pdf")


def plot_sankey_cumulative_tech_metal(
    df,
    value_col="Metal_demand_t",
    scenario=None,
    country=None,
    year_min=None,
    year_max=None,
    top_n_metals=None,
    top_n_techs=None,
    output_html="sankey_cumulative_tech_metal.html",
    output_pdf=None,                 # optional PDF path (requires kaleido)
    pdf_width=2200,                  # bigger for publication
    pdf_height=1300,
    # style
    template="plotly_white",
    tech_node_color="rgba(210,210,210,1.0)",
    link_alpha=0.55,
    metal_color_map=None,            # dict: {"Copper":"rgba(...)", ...} optional
    font_size=22,                    # bigger labels
    node_thickness=20,
    node_pad=18,
    # keep labels inside canvas (avoid clipping)
    domain_x=(0.02, 0.98),
    domain_y=(0.02, 0.98),
):
    """
    Publication-ready Sankey (Technology -> Metal), cumulative over selected years.

    Fixes vs default:
    - No title (clean figure)
    - Larger, black text
    - Larger canvas + margins
    - Sankey domain tightened to avoid right/left clipping
    - Higher node pad & thickness for readability
    - PDF export: high resolution vector via kaleido
    """

    d = df.copy()

    # infer defaults
    if scenario is None and "Scenario" in d.columns:
        scen = d["Scenario"].dropna().unique()
        scenario = scen[0] if len(scen) else None
    if country is None and "Country" in d.columns:
        ctry = d["Country"].dropna().unique()
        country = ctry[0] if len(ctry) else None

    # filters
    if scenario is not None and "Scenario" in d.columns:
        d = d[d["Scenario"] == scenario]
    if country is not None and "Country" in d.columns:
        d = d[d["Country"] == country]
    if year_min is not None:
        d = d[d["Year"] >= year_min]
    if year_max is not None:
        d = d[d["Year"] <= year_max]

    if d.empty:
        raise ValueError("No data left after filtering (scenario/country/year).")

    agg = (
        d.groupby(["Technology", "Metal"], dropna=False)[value_col]
        .sum()
        .reset_index()
    )

    if top_n_metals is not None:
        top_metals = (
            agg.groupby("Metal")[value_col].sum()
            .sort_values(ascending=False)
            .head(top_n_metals)
            .index
        )
        agg = agg[agg["Metal"].isin(top_metals)]

    if top_n_techs is not None:
        top_techs = (
            agg.groupby("Technology")[value_col].sum()
            .sort_values(ascending=False)
            .head(top_n_techs)
            .index
        )
        agg = agg[agg["Technology"].isin(top_techs)]

    agg["Technology"] = agg["Technology"].fillna("Unknown technology")
    agg["Metal"] = agg["Metal"].fillna("Unknown metal")

    # Optional: drop zero links (avoids clutter)
    agg = agg[agg[value_col].astype(float) > 0].copy()
    if agg.empty:
        raise ValueError("All links are zero after aggregation/filtering.")

    techs = sorted(agg["Technology"].unique().tolist())
    metals = sorted(agg["Metal"].unique().tolist())

    nodes = techs + metals
    node_index = {n: i for i, n in enumerate(nodes)}

    # --- Colors ---
    default_palette = [
        "rgba(31,119,180,1)",   # blue
        "rgba(255,127,14,1)",   # orange
        "rgba(44,160,44,1)",    # green
        "rgba(214,39,40,1)",    # red
        "rgba(148,103,189,1)",  # purple
        "rgba(140,86,75,1)",    # brown
        "rgba(227,119,194,1)",  # pink
        "rgba(127,127,127,1)",  # gray
        "rgba(188,189,34,1)",   # olive
        "rgba(23,190,207,1)",   # cyan
    ]

    if metal_color_map is None:
        metal_color_map = {}

    metal_colors = {}
    for i, m in enumerate(metals):
        metal_colors[m] = metal_color_map.get(m, default_palette[i % len(default_palette)])

    node_colors = [tech_node_color] * len(techs) + [metal_colors[m] for m in metals]

    def with_alpha(rgba_str, alpha):
        if rgba_str.startswith("rgba(") and rgba_str.endswith(")"):
            inner = rgba_str[5:-1]
            parts = inner.split(",")
            if len(parts) >= 3:
                r = parts[0].strip()
                g = parts[1].strip()
                b = parts[2].strip()
                return f"rgba({r},{g},{b},{alpha})"
        return rgba_str

    link_colors = [with_alpha(metal_colors[m], link_alpha) for m in agg["Metal"].tolist()]

    # Build sankey
    sankey = go.Sankey(
        arrangement="snap",
        domain=dict(x=list(domain_x), y=list(domain_y)),  # prevents edge clipping
        node=dict(
            pad=node_pad,
            thickness=node_thickness,
            label=nodes,
            color=node_colors,
            line=dict(color="black", width=0.8),
        ),
        link=dict(
            source=agg["Technology"].map(node_index).astype(int).tolist(),
            target=agg["Metal"].map(node_index).astype(int).tolist(),
            value=agg[value_col].astype(float).tolist(),
            color=link_colors,
        ),
    )

    fig = go.Figure(data=[sankey])

    # Clean layout: no title
    fig.update_layout(
        template=template,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="black", size=font_size),
        height=pdf_height if output_pdf else 900,
        margin=dict(l=30, r=30, t=10, b=10),  # extra margins avoid cut
    )

    # Write HTML
    if output_html:
        fig.write_html(output_html, include_plotlyjs="cdn")

    # Default PDF name
    if output_pdf is None and output_html and output_html.lower().endswith(".html"):
        output_pdf = output_html[:-5] + ".pdf"

    # Write PDF (vector) via kaleido
    if output_pdf:
        try:
            fig.write_image(
                output_pdf,
                format="pdf",
                width=pdf_width,
                height=pdf_height,
                scale=1,
            )
        except Exception as e:
            raise RuntimeError(
                "PDF export failed. Install kaleido with: pip install -U kaleido\n"
                f"Original error: {e}"
            )

    return fig, agg


# def plot_scenario_difference(
#     df,
#     scenario_col="Scenario",
#     value_col="Metal_demand_t",
#     variable_col="Metal",     # or "Variable"
#     scenario_a="High",
#     scenario_b="Low",
#     kind="bar",               # or "strip"
#     figsize=(8, 5),
#     dpi=300,
#     alphabetical=True,        # ✅ NEW
#     savepath=None,
# ):
#     """
#     Plot % difference between two scenarios (scenario_a vs scenario_b)
#     across metals or technologies.
#
#     Formula: (A - B) / B * 100
#     Positive = higher in scenario_a
#     Negative = lower in scenario_a
#     """
#
#     # --- Data checks ---
#     for col in [scenario_col, value_col, variable_col]:
#         if col not in df.columns:
#             raise KeyError(f"❌ Column '{col}' not found in DataFrame.")
#
#     # --- Aggregate ---
#     agg = (
#         df.groupby([scenario_col, variable_col])[value_col]
#         .sum()
#         .reset_index()
#         .pivot(index=variable_col, columns=scenario_col, values=value_col)
#     )
#
#     if scenario_a not in agg.columns or scenario_b not in agg.columns:
#         raise ValueError(f"Scenarios '{scenario_a}' and/or '{scenario_b}' not found in '{scenario_col}'.")
#
#     # --- Compute % difference ---
#     agg["% difference"] = (agg[scenario_a] - agg[scenario_b]) / agg[scenario_b] * 100
#
#     # ✅ Sort alphabetically or by magnitude
#     if alphabetical:
#         agg = agg.sort_index()
#     else:
#         agg = agg.sort_values("% difference", ascending=False)
#
#     # --- Plot ---
#     plt.figure(figsize=figsize, dpi=dpi)
#     sns.set_style("whitegrid")
#
#     # Generate color palette: green = positive, red = negative
#     colors = ["#2ca02c" if x > 0 else "#d62728" for x in agg["% difference"]]
#
#     if kind == "bar":
#         ax = sns.barplot(
#             data=agg.reset_index(),
#             x=variable_col,
#             y="% difference",
#             palette=colors,
#         )
#         plt.axhline(0, color="black", linewidth=1)
#         plt.xticks(rotation=90, ha="right")
#         plt.xlabel('')
#         plt.ylabel(f"% difference {scenario_a} vs {scenario_b}")
#         plt.title(f"Relative difference in {value_col} between {scenario_a} and {scenario_b}")
#         ax.yaxis.set_major_formatter(mticker.PercentFormatter())
#     else:
#         ax = sns.stripplot(
#             data=agg.reset_index(),
#             x=variable_col,
#             y="% difference",
#             hue="% difference" > 0,
#             palette={True: "#2ca02c", False: "#d62728"},
#             size=8,
#         )
#         plt.axhline(0, color="black", linewidth=1)
#         plt.legend([], [], frameon=False)
#         plt.ylabel(f"% difference {scenario_a} vs {scenario_b}")
#         plt.title(f"Relative difference in {value_col} between {scenario_a} and {scenario_b}")
#
#     plt.tight_layout()
#
#     if savepath:
#         plt.savefig(f"{savepath}.png", bbox_inches="tight")
#         plt.savefig(f"{savepath}.svg", bbox_inches="tight")
#         print(f"✅ Saved to {savepath}.png / .svg")
#
#     #plt.show()
#
#     return agg[["% difference"]]



# def plot_masse_stats_per_clas(df, col_clas="CLAS", col_mass="MASSE_NETTE"):
#     """
#     Compute summary statistics and plot a styled boxplot of mass per CLAS.
#
#     Parameters
#     ----------
#     df : pd.DataFrame
#         DataFrame containing at least columns for class and mass.
#     col_clas : str, default="CLAS"
#         Column name for the vehicle class.
#     col_mass : str, default="MASSE_NETTE"
#         Column name for the vehicle mass (numeric).
#     """
#     # Ensure numeric
#     df = df.copy()
#     df[col_mass] = pd.to_numeric(df[col_mass], errors="coerce")
#     df = df.dropna(subset=[col_clas, col_mass])
#
#     # Summary stats
#     summary = df.groupby(col_clas)[col_mass].agg(
#         Mean="mean",
#         Median="median",
#         Min="min",
#         Max="max",
#         Count="count",
#         Q25=lambda x: x.quantile(0.25),
#         Q75=lambda x: x.quantile(0.75),
#     ).sort_values("Mean", ascending=False)
#
#     # --- Plot ---
#     plt.figure(figsize=(12, 10))
#     sns.boxplot(x=col_clas, y=col_mass, data=df, showfliers=False, palette="Set3")
#
#     # Add number of samples above each box
#     counts = df[col_clas].value_counts()
#     positions = range(len(counts))
#     for pos, clas in enumerate(counts.index):
#         plt.text(pos, df.loc[df[col_clas]==clas, col_mass].max() * 1.02,
#                  f"n={counts[clas]}", ha="center", fontsize=9, color="black")
#
#     plt.xticks(rotation=90)
#     plt.title("Distribution of Vehicle Mass (MASSE_NETTE) per CLAS")
#     plt.xlabel("CLAS")
#     plt.ylabel("MASSE_NETTE (kg)")
#     plt.tight_layout()
#     plt.show()
#
#     return summary



# ======================================================
# Production scenarios
# ======================================================

def plot_metal_scenarios_panels(df, color_map,
                                figsize=(10, 7), dpi=350, savepath=None):
    """
    Create 3-panel Matplotlib figure:
    - Top: line chart across both scenarios (solid/dashed lines)
    - Bottom: 2 stacked area charts (one per scenario, same y scale)
    """

    import numpy as np
    import matplotlib.pyplot as plt

    df_long = df.melt(
        id_vars=["Scenario", "Year", "Unit"],
        var_name="Metal",
        value_name="Value"
    )

    metals = df_long["Metal"].unique().tolist()
    scenarios = df_long["Scenario"].unique().tolist()
    unit = df_long["Unit"].iloc[0]

    # Auto line styles
    if len(scenarios) == 2:
        scenario_styles = {
            scenarios[0]: {"linestyle": "-", "label": f"{scenarios[0]}"},
            scenarios[1]: {"linestyle": "--", "label": f"{scenarios[1]}"}
        }
    else:
        scenario_styles = {s: {"linestyle": "-", "label": s} for s in scenarios}

    # --- Figure setup ---
    fig = plt.figure(figsize=figsize, dpi=dpi)
    gs = fig.add_gridspec(2, 2, height_ratios=[2, 1])
    ax_top = fig.add_subplot(gs[0, :])
    ax_bottom_left = fig.add_subplot(gs[1, 0], sharex=ax_top)
    ax_bottom_right = fig.add_subplot(gs[1, 1], sharex=ax_top)

    # =======================================================
    # 1️⃣ Top panel: line chart
    # =======================================================
    for metal in metals:
        for scen in scenarios:
            dsub = df_long[(df_long["Metal"] == metal) & (df_long["Scenario"] == scen)]
            ax_top.plot(
                dsub["Year"],
                dsub["Value"],
                color=color_map.get(metal, "#cccccc"),
                linestyle=scenario_styles[scen]["linestyle"],
                linewidth=1.8,
                alpha=0.9,
            )

    ax_top.set_title("Production by metal and scenario", fontsize=12, fontweight="bold")
    ax_top.set_ylabel(f"Production ({unit})", fontsize=10)
    #ax_top.grid(True, linestyle="--", alpha=0.3)
    ax_top.tick_params(labelsize=9)
    ax_top.set_xlim(df_long["Year"].min(), df_long["Year"].max())
    ax_top.set_ylim(bottom=0)


    xticks = np.arange(df_long["Year"].min(), df_long["Year"].max() + 1, 5)
    ax_top.set_xticks(xticks)

    # Legend for scenario line styles
    scen_handles = [
        plt.Line2D([0], [0], color="black",
                   linestyle=scenario_styles[s]["linestyle"],
                   label=scenario_styles[s]["label"]) for s in scenarios
    ]
    ax_top.legend(handles=scen_handles, loc="upper left", fontsize=11, frameon=False)

    # =======================================================
    # 2️⃣ Bottom panels: stacked areas
    # =======================================================
    bottom_axes = [ax_bottom_left, ax_bottom_right]
    y_max = 0

    # find global y limit first
    for scen in scenarios:
        d_scen = df_long[df_long["Scenario"] == scen]
        pivot = d_scen.pivot_table(index="Year", columns="Metal", values="Value",
                                   aggfunc="sum", fill_value=0)
        y_max = max(y_max, pivot.sum(axis=1).max())

    # plot each scenario
    for ax, scen in zip(bottom_axes, scenarios):
        d_scen = df_long[df_long["Scenario"] == scen]
        pivot = d_scen.pivot_table(index="Year", columns="Metal",
                                   values="Value", aggfunc="sum", fill_value=0)
        cols = [color_map.get(c, "#cccccc") for c in pivot.columns]
        ax.stackplot(pivot.index, pivot.T, labels=pivot.columns, colors=cols, alpha=0.9)
        ax.set_title(scen, fontsize=11, fontweight="bold")
        ax.set_ylabel(f"Production ({unit})", fontsize=9)
        #ax.grid(True, linestyle="--", alpha=0.3)
        ax.tick_params(labelsize=9)
        ax.set_xticks(xticks)
        #ax.set_xlabel("Year", fontsize=9)
        ax.set_ylim(0, y_max * 1.05)  # unified y scale + small headroom
        ax.set_yticks([y for y in ax.get_yticks() if y != 0])


    for a in [ax_top, ax_bottom_left, ax_bottom_right]:
        a.set_yticks([y for y in a.get_yticks() if y != 0])

    # =======================================================
    # 3️⃣ Shared legend (metals)
    # =======================================================
    handles, labels = ax_bottom_right.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center",
               bbox_to_anchor=(0.5, 0.02),
               ncol=min(len(labels), 6),
               fontsize=12, frameon=False)

    # =======================================================
    # Layout
    # =======================================================
    plt.subplots_adjust(hspace=0.35, bottom=0.13, top=0.93, wspace=0.25)
    #fig.suptitle("Metal production scenarios comparison", fontsize=14, fontweight="bold")

    if savepath:
        fig.savefig(f"{savepath}.png", bbox_inches="tight")
        fig.savefig(f"{savepath}.svg", bbox_inches="tight")
        print(f"✅ Saved to {savepath}.png and .svg")

    #plt.show()


# ======================================================
# LCA results
# ======================================================
def plot_lca_stackplots_by_scenario(
    df,
    scenario,
    impact_cols,
    color_map=None,
    group_small_metals=True,
    threshold=0.01,
    figsize=(10, 7),
    dpi=300,
    log_scale=False,              # NEW
    years=[2025, 2030, 2035, 2040],   # NEW
    savepath=None,
):
    """
    Stacked ACV results by metal and year for a given scenario.
    """

    # --- Filter scenario ---
    d0 = df[df["Scenario"] == scenario].copy()
    if d0.empty:
        raise ValueError(f"❌ No rows for scenario = {scenario}")

    # --- Clean year and filter the required values ---
    d0["Year"] = d0["Year"].astype(int)
    d0 = d0[d0["Year"].isin(years)]
    d0 = d0.sort_values("Year")

    metals = sorted(d0["Metal"].unique())

    # --- Colors ---
    if color_map:
        for m in metals:
            if m not in color_map:
                color_map[m] = "#" + ''.join(np.random.choice(list('0123456789ABCDEF'), 6))
    else:
        # auto colors
        def pastel(n):
            hsv = [(i/n, 0.45 + 0.2*np.random.rand(), 0.9) for i in range(n)]
            return [mcolors.to_hex(mcolors.hsv_to_rgb(h)) for h in hsv]
        colors = pastel(len(metals))
        color_map = dict(zip(metals, colors))

    # --- Figure ---
    fig, axes = plt.subplots(len(impact_cols), 1, figsize=figsize, dpi=dpi, sharex=True)
    if len(impact_cols) == 1:
        axes = [axes]

    for ax, impact in zip(axes, impact_cols):

        pivot = d0.pivot_table(
            index="Year",
            columns="Metal",
            values=impact,
            aggfunc="sum",
            fill_value=0
        )

        # --- Optional grouping ---
        if group_small_metals:
            total_all = pivot.sum().sum()
            share = pivot.sum() / total_all
            small = share[share < threshold].index

            if len(small) > 0:
                pivot["Other"] = pivot[small].sum(axis=1)
                pivot = pivot.drop(columns=small)
                color_map["Other"] = "#999999"

        # --- Colors order ---
        colors = [color_map[m] for m in pivot.columns]

        # --- Stack plot ---
        ax.stackplot(pivot.index, pivot.T, labels=pivot.columns, colors=colors)

        # Apply log scale if requested
        if log_scale:
            ax.set_yscale("log")

        ax.set_ylabel(impact, fontsize=12)
        ax.set_title(f"{impact} – {scenario}", fontsize=13, fontweight="bold")
        ax.legend(loc="upper left", ncol=3, fontsize=11, frameon=False)

    # --- Clean x-axis with fixed tick labels ---
    axes[-1].set_xticks(years)
    axes[-1].set_xticklabels([str(y) for y in years], fontsize=11)
    axes[-1].set_xlabel("", fontsize=12)

    fig.tight_layout()

    if savepath:
        fig.savefig(savepath + ".png", bbox_inches="tight")
        fig.savefig(savepath + ".svg", bbox_inches="tight")

    #return fig