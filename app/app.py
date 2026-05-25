"""
app.py — Football Stats Analysis Web Application
Flask app that loads data from data/football.db and presents player
statistics, analysis results, and matplotlib charts interactively.
"""

import io
import os
import base64
import sqlite3

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # non-interactive backend — no display needed
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from flask import Flask

# ─── App setup ────────────────────────────────────────────────────────────────

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "notebooks", "data", "football.db")
DATA_DIR = os.path.join(BASE_DIR, "notebooks", "data")


# ─── Database helper ──────────────────────────────────────────────────────────

def get_db_connection():
    """Return a new SQLite connection with Row factory enabled."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def load_dataframe():
    """Load players_cleaned from the football.db SQLite database."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM players_cleaned", conn)
    conn.close()
    return df


# ─── HTML helpers ─────────────────────────────────────────────────────────────

# All top-level navigation links
_NAV_LINKS = [
    ("/",         "Home"),
    ("/players",  "Players"),
    ("/analysis", "Analysis"),
    ("/charts",   "Charts"),
]


def _nav_html(active: str) -> str:
    """Render Bootstrap 5 navbar; highlights the currently active link."""
    items = ""
    for href, label in _NAV_LINKS:
        cls = "nav-link active" if href == active else "nav-link"
        items += f'<li class="nav-item"><a class="{cls}" href="{href}">{label}</a></li>'
    return f"""
<nav class="navbar navbar-expand-lg navbar-dark bg-success shadow-sm">
  <div class="container">
    <a class="navbar-brand fw-bold fs-5" href="/">⚽ Football Stats</a>
    <button class="navbar-toggler" type="button"
            data-bs-toggle="collapse" data-bs-target="#navMenu">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navMenu">
      <ul class="navbar-nav ms-auto gap-1">{items}</ul>
    </div>
  </div>
</nav>"""


def render_page(title: str, description: str, content: str, active: str = "/") -> str:
    """Wrap page content in the full Bootstrap 5 HTML shell with navbar and footer."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} – Football Stats</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
        rel="stylesheet">
  <style>
    body             {{ background-color: #f8f9fa; }}
    .metric-card     {{ border-left: 5px solid #198754; }}
    .metric-icon     {{ font-size: 2rem; }}
    .metric-value    {{ font-size: 2rem; font-weight: 700; color: #198754; }}
    .table-hover tbody tr:hover {{ background-color: #f0fff4; }}
  </style>
</head>
<body>
{_nav_html(active)}
<div class="container py-4">
  <h1 class="mb-1">{title}</h1>
  <p class="text-muted mb-4">{description}</p>
  {content}
</div>
<footer class="text-center text-muted py-3 mt-4 border-top small">
  Football Stats Analysis — ZHAW Scientific Programming FS2026
</footer>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""


# ─── Chart helpers ────────────────────────────────────────────────────────────

def _fig_to_base64(fig) -> str:
    """Save a matplotlib Figure to a base64-encoded PNG string and close it."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=130)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def make_avg_market_value_chart(df: pd.DataFrame) -> str:
    """Bar chart: average market value per position group (returns base64 PNG)."""
    # Aggregate mean market value per position, drop positions without data
    avg_mv = (
        df.dropna(subset=["market_value_tm"])
        .groupby("position_group")["market_value_tm"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    palette = ["#198754", "#0d6efd", "#fd7e14", "#dc3545", "#6c757d"]
    fig, ax = plt.subplots(figsize=(8, 5))
    # market_value_tm is stored in €M (e.g. 22.3 = €22.3M) — use directly
    bars = ax.bar(
        avg_mv["position_group"],
        avg_mv["market_value_tm"],
        color=palette[: len(avg_mv)],
        edgecolor="white",
        linewidth=0.8,
    )

    # Annotate bar heights
    ax.bar_label(
        bars,
        labels=[f"€{v:.1f}M" for v in avg_mv["market_value_tm"]],
        padding=4,
        fontsize=10,
    )

    ax.set_title("Average Market Value per Position Group", fontsize=14, fontweight="bold")
    ax.set_xlabel("Position Group", fontsize=12)
    ax.set_ylabel("Average Market Value (€M)", fontsize=12)
    ax.set_ylim(0, avg_mv["market_value_tm"].max() * 1.2)
    plt.tight_layout()
    return _fig_to_base64(fig)


def make_age_vs_market_value_chart(df: pd.DataFrame) -> str:
    """Scatter plot: age vs market value, coloured by position (returns base64 PNG)."""
    # Drop rows with missing data in the columns we need
    plot_data = df.dropna(subset=["age", "market_value_tm", "position_group"])

    position_palette = {
        "Forward":    "#dc3545",
        "Midfielder": "#0d6efd",
        "Defender":   "#198754",
        "Goalkeeper": "#fd7e14",
        "Unknown":    "#adb5bd",
    }

    fig, ax = plt.subplots(figsize=(9, 5))

    for pos, group in plot_data.groupby("position_group"):
        # market_value_tm is in €M — use directly
        ax.scatter(
            group["age"],
            group["market_value_tm"],
            label=pos,
            color=position_palette.get(pos, "#adb5bd"),
            alpha=0.5,
            s=18,
        )

    ax.set_title("Age vs Market Value by Position Group", fontsize=14, fontweight="bold")
    ax.set_xlabel("Age (years)", fontsize=12)
    ax.set_ylabel("Market Value (€M)", fontsize=12)
    ax.legend(title="Position", fontsize=10)
    plt.tight_layout()
    return _fig_to_base64(fig)


def make_players_per_position_chart(df: pd.DataFrame) -> str:
    """Bar chart: number of players per position group (returns base64 PNG)."""
    # Count players in each position group and sort descending
    counts = (
        df["position_group"]
        .value_counts()
        .reset_index()
    )
    counts.columns = ["position_group", "count"]

    palette = ["#198754", "#0d6efd", "#fd7e14", "#dc3545", "#6c757d"]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        counts["position_group"],
        counts["count"],
        color=palette[: len(counts)],
        edgecolor="white",
        linewidth=0.8,
    )

    # Annotate each bar with its exact count
    ax.bar_label(bars, padding=4, fontsize=11)

    ax.set_title("Number of Players per Position Group", fontsize=14, fontweight="bold")
    ax.set_xlabel("Position Group", fontsize=12)
    ax.set_ylabel("Number of Players", fontsize=12)
    ax.set_ylim(0, counts["count"].max() * 1.15)
    plt.tight_layout()
    return _fig_to_base64(fig)


def make_top_nationalities_chart(df: pd.DataFrame, top_n: int = 10) -> str:
    """Bar chart: top N nationalities by player count (returns base64 PNG)."""
    top_nat = (
        df["nationality"]
        .value_counts()
        .head(top_n)
        .reset_index()
    )
    top_nat.columns = ["nationality", "count"]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(
        top_nat["nationality"],
        top_nat["count"],
        color=sns.color_palette("Greens_d", top_n),
        edgecolor="white",
        linewidth=0.8,
    )

    # Annotate each bar
    ax.bar_label(bars, padding=3, fontsize=10)

    ax.set_title(f"Top {top_n} Nationalities by Player Count", fontsize=14, fontweight="bold")
    ax.set_xlabel("Nationality", fontsize=12)
    ax.set_ylabel("Number of Players", fontsize=12)
    ax.set_ylim(0, top_nat["count"].max() * 1.15)
    ax.tick_params(axis="x", rotation=30)
    plt.tight_layout()
    return _fig_to_base64(fig)


def make_age_distribution_chart(df: pd.DataFrame) -> str:
    """Boxplot: age distribution per position group (returns base64 PNG)."""
    # Drop rows where age is missing before plotting
    age_data = df.dropna(subset=["age", "position_group"])

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(
        data=age_data,
        x="position_group",
        y="age",
        palette="Purples",
        ax=ax,
    )

    ax.set_title("Age Distribution per Position Group", fontsize=14, fontweight="bold")
    ax.set_xlabel("Position Group", fontsize=12)
    ax.set_ylabel("Age (years)", fontsize=12)
    plt.tight_layout()
    return _fig_to_base64(fig)


def make_correlation_matrix_chart(df: pd.DataFrame) -> str:
    """Heatmap of the Pearson correlation matrix for all numeric columns (returns base64 PNG)."""
    # Keep only numeric columns that actually vary
    numeric_df = df.select_dtypes(include=[np.number]).dropna(axis=1, how="all")

    corr = numeric_df.corr()

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        linewidths=0.4,
        ax=ax,
    )

    ax.set_title("Correlation Matrix of Numeric Player Attributes",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    return _fig_to_base64(fig)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    """Home page: project overview and 4 summary metric cards."""
    df = load_dataframe()

    total_players       = len(df)
    unique_teams        = df["team_id"].nunique() if "team_id" in df.columns else "–"
    unique_nationalities = df["nationality"].nunique() if "nationality" in df.columns else "–"
    players_with_mv     = int(df["market_value_tm"].notna().sum()) if "market_value_tm" in df.columns else 0

    metrics = [
        ("👤", f"{total_players:,}",          "Total Players"),
        ("🏟️",  str(unique_teams),             "Unique Teams"),
        ("🌍", str(unique_nationalities),      "Unique Nationalities"),
        ("💶", f"{players_with_mv:,}",         "Players with Market Value"),
    ]

    # Build metric card grid
    cards_html = ""
    for icon, value, label in metrics:
        cards_html += f"""
  <div class="col-sm-6 col-md-3">
    <div class="card metric-card shadow-sm h-100">
      <div class="card-body text-center py-4">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="text-muted small mt-1">{label}</div>
      </div>
    </div>
  </div>"""

    content = f"""
<div class="row g-4 mb-5">
{cards_html}
</div>

<div class="card shadow-sm">
  <div class="card-body">
    <h5 class="card-title">About this project</h5>
    <p class="card-text">
      This dashboard analyses a dataset of professional football players collected from
      Transfermarkt. The data pipeline covers scraping, cleaning, feature engineering,
      exploratory analysis, correlation and regression statistics, and market value
      insights across positions and nationalities.
    </p>
    <a href="/players"  class="btn btn-success me-2">Browse Players →</a>
    <a href="/analysis" class="btn btn-outline-success me-2">View Analysis →</a>
    <a href="/charts"   class="btn btn-outline-success">View Charts →</a>
  </div>
</div>"""

    return render_page(
        title="Football Stats Analysis",
        description="Welcome to the football player statistics dashboard.",
        content=content,
        active="/",
    )


@app.route("/players")
def players():
    """Player table — all players sorted by market value, searchable client-side."""
    df = load_dataframe()

    # Select and order the display columns (skip any that are absent)
    display_cols = ["name", "position_group", "nationality", "age", "market_value_tm"]
    cols = [c for c in display_cols if c in df.columns]

    table_df = (
        df[cols]
        .sort_values("market_value_tm", ascending=False)
        .reset_index(drop=True)
    )

    # Table header
    col_labels = {
        "name":             "Name",
        "position_group":   "Position",
        "nationality":      "Nationality",
        "age":              "Age",
        "market_value_tm":  "Market Value (€M)",
    }
    thead = "".join(f"<th>{col_labels.get(c, c)}</th>" for c in cols)

    # Table rows
    rows_html = ""
    for _, row in table_df.iterrows():
        cells = ""
        for col in cols:
            val = row[col]
            if col == "market_value_tm" and pd.notna(val):
                cells += f"<td>€{val:.1f}M</td>"
            elif pd.isna(val):
                cells += "<td class='text-muted'>–</td>"
            else:
                cells += f"<td>{val}</td>"
        rows_html += f"<tr>{cells}</tr>"

    content = f"""
<div class="mb-3">
  <input type="text" id="tableSearch" class="form-control form-control-lg"
         placeholder="Search by name, nationality, position…">
</div>
<div class="table-responsive">
  <table class="table table-hover table-bordered table-sm" id="playersTable">
    <thead class="table-success sticky-top"><tr>{thead}</tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>
<small class="text-muted">
  Showing <span id="rowCount" class="fw-bold">{len(table_df)}</span>
  of {len(table_df):,} players
</small>

<script>
// Client-side search: hide rows that don't match the search term
const searchInput = document.getElementById("tableSearch");
const tableRows   = document.querySelectorAll("#playersTable tbody tr");
const rowCounter  = document.getElementById("rowCount");

searchInput.addEventListener("input", function () {{
  const term = this.value.toLowerCase();
  let visible = 0;
  tableRows.forEach(row => {{
    const match = row.textContent.toLowerCase().includes(term);
    row.style.display = match ? "" : "none";
    if (match) visible++;
  }});
  rowCounter.textContent = visible;
}});
</script>"""

    return render_page(
        title="Player Table",
        description=f"All {len(table_df):,} players sorted by market value. Use the search box to filter instantly.",
        content=content,
        active="/players",
    )


@app.route("/analysis")
def analysis():
    """Analysis page: top 10 players, avg market value per position, t-test result."""
    df = load_dataframe()

    # ── Top 10 most valuable players ──────────────────────────────────────────
    top_cols = ["name", "position_group", "nationality", "age", "market_value_tm"]
    top_cols = [c for c in top_cols if c in df.columns]
    top10 = (
        df.dropna(subset=["market_value_tm"])
        .sort_values("market_value_tm", ascending=False)
        .head(10)[top_cols]
        .reset_index(drop=True)
    )

    top10_header = "".join(
        f"<th>{c.replace('_', ' ').replace('tm', '(€)').title()}</th>"
        for c in top_cols
    )
    top10_rows = ""
    for rank, (_, row) in enumerate(top10.iterrows(), start=1):
        cells = f"<td class='fw-bold text-success'>{rank}</td>"
        for col in top_cols:
            val = row[col]
            if col == "market_value_tm" and pd.notna(val):
                cells += f"<td>€{val:.1f}M</td>"
            elif pd.isna(val):
                cells += "<td class='text-muted'>–</td>"
            else:
                cells += f"<td>{val}</td>"
        top10_rows += f"<tr>{cells}</tr>"

    # ── Average market value per position group ────────────────────────────────
    avg_mv = (
        df.dropna(subset=["market_value_tm"])
        .groupby("position_group")["market_value_tm"]
        .agg(mean="mean", median="median", count="count")
        .sort_values("mean", ascending=False)
        .reset_index()
    )

    avg_rows = ""
    for _, row in avg_mv.iterrows():
        avg_rows += (
            f"<tr>"
            f"<td>{row['position_group']}</td>"
            f"<td>€{row['mean']:.1f}M</td>"
            f"<td>€{row['median']:.1f}M</td>"
            f"<td>{int(row['count'])}</td>"
            f"</tr>"
        )

    # ── T-test: Forwards vs Defenders ─────────────────────────────────────────
    forwards  = df.loc[df["position_group"] == "Forward",  "market_value_tm"].dropna()
    defenders = df.loc[df["position_group"] == "Defender", "market_value_tm"].dropna()

    t_stat, p_value = stats.ttest_ind(forwards, defenders, equal_var=False)

    if p_value < 0.05:
        badge_color   = "success"
        badge_label   = "✓ Significant"
        interpretation = (
            f"p = {p_value:.4f} &lt; 0.05 → statistically significant difference "
            f"in market values between Forwards and Defenders."
        )
    else:
        badge_color   = "warning"
        badge_label   = "✗ Not Significant"
        interpretation = (
            f"p = {p_value:.4f} ≥ 0.05 → no statistically significant difference "
            f"in market values between Forwards and Defenders."
        )

    content = f"""

<!-- Top 10 most valuable players -->
<h4 class="mt-2">🏆 Top 10 Most Valuable Players</h4>
<div class="table-responsive mb-5">
  <table class="table table-hover table-bordered table-sm">
    <thead class="table-success">
      <tr><th>#</th>{top10_header}</tr>
    </thead>
    <tbody>{top10_rows}</tbody>
  </table>
</div>

<!-- Average market value per position -->
<h4>💶 Average Market Value per Position Group</h4>
<div class="table-responsive mb-5">
  <table class="table table-hover table-bordered table-sm" style="max-width:580px">
    <thead class="table-success">
      <tr>
        <th>Position Group</th>
        <th>Mean</th>
        <th>Median</th>
        <th>Players</th>
      </tr>
    </thead>
    <tbody>{avg_rows}</tbody>
  </table>
</div>

<!-- T-test: Forwards vs Defenders -->
<h4>📊 T-test: Forwards vs Defenders (Market Value)</h4>
<div class="card shadow-sm mb-4" style="max-width:560px">
  <div class="card-body">
    <table class="table table-sm mb-3">
      <tbody>
        <tr><th scope="row">Forwards (n)</th>   <td>{len(forwards):,}</td></tr>
        <tr><th scope="row">Defenders (n)</th>  <td>{len(defenders):,}</td></tr>
        <tr><th scope="row">Forwards mean</th>  <td>€{forwards.mean():.1f}M</td></tr>
        <tr><th scope="row">Defenders mean</th> <td>€{defenders.mean():.1f}M</td></tr>
        <tr><th scope="row">t-statistic</th>    <td>{t_stat:.4f}</td></tr>
        <tr><th scope="row">p-value</th>
            <td><strong>p = {p_value:.4f}</strong></td></tr>
      </tbody>
    </table>
    <div class="alert alert-{badge_color} mb-0 py-2">
      <strong>{badge_label}:</strong> {interpretation}
    </div>
  </div>
</div>"""

    return render_page(
        title="Analysis",
        description="Top players, position market value statistics, and the Forwards vs Defenders t-test.",
        content=content,
        active="/analysis",
    )


@app.route("/charts")
def charts():
    """Charts page — 6 matplotlib/seaborn charts embedded as base64 PNG images."""
    df = load_dataframe()

    # Generate all six charts; each returns a base64-encoded PNG string
    positions_b64    = make_players_per_position_chart(df)
    nationalities_b64 = make_top_nationalities_chart(df)
    age_box_b64      = make_age_distribution_chart(df)
    corr_b64         = make_correlation_matrix_chart(df)
    avg_mv_b64       = make_avg_market_value_chart(df)
    scatter_b64      = make_age_vs_market_value_chart(df)

    # Each entry: (title, description, alt-text, base64 string)
    chart_cards = [
        (
            "Players per Position",
            "Number of players in each position group across all Premier League squads.",
            "Bar chart: players per position group",
            positions_b64,
        ),
        (
            "Top 10 Nationalities",
            "The ten most common nationalities represented in the dataset.",
            "Bar chart: top 10 nationalities by player count",
            nationalities_b64,
        ),
        (
            "Age Distribution per Position",
            "Boxplot of player ages split by position — shows median, spread, and outliers.",
            "Boxplot: age distribution per position group",
            age_box_b64,
        ),
        (
            "Correlation Matrix",
            "Pearson correlation heatmap of all numeric player attributes.",
            "Heatmap: correlation matrix of numeric columns",
            corr_b64,
        ),
        (
            "Average Market Value per Position",
            "Mean player market value in €M, grouped by field position.",
            "Bar chart: average market value per position",
            avg_mv_b64,
        ),
        (
            "Age vs Market Value by Position",
            "Each dot is one player; colour indicates position group.",
            "Scatter plot: age vs market value coloured by position",
            scatter_b64,
        ),
    ]

    # Build 2-column Bootstrap grid — one card per chart
    cards_html = ""
    for title, description, alt, b64 in chart_cards:
        cards_html += f"""
  <div class="col-lg-6">
    <div class="card shadow-sm h-100">
      <div class="card-body">
        <h5 class="card-title">{title}</h5>
        <p class="text-muted small mb-2">{description}</p>
        <img src="data:image/png;base64,{b64}"
             class="img-fluid rounded"
             alt="{alt}">
      </div>
    </div>
  </div>"""

    content = f'<div class="row g-4">{cards_html}\n</div>'

    return render_page(
        title="Charts",
        description="Six matplotlib/seaborn visualisations of the football player dataset.",
        content=content,
        active="/charts",
    )


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
