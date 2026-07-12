"""Streamlit-Dashboard (v2) im Nordzucker-Style — mit Befragungs-Admin.

Auswertung  = nur Nordzucker, konfigurierbarer Chart-Baukasten.
Vergleich   = Nordzucker vs. Wettbewerber (Radar).
Bewertungen = Datenexplorer mit Filter & Suche.
RAG-Chat    = Fragen an die Bewertungen.
Befragung   = Mails eintragen, QR/Link, Einladungen senden, Antworten einlesen.
"""
import json
import datetime as dt
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import config
import schema

st.set_page_config(page_title="Nordzucker Mitarbeiterfeedback", page_icon="🌿", layout="wide")

BLUE = "#0033A0"
GREEN = "#5BB12F"
GREY = "#C2CCD6"
RED = "#E2574C"
MUTED = "#667085"
PALETTE = {"positiv": GREEN, "neutral": GREY, "negativ": RED}
GREEN_SCALE = ["#CFE8BD", GREEN]

RATING_LABELS = {
    "arbeitsatmosphaere": "Arbeitsatmosphäre", "work_life_balance": "Work-Life-Balance",
    "gehalt": "Gehalt", "karriere": "Karriere", "vorgesetzte": "Vorgesetzte",
    "gleichberechtigung": "Gleichberechtigung", "image": "Image",
    "umwelt_sozial": "Umwelt & Soziales", "kollegen": "Kollegenzusammenhalt",
    "umgang_aeltere": "Umgang mit älteren Kollegen", "arbeitsbedingungen": "Arbeitsbedingungen",
    "kommunikation": "Kommunikation", "interessante_aufgaben": "Interessante Aufgaben",
}

STOPWORDS_DE = {
    "und", "oder", "aber", "auch", "dass", "weil", "wenn", "denn", "doch", "sowie",
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "einem", "einen",
    "eines", "kein", "keine", "keiner", "ist", "sind", "war", "waren", "wird", "werden",
    "wurde", "wurden", "sein", "seine", "seiner", "hat", "habe", "haben", "hatte", "hatten",
    "kann", "koennen", "konnte", "muss", "muessen", "soll", "sollen", "will", "wollen",
    "wuerde", "wuerden", "ich", "du", "er", "sie", "es", "wir", "ihr", "man", "mich",
    "mir", "dich", "dir", "sich", "uns", "euch", "ihm", "ihn", "ihnen", "mein", "dein",
    "fuer", "mit", "ohne", "bei", "von", "vom", "zum", "zur", "zu", "an", "am", "auf",
    "aus", "in", "im", "ins", "ueber", "unter", "vor", "nach", "durch", "gegen", "um",
    "als", "wie", "so", "noch", "nur", "schon", "sehr", "mehr", "viel", "viele", "etwas",
    "alle", "allem", "alles", "jede", "jeder", "jedes", "diese", "dieser", "dieses",
    "nicht", "nichts", "ja", "nein", "hier", "dort", "da", "dann", "immer", "wieder",
    "machen", "macht", "gibt", "gut", "gute", "guter", "gutes", "schlecht",
    "ganz", "mal", "eher", "teilweise", "manche", "manchmal", "oft", "meist", "bisschen",
    "arbeitgeber", "arbeitgebers", "unternehmen", "firma", "nordzucker", "vw", "fs",
    "the", "and", "for", "with", "are", "was", "this", "that", "you", "but", "not",
    "für", "über", "wäre", "wären", "würde", "würden", "müssen", "müsste", "können",
    "könnte", "könnten", "möchte", "mögen", "während", "natürlich", "hätte", "hätten",
    "dürfen", "größer", "größere", "schöne", "schön", "täglich", "ständig", "öfter",
    "work", "life", "good", "very", "they", "have", "from",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
.stApp { background: #F4F6F9; }
#MainMenu, footer, [data-testid="stStatusWidget"] { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; padding-bottom: 2rem; max-width: 1520px; }
section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E8ECF2; }
.brand { display:flex; align-items:center; gap:11px; padding:2px 2px 18px; }
.brand-name { font-size:23px; font-weight:800; color:#0033A0; letter-spacing:-.3px; }
.page-title { font-size:30px; font-weight:800; color:#0F1C3F; margin:0 0 16px; letter-spacing:-.5px; }
.kpi-row { display:flex; gap:18px; margin:2px 0 12px; flex-wrap:wrap; }
.kpi-card { flex:1; min-width:190px; background:#fff; border:1px solid #EAEEF3; border-radius:16px;
  padding:18px 22px; display:flex; align-items:center; gap:16px; box-shadow:0 1px 2px rgba(16,24,40,.05); }
.kpi-icon { width:48px; height:48px; border-radius:13px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.kpi-icon svg { width:24px; height:24px; }
.icon-blue { background:#E8EEFB; color:#0033A0; }
.icon-green { background:#E9F6E7; color:#5BB12F; }
.kpi-label { color:#667085; font-size:14px; margin-bottom:3px; }
.kpi-value { font-size:30px; font-weight:800; line-height:1; color:#0033A0; }
.kpi-value.green { color:#5BB12F; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border:1px solid #EAEEF3 !important;
  border-radius:16px; box-shadow:0 1px 2px rgba(16,24,40,.05); padding:6px 14px 10px; }
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] { box-shadow:none; }
.card-title { font-size:17px; font-weight:700; color:#0F1C3F; margin:6px 2px 4px; }
.stTabs [data-baseweb="tab-list"] { gap:26px; border-bottom:1px solid #E6EAF0; }
.stTabs [data-baseweb="tab"] { height:46px; padding:0 2px; color:#667085; font-weight:600; font-size:15px; }
.stTabs [aria-selected="true"] { color:#0033A0 !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color:#0033A0; height:3px; }
.stButton button { background:#0033A0; color:#fff; border:none; border-radius:10px; font-weight:600; padding:.45rem 1rem; }
.stButton button:hover { background:#002577; color:#fff; }
h1,h2,h3 { color:#0F1C3F; }
.app-footer { display:flex; justify-content:space-between; color:#98A2B3; font-size:13px;
  margin-top:18px; padding-top:14px; border-top:1px solid #E6EAF0; }
</style>
"""

ICONS = {
    "chat": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    "star": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><polygon points="12 2 15.1 8.6 22 9.3 16.8 14 18.2 21 12 17.3 5.8 21 7.2 14 2 9.3 8.9 8.6 12 2"/></svg>',
    "smile": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 14.5s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9.2" x2="9.01" y2="9.2"/><line x1="15" y1="9.2" x2="15.01" y2="9.2"/></svg>',
    "layers": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
}
LEAF = ('<svg width="30" height="30" viewBox="0 0 24 24" fill="none">'
        '<path d="M4 20c0-7 6-13 16-15-1 9-6 15-13 15-1 0-3-.3-3-.3z" fill="#7AB51D"/>'
        '<path d="M3 21c3-5 7-7 9-8" stroke="#0033A0" stroke-width="1.6" stroke-linecap="round"/></svg>')


def _style(fig, h=300, showlegend=False):
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, Segoe UI, sans-serif", color=MUTED, size=13),
                      height=h, margin=dict(t=12, l=8, r=8, b=8), showlegend=showlegend,
                      legend=dict(orientation="h", y=-0.15))
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#EEF1F5", zeroline=False)
    return fig


def card_title(t):
    st.markdown(f'<div class="card-title">{t}</div>', unsafe_allow_html=True)


@st.cache_data
def load_data():
    df = pd.read_csv(config.ENRICHED_CSV)
    df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
    if "is_duplicate" in df:
        df = df[~df["is_duplicate"].fillna(False)]
    for col in ["kategorien", "keywords"]:
        if col in df:
            df[col] = df[col].map(lambda x: json.loads(x) if isinstance(x, str) and x.startswith("[") else [])
    if "unternehmen" not in df:
        df["unternehmen"] = config.HAUPTUNTERNEHMEN
    return df


def kpi_cards(df):
    pos = (df["sentiment"] == "positiv").mean() * 100 if "sentiment" in df else 0
    cards = [
        ("chat", "blue", "Bewertungen", f"{len(df)}", False),
        ("star", "blue", "Ø Gesamtscore", f"{df['gesamt_score'].mean():.2f}", False),
        ("smile", "green", "Positiv-Anteil", f"{pos:.0f}%", True),
        ("layers", "blue", "Quellen", f"{df['source'].nunique()}", False),
    ]
    html = '<div class="kpi-row">'
    for icon, color, label, value, green in cards:
        html += (f'<div class="kpi-card"><div class="kpi-icon icon-{color}">{ICONS[icon]}</div>'
                 f'<div><div class="kpi-label">{label}</div>'
                 f'<div class="kpi-value {"green" if green else ""}">{value}</div></div></div>')
    st.markdown(html + "</div>", unsafe_allow_html=True)


# ---------------- Chart-Bausteine ----------------
def c_sentiment(df):
    v = df["sentiment"].value_counts().reindex(["positiv", "neutral", "negativ"]).fillna(0)
    fig = px.bar(x=v.index, y=v.values, color=v.index, color_discrete_map=PALETTE, text=v.values.astype(int))
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    st.plotly_chart(_style(fig), use_container_width=True)


def c_trend(df):
    d = df.dropna(subset=["datum"]).copy()
    if d.empty:
        st.info("Keine Datumsangaben."); return
    d["monat"] = d["datum"].dt.to_period("M").dt.to_timestamp()
    g = d.groupby("monat")["gesamt_score"].mean().reset_index()
    fig = px.line(g, x="monat", y="gesamt_score", markers=True)
    fig.update_traces(line_color=BLUE, line_width=2.5, marker=dict(size=6, color=BLUE),
                      fill="tozeroy", fillcolor="rgba(0,51,160,.07)")
    fig.update_layout(xaxis_title=None, yaxis_title="Ø Score", yaxis_range=[1, 5])
    st.plotly_chart(_style(fig), use_container_width=True)


def c_dimensionen(df):
    dims = [c for c in schema.ALL_RATINGS if c in df]
    m = df[dims].mean().dropna().sort_values()
    if m.empty:
        st.info("Keine Bewertungsdimensionen."); return
    g = pd.DataFrame({"thema": [RATING_LABELS.get(i, i) for i in m.index], "score": m.values})
    fig = px.bar(g, x="score", y="thema", orientation="h", color="score", range_color=[1, 5],
                 color_continuous_scale=GREEN_SCALE, text=g["score"].map(lambda v: f"{v:.2f}"))
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(xaxis_title=None, yaxis_title=None, coloraxis_showscale=False, xaxis_range=[0, 5.4])
    st.plotly_chart(_style(fig, 340), use_container_width=True)


def c_ki_themen(df):
    rows = [(k, r["gesamt_score"]) for _, r in df.iterrows() for k in (r.get("kategorien") or [])]
    if not rows:
        st.info("Keine KI-Kategorien (volle Anreicherung: `py 03_enrich.py`)."); return
    kd = pd.DataFrame(rows, columns=["kat", "score"])
    g = (kd.groupby("kat").agg(score=("score", "mean"), n=("score", "size"))
         .reset_index().sort_values("n", ascending=False).head(8).sort_values("score"))
    fig = px.bar(g, x="score", y="kat", orientation="h", color="score", range_color=[1, 5],
                 color_continuous_scale=GREEN_SCALE, text=g["score"].map(lambda v: f"{v:.2f}"))
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(xaxis_title=None, yaxis_title=None, coloraxis_showscale=False, xaxis_range=[0, 5.4])
    st.plotly_chart(_style(fig, 340), use_container_width=True)


def c_heatmap(df):
    cols = [c for c in schema.COMMON_RATINGS if c in df]
    g = df.groupby("bereich")[cols].mean()
    g = g.loc[g.index != "Unbekannt"].dropna(how="all")
    if g.empty:
        st.info("Zu wenige Daten."); return
    g = g.rename(columns=RATING_LABELS)
    fig = px.imshow(g, color_continuous_scale="RdYlGn", zmin=1, zmax=5, aspect="auto", labels=dict(color="Ø Score"))
    st.plotly_chart(_style(fig, 360), use_container_width=True)


def c_wordcloud(df):
    try:
        from wordcloud import WordCloud, STOPWORDS
        stops = set(STOPWORDS) | STOPWORDS_DE
    except ImportError:
        st.info("wordcloud nicht installiert."); return
    text = " ".join(str(t) for col in ["text_positiv", "text_negativ", "text_freitext", "titel"]
                    for t in df.get(col, []) if pd.notna(t))
    if len(text.strip()) < 20:
        st.info("Zu wenig Freitext."); return
    wc = WordCloud(width=800, height=320, background_color="white", stopwords=stops,
                   min_word_length=3, collocations=False, colormap="GnBu").generate(text.lower())
    st.image(wc.to_array(), use_container_width=True)


def c_score_hist(df):
    fig = px.histogram(df, x="gesamt_score", nbins=9, color_discrete_sequence=[BLUE])
    fig.update_layout(xaxis_title="Gesamtscore", yaxis_title="Anzahl", bargap=0.05)
    st.plotly_chart(_style(fig), use_container_width=True)


def c_quelle(df):
    v = df["source"].value_counts()
    fig = px.pie(values=v.values, names=v.index, hole=0.55,
                 color_discrete_sequence=["#0033A0", "#5BB12F", "#7FB2F0", "#F5C518"])
    fig.update_traces(textinfo="label+percent")
    st.plotly_chart(_style(fig, 300, showlegend=False), use_container_width=True)


def c_typ(df):
    v = df["typ"].value_counts()
    fig = px.bar(x=v.index, y=v.values, text=v.values, color_discrete_sequence=[BLUE])
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(xaxis_title=None, yaxis_title="Anzahl")
    st.plotly_chart(_style(fig), use_container_width=True)


def c_ort(df):
    g = (df[df["ort"] != "Unbekannt"].groupby("ort")["gesamt_score"].agg(["mean", "size"]).reset_index())
    g = g[g["size"] >= 2].sort_values("mean").tail(10)
    if g.empty:
        st.info("Zu wenige Standortdaten."); return
    fig = px.bar(g, x="mean", y="ort", orientation="h", range_color=[1, 5], color="mean",
                 color_continuous_scale=GREEN_SCALE, text=g["mean"].map(lambda v: f"{v:.2f}"))
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(xaxis_title="Ø Score", yaxis_title=None, coloraxis_showscale=False, xaxis_range=[0, 5.4])
    st.plotly_chart(_style(fig, 340), use_container_width=True)


def c_empfehlung(df):
    v = df["empfehlung"].value_counts()
    fig = px.pie(values=v.values, names=v.index, hole=0.55,
                 color_discrete_sequence=["#5BB12F", "#E2574C", "#C2CCD6", "#7FB2F0", "#F5C518"])
    fig.update_traces(textinfo="percent")
    st.plotly_chart(_style(fig, 300, showlegend=True), use_container_width=True)


def c_sentiment_zeit(df):
    d = df.dropna(subset=["datum"]).copy()
    if d.empty:
        st.info("Keine Datumsangaben."); return
    d["jahr"] = d["datum"].dt.year
    g = d.groupby(["jahr", "sentiment"]).size().reset_index(name="n")
    fig = px.bar(g, x="jahr", y="n", color="sentiment", color_discrete_map=PALETTE,
                 category_orders={"sentiment": ["positiv", "neutral", "negativ"]})
    fig.update_layout(xaxis_title=None, yaxis_title="Anzahl", barmode="stack")
    st.plotly_chart(_style(fig, 300, showlegend=True), use_container_width=True)


def c_bereich_score(df):
    g = (df[df["bereich"] != "Unbekannt"].groupby("bereich")["gesamt_score"].agg(["mean", "size"]).reset_index())
    g = g[g["size"] >= 2].sort_values("mean")
    if g.empty:
        st.info("Zu wenige Bereichsdaten."); return
    fig = px.bar(g, x="mean", y="bereich", orientation="h", color="mean", range_color=[1, 5],
                 color_continuous_scale=GREEN_SCALE, text=g["mean"].map(lambda v: f"{v:.2f}"))
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(xaxis_title="Ø Score", yaxis_title=None, coloraxis_showscale=False, xaxis_range=[0, 5.4])
    st.plotly_chart(_style(fig, 340), use_container_width=True)


def c_radar_self(df):
    dims = [c for c in schema.ALL_RATINGS if c in df and df[c].notna().any()]
    labels = [RATING_LABELS.get(c, c) for c in dims]
    werte = [round(df[c].mean(), 2) for c in dims]
    fig = go.Figure(go.Scatterpolar(r=werte + [werte[0]], theta=labels + [labels[0]],
                                     fill="toself", line_color=BLUE, name="Nordzucker"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[1, 5])), height=380, margin=dict(t=30, b=20),
                      paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                      font=dict(family="Inter, Segoe UI, sans-serif", color=MUTED))
    st.plotly_chart(fig, use_container_width=True)


def c_keywords(df):
    kws = [k for lst in df.get("keywords", []) for k in (lst or [])]
    if not kws:
        st.info("Keine Keywords (volle KI-Anreicherung noetig)."); return
    s = pd.Series([k.lower() for k in kws]).value_counts().head(15).sort_values()
    fig = px.bar(x=s.values, y=s.index, orientation="h", color_discrete_sequence=[GREEN])
    fig.update_layout(xaxis_title="Nennungen", yaxis_title=None)
    st.plotly_chart(_style(fig, 360), use_container_width=True)


def c_monat_count(df):
    d = df.dropna(subset=["datum"]).copy()
    if d.empty:
        st.info("Keine Datumsangaben."); return
    d["monat"] = d["datum"].dt.to_period("M").dt.to_timestamp()
    g = d.groupby("monat").size().reset_index(name="n")
    fig = px.bar(g, x="monat", y="n", color_discrete_sequence=[BLUE])
    fig.update_layout(xaxis_title=None, yaxis_title="Bewertungen")
    st.plotly_chart(_style(fig), use_container_width=True)


def c_box_bereich(df):
    d = df[df["bereich"] != "Unbekannt"]
    top = d["bereich"].value_counts().head(6).index
    d = d[d["bereich"].isin(top)]
    if d.empty:
        st.info("Zu wenige Bereichsdaten."); return
    fig = px.box(d, x="bereich", y="gesamt_score", color_discrete_sequence=[BLUE])
    fig.update_layout(xaxis_title=None, yaxis_title="Score", yaxis_range=[1, 5])
    st.plotly_chart(_style(fig, 340), use_container_width=True)


CHARTS = {
    "Sentiment-Verteilung": c_sentiment,
    "Score-Trend (Zeit)": c_trend,
    "Themen-Ranking (Ø Score)": c_dimensionen,
    "KI-Themen-Ranking": c_ki_themen,
    "Heatmap: Bereich × Dimension": c_heatmap,
    "Score-Verteilung (Histogramm)": c_score_hist,
    "Bewertungen je Quelle": c_quelle,
    "Ø Score je Standort": c_ort,
    "Empfehlungsquote": c_empfehlung,
    "Sentiment über die Jahre": c_sentiment_zeit,
    "Ø Score je Bereich": c_bereich_score,
    "Ratings-Profil (Radar)": c_radar_self,
    "Top Keywords": c_keywords,
    "Bewertungen je Monat": c_monat_count,
    "Score-Streuung je Bereich (Boxplot)": c_box_bereich,
}
DEFAULT_CHARTS = ["Sentiment-Verteilung", "Score-Trend (Zeit)", "Themen-Ranking (Ø Score)", "KI-Themen-Ranking"]


def auswertung_tab(df):
    kpi_cards(df)
    with st.container(border=True):
        st.markdown("**Dashboard zusammenstellen**")
        cc1, cc2 = st.columns([5, 1])
        if "charts" not in st.session_state:
            st.session_state["charts"] = DEFAULT_CHARTS
        cc1.multiselect("Auswertungen (Reihenfolge = Anordnung)", list(CHARTS), key="charts")
        spalten = cc2.selectbox("Spalten", [1, 2, 3], index=1)
    sel = [s for s in st.session_state["charts"] if s in CHARTS]
    if not sel:
        st.info("Wähle oben mindestens eine Auswertung aus."); return
    objs = st.columns(spalten)
    for i, name in enumerate(sel):
        with objs[i % spalten]:
            with st.container(border=True):
                card_title(name)
                CHARTS[name](df)


def vergleich_tab(df_all):
    firmen = sorted(df_all["unternehmen"].dropna().unique())
    haupt = config.HAUPTUNTERNEHMEN if config.HAUPTUNTERNEHMEN in firmen else firmen[0]
    optionen = [f for f in firmen if f != haupt]
    if not optionen:
        st.info("Keine Wettbewerbsdaten geladen."); return
    wb = st.selectbox("Wettbewerber auswählen", optionen)
    a = df_all[df_all["unternehmen"] == haupt]
    b = df_all[df_all["unternehmen"] == wb]
    c1, c2, c3 = st.columns(3)
    da = a["gesamt_score"].mean() - b["gesamt_score"].mean()
    c1.metric(f"Ø Score · {haupt}", f"{a['gesamt_score'].mean():.2f}", delta=f"{da:+.2f} vs. {wb}")
    c2.metric(f"Ø Score · {wb}", f"{b['gesamt_score'].mean():.2f}")
    pa = (a["sentiment"] == "positiv").mean() * 100
    pb = (b["sentiment"] == "positiv").mean() * 100
    c3.metric(f"Positiv · {haupt}", f"{pa:.0f}%", delta=f"{pa-pb:+.0f} %-Pkt")
    cc1, cc2 = st.columns([3, 2])
    cols = [c for c in schema.COMMON_RATINGS if c in df_all]
    labels = [RATING_LABELS.get(c, c) for c in cols]
    with cc1:
        with st.container(border=True):
            card_title("Stärkenprofil im Vergleich")
            fig = go.Figure()
            for firma, sub, color in [(haupt, a, BLUE), (wb, b, GREEN)]:
                werte = [round(sub[c].mean(), 2) for c in cols]
                fig.add_trace(go.Scatterpolar(r=werte + [werte[0]], theta=labels + [labels[0]],
                                              fill="toself", name=firma, line_color=color))
            fig.update_layout(polar=dict(radialaxis=dict(range=[1, 5])), height=430, margin=dict(t=30, b=30),
                              paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, Segoe UI, sans-serif", color=MUTED),
                              legend=dict(orientation="h", y=-0.08))
            st.plotly_chart(fig, use_container_width=True)
    with cc2:
        with st.container(border=True):
            card_title("Werte je Dimension")
            tab = pd.DataFrame({"Dimension": labels, haupt: [round(a[c].mean(), 2) for c in cols],
                                wb: [round(b[c].mean(), 2) for c in cols]})
            tab["Δ"] = (tab[haupt] - tab[wb]).round(2)
            st.dataframe(tab, use_container_width=True, hide_index=True, height=300)
    with st.container(border=True):
        card_title("Sentiment-Verteilung im Vergleich")
        sv = (df_all[df_all["unternehmen"].isin([haupt, wb])]
              .groupby(["unternehmen", "sentiment"]).size().reset_index(name="anzahl"))
        fig2 = px.bar(sv, x="sentiment", y="anzahl", color="unternehmen", barmode="group",
                      category_orders={"sentiment": ["positiv", "neutral", "negativ"]},
                      color_discrete_map={haupt: BLUE, wb: GREEN})
        fig2.update_layout(xaxis_title=None, yaxis_title=None)
        st.plotly_chart(_style(fig2, 300, showlegend=True), use_container_width=True)


def explorer_tab(df):
    with st.container(border=True):
        st.markdown("**Filter & Suche**")
        c1, c2, c3, c4 = st.columns(4)
        unt = c1.selectbox("Unternehmen", ["alle"] + sorted(df["unternehmen"].dropna().unique().tolist()), key="exp_unt")
        quelle = c2.selectbox("Quelle", ["alle"] + sorted(df["source"].dropna().unique().tolist()), key="exp_quelle")
        typ = c3.selectbox("Typ", ["alle"] + sorted(df["typ"].dropna().unique().tolist()), key="exp_typ")
        sentiment = c4.selectbox("Sentiment", ["alle", "positiv", "neutral", "negativ"], key="exp_sentiment")
        suche = st.text_input("Volltextsuche (Titel & Freitexte)", "", placeholder="z. B. Schicht, Gehalt ...")
    d = df.copy()
    if unt != "alle": d = d[d["unternehmen"] == unt]
    if quelle != "alle": d = d[d["source"] == quelle]
    if typ != "alle": d = d[d["typ"] == typ]
    if sentiment != "alle": d = d[d["sentiment"] == sentiment]
    if suche.strip():
        s = suche.lower()
        textcols = [c for c in ["titel", "text_positiv", "text_negativ", "text_verbesserung", "text_freitext"] if c in d]
        mask = pd.Series(False, index=d.index)
        for c in textcols:
            mask = mask | d[c].astype(str).str.lower().str.contains(s, na=False)
        d = d[mask]
    st.caption(f"{len(d)} von {len(df)} Bewertungen")
    dim_cols = ["arbeitsatmosphaere", "work_life_balance", "gehalt", "karriere", "vorgesetzte",
                "gleichberechtigung", "image", "umwelt_sozial", "kollegen", "umgang_aeltere",
                "arbeitsbedingungen", "kommunikation", "interessante_aufgaben"]
    show = [c for c in (["unternehmen", "source", "typ", "datum", "gesamt_score", "sentiment",
                         "position", "bereich", "ort"] + dim_cols +
                        ["titel", "text_positiv", "text_negativ", "text_verbesserung",
                         "text_freitext"]) if c in d]
    view = d[show].copy()
    if "datum" in view:
        view["datum"] = pd.to_datetime(view["datum"], errors="coerce").dt.date
    st.dataframe(view, use_container_width=True, hide_index=True, height=520,
                 column_config={"gesamt_score": st.column_config.NumberColumn("Score", format="%.1f")})
    st.download_button("Gefilterte Bewertungen als CSV", view.to_csv(index=False).encode("utf-8-sig"),
                       "bewertungen_gefiltert.csv", "text/csv")


def rag_tab(df):
    try:
        import llm, importlib
        rag = importlib.import_module("05_rag")
    except Exception as e:
        st.error(f"RAG-Modul nicht ladbar: {e}"); return
    if not llm.ollama_available():
        st.warning("Ollama laeuft nicht. Starte Ollama und baue den Index, dann ist der Chat aktiv."); return
    c1, c2, c3, c4 = st.columns(4)
    unt = c1.selectbox("Unternehmen", ["alle"] + sorted(df["unternehmen"].dropna().unique().tolist()), key="rag_unt")
    quelle = c2.selectbox("Quelle", ["alle", "kununu", "glassdoor", "indeed", "intern"], key="rag_quelle")
    typ = c3.selectbox("Typ", ["alle"] + sorted(df["typ"].dropna().unique().tolist()), key="rag_typ")
    sentiment = c4.selectbox("Sentiment", ["alle", "positiv", "neutral", "negativ"], key="rag_sentiment")
    frage = st.text_input("Frage", "Welche Probleme treten in der Produktion besonders haeufig auf?")
    if st.button("Antwort erzeugen", type="primary"):
        bed = []
        if unt != "alle": bed.append({"unternehmen": unt})
        if quelle != "alle": bed.append({"source": quelle})
        if typ != "alle": bed.append({"typ": typ})
        if sentiment != "alle": bed.append({"sentiment": sentiment})
        where = bed[0] if len(bed) == 1 else ({"$and": bed} if bed else None)
        with st.spinner("Suche Belege und erzeuge Antwort ..."):
            res = rag.answer(frage, where=where)
        st.markdown("### Antwort"); st.write(res["answer"])
        with st.expander("Herangezogene Belege"):
            for i, (doc, m) in enumerate(res["belege"], 1):
                st.markdown(f"**[{i}]** _{m.get('unternehmen','')} · {m['source']} / {m['typ']} / Score {m['gesamt_score']}_")
                st.text(doc)


ABTEILUNGEN = ["Administration", "Produktion", "IT", "Logistik / Materialwirtschaft",
               "Finanzen / Controlling", "Personal", "Vertrieb / Verkauf"]
STANDORTE = ["Braunschweig", "Schladen", "Hohenhameln", "Nordstemmen", "Uelzen", "Klein Wanzleben"]
EMP_COLS = ["name", "abteilung", "standort", "email"]


def _load_empfaenger():
    if config.EMPFAENGER_CSV.exists():
        d = pd.read_csv(config.EMPFAENGER_CSV)
        for c in EMP_COLS:
            if c not in d:
                d[c] = ""
        return d[EMP_COLS]
    return pd.DataFrame(columns=EMP_COLS)


def admin_tab():
    import feedback_utils as fb

    # --- Passwortschutz ---
    if not st.session_state.get("admin_ok"):
        st.subheader("Geschützter Bereich")
        pw = st.text_input("Passwort", type="password")
        if st.button("Anmelden"):
            if pw == "Nordzucker":
                st.session_state["admin_ok"] = True
                st.rerun()
            else:
                st.error("Falsches Passwort.")
        return

    st.subheader("Mitarbeiterbefragung steuern")

    # 1 · Mitarbeiter hinzufügen
    with st.container(border=True):
        st.markdown("**1 · Mitarbeiter hinzufügen**")
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        email = c2.text_input("E-Mail")
        c3, c4 = st.columns(2)
        abteilung = c3.selectbox("Abteilung", ABTEILUNGEN)
        standort = c4.selectbox("Standort", STANDORTE)
        if st.button("Zur Liste hinzufügen", type="primary"):
            if name.strip() and "@" in email:
                d = _load_empfaenger()
                neu = {"name": name.strip(), "abteilung": abteilung,
                       "standort": standort, "email": email.strip().lower()}
                d = pd.concat([d, pd.DataFrame([neu])], ignore_index=True)
                d = d.drop_duplicates(subset="email", keep="last")
                d.to_csv(config.EMPFAENGER_CSV, index=False)
                st.success(f"{name} hinzugefügt.")
            else:
                st.error("Bitte Name und gültige E-Mail angeben.")

    # 2 · Empfängerliste
    with st.container(border=True):
        st.markdown("**2 · Empfängerliste**")
        d = _load_empfaenger()
        st.caption(f"{len(d)} Mitarbeiter in der Liste")
        st.dataframe(d, use_container_width=True, hide_index=True)
        if len(d) and st.button("Liste leeren"):
            pd.DataFrame(columns=EMP_COLS).to_csv(config.EMPFAENGER_CSV, index=False)
            st.rerun()

    # 3 · Link & QR-Code
    with st.container(border=True):
        st.markdown("**3 · Link & QR-Code**")
        auto = fb.ngrok_url()
        manuell = st.text_input(
            "Öffentliche URL (ngrok) – wird automatisch erkannt, sonst hier einfügen",
            value=auto or "", placeholder="https://xxxx.ngrok-free.app")
        base = manuell.strip() or auto or f"http://localhost:{config.FORM_PORT}"
        if base.startswith("http") and "localhost" not in base:
            st.success(f"Öffentlicher Link aktiv: {base}")
        else:
            st.info(f"Noch lokal ({base}). Starte `ngrok http {config.FORM_PORT}` und füge die "
                    "angezeigte https-Adresse oben ein – dann funktioniert der QR auf jedem Handy.")
        link = fb.form_link(base)
        st.code(link)
        try:
            gross = st.checkbox("QR-Code vergrößern")
            st.image(fb.qr_png(link), width=520 if gross else 240,
                     caption="QR zum Formular (Haken setzen zum Vergrößern)")
        except Exception as e:
            st.warning(f"QR nicht erzeugbar ({e}). Bitte `py -m pip install qrcode` ausführen.")

    # 4 · Einladungen versenden
    with st.container(border=True):
        st.markdown("**4 · Einladungen versenden**")
        if st.button("Einladungen jetzt senden", type="primary"):
            try:
                import versand
                n, used = versand.send_invitations(base)
                st.success(f"{n} Einladung(en) über {used} versendet.")
            except SystemExit as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Versand fehlgeschlagen: {e}")

    # 5 · Neue Antworten einlesen
    with st.container(border=True):
        st.markdown("**5 · Neue Antworten einlesen**")
        offen = fb.unverarbeitete()
        st.caption(f"{len(offen)} unverarbeitete Antwort(en)")
        if st.button("Neue Antworten verarbeiten"):
            import importlib, llm
            ing = importlib.import_module("ingest")
            with st.spinner("Verarbeite Antworten durch die Pipeline ..."):
                n = ing.verarbeite(llm.ollama_available())
            st.cache_data.clear()
            st.success(f"{n} Antwort(en) verarbeitet. Bitte Seite neu laden.")


# ---------------- Layout ----------------
st.markdown(CSS, unsafe_allow_html=True)
try:
    df = load_data()
except FileNotFoundError:
    st.error("Noch keine Daten. Bitte zuerst die Pipeline ausfuehren."); st.stop()

with st.sidebar:
    assets = config.BASE_DIR / "assets"
    logos = (list(assets.glob("*.png")) + list(assets.glob("*.jpg"))) if assets.exists() else []
    if logos:
        st.image(str(logos[0]), use_container_width=True); st.write("")
    else:
        st.markdown(f'<div class="brand">{LEAF}<span class="brand-name">Nordzucker</span></div>', unsafe_allow_html=True)
    st.markdown("##### Filter")
    quellen = st.multiselect("Quelle", sorted(df["source"].unique()), default=sorted(df["source"].unique()))
    typen = st.multiselect("Typ", sorted(df["typ"].dropna().unique()), default=sorted(df["typ"].dropna().unique()))

f_all = df[df["source"].isin(quellen) & df["typ"].isin(typen)]
nordzucker = f_all[f_all["unternehmen"] == config.HAUPTUNTERNEHMEN]

st.markdown('<div class="page-title">Mitarbeiterfeedback-Analyse · Nordzucker</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Auswertung", "Wettbewerbsvergleich", "Bewertungen", "RAG-Chat", "Befragung"])
with tab1:
    auswertung_tab(nordzucker)
with tab2:
    vergleich_tab(f_all)
with tab3:
    explorer_tab(df)
with tab4:
    rag_tab(f_all)
with tab5:
    admin_tab()

st.markdown(
    f'<div class="app-footer"><span>Stand: {dt.date.today().strftime("%d.%m.%Y")}</span>'
    f'<span>Datenbasis Nordzucker: {len(nordzucker)} Bewertungen aus '
    f'{nordzucker["source"].nunique()} Quellen</span></div>', unsafe_allow_html=True)
