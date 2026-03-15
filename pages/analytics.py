import streamlit as st
import sqlite3
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Sambung Kata — Analytics", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stat-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #2d2d5e; border-radius: 14px;
        padding: 20px 24px; text-align: center;
        box-shadow: 0 4px 24px #0005;
    }
    .stat-value {
        font-size: 2.2rem; font-weight: 800; color: #7c83ff;
        text-shadow: 0 0 16px #7c83ff88; line-height: 1;
    }
    .stat-label { font-size: 0.82rem; color: #8892b0; margin-top: 6px; }
    .section-title {
        font-size: 1.25rem; font-weight: 800; color: #e0e0ff;
        margin: 28px 0 12px; letter-spacing: 0.5px;
    }
    
    /* ── Sidebar Navigation Glow ── */
    [data-testid="stSidebarNav"] span {
        font-weight: 700;
        font-size: 1.05rem;
    }
    [data-testid="stSidebarNav"] a {
        border-radius: 10px;
        margin: 4px 16px;
        transition: all 0.3s ease;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: linear-gradient(90deg, #7c83ff33, transparent) !important;
        box-shadow: -4px 0 16px #7c83ff44;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #7c83ff, #38bdf8) !important;
        box-shadow: 0 0 18px #7c83ffaa;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #fff !important;
        text-shadow: 0 2px 4px #0006;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "game_records.db")

# ── Load Data ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def load_data():
    if not os.path.exists(DB_PATH):
        return None, None, None, None
    con = sqlite3.connect(DB_PATH)
    games    = pd.read_sql("SELECT * FROM games",    con)
    turns    = pd.read_sql("SELECT * FROM turns",    con)
    try:
        invalids = pd.read_sql("SELECT * FROM invalid_attempts", con)
    except Exception:
        invalids = pd.DataFrame()
    con.close()
    return games, turns, invalids

# ── PLOTLY DARK TEMPLATE ──────────────────────────────────────────────────────
DARK = dict(
    plot_bgcolor  = "#0e0e1a",
    paper_bgcolor = "#0e0e1a",
    font          = dict(color="#c7c7e9", family="Inter"),
    xaxis         = dict(gridcolor="#1e1e3a", zerolinecolor="#1e1e3a"),
    yaxis         = dict(gridcolor="#1e1e3a", zerolinecolor="#1e1e3a"),
)
ACCENT = ["#7c83ff","#34d399","#fb923c","#c084fc","#f472b6","#38bdf8","#facc15","#4ade80"]

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    '<p style="text-align:center;font-size:2.4rem;font-weight:800;'
    'background:linear-gradient(135deg,#7c83ff,#a78bfa,#38bdf8);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
    'filter:drop-shadow(0 0 18px #7c83ff88);margin-bottom:0;">📊 Analytics</p>',
    unsafe_allow_html=True
)
st.markdown(
    '<p style="text-align:center;color:#8892b0;margin-top:4px;margin-bottom:24px;">'
    'Visualisasi data dari semua sesi game yang pernah dimainkan</p>',
    unsafe_allow_html=True
)

if st.button("🔄 Refresh Data", type="secondary"):
    st.cache_data.clear()
    st.rerun()

games, turns, invalids = load_data()

if games is None or games.empty:
    st.info("📭 Belum ada data game. Mainkan beberapa sesi dulu!")
    st.stop()

# ── Summary Stats ─────────────────────────────────────────────────────────────
total_games   = len(games)
total_turns   = len(turns)
total_words   = turns["word"].nunique() if not turns.empty else 0
total_invalid = len(invalids) if not invalids.empty else 0

c1, c2, c3, c4 = st.columns(4)
for col, val, label in [
    (c1, total_games,   "Total Game"),
    (c2, total_turns,   "Total Giliran"),
    (c3, total_words,   "Kata Unik Dimainkan"),
    (c4, total_invalid, "Kata Tidak Valid"),
]:
    with col:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-value">{val:,}</div>'
            f'<div class="stat-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

st.markdown("---")

if turns.empty:
    st.info("Belum ada giliran yang direkam.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# 1. KATA PALING SERING DIPAKAI
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="section-title">🏆 Kata Paling Sering Dipakai</p>', unsafe_allow_html=True)

top_n   = st.slider("Tampilkan top N kata", 5, 30, 15, key="top_n")
word_freq = (
    turns.groupby("word")
         .size()
         .reset_index(name="count")
         .sort_values("count", ascending=False)
         .head(top_n)
)
total_word_plays = len(turns)
word_freq["persen"] = (word_freq["count"] / total_word_plays * 100).round(2)

fig1 = px.bar(
    word_freq,
    x="count", y="word",
    orientation="h",
    text="count",
    color="count",
    color_continuous_scale=[[0,"#1e1e5a"],[0.5,"#7c83ff"],[1,"#38bdf8"]],
    labels={"count":"Jumlah Dipakai","word":"Kata","persen":"Persentase"},
    hover_data={"persen": ":.2f"},
    custom_data=["persen"],
)
fig1.update_traces(
    textposition="outside",
    textfont=dict(color="#e0e0ff", size=12),
    hovertemplate="<b>%{y}</b><br>Dipakai: %{x}×<br>Persentase: %{customdata[0]:.2f}%<extra></extra>",
)
fig1.update_layout(
    **DARK,
    height=max(300, top_n * 32),
    showlegend=False,
    coloraxis_showscale=False,
    margin=dict(l=10, r=40, t=10, b=10),
)
fig1.update_yaxes(categoryorder="total ascending")
st.plotly_chart(fig1, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# 4. PERSENTASE KATA (pie / treemap)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="section-title">📐 Persentase Pemakaian Kata (Top 10)</p>', unsafe_allow_html=True)

top10 = word_freq.head(10).copy()
other_count = total_word_plays - top10["count"].sum()
if other_count > 0:
    other_row = pd.DataFrame([{"word": "Lainnya", "count": other_count,
                                "persen": round(other_count/total_word_plays*100,2)}])
    top10 = pd.concat([top10, other_row], ignore_index=True)

fig_pie = px.pie(
    top10, names="word", values="count",
    hole=0.5,
    color_discrete_sequence=ACCENT,
)
fig_pie.update_traces(
    textinfo="label+percent",
    textfont=dict(size=13),
    hovertemplate="<b>%{label}</b><br>%{value}× dipakai<br>%{percent}<extra></extra>",
    pull=[0.05 if i == 0 else 0 for i in range(len(top10))],
)
fig_pie.update_layout(
    **DARK,
    height=420,
    margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(font=dict(color="#c7c7e9")),
)
st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# 2. RATA-RATA GAME PER PLAYER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="section-title">👥 Rata-rata Game per Pemain</p>', unsafe_allow_html=True)

import json

def expand_players(games_df):
    rows = []
    for _, row in games_df.iterrows():
        try:
            names = json.loads(row["player_names"])
        except Exception:
            names = [row["player_names"]]
        for name in names:
            rows.append({"game_id": row["game_id"], "player_name": name,
                         "total_turns": row["total_turns"], "status": row["status"]})
    return pd.DataFrame(rows)

player_games = expand_players(games)

if not player_games.empty:
    player_stats = (
        player_games.groupby("player_name")
        .agg(games_played=("game_id","count"),
             total_turns_across_games=("total_turns","sum"))
        .reset_index()
        .sort_values("games_played", ascending=False)
    )
    avg_games = player_stats["games_played"].mean()

    col_a, col_b = st.columns([2, 1])
    with col_a:
        fig2 = px.bar(
            player_stats,
            x="player_name", y="games_played",
            color="games_played",
            color_continuous_scale=[[0,"#16213e"],[1,"#34d399"]],
            text="games_played",
            labels={"player_name":"Pemain","games_played":"Jumlah Game"},
        )
        fig2.update_traces(textposition="outside", textfont=dict(color="#e0e0ff"))
        fig2.update_layout(
            **DARK, height=360, showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.markdown(
            f'<div class="stat-card" style="margin-top:60px;">'
            f'<div class="stat-value" style="color:#34d399;text-shadow:0 0 16px #34d39988;">'
            f'{avg_games:.1f}</div>'
            f'<div class="stat-label">Rata-rata game per pemain</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        top_player = player_stats.iloc[0] if not player_stats.empty else None
        if top_player is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-value" style="font-size:1.3rem;color:#fb923c;'
                f'text-shadow:0 0 14px #fb923c88;">{top_player["player_name"]}</div>'
                f'<div class="stat-label">Pemain terbanyak bermain<br>'
                f'({int(top_player["games_played"])} game)</div>'
                f'</div>',
                unsafe_allow_html=True
            )

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# 3. KATA YANG SULIT (paling banyak memicu kegagalan)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    '<p class="section-title">💀 Kata Paling "Berbahaya" (memicu input tidak valid)</p>',
    unsafe_allow_html=True
)
st.caption("Kata yang paling sering menjadi prev_word sebelum player berikutnya gagal merespon dengan kata valid.")

if not invalids.empty and "prev_word" in invalids.columns:
    danger = (
        invalids[invalids["prev_word"].notna() & (invalids["prev_word"] != "")]
        .groupby("prev_word")
        .size()
        .reset_index(name="gagal_count")
        .sort_values("gagal_count", ascending=False)
        .head(20)
    )

    if not danger.empty:
        # Enrich with how many times each word was played
        word_play_count = turns.groupby("word").size().reset_index(name="play_count")
        danger = danger.merge(word_play_count, left_on="prev_word", right_on="word", how="left")
        danger["fail_rate"] = (danger["gagal_count"] / danger["play_count"] * 100).round(1)
        danger["fail_rate"] = danger["fail_rate"].fillna(0)

        fig3 = px.scatter(
            danger,
            x="play_count", y="gagal_count",
            size="fail_rate",
            color="fail_rate",
            text="prev_word",
            color_continuous_scale=[[0,"#1e1e3a"],[0.5,"#fb923c"],[1,"#ef4444"]],
            labels={
                "play_count":  "Jumlah Kali Dimainkan",
                "gagal_count": "Kali Memicu Kegagalan",
                "fail_rate":   "Tingkat Kegagalan (%)",
                "prev_word":   "Kata",
            },
            hover_data={"fail_rate": ":.1f", "prev_word": True},
        )
        fig3.update_traces(
            textposition="top center",
            textfont=dict(size=11, color="#e0e0ff"),
            marker=dict(line=dict(width=1, color="#2d2d5e")),
        )
        fig3.update_layout(
            **DARK,
            height=440,
            coloraxis_colorbar=dict(
                title="Fail Rate %",
                tickfont=dict(color="#c7c7e9"),
                title_font=dict(color="#c7c7e9"),
            ),
            margin=dict(l=10, r=20, t=10, b=10),
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown("**Detail tabel:**")
        show = danger[["prev_word","play_count","gagal_count","fail_rate"]].rename(columns={
            "prev_word":   "Kata",
            "play_count":  "Kali Dimainkan",
            "gagal_count": "Memicu Kegagalan",
            "fail_rate":   "Tingkat Kegagalan (%)",
        })
        st.dataframe(show, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data percobaan tidak valid yang tercatat.")
else:
    st.info("Belum ada percobaan tidak valid yang direkam. Data akan muncul setelah ada pemain yang menginput kata tidak kamus.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BONUS: Timeline game per hari
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="section-title">📅 Aktivitas Game per Hari</p>', unsafe_allow_html=True)

if "started_at" in games.columns:
    games["date"] = pd.to_datetime(games["started_at"]).dt.date
    daily = games.groupby("date").size().reset_index(name="jumlah_game")
    fig4 = px.area(
        daily, x="date", y="jumlah_game",
        labels={"date":"Tanggal","jumlah_game":"Jumlah Game"},
        color_discrete_sequence=["#7c83ff"],
    )
    fig4.update_traces(fill="tozeroy", fillcolor="rgba(124, 131, 255, 0.15)", line=dict(width=2))
    fig4.update_layout(
        **DARK, height=280,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig4, use_container_width=True)

st.markdown(
    '<p style="text-align:center;color:#2d2d5e;font-size:0.78rem;margin-top:20px;">'
    'Data diambil langsung dari game_records.db · Refresh untuk data terbaru</p>',
    unsafe_allow_html=True
)
