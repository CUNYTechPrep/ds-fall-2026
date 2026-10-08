"""Two Inks, Five Stars: a risograph-zine dashboard of the MovieLens 100K ratings.

Run:  streamlit run Mohammad_Bahar_week4_HM.py
"""
import html
import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from plotly.subplots import make_subplots

# --------------------------------------------------------------------------
# Palette: two "inks" (violet + pink) on grey-lilac stock, sunflower as the
# fill/highlight ink. Sunflower is too light to carry thin marks on this stock,
# so it only ever appears as a fill with a violet outline, or as a highlight.
# --------------------------------------------------------------------------
STOCK = "#E7E4EF"       # page
PANEL = "#F4F2F8"       # chart panels
INK = "#1A1330"         # text
MUTED = "#5E5878"       # secondary text
VIOLET = "#3A2377"      # ink 1: above average / primary marks
PINK = "#D61F69"        # ink 2: below average / drop-outs
SUNFLOWER = "#FFC31A"   # ink 3: fills, highlights
GRID = "rgba(58,35,119,0.14)"
FONT_DISPLAY = "Bowlby One"
FONT_BODY = "Courier Prime"
# Set on every figure: Streamlit otherwise repaints the plot paper and font with its own theme.
SURFACE = dict(paper_bgcolor=PANEL, plot_bgcolor=PANEL,
               font=dict(family=f"{FONT_BODY}, monospace", size=13, color=INK))

# Data-honesty knobs (all explained in the page copy)
MIN_GENRE_RATINGS = 500   # chart 2: genres with fewer ratings sit out
MIN_YEAR_RATINGS = 30     # chart 3: release years with fewer ratings are hidden
DATA_PATH = Path(__file__).parent / "data" / "movie_ratings.csv"

st.set_page_config(
    page_title="Two Inks, Five Stars",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# One custom Plotly template, used by every chart
# --------------------------------------------------------------------------
_axis = dict(
    gridcolor=GRID, zeroline=False, linecolor=INK, linewidth=1.5,
    ticks="outside", tickcolor=INK, automargin=True,
    title=dict(font=dict(size=12, color=MUTED)), tickfont=dict(size=12, color=INK),
)
pio.templates["riso"] = go.layout.Template(
    layout=dict(
        font=dict(family=f"{FONT_BODY}, monospace", size=13, color=INK),
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        colorway=[VIOLET, PINK, SUNFLOWER],
        xaxis=_axis,
        yaxis=_axis,
        hoverlabel=dict(
            bgcolor=INK, bordercolor=PINK,
            font=dict(family=f"{FONT_BODY}, monospace", color=STOCK, size=13),
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.2, x=0, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=20, t=20, b=10),
    )
)

# --------------------------------------------------------------------------
# One injected CSS block
# --------------------------------------------------------------------------
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bowlby+One&family=Courier+Prime:ital,wght@0,400;0,700;1,400&display=swap');
:root {{ --stock:{STOCK}; --panel:{PANEL}; --ink:{INK}; --muted:{MUTED};
        --violet:{VIOLET}; --pink:{PINK}; --sun:{SUNFLOWER}; }}

html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {{
  background: var(--stock); color: var(--ink); font-family:'{FONT_BODY}', monospace; }}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] {{ visibility:hidden; display:none; }}
header[data-testid="stHeader"] {{ background:transparent; }}
.block-container {{ max-width:1180px; padding-top:1.4rem; padding-bottom:3rem; }}
p, li, label, span, div {{ font-family:'{FONT_BODY}', monospace; }}
/* headings wrap their text in a span, so the rule above must not reach them */
.masthead h1, .masthead h1 *, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h2 *,
.headline, .headline * {{ font-family:'{FONT_DISPLAY}', sans-serif !important; }}

/* masthead */
.kicker {{ display:inline-block; background:var(--pink); color:#fff; font-weight:700;
  letter-spacing:.14em; text-transform:uppercase; font-size:.78rem; padding:.2rem .6rem;
  transform:rotate(-1.4deg); }}
.masthead h1 {{ font-family:'{FONT_DISPLAY}', sans-serif !important; font-weight:400;
  font-size:clamp(2.6rem, 8vw, 5.6rem); line-height:.95; margin:.5rem 0 .2rem;
  color:var(--violet); text-shadow:5px 4px 0 var(--pink); letter-spacing:.035em; padding:0; }}
.masthead .tagline {{ font-size:1.12rem; max-width:46rem; margin:.9rem 0 .6rem; }}
.halftone {{ height:18px; margin:.5rem 0 1.6rem;
  background-image:radial-gradient(var(--pink) 30%, transparent 32%);
  background-size:9px 9px;
  -webkit-mask-image:linear-gradient(90deg,#000 0%,transparent 100%);
          mask-image:linear-gradient(90deg,#000 0%,transparent 100%); }}

/* chart panels: bordered sheets with a misregistered shadow */
[class*="st-key-panel"] {{ background:var(--panel); border:2px solid var(--ink);
  padding:1.3rem 1.6rem 1rem; margin:0 .6rem 2.2rem 0; }}
.st-key-panel_crowd  {{ box-shadow:9px 9px 0 var(--sun); }}
.st-key-panel_mood   {{ box-shadow:9px 9px 0 var(--pink); }}
.st-key-panel_drift  {{ box-shadow:9px 9px 0 var(--violet); }}
.st-key-panel_podium {{ box-shadow:9px 9px 0 var(--sun); }}
.tag {{ display:inline-block; border:2px solid var(--violet); color:var(--violet);
  font-weight:700; letter-spacing:.12em; text-transform:uppercase; font-size:.72rem;
  padding:.05rem .5rem; transform:rotate(-1deg); }}
.headline {{ font-family:'{FONT_DISPLAY}', sans-serif; font-size:clamp(1.25rem, 2.6vw, 1.8rem);
  line-height:1.15; color:var(--violet); margin:.55rem 0 .9rem; }}
.notice {{ font-size:.95rem; margin:.2rem 0 .4rem; }}
.notice b {{ background:linear-gradient(transparent 55%, rgba(255,195,26,.75) 55%); padding:0 .15rem; }}
.empty {{ border:2px dashed var(--pink); padding:1.2rem 1.4rem; color:var(--pink);
  font-weight:700; background:var(--panel); }}

/* taped-in oddity */
.oddity {{ background:var(--sun); border:2px solid var(--ink); padding:.9rem 1.3rem;
  margin:0 0 2.2rem; transform:rotate(-.6deg); box-shadow:5px 5px 0 var(--violet); max-width:46rem; }}
.oddity .tag {{ border-color:var(--ink); color:var(--ink); }}
.oddity p {{ margin:.5rem 0 0; font-size:1.02rem; }}

/* sidebar: sunflower sheet */
section[data-testid="stSidebar"] {{ background:var(--sun); border-right:3px solid var(--ink); }}
section[data-testid="stSidebar"] h2 {{ font-family:'{FONT_DISPLAY}', sans-serif; font-weight:400;
  color:var(--violet); font-size:1.5rem; }}
.slip {{ background:var(--panel); border:2px dashed var(--ink); padding:.7rem .9rem;
  font-size:.92rem; margin-top:.6rem; }}
.colophon {{ font-size:.85rem; color:var(--muted); max-width:52rem; margin-top:1rem; }}
div[data-testid="stExpander"] details {{ border:2px solid var(--ink); background:var(--panel); }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
def clean_title(raw):
    """'Shawshank Redemption, The (1994)' -> 'The Shawshank Redemption'."""
    t = re.sub(r"\s*\((\d{4}|V)\)", "", raw).strip()
    m = re.match(r"^(.+?), (The|A|An)(\s*\(.*\))?$", t)
    return f"{m.group(2)} {m.group(1)}{m.group(3) or ''}" if m else t


@st.cache_data(show_spinner="Warming up the Risograph drum…")
def load_data():
    df = pd.read_csv(DATA_PATH, usecols=["movie_id", "rating", "title", "year", "genres"])
    # 5 movies (30 ratings) have no release year; every chart is year-aware, so they sit out.
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)
    ratings = df[["movie_id", "rating", "year", "genres"]].copy()
    ratings["genre"] = ratings["genres"].str.split("|")
    ratings = ratings.drop(columns="genres")

    movies = df.drop_duplicates("movie_id")[["movie_id", "title", "year", "genres"]].copy()
    movies["label"] = movies["title"].map(clean_title)
    movies["genre"] = movies["genres"].str.split("|")
    movies = movies.drop(columns=["genres", "title"]).reset_index(drop=True)
    # Exploded views: a movie / rating counts once in EACH of its genres.
    # "unknown" is MovieLens's no-genre bucket, so it is dropped from genre charts.
    ratings_x = ratings.explode("genre").query("genre != 'unknown'")
    movies_x = movies.explode("genre").query("genre != 'unknown'")
    return ratings.drop(columns="genre"), ratings_x, movies, movies_x


ratings, ratings_x, movies, movies_x = load_data()
GENRES = sorted(movies_x["genre"].unique())
YEAR_MIN, YEAR_MAX = int(movies["year"].min()), int(movies["year"].max())

movie_stats = ratings.groupby("movie_id")["rating"].agg(n="size", mean="mean").reset_index()
movie_stats = movie_stats.merge(movies[["movie_id", "label", "year"]], on="movie_id")

# --------------------------------------------------------------------------
# Sidebar controls
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## Knobs & dials")
    picked = st.multiselect(
        "Which genres go on the drum?", GENRES, default=GENRES,
        help="A film stays on the page if it wears ANY of these tags. Empty the drum and the copier goes quiet.",
    )
    yr = st.slider(
        "Release years on the sheet", YEAR_MIN, YEAR_MAX, (YEAR_MIN, YEAR_MAX),
        help="The year the film came out, not the year it was rated. Everyone here voted in 1997–98.",
    )
    st.markdown("**The podium's bouncer**")
    floor_a = st.slider(
        "Door policy: fewest votes allowed", 10, 400, 50, step=10,
        help="Films with fewer ratings than this don't get in the room. Default 50.",
    )
    floor_b = st.slider(
        "A stricter door, for comparison", 10, 400, 150, step=10,
        help="The same list again behind a pickier bouncer. Default 150.",
    )
    st.markdown("---")
    if st.button("✂️  Pull a fortune slip"):
        pool = movie_stats[movie_stats["n"] >= 50].nlargest(100, "mean")
        st.session_state["fortune"] = pool.sample(1).iloc[0].to_dict()
    if "fortune" in st.session_state:
        f = st.session_state["fortune"]
        st.markdown(
            f'<div class="slip">Tonight, 943 strangers recommend:<br><b>{html.escape(f["label"])}</b>'
            f' ({f["year"]}), {f["mean"]:.2f} ★ from {int(f["n"]):,} votes.</div>',
            unsafe_allow_html=True,
        )

# --------------------------------------------------------------------------
# Masthead
# --------------------------------------------------------------------------
st.markdown(
    f"""<div class="masthead">
<span class="kicker">a photocopied field guide</span>
<h1>Two Inks,<br>Five Stars</h1>
<p class="tagline">{len(ratings):,} opinions about {len(movies):,} movies, run through the copier
until only the arguments were left.</p>
<div class="halftone"></div></div>""",
    unsafe_allow_html=True,
)

# Surprising fact, computed from the whole data set (ignores the filters on purpose)
perfect = movie_stats[movie_stats["mean"] == 5]
if len(perfect):
    top_perfect = perfect.nlargest(1, "n").iloc[0]
    st.markdown(
        f"""<div class="oddity"><span class="tag">taped-in oddity</span>
<p><b>{len(perfect)} movies have a flawless 5.00 average.</b> The busiest of them,
<i>{html.escape(top_perfect['label'])}</i>, got just {int(top_perfect['n'])} votes. Perfection is cheap when nobody's counting,
which is why the podium below has a door policy.</p></div>""",
        unsafe_allow_html=True,
    )


def panel_header(tag, headline, notice):
    st.markdown(
        f'<span class="tag">{tag}</span><div class="headline">{headline}</div>'
        f'<div class="notice"><b>What to notice —</b> {notice}</div>',
        unsafe_allow_html=True,
    )


def empty(msg):
    st.markdown(f'<div class="empty">{msg}</div>', unsafe_allow_html=True)


PLOT_CFG = {"displayModeBar": False}

if not picked:
    empty("The drum is empty. Pick at least one genre in the margin and the copier will start up again.")
    st.stop()

# --------------------------------------------------------------------------
# Shared filters: genre tags + release-year range
# --------------------------------------------------------------------------
sel = set(picked)
y0, y1 = yr
movies_ok = movies[movies["year"].between(y0, y1) & movies["genre"].map(lambda g: bool(sel & set(g)))]
ratings_ok = ratings[ratings["movie_id"].isin(movies_ok["movie_id"])]
if movies_ok.empty:
    empty("No films wear those tags in those years. Widen the year range or add a genre.")
    st.stop()

# ==========================================================================
# CHART 1: genre breakdown (distinct movies per genre, via exploded genres)
# ==========================================================================
with st.container(key="panel_crowd"):
    g_counts = (
        movies_x[movies_x["year"].between(y0, y1) & movies_x["genre"].isin(sel)]
        .groupby("genre")["movie_id"].nunique().sort_values(ascending=False)
    )
    if g_counts.empty:
        empty("Nothing to count. Widen the years or pick another genre.")
    else:
        top = list(g_counts.index[:2])
        union = movies_ok["genre"].map(lambda g: bool(set(top) & set(g))).mean()
        head = (f"{top[0]} and {top[1]} tag {union:.0%} of the films on this sheet"
                if len(top) == 2 else f"{top[0]} is the only genre on this sheet: {g_counts.iloc[0]:,} films")
        tags_per = g_counts.sum() / len(movies_ok)
        panel_header(
            "The crowd", html.escape(head),
            f"the bars add up to more than the {len(movies_ok):,} films because a film counts once in "
            f"<i>every</i> genre it wears ({tags_per:.1f} tags per film, on average).",
        )
        fig = go.Figure(go.Bar(
            y=g_counts.index, x=g_counts.values, orientation="h",
            marker=dict(
                color=[VIOLET if g in top else SUNFLOWER for g in g_counts.index],
                line=dict(color=VIOLET, width=2),
            ),
            text=[f"{v:,}" for v in g_counts.values], textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x:,} distinct films<extra></extra>",
        ))
        fig.update_layout(
            template="riso", **SURFACE, height=max(220, 27 * len(g_counts) + 70),
            yaxis=dict(autorange="reversed", showgrid=False, title=None),
            xaxis=dict(title="Distinct movies rated (sorted, largest first)", range=[0, g_counts.max() * 1.12]),
            showlegend=False,
        )
        st.plotly_chart(fig, width="stretch", config=PLOT_CFG, theme=None)

# ==========================================================================
# CHART 2: genre satisfaction. Dot plot of genre mean vs. the overall mean.
# Mean = average over ALL ratings of films with that tag (not per-movie), so
# popular films weigh more; a rating counts toward each tag its film wears.
# Genres under MIN_GENRE_RATINGS ratings sit out so tiny genres can't distort it.
# ==========================================================================
with st.container(key="panel_mood"):
    rx = ratings_x[ratings_x["year"].between(y0, y1) & ratings_x["genre"].isin(sel)]
    g_mean = rx.groupby("genre")["rating"].agg(n="size", mean="mean")
    g_movies = rx.groupby("genre")["movie_id"].nunique()
    benched = g_mean[g_mean["n"] < MIN_GENRE_RATINGS]
    g_mean = g_mean[g_mean["n"] >= MIN_GENRE_RATINGS].join(g_movies.rename("movies"))
    g_mean = g_mean.sort_values("mean", ascending=False)
    overall = ratings[ratings["year"].between(y0, y1)]["rating"].mean()
    if len(g_mean) < 2:
        empty("Not enough ink for this one. Add more genres or widen the years so at least two genres clear "
              f"{MIN_GENRE_RATINGS} votes.")
    else:
        hi, lo = g_mean.index[0], g_mean.index[-1]
        gap = g_mean["mean"].iloc[0] - g_mean["mean"].iloc[-1]
        bench_txt = (f" {', '.join(benched.index)} sat out (under {MIN_GENRE_RATINGS} votes)." if len(benched) else "")
        panel_header(
            "The mood",
            f"{hi} is the crowd-pleaser at {g_mean['mean'].iloc[0]:.2f} ★; {lo} is the tough room at {g_mean['mean'].iloc[-1]:.2f} ★",
            f"the whole spread is only {gap:.2f} stars, and the axis is zoomed to show it, so don't read dot distance as a landslide.{bench_txt}",
        )
        fig = go.Figure()
        for name, mask, color in (
            ("Above the overall average", g_mean["mean"] >= overall, VIOLET),
            ("Below the overall average", g_mean["mean"] < overall, PINK),
        ):
            d = g_mean[mask]
            # stem from the overall mean out to the dot
            sx, sy = [], []
            for g, m in d["mean"].items():
                sx += [overall, m, None]
                sy += [g, g, None]
            fig.add_trace(go.Scatter(x=sx, y=sy, mode="lines", line=dict(color=color, width=2.5),
                                     hoverinfo="skip", showlegend=False))
            fig.add_trace(go.Scatter(
                x=d["mean"], y=d.index, mode="markers+text", name=name,
                marker=dict(color=color, size=14, line=dict(color=INK, width=1.5)),
                text=[f"{m:.2f}" for m in d["mean"]],
                textposition="middle right" if color == VIOLET else "middle left",
                textfont=dict(color=INK, size=12),
                customdata=np.c_[d["n"], d["movies"]],
                hovertemplate="<b>%{y}</b><br>mean %{x:.3f} ★<br>%{customdata[0]:,} ratings · %{customdata[1]:,} films<extra></extra>",
            ))
        pad = max(0.12, gap * 0.12)
        fig.add_vline(x=overall, line=dict(color=INK, width=1.5, dash="dash"))
        fig.add_annotation(x=overall, y=1.0, yref="paper", yanchor="bottom", showarrow=False,
                           text=f"all films: {overall:.2f}", font=dict(size=12, color=INK),
                           bgcolor=SUNFLOWER, bordercolor=INK, borderwidth=1.5, borderpad=3)
        fig.update_layout(
            template="riso", **SURFACE, height=max(260, 30 * len(g_mean) + 120),
            yaxis=dict(autorange="reversed", categoryorder="array", categoryarray=list(g_mean.index), showgrid=True),
            xaxis=dict(title="Mean rating (★), axis zoomed, does not start at 0",
                       range=[g_mean["mean"].min() - pad, g_mean["mean"].max() + pad]),
            margin=dict(t=40),
        )
        st.plotly_chart(fig, width="stretch", config=PLOT_CFG, theme=None)

# ==========================================================================
# CHART 3: ratings over time, by movie RELEASE year (not the year it was rated).
# Years with < MIN_YEAR_RATINGS ratings are hidden (gaps break the line, not interpolated).
# ==========================================================================
with st.container(key="panel_drift"):
    by_year = ratings_ok.groupby("year")["rating"].agg(n="size", mean="mean")
    by_year = by_year.reindex(range(y0, y1 + 1))
    by_year["n"] = by_year["n"].fillna(0)
    shown = by_year["n"] >= MIN_YEAR_RATINGS
    ym = by_year["mean"].where(shown)
    if shown.sum() < 3:
        empty(f"Too few release years clear {MIN_YEAR_RATINGS} votes to draw a line. Widen the year range or add genres.")
    else:
        yrs = by_year.index[shown]
        slope = np.polyfit(yrs, by_year.loc[shown, "mean"], 1, w=np.sqrt(by_year.loc[shown, "n"]))
        per_dec = slope[0] * 10
        if abs(per_dec) < 0.03:
            head = f"Release year barely moves the verdict: {per_dec:+.2f} ★ per decade"
        elif per_dec < 0:
            head = f"Newer films score lower: about {abs(per_dec):.2f} ★ less per decade of release"
        else:
            head = f"Newer films score higher: about {per_dec:.2f} ★ more per decade of release"
        hidden = int((~shown).sum())
        peak, trough = ym.idxmax(), ym.idxmin()
        panel_header(
            "The drift", html.escape(head),
            f"this is the year the film <i>came out</i>; every vote was cast in 1997–98. The dashed trend is weighted by votes, "
            f"the axis is zoomed, and {hidden} year{'s' if hidden != 1 else ''} with under {MIN_YEAR_RATINGS} votes "
            f"{'are' if hidden != 1 else 'is'} left blank rather than guessed.",
        )
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.76, 0.24], vertical_spacing=0.05)
        fig.add_trace(go.Scatter(
            x=ym.index, y=ym.values, mode="lines+markers", name="Mean rating by release year",
            line=dict(color=VIOLET, width=2.5), connectgaps=False,
            marker=dict(color=VIOLET, size=8, line=dict(color=PANEL, width=2)),
            customdata=by_year["n"], hovertemplate="<b>%{x}</b><br>mean %{y:.2f} ★<br>%{customdata:,.0f} ratings<extra></extra>",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=[yrs.min(), yrs.max()], y=np.polyval(slope, [yrs.min(), yrs.max()]), mode="lines",
            name="Trend (weighted by votes)", line=dict(color=PINK, width=2, dash="dash"), hoverinfo="skip",
        ), row=1, col=1)
        fig.add_trace(go.Bar(
            x=by_year.index, y=by_year["n"], name="Votes that year", showlegend=False,
            marker=dict(color=[SUNFLOWER if s else "rgba(94,88,120,0.35)" for s in shown],
                        line=dict(color=VIOLET, width=1)),
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} ratings<extra></extra>",
        ), row=2, col=1)
        for yy, txt, ax, ay in ((peak, "high", 0, -42), (trough, "low", -55, 38)):
            fig.add_annotation(
                x=yy, y=ym[yy], xref="x", yref="y", ax=ax, ay=ay, arrowhead=0, arrowwidth=1.5, arrowcolor=INK,
                text=f"{txt}: {yy}, {ym[yy]:.2f} ★", font=dict(size=12, color=INK),
                bgcolor=SUNFLOWER, bordercolor=INK, borderwidth=1.5, borderpad=3,
            )
        lo_y, hi_y = ym.min(), ym.max()
        pad = max(0.15, (hi_y - lo_y) * 0.25)
        fig.update_layout(template="riso", **SURFACE, height=520, bargap=0.15,
                          legend=dict(yanchor="bottom", y=1.0), margin=dict(t=60))
        fig.update_yaxes(title_text="Mean rating (★), axis zoomed", range=[lo_y - pad, hi_y + pad], row=1, col=1)
        fig.update_yaxes(title_text="Votes", row=2, col=1)
        fig.update_xaxes(title_text="Movie release year", row=2, col=1)
        st.plotly_chart(fig, width="stretch", config=PLOT_CFG, theme=None)

# ==========================================================================
# CHART 4: best movies behind a door policy (min ratings). A rank-change
# "bump" board between two floors. Ties in the mean break on more votes.
# ==========================================================================
with st.container(key="panel_podium"):
    stats = movie_stats[movie_stats["movie_id"].isin(movies_ok["movie_id"])]

    def board(floor):
        q = stats[stats["n"] >= floor].sort_values(["mean", "n", "label"], ascending=[False, False, True])
        q = q.reset_index(drop=True)
        q["rank"] = q.index + 1
        return q.set_index("movie_id")

    A, B = board(floor_a), board(floor_b)
    ids = list(dict.fromkeys(list(A.index[:5]) + list(B.index[:5])))
    if not ids:
        empty(f"Nobody gets past a door policy of {floor_a} votes with these filters. Lower the bouncer's standards.")
    else:
        kept = len(set(A.index[:5]) & set(B.index[:5]))
        lead_a = A["label"].iloc[0] if len(A) else None
        lead_b = B["label"].iloc[0] if len(B) else None
        if lead_a and lead_b and lead_a == lead_b:
            lead_txt = f"{lead_a} wins at both doors"
        elif lead_b:
            lead_txt = f"{lead_b} takes over at the stricter door"
        else:
            lead_txt = "nobody clears the stricter door"
        top_n = min(5, len(A))
        head = f"Raise the door from {floor_a} to {floor_b} votes and {kept} of the top {top_n} survive; {lead_txt}"
        panel_header(
            "The podium", html.escape(head),
            f"each line follows one film from the {floor_a}-vote list to the {floor_b}-vote list. Violet climbs, pink falls, "
            f"a pink X means the film couldn't get through the door. Rank is by mean rating; ties go to the film with more votes.",
        )

        ranks_max = max([5] + [int(A["rank"].get(i, 0)) for i in ids] + [int(B["rank"].get(i, 0)) for i in ids])
        off_y = ranks_max + 1.6
        lane = {"a": 0, "b": 0}

        def pos(df, i, side):
            if i in df.index:
                return int(df.loc[i, "rank"]), True
            y = off_y + 0.95 * lane[side]
            lane[side] += 1
            return y, False

        fig = go.Figure()
        any_off = False
        for i in ids:
            row = movie_stats.set_index("movie_id").loc[i]
            ya, ina = pos(A, i, "a")
            yb, inb = pos(B, i, "b")
            any_off |= not (ina and inb)
            if ina and inb:
                color = VIOLET if yb < ya else PINK if yb > ya else MUTED
                dash = "solid"
            else:
                color, dash = (PINK, "dot") if not inb else (VIOLET, "solid")
            fig.add_trace(go.Scatter(x=[0, 1], y=[ya, yb], mode="lines", showlegend=False, hoverinfo="skip",
                                     line=dict(color=color, width=3 if dash == "solid" else 2, dash=dash)))
            for x, y, ok, rk in ((0, ya, ina, ya), (1, yb, inb, yb)):
                hover = (f"<b>{html.escape(row['label'])}</b> ({int(row['year'])})<br>mean {row['mean']:.2f} ★ · "
                         f"{int(row['n']):,} votes" + (f"<br>rank #{int(rk)}" if ok else "<br>below this door"))
                fig.add_trace(go.Scatter(
                    x=[x], y=[y], mode="markers+text" if ok else "markers", showlegend=False,
                    marker=dict(size=26 if ok else 15, symbol="circle" if ok else "x",
                                color=(SUNFLOWER if rk == 1 else VIOLET) if ok else PINK,
                                line=dict(color=INK if ok else PINK, width=1.5 if ok else 3)),
                    text=[str(int(rk))] if ok else None,
                    textfont=dict(color=INK if rk == 1 else "#fff", size=12, family=FONT_BODY),
                    hovertemplate=hover + "<extra></extra>",
                ))
            # labels: titles on whichever side the film is in that side's top 5 (or a drop-out)
            lab = html.escape(row["label"] if len(row["label"]) <= 32 else row["label"][:31] + "…")
            stat = f"{row['mean']:.2f} ★ · {int(row['n']):,} votes"
            if ina and ya <= 5:
                fig.add_annotation(x=-0.05, y=ya, xanchor="right", showarrow=False, align="right",
                                   text=f"<b>{lab}</b><br>{stat}", font=dict(size=12))
            elif not ina:
                fig.add_annotation(x=-0.05, y=ya, xanchor="right", showarrow=False, align="right",
                                   text=f"<b>{lab}</b><br>✕ only {int(row['n'])} votes", font=dict(size=12, color=PINK))
            elif ya > 5:
                fig.add_annotation(x=-0.05, y=ya, xanchor="right", showarrow=False, align="right",
                                   text=f"was #{int(ya)}", font=dict(size=12, color=MUTED))
            if inb and yb <= 5:
                delta = "" if not ina else (f"  ▲ up {int(ya - yb)}" if yb < ya else f"  ▼ down {int(yb - ya)}" if yb > ya else "  ＝ same")
                fig.add_annotation(x=1.05, y=yb, xanchor="left", showarrow=False, align="left",
                                   text=f"<b>{lab}</b><br>{stat}{delta}", font=dict(size=12))
            elif not inb:
                fig.add_annotation(x=1.05, y=yb, xanchor="left", showarrow=False, align="left",
                                   text=f"<b>{lab}</b><br>✕ doesn't clear {floor_b} votes", font=dict(size=12, color=PINK))
        for x, fl in ((0, floor_a), (1, floor_b)):
            fig.add_annotation(x=x, y=1.0, yref="paper", yanchor="bottom", showarrow=False,
                               text=f"<b>DOOR: {fl}+ VOTES</b>", font=dict(size=12, color="#fff"),
                               bgcolor=VIOLET, borderpad=4)
        if any_off:
            fig.add_hline(y=off_y - 0.7, line=dict(color=PINK, width=1.5, dash="dot"))
            fig.add_annotation(x=0.5, y=off_y - 0.7, yanchor="bottom", showarrow=False,
                               text="below the door", font=dict(size=11, color=PINK), bgcolor=PANEL, borderpad=2)
        y_bottom = (off_y + 0.95 * max(lane.values()) + 0.2) if any_off else ranks_max + 0.7
        fig.update_layout(
            template="riso", **SURFACE, showlegend=False, height=int(max(420, 62 * (y_bottom - 0.3) + 90)),
            margin=dict(l=250, r=270, t=50, b=10),
            xaxis=dict(range=[-0.12, 1.12], visible=False, fixedrange=True),
            yaxis=dict(range=[y_bottom, 0.3], visible=False, showgrid=False, fixedrange=True),
        )
        st.plotly_chart(fig, width="stretch", config=PLOT_CFG, theme=None)

# --------------------------------------------------------------------------
# The numbers behind the pictures (a table view for every chart)
# --------------------------------------------------------------------------
with st.expander("Lift the flap: the raw numbers behind each picture"):
    st.markdown("**The crowd**: distinct films per genre")
    st.dataframe(g_counts.rename("films").to_frame(), width="stretch")
    if len(g_mean) >= 2:
        st.markdown("**The mood**: mean rating per genre")
        st.dataframe(g_mean.rename(columns={"n": "ratings", "mean": "mean_rating"}).round(3), width="stretch")
    if shown.sum() >= 3:
        st.markdown("**The drift**: mean rating per release year")
        st.dataframe(by_year.rename(columns={"n": "ratings", "mean": "mean_rating"}).round(3), width="stretch")
    if ids:
        st.markdown("**The podium**: both top lists")
        st.dataframe(pd.concat({f"≥{floor_a}": A.head(5), f"≥{floor_b}": B.head(5)})[["label", "year", "mean", "n"]].round(3),
                     width="stretch")

st.markdown(
    f"""<div class="colophon">Set in Bowlby One and Courier Prime, printed in two inks and a highlighter.
{len(ratings):,} ratings of {len(movies):,} films by 943 viewers, collected Sept 1997 – Apr 1998. Five films with no
release year are left off the sheet, and the 'unknown' genre bucket is skipped in the genre charts.
Made by Mohammad Bahar.</div>""",
    unsafe_allow_html=True,
)
