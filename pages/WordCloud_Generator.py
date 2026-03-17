import os
import random
import sys
from typing import Dict, List, Optional, Tuple

import streamlit as st

st.set_page_config(page_title="Sambung Kata - WordCloud Generator", page_icon="WG", layout="centered")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from auth import check_password

if not check_password():
    st.stop()

WORDLIST_PATH = os.path.join(BASE_DIR, "wordlist.txt")

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .wc-title {
        text-align: center;
        font-weight: 800;
        font-size: 2.45rem;
        margin-bottom: 0;
        background: linear-gradient(135deg, #7c83ff, #a78bfa, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 18px #7c83ff88);
    }

    .wc-subtitle {
        text-align: center;
        color: #8892b0;
        font-size: 1rem;
        margin-bottom: 1.2rem;
    }

    .setup-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #2d2d5e;
        border-radius: 16px;
        padding: 16px 18px;
        margin-bottom: 14px;
        box-shadow: 0 4px 28px #0006;
    }

    .lane-wrap {
        background: linear-gradient(135deg, #17172f, #101024);
        border: 1px solid #2d2d5e;
        border-radius: 12px;
        padding: 12px;
        min-height: 255px;
        box-shadow: inset 0 0 20px #7c83ff0f;
    }

    .lane-title {
        font-size: 0.86rem;
        font-weight: 800;
        margin-bottom: 10px;
        letter-spacing: 0.6px;
    }

    @keyframes popIn {
        0% { opacity: 0; transform: translateY(10px) scale(0.96); }
        100% { opacity: 1; transform: translateY(0) scale(1); }
    }

    .rec-card {
        border-left: 5px solid var(--lane-color);
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 9px;
        background: linear-gradient(135deg, var(--lane-bg-1), var(--lane-bg-2));
        color: var(--lane-color);
        box-shadow: 0 0 14px var(--lane-shadow), inset 0 0 20px #ffffff08;
        animation: popIn 0.25s ease both;
    }

    .rec-meta {
        font-size: 0.66rem;
        opacity: 0.72;
        letter-spacing: 0.45px;
        margin-bottom: 3px;
    }

    .rec-word {
        font-size: 1.05rem;
        font-weight: 800;
        letter-spacing: 1.6px;
    }

    .chip {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 14px;
        font-size: 0.72rem;
        font-weight: 700;
        border: 1px solid currentColor;
        margin-right: 6px;
    }

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
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_word_set() -> set:
    if not os.path.exists(WORDLIST_PATH):
        return set()
    with open(WORDLIST_PATH, "r", encoding="utf-8") as f:
        return {line.strip().upper() for line in f if line.strip() and line.strip().isalpha()}


@st.cache_data(show_spinner=False)
def build_first_letter_freq(words: set) -> Dict[str, int]:
    freq: Dict[str, int] = {}
    for word in words:
        if word:
            first = word[0]
            freq[first] = freq.get(first, 0) + 1
    return freq


def word_difficulty_score(word: str, first_letter_freq: Dict[str, int], max_freq: int) -> float:
    w = word.upper()
    score = 0.0
    for offset, weight in ((1, 3.0), (2, 2.0), (3, 1.0)):
        if len(w) >= offset:
            rarity = 1.0 - (first_letter_freq.get(w[-offset], 0) / max_freq)
            score += rarity * weight
    return score


def recommend_pool_by_tier(
    prefix: str,
    words: set,
    first_letter_freq: Dict[str, int],
    tier: str,
    limit: int = 3,
    exclude: Optional[set] = None,
) -> List[str]:
    if not prefix:
        return []

    p = prefix.upper()
    exclude = exclude or set()
    max_freq = max(first_letter_freq.values()) if first_letter_freq else 1
    candidates = [w for w in words if w.startswith(p) and len(w) > len(p) and w not in exclude]
    if not candidates:
        return []

    scored = [(w, word_difficulty_score(w, first_letter_freq, max_freq)) for w in candidates]
    scored.sort(key=lambda item: item[1], reverse=True)

    n = len(scored)
    if tier == "hard":
        pool = [w for w, _ in scored[: max(6, n // 4)]]
    elif tier == "medium":
        mid = n // 2
        lower = max(0, mid - max(3, n // 10))
        upper = min(n, mid + max(3, n // 10))
        pool = [w for w, _ in scored[lower:upper]]
    elif tier == "easy":
        pool = [w for w, _ in scored[-max(6, n // 4):]]
    else:
        pool = [w for w, _ in scored]

    if not pool:
        pool = [w for w, _ in scored]

    random.shuffle(pool)
    chosen = []
    for w in pool:
        if w not in chosen:
            chosen.append(w)
        if len(chosen) == limit:
            break

    if len(chosen) < limit:
        for w, _ in scored:
            if w not in chosen:
                chosen.append(w)
            if len(chosen) == limit:
                break

    return chosen


def derive_prefixes(base_prefix: str) -> Dict[str, str]:
    bp = "".join(c for c in base_prefix.upper() if c.isalpha())[:3]
    if not bp:
        return {"1 huruf": "", "2 huruf": "", "3 huruf": ""}
    p1 = bp[:1]
    p2 = bp[:2] if len(bp) >= 2 else p1
    p3 = bp[:3] if len(bp) >= 3 else p2
    return {"1 huruf": p1, "2 huruf": p2, "3 huruf": p3}


def render_lane_cards(title: str, words: List[str], color: str, label: str, prefix: str):
    st.markdown(
        f'<div class="lane-title" style="color:{color};">{title} '
        f'<span class="chip" style="color:{color};">{label}</span>'
        f'<span class="chip" style="color:{color};">prefix: {prefix or "-"}</span></div>',
        unsafe_allow_html=True,
    )
    if not words:
        st.markdown('<p style="color:#666;font-style:italic;">Tidak ada kata untuk awalan ini.</p>', unsafe_allow_html=True)
        return

    lane_bg = {
        "#fb923c": ("#fb923c22", "#fb923c08", "#fb923c44"),
        "#34d399": ("#34d39922", "#34d39908", "#34d39944"),
        "#7c83ff": ("#7c83ff22", "#7c83ff08", "#7c83ff44"),
    }
    bg1, bg2, shadow = lane_bg.get(color, ("#99999922", "#99999908", "#99999933"))
    for idx, word in enumerate(words, start=1):
        st.markdown(
            f'<div class="rec-card" style="--lane-color:{color};--lane-bg-1:{bg1};--lane-bg-2:{bg2};--lane-shadow:{shadow};">'
            f'<div class="rec-meta">OPSI {idx}</div>'
            f'<div class="rec-word">{word}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


st.markdown('<p class="wc-title">WordCloud Generator</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="wc-subtitle">Mode 1 pemain: masukkan awalan 1-3 huruf, lalu sistem langsung memberi 3 opsi kata untuk lane 1, 2, dan 3 huruf.</p>',
    unsafe_allow_html=True,
)

word_set = load_word_set()
first_letter_freq = build_first_letter_freq(word_set)

st.markdown('<div class="setup-card">', unsafe_allow_html=True)
base_prefix_input = st.text_input(
    "Awalan dasar (1-3 huruf)",
    value="",
    placeholder="Contoh: P, PE, atau PER",
    help="Rekomendasi akan muncul otomatis saat kamu mengetik.",
)
st.markdown('</div>', unsafe_allow_html=True)

clean_prefix = "".join(c for c in base_prefix_input.upper() if c.isalpha())[:3]
if not clean_prefix:
    st.info("Masukkan awalan 1-3 huruf untuk melihat rekomendasi cepat.")
    st.stop()

prefixes = derive_prefixes(clean_prefix)

used_global = set()
hard_words = recommend_pool_by_tier(prefixes["3 huruf"], word_set, first_letter_freq, "hard", limit=3, exclude=used_global)
used_global.update(hard_words)
med_words = recommend_pool_by_tier(prefixes["2 huruf"], word_set, first_letter_freq, "medium", limit=3, exclude=used_global)
used_global.update(med_words)
easy_words = recommend_pool_by_tier(prefixes["1 huruf"], word_set, first_letter_freq, "easy", limit=3, exclude=used_global)

st.markdown(
    '<div style="margin-bottom:4px;">'
    f'<span class="chip" style="color:#fb923c;">3 huruf: {prefixes["3 huruf"]}</span>'
    f'<span class="chip" style="color:#34d399;">2 huruf: {prefixes["2 huruf"]}</span>'
    f'<span class="chip" style="color:#7c83ff;">1 huruf: {prefixes["1 huruf"]}</span>'
    '</div>',
    unsafe_allow_html=True,
)

col_hard, col_medium, col_easy = st.columns(3)
with col_hard:
    render_lane_cards("3 HURUF", hard_words, "#fb923c", "SENJATA UTAMA", prefixes["3 huruf"])

with col_medium:
    render_lane_cards("2 HURUF", med_words, "#34d399", "MENENGAH", prefixes["2 huruf"])

with col_easy:
    render_lane_cards("1 HURUF", easy_words, "#7c83ff", "MUDAH DITEBAK", prefixes["1 huruf"])

popup_title = f"Lihat popup rekomendasi untuk awalan '{clean_prefix}'"
if hasattr(st, "popover"):
    with st.popover(popup_title, use_container_width=True):
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown("**3 huruf (senjata utama)**")
            for w in hard_words:
                st.markdown(f"- <span style='color:#fb923c;font-weight:700;'>{w}</span>", unsafe_allow_html=True)
            if not hard_words:
                st.write("Tidak ada kata")
        with p2:
            st.markdown("**2 huruf (menengah)**")
            for w in med_words:
                st.markdown(f"- <span style='color:#34d399;font-weight:700;'>{w}</span>", unsafe_allow_html=True)
            if not med_words:
                st.write("Tidak ada kata")
        with p3:
            st.markdown("**1 huruf (mudah ditebak)**")
            for w in easy_words:
                st.markdown(f"- <span style='color:#7c83ff;font-weight:700;'>{w}</span>", unsafe_allow_html=True)
            if not easy_words:
                st.write("Tidak ada kata")
else:
    with st.expander(popup_title, expanded=False):
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown("**3 huruf (senjata utama)**")
            for w in hard_words:
                st.markdown(f"- <span style='color:#fb923c;font-weight:700;'>{w}</span>", unsafe_allow_html=True)
            if not hard_words:
                st.write("Tidak ada kata")
        with p2:
            st.markdown("**2 huruf (menengah)**")
            for w in med_words:
                st.markdown(f"- <span style='color:#34d399;font-weight:700;'>{w}</span>", unsafe_allow_html=True)
            if not med_words:
                st.write("Tidak ada kata")
        with p3:
            st.markdown("**1 huruf (mudah ditebak)**")
            for w in easy_words:
                st.markdown(f"- <span style='color:#7c83ff;font-weight:700;'>{w}</span>", unsafe_allow_html=True)
            if not easy_words:
                st.write("Tidak ada kata")
