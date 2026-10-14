# =========================================================================
# DataPulse HTML Report Components
# Reusable HTML markup builders for findings, columns, correlations, & keys.
# =========================================================================

from html import escape

from datapulse.models.report import (
    ColumnProfile,
    CorrelationPair,
    Finding,
    KeyCandidate,
)

# =========================================================================
# FINDINGS & ALERTS COMPONENT
# =========================================================================

def render_findings(findings: list[Finding]) -> str:
    """Render data quality findings as color-coded alert cards."""
    if not findings:
        return (
            "<div class='empty-state'>"
            "No automated quality anomalies detected. Dataset looks clean!"
            "</div>"
        )
    cards = []
    for f in findings:
        sev = f.severity.lower()
        cols_text = escape(", ".join(f.affected_columns))
        cols_badge = (
            f"<span class='badge badge-neutral'>{cols_text}</span>"
            if f.affected_columns
            else ""
        )
        card = (
            f"<div class='finding-card finding-{sev}'>"
            f"<div class='finding-header'>"
            f"<span class='badge badge-{sev}'>{escape(f.severity.upper())}</span>"
            f"<span class='finding-title'>{escape(f.title)}</span>"
            f"{cols_badge}"
            f"</div>"
            f"<div class='finding-desc'>{escape(f.description)}</div>"
            f"</div>"
        )
        cards.append(card)
    return "\n".join(cards)


# =========================================================================
# COLUMN PROFILES TABLE COMPONENT
# =========================================================================

def render_column_rows(columns: list[ColumnProfile]) -> str:
    """Render tabular rows for each profiled column with search attributes."""
    col_rows = []
    for col in columns:
        role = escape(col.inferred_role)
        stats_items = []
        for k, v in col.statistics.items():
            if k in ("top_categories", "25%", "50%", "75%"):
                continue
            if v is not None:
                stats_items.append(
                    f"<span class='stat-pill'>{escape(k)}: "
                    f"<strong>{escape(str(v))}</strong></span>"
                )

        stats_summary = (
            " ".join(stats_items)
            if stats_items
            else "<span class='text-muted'>-</span>"
        )

        top_cats = col.statistics.get("top_categories", [])
        if isinstance(top_cats, list) and top_cats:
            cat_pills = [
                f"<span class='cat-pill'>{escape(str(c.get('value', '')))} "
                f"({float(c.get('percentage', 0.0)):.1f}%)</span>"
                for c in top_cats[:5]
                if isinstance(c, dict)
            ]
            if cat_pills:
                pills_html = " ".join(cat_pills)
                stats_summary += f"<div class='cat-pills-row'>{pills_html}</div>"

        missing_width = min(col.missing_percentage, 100)
        missing_bar = (
            "<div class='progress-wrap'>"
            f"<div class='progress-bar' style='width: {missing_width:.1f}%'></div>"
            f"<span class='progress-text'>{col.total_missing_count:,} "
            f"({col.missing_percentage:.1f}%)</span>"
            "</div>"
        )

        esc_type = escape(col.physical_type)
        row = (
            f"<tr class='col-row' data-name='{escape(col.name.lower())}' "
            f"data-role='{role}'>"
            f"<td class='font-mono font-bold'>{escape(col.name)}</td>"
            f"<td><span class='badge badge-type'>{esc_type}</span></td>"
            f"<td><span class='badge badge-role role-{role}'>{role}</span></td>"
            f"<td>{missing_bar}</td>"
            f"<td class='text-right font-mono'>{col.unique_count:,}</td>"
            f"<td class='stats-cell'>{stats_summary}</td>"
            f"</tr>"
        )
        col_rows.append(row)
    return "\n".join(col_rows)


# =========================================================================
# CORRELATION & KEY CANDIDATES COMPONENTS
# =========================================================================

def render_correlations(correlations: list[CorrelationPair]) -> str:
    """Render top numeric correlations table."""
    if not correlations:
        return ""
    corr_rows = []
    for pair in correlations[:20]:
        abs_coef = abs(pair.coefficient)
        sev_class = (
            "badge-critical"
            if abs_coef >= 0.85
            else ("badge-warning" if abs_coef >= 0.60 else "badge-neutral")
        )
        coef_str = f"{pair.coefficient:+.4f}"
        corr_rows.append(
            f"<tr>"
            f"<td class='font-mono'>{escape(pair.column_a)}</td>"
            f"<td class='font-mono'>{escape(pair.column_b)}</td>"
            f"<td class='text-right font-mono font-bold'>{coef_str}</td>"
            f"<td class='text-right font-mono text-muted'>"
            f"{pair.common_observations:,}</td>"
            f"<td><span class='badge {sev_class}'>{abs_coef:.2f}</span></td>"
            f"<td class='text-muted'>{escape(pair.method)}</td>"
            f"</tr>"
        )
    return (
        "<div class='section-card'>"
        "<div class='section-title'>Top Pairwise Correlations</div>"
        "<div class='table-container'>"
        "<table class='data-table'>"
        "<thead><tr>"
        "<th>Column A</th><th>Column B</th>"
        "<th class='text-right'>Coefficient (r)</th>"
        "<th class='text-right'>Joint Obs (N)</th>"
        "<th>Strength</th><th>Method</th>"
        "</tr></thead>"
        f"<tbody>{' '.join(corr_rows)}</tbody>"
        "</table></div></div>"
    )


def render_key_candidates(key_candidates: list[KeyCandidate]) -> str:
    """Render primary key and identifier candidate table."""
    if not key_candidates:
        return ""
    key_rows = []
    for key in key_candidates:
        key_rows.append(
            f"<tr>"
            f"<td class='font-mono font-bold'>{escape(key.column)}</td>"
            f"<td class='text-right font-mono'>{key.unique_count:,}</td>"
            f"<td><span class='badge badge-success'>"
            f"Primary Key Candidate (100% Unique)</span></td>"
            f"</tr>"
        )
    return (
        "<div class='section-card'>"
        "<div class='section-title'>Key & Identifier Candidates</div>"
        "<div class='table-container'>"
        "<table class='data-table'>"
        "<thead><tr>"
        "<th>Column</th><th class='text-right'>Unique Values</th>"
        "<th>Candidate Status</th>"
        "</tr></thead>"
        f"<tbody>{' '.join(key_rows)}</tbody>"
        "</table></div></div>"
    )
