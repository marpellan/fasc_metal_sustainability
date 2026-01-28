import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

def plot_stacked_contribution_by_activity(
    df,
    impact_col="share_%",
    commodity_col="reference_product_market",
    name_col="name",
    flow_type_col="flow_type",
    commodity_order=None,
    act_to_hex=None,                     # dict: {activity_name: "#RRGGBB"}
    act_to_plot=None,                    # list of activities to display (order preserved)
    top_n=12,                            # used only if act_to_plot=None
    others_label="Others",
    hatch_technosphere="///",
    hatch_biosphere=None,
    bar_spacing=0.15,
    figsize=(11, 7),
    xlabel=None,
    title=None,
    normalize_to_percent=False,          # if True: each commodity is normalized to 100%
    legend=True,
    legend_fontsize=9,
    legend_ncol=1,
    output_path=None,
    dpi=600,
    # --- NEW ---
    direct_first=True,                   # force all Direct (biosphere) to the left
    legend_direct_first=True,            # force Direct entries first in legend
    direct_label="",
    indirect_label=" ",
):
    """
    Horizontal stacked contribution barplot across ALL commodities.

    - Colors encode activity (name)
    - Hatch encodes flow_type (Technosphere hatched; Biosphere solid)
    - Unselected activities grouped into 'Others'
    - Legend style: "Activity — Direct" and "Activity — Indirect"

    NEW:
    - direct_first=True: draw ALL Direct segments first (thus leftmost), then Indirect.
    - legend_direct_first=True: reorder legend so Direct entries appear first.

    Required columns in df:
      - commodity_col
      - name_col
      - flow_type_col (expects e.g. 'Technosphere (first-tier)' and 'Biosphere (direct)')
      - impact_col
    """
    df = df.copy()

    # --- Basic checks
    for c in [commodity_col, name_col, flow_type_col, impact_col]:
        if c not in df.columns:
            raise ValueError(f"Missing column: '{c}'")

    # Coerce impacts to numeric
    df[impact_col] = pd.to_numeric(df[impact_col], errors="coerce").fillna(0.0)

    # --- Decide which activities to plot
    if act_to_plot is None:
        tmp = (
            df.groupby(name_col, as_index=False)[impact_col].sum()
            .assign(_abs=lambda x: x[impact_col].abs())
            .sort_values("_abs", ascending=False)
        )
        act_to_plot = tmp[name_col].head(top_n).tolist()
    act_to_plot = list(act_to_plot)  # preserve given order

    # --- Colors
    act_to_hex = act_to_hex or {}

    def _get_color(act, i):
        if act in act_to_hex:
            return act_to_hex[act]
        cmap = plt.get_cmap("tab20")
        return cmap(i % 20)

    # --- Group non-selected -> Others
    df["_act"] = df[name_col].where(df[name_col].isin(act_to_plot), others_label)

    # --- Aggregate
    agg = (
        df.groupby([commodity_col, "_act", flow_type_col], as_index=False)[impact_col]
        .sum()
        .rename(columns={impact_col: "impact"})
    )

    # --- Commodity order
    if commodity_order is not None:
        missing = set(commodity_order) - set(agg[commodity_col].unique())
        if missing:
            raise ValueError(f"Commodities not found in data: {missing}")
    else:
        commodity_order = (
            agg.groupby(commodity_col, as_index=False)["impact"].sum()
            .assign(_abs=lambda x: x["impact"].abs())
            .sort_values("_abs", ascending=False)[commodity_col]
            .tolist()
        )

    # --- Fixed bar heights
    heights = np.full(len(commodity_order), 0.7, dtype=float)

    # y positions with spacing
    y_pos = np.zeros(len(commodity_order), dtype=float)
    for i in range(1, len(commodity_order)):
        y_pos[i] = y_pos[i - 1] + heights[i - 1] + bar_spacing

    # --- Flow labels (expected)
    flow_bio = "Biosphere (direct)"
    flow_tech = "Technosphere (first-tier)"

    # --- Flow order: bio first, then tech, then any others
    flow_types_present = set(agg[flow_type_col].unique().tolist())
    flow_order = []
    if flow_bio in flow_types_present:
        flow_order.append(flow_bio)
    if flow_tech in flow_types_present:
        flow_order.append(flow_tech)
    flow_order += [ft for ft in sorted(flow_types_present) if ft not in set(flow_order)]

    # --- Activity order
    acts_present = set(agg["_act"].unique().tolist())
    act_order = [a for a in act_to_plot if a in acts_present]
    if others_label in acts_present:
        act_order.append(others_label)

    # --- Pivot
    pivot = (
        agg.pivot_table(
            index=[commodity_col],
            columns=["_act", flow_type_col],
            values="impact",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reindex(index=commodity_order, fill_value=0.0)
    )

    # Normalize each commodity to 100% if requested
    if normalize_to_percent:
        row_sums = pivot.sum(axis=1).replace(0, np.nan)
        pivot = (pivot.div(row_sums, axis=0) * 100.0).fillna(0.0)
        if xlabel is None:
            xlabel = "Contribution (%)"
    else:
        if xlabel is None:
            xlabel = impact_col

    # --- Plot
    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    left = np.zeros(len(commodity_order), dtype=float)

    labeled = set()

    def _direct_or_indirect(ft: str) -> str:
        # Map known flow types to Direct/Indirect; fallback: treat as Indirect
        if ft == flow_bio:
            return direct_label
        if ft == flow_tech:
            return indirect_label
        return indirect_label

    def _hatch_for(ft: str):
        if ft == flow_tech:
            return hatch_technosphere
        if ft == flow_bio:
            return hatch_biosphere
        # unknown: treat like indirect hatch (safer visual cue)
        return hatch_technosphere

    # --- Drawing order:
    # If direct_first: draw ALL flows in flow_order outer loop (Direct first), so Direct is leftmost.
    # Else: draw by activity first, then flow (original behavior).
    if direct_first:
        outer = [("flow", ft) for ft in flow_order]
        inner_kind = "act"
    else:
        outer = [("act", act) for act in act_order]
        inner_kind = "flow"

    def _iter_pairs():
        if direct_first:
            for ft in flow_order:
                for i_act, act in enumerate(act_order):
                    yield act, i_act, ft
        else:
            for i_act, act in enumerate(act_order):
                for ft in flow_order:
                    yield act, i_act, ft

    for act, i_act, ft in _iter_pairs():
        color = _get_color(act, i_act)

        try:
            vals = pivot[(act, ft)].values
        except KeyError:
            vals = np.zeros(len(commodity_order), dtype=float)

        if np.allclose(vals, 0):
            continue

        hatch = _hatch_for(ft)

        suffix = _direct_or_indirect(ft)
        label_full = f"{act} {suffix}"
        label = label_full if label_full not in labeled else "_nolegend_"
        if label != "_nolegend_":
            labeled.add(label_full)

        ax.barh(
            y_pos,
            vals,
            left=left,
            height=heights,
            color=color,
            hatch=hatch,
            edgecolor="black",
            linewidth=0.5,
            label=label,
        )
        left += vals

    # Axes
    ax.set_yticks(y_pos)
    ax.set_yticklabels(commodity_order)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=12)
    ax.tick_params(axis="x", labelsize=11)
    ax.tick_params(axis="y", labelsize=11)

    if title is not None:
        ax.set_title(title, fontsize=12)

    # --- Legend: force Direct entries first (then Indirect)
    if legend:
        handles, labels = ax.get_legend_handles_labels()
        pairs = [(h, l) for h, l in zip(handles, labels) if l and l != "_nolegend_"]

        if legend_direct_first:
            def _is_direct(lbl: str) -> bool:
                return f"— {direct_label}" in lbl

            # Direct first; stable sort keeps within-group order
            pairs = sorted(pairs, key=lambda hl: (0 if _is_direct(hl[1]) else 1))

        handles_sorted = [h for h, _ in pairs]
        labels_sorted = [l for _, l in pairs]

        ax.legend(
            handles_sorted,
            labels_sorted,
            loc="upper left",
            bbox_to_anchor=(1.01, 1.0),
            frameon=False,
            fontsize=legend_fontsize,
            ncol=legend_ncol,
        )

    # Save
    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")

    plt.show()
    return fig, ax

def plot_midpoint_contributions(df, category, threshold=0.05, combine_terms=True, save_path=None):
    """
    Plots a high‑resolution stacked bar chart of midpoint contributions for each commodity,
    with optional merging of 'long term'/'short term' into a single category and
    thresholding to group small contributors into 'Other'.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain a 'Commodity' column and one column per midpoint (fractions 0–1).
    category : str
        'Human health' or 'Ecosystem quality' (used for title).
    threshold : float
        Minimum fraction (0–1) for a category to be shown; others are grouped into 'Other'.
    combine_terms : bool
        If True, merges columns ending in 'long term' or 'short term' into a single prefix.

    Usage
    -----
    plot_midpoint_shares_grouped(df_hh, 'Human health', threshold=0.05)
    plot_midpoint_shares_grouped(df_eq, 'Ecosystem quality', threshold=0.05)
    """
    df_proc = df.copy()
    # 1) optionally combine long/short term
    if combine_terms:
        def simplify(col):
            parts = col.split(', ')
            if parts[-1].lower() in ('long term', 'short term'):
                parts = parts[:-1]
            return ', '.join(parts)
        # Group by simplified label
        label_map = {}
        for col in df_proc.columns:
            if col == 'Commodity':
                continue
            label_map.setdefault(simplify(col), []).append(col)
        df_grouped = pd.DataFrame({'Commodity': df_proc['Commodity']})
        for label, cols in label_map.items():
            df_grouped[label] = df_proc[cols].sum(axis=1)
    else:
        df_grouped = df_proc

    # 2) thresholding: keep categories with max >= threshold
    cats = [c for c in df_grouped.columns if c != 'Commodity']
    keep = [c for c in cats if df_grouped[c].max() >= threshold]
    drop = [c for c in cats if c not in keep]

    # Build final df and compute 'Other'
    df_final = pd.DataFrame({'Commodity': df_grouped['Commodity']})
    for c in keep:
        df_final[c] = df_grouped[c]
    if drop:
        df_final['Other'] = df_grouped[drop].sum(axis=1)
        plot_cats = keep + ['Other']
    else:
        plot_cats = keep

    # Sort categories by mean share descending (largest at bottom of stack)
    plot_cats = sorted(plot_cats, key=lambda x: df_final[x].mean(), reverse=True)

    # 3) plotting
    x = range(len(df_final))
    bottoms = [0] * len(df_final)

    plt.figure(figsize=(12, 6), dpi=300)
    for cat_label in plot_cats:
        vals = df_final[cat_label].fillna(0).values * 100  # to percent
        plt.bar(x, vals, bottom=bottoms, label=cat_label)
        bottoms = [b + v for b, v in zip(bottoms, vals)]

    plt.xticks(x, df_final['Commodity'], rotation=45, ha='right')
    plt.ylabel('Percentage contribution (%)')
    plt.title(f'{category} midpoint contributions (≥{threshold*100:.0f}% or combined)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    # Save the plot if a path is provided, otherwise display it
    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
        print(f"Plot saved to {save_path}")
    else:
        plt.show()