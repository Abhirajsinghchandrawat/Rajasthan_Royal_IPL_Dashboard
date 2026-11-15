"""Reusable Plotly chart builders following the PressureIQ semantic design system.

Colour semantics (config.settings.SEMANTIC):
  teal  = positive contribution / improvement     coral = negative / deterioration
  amber = pressure, caution, uncertainty          navy  = structure
  grey  = baselines, references, unavailable
Every colour-coded series is also distinguished by marker symbol or label so
charts remain readable without colour.
"""

from __future__ import annotations

import textwrap

import pandas as pd
import plotly.graph_objects as go

from config.settings import COLORS, SEMANTIC


def _format_chart_title(title: str, max_line_chars: int = 44) -> tuple[str, int]:
    """Format chart title so it never overflows the container width.

    Splits on ' — ' (or trailing parenthetical) into a bold primary heading
    and a muted subtitle line, ensuring every line stays concise even inside
    2-column and 3-column dashboard grids.
    """
    if not title:
        return "", 0
    if "<br>" in title:
        return title, title.count("<br>") + 1

    main = title.strip()
    sub = ""
    if " — " in main:
        parts = main.split(" — ", 1)
        if len(parts[0]) <= max_line_chars:
            main, sub = parts[0].strip(), parts[1].strip()
    elif " (" in main and main.endswith(")") and len(main) > max_line_chars:
        idx = main.find(" (")
        if idx <= max_line_chars:
            main, sub = main[:idx].strip(), main[idx + 2 : -1].strip()

    if len(main) > max_line_chars:
        wrapped = textwrap.wrap(main, width=max_line_chars)
        main_html = "<br>".join(f"<b>{line}</b>" for line in wrapped)
        n_lines = len(wrapped)
    else:
        main_html = f"<b>{main}</b>"
        n_lines = 1

    if sub:
        if len(sub) > 58:
            sub_lines = textwrap.wrap(sub, width=56)
            sub_txt = "<br>".join(sub_lines)
            n_lines += len(sub_lines)
        else:
            sub_txt = sub
            n_lines += 1
        full_html = (
            f"{main_html}<br>"
            f"<span style='font-size:11.5px;color:#475569;font-weight:500;'>{sub_txt}</span>"
        )
        return full_html, n_lines

    return main_html, n_lines


def apply_piq_theme(fig: go.Figure, title: str = "", height: int = 380, legend: bool = True) -> go.Figure:
    formatted_title, n_lines = _format_chart_title(title)
    if n_lines >= 2:
        top_margin = 98 if legend else 74
    elif n_lines == 1:
        top_margin = 78 if legend else 54
    else:
        top_margin = 40

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=formatted_title,
            font=dict(size=13.5, family="Inter, sans-serif", color=COLORS["navy"]),
            x=0.015,
            xanchor="left",
            xref="container",
            y=0.965,
            yref="container",
            yanchor="top",
        ),
        font=dict(family="Inter, sans-serif", size=12, color=COLORS["text"]),
        paper_bgcolor=COLORS["card"],
        plot_bgcolor=COLORS["card"],
        height=height,
        margin=dict(l=14, r=24, t=top_margin, b=16),
        showlegend=legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0.0,
            bgcolor="rgba(255,255,255,0)",
            font=dict(color=COLORS["text"], size=11),
            title_text="",
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=COLORS["navy"],
            font_size=12,
            font_family="Inter",
            font_color=COLORS["text"],
        ),
    )
    axis = dict(
        showgrid=True,
        gridcolor="#E2E8F0",
        zeroline=False,
        linecolor="#CBD5E1",
        automargin=True,
        tickfont=dict(color=COLORS["text"], size=11),
        title_font=dict(color=COLORS["navy"], size=11.5),
        title_standoff=10,
    )
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    return fig


def sign_colors(values) -> list[str]:
    return [SEMANTIC["positive"] if (v is not None and v >= 0) else SEMANTIC["negative"] for v in values]


def horizontal_leaderboard(
    df: pd.DataFrame,
    value_col: str,
    label_col: str,
    title: str,
    x_label: str,
    order_col: str = "rank",
    ci_lo: str | None = None,
    ci_hi: str | None = None,
    marker_col: str | None = None,
    marker_name: str = "",
    value_name: str = "",
    height: int = 390,
) -> go.Figure:
    """Bars ordered strictly by `order_col` (rank 1 at the top), so the rank label and
    the visual order always come from the same metric. Bar colour = sign of value."""
    d = df.sort_values(order_col, ascending=True).copy()
    cats = d[label_col].tolist()[::-1]  # plotly draws the first category at the bottom
    fig = go.Figure()
    err_x = None
    if ci_lo and ci_hi:
        err_x = dict(
            type="data",
            symmetric=False,
            array=(d[ci_hi] - d[value_col]).clip(lower=0),
            arrayminus=(d[value_col] - d[ci_lo]).clip(lower=0),
            color="rgba(20,36,58,0.38)",
            thickness=1.1,
            width=3,
        )
    hover = "<b>%{y}</b><br>" + (value_name or x_label) + ": %{x:+.2f}"
    if ci_lo and ci_hi:
        hover += "<br>90% CI: [%{customdata[0]:+.2f}, %{customdata[1]:+.2f}]"
    fig.add_trace(
        go.Bar(
            x=d[value_col],
            y=d[label_col],
            orientation="h",
            name=value_name or x_label,
            marker=dict(color=sign_colors(d[value_col]), line=dict(width=0)),
            opacity=0.9,
            error_x=err_x,
            customdata=d[[ci_lo, ci_hi]].to_numpy() if (ci_lo and ci_hi) else None,
            text=None if err_x else d[value_col].map(lambda v: f"{v:+.2f}"),
            textposition="outside",
            cliponaxis=False,
            hovertemplate=hover + "<extra></extra>",
        )
    )
    if marker_col:
        fig.add_trace(
            go.Scatter(
                x=d[marker_col],
                y=d[label_col],
                mode="markers",
                name=marker_name or marker_col,
                marker=dict(symbol="diamond", size=9, color=SEMANTIC["pressure"], line=dict(color="#FFFFFF", width=1)),
                hovertemplate="<b>%{y}</b><br>" + (marker_name or marker_col) + ": %{x:+.2f}<extra></extra>",
            )
        )
    apply_piq_theme(fig, title=title, height=height, legend=bool(marker_col))
    fig.update_yaxes(categoryorder="array", categoryarray=cats, title_text="", showgrid=False)
    fig.update_xaxes(title_text=x_label, zeroline=True, zerolinecolor=SEMANTIC["baseline_dark"], zerolinewidth=1)
    return fig


def dumbbell_chart(
    df: pd.DataFrame,
    name_col: str,
    normal_col: str,
    pressure_col: str,
    title: str,
    x_label: str,
    height: int = 420,
) -> go.Figure:
    """Grey circle = own normal baseline; diamond = under pressure, teal when the
    pressure value is higher (improved) and coral when lower (declined)."""
    d = df.copy()
    up = d[pressure_col] >= d[normal_col]
    fig = go.Figure()
    for _, r in d.iterrows():
        col = "rgba(13,148,136,0.45)" if r[pressure_col] >= r[normal_col] else "rgba(220,98,98,0.45)"
        fig.add_trace(
            go.Scatter(
                x=[r[normal_col], r[pressure_col]],
                y=[r[name_col], r[name_col]],
                mode="lines",
                line=dict(color=col, width=3),
                showlegend=False,
                hoverinfo="skip",
            )
        )
    fig.add_trace(
        go.Scatter(
            x=d[normal_col],
            y=d[name_col],
            mode="markers",
            name="Own normal baseline",
            marker=dict(color=SEMANTIC["baseline_dark"], size=9, symbol="circle"),
            hovertemplate="<b>%{y}</b><br>Normal (shrunk): %{x:+.2f}<extra></extra>",
        )
    )
    for mask, name, col in [
        (up, "Under pressure (≥ normal)", SEMANTIC["positive"]),
        (~up, "Under pressure (< normal)", SEMANTIC["negative"]),
    ]:
        if mask.any():
            fig.add_trace(
                go.Scatter(
                    x=d.loc[mask, pressure_col],
                    y=d.loc[mask, name_col],
                    mode="markers",
                    name=name,
                    marker=dict(color=col, size=11, symbol="diamond", line=dict(color="#FFFFFF", width=1)),
                    hovertemplate="<b>%{y}</b><br>Pressure (shrunk): %{x:+.2f}<extra></extra>",
                )
            )
    apply_piq_theme(fig, title=title, height=height)
    fig.update_yaxes(categoryorder="array", categoryarray=d[name_col].tolist(), showgrid=False)
    fig.update_xaxes(title_text=x_label, zeroline=True, zerolinecolor=SEMANTIC["baseline_dark"])
    return fig


def forest_plot(
    df: pd.DataFrame,
    name_col: str,
    mean_col: str,
    lo_col: str,
    hi_col: str,
    rpr_col: str,
    title: str,
    x_label: str,
    height: int = 440,
) -> go.Figure:
    d = df.sort_values(rpr_col, ascending=True).copy()
    fig = go.Figure()
    for _, r in d.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[r[lo_col], r[hi_col]],
                y=[r[name_col], r[name_col]],
                mode="lines",
                line=dict(color="rgba(20,36,58,0.45)", width=2.5),
                showlegend=False,
                hoverinfo="skip",
            )
        )
    fig.add_trace(
        go.Scatter(
            x=d[mean_col],
            y=d[name_col],
            mode="markers",
            name="Shrunk mean (APR)",
            marker=dict(color=sign_colors(d[mean_col]), size=10, symbol="circle"),
            customdata=d[[lo_col, hi_col]].to_numpy(),
            hovertemplate="<b>%{y}</b><br>APR: %{x:+.2f}<br>90% CI: [%{customdata[0]:+.2f}, %{customdata[1]:+.2f}]<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=d[rpr_col],
            y=d[name_col],
            mode="markers",
            name="RPR (90% lower bound)",
            marker=dict(color=SEMANTIC["pressure"], size=9, symbol="triangle-right"),
            hovertemplate="<b>%{y}</b><br>RPR: %{x:+.2f}<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_dash="dash", line_color=SEMANTIC["baseline_dark"])
    apply_piq_theme(fig, title=title, height=height)
    fig.update_yaxes(categoryorder="array", categoryarray=d[name_col].tolist(), showgrid=False)
    fig.update_xaxes(title_text=x_label)
    return fig


def style_single_box(fig: go.Figure, color: str | None = None) -> go.Figure:
    """Uniform navy/teal box styling: player identity is on the axis, not in colour."""
    fig.update_traces(
        marker=dict(color=color or SEMANTIC["structure"], size=4, opacity=0.55),
        line=dict(color=SEMANTIC["structure"], width=1.4),
        fillcolor="rgba(13,148,136,0.16)",
        showlegend=False,
    )
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color=SEMANTIC["baseline_dark"],
        annotation_text="Context expectation (0)",
        annotation_position="top left",
        annotation_font_color=SEMANTIC["baseline_dark"],
    )
    return fig
