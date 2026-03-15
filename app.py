import streamlit as st
import google.generativeai as genai
import random
import os
import sqlite3
import uuid
from datetime import datetime

st.set_page_config(page_title="Sambung Kata", page_icon="🔗", layout="centered")

from auth import check_password
if not check_password():
    st.stop()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ── Title ── */
    .game-title {
        text-align: center; font-weight: 800; font-size: 2.6rem; margin-bottom: 0;
        background: linear-gradient(135deg, #7c83ff, #a78bfa, #38bdf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 18px #7c83ff88);
    }
    .game-subtitle {
        text-align: center; color: #8892b0; font-size: 1.05rem; margin-bottom: 1.5rem;
    }

    /* ── Setup Card ── */
    .setup-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #2d2d5e; border-radius: 16px;
        padding: 24px 28px; margin-bottom: 16px;
        box-shadow: 0 4px 32px #0006;
    }

    /* ── Player Badge ── */
    .player-badge {
        display: inline-block; padding: 4px 14px; border-radius: 20px;
        font-weight: 700; font-size: 0.85rem; margin-bottom: 8px;
        border: 1px solid currentColor;
    }

    /* ── Turn Indicator ── */
    .turn-indicator {
        color: #fff; border-radius: 12px; padding: 14px 20px;
        text-align: center; font-weight: 800; font-size: 1.15rem; margin-bottom: 16px;
        letter-spacing: 0.5px; box-shadow: 0 4px 24px #0008;
    }

    /* ── Chain Info ── */
    .chain-info {
        background: #12122a; border-left: 4px solid #7c83ff;
        border-radius: 8px; padding: 12px 18px; margin-bottom: 12px;
        font-size: 0.95rem; color: #c7c7e9;
        box-shadow: inset 0 0 20px #7c83ff08;
    }

    /* ── Valid Start Badges ── */
    .valid-starts { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
    .start-badge {
        padding: 4px 16px; border-radius: 20px; font-weight: 800;
        font-size: 1.05rem; letter-spacing: 2px;
        border: 2px solid currentColor;
        box-shadow: 0 0 8px currentColor44;
    }
    /* ── Recommendation Card Animations ── */
    @keyframes popIn {
        0%   { opacity: 0; transform: translateY(12px) scale(0.95); }
        60%  { transform: translateY(-3px) scale(1.02); }
        100% { opacity: 1; transform: translateY(0) scale(1); }
    }
    @keyframes glowPulse {
        0%, 100% { box-shadow: 0 0 10px var(--glow), 0 0 20px var(--glow); }
        50%       { box-shadow: 0 0 22px var(--glow), 0 0 44px var(--glow); }
    }
    .rec-card {
        animation: popIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    }
    .rec-card:hover {
        animation: glowPulse 1.5s ease-in-out infinite;
        transform: translateX(4px);
        transition: transform 0.2s ease;
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORDLIST_PATH = os.path.join(BASE_DIR, "wordlist.txt")
DB_PATH       = os.path.join(BASE_DIR, "game_records.db")

# ─── SQLite Game Recording ───────────────────────────────────────────────────
DB_AVAILABLE = False  # will be set True if init succeeds

def init_db():
    global DB_AVAILABLE
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS games (
                game_id     TEXT PRIMARY KEY,
                started_at  TEXT NOT NULL,
                ended_at    TEXT,
                num_players INTEGER NOT NULL,
                player_names TEXT NOT NULL,
                total_turns INTEGER DEFAULT 0,
                status      TEXT DEFAULT 'ongoing'
            );
            CREATE TABLE IF NOT EXISTS turns (
                turn_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id         TEXT NOT NULL,
                turn_number     INTEGER NOT NULL,
                player_idx      INTEGER NOT NULL,
                player_name     TEXT NOT NULL,
                word            TEXT NOT NULL,
                word_starts_with TEXT NOT NULL,
                rec_source      TEXT NOT NULL,
                new_words_saved TEXT,
                played_at       TEXT NOT NULL,
                FOREIGN KEY (game_id) REFERENCES games(game_id)
            );
            CREATE TABLE IF NOT EXISTS recommendations (
                rec_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                turn_id     INTEGER NOT NULL,
                slot        INTEGER NOT NULL,
                label       TEXT NOT NULL,
                word        TEXT,
                source      TEXT NOT NULL,
                FOREIGN KEY (turn_id) REFERENCES turns(turn_id)
            );
            CREATE TABLE IF NOT EXISTS invalid_attempts (
                attempt_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id         TEXT NOT NULL,
                turn_number     INTEGER NOT NULL,
                player_idx      INTEGER NOT NULL,
                player_name     TEXT NOT NULL,
                word_tried      TEXT NOT NULL,
                prev_word       TEXT,
                attempted_at    TEXT NOT NULL,
                FOREIGN KEY (game_id) REFERENCES games(game_id)
            );
        """)
        con.commit()
        con.close()
        DB_AVAILABLE = True
    except Exception:
        DB_AVAILABLE = False

init_db()

import json

def db_create_game(game_id, num_players, player_names):
    if not DB_AVAILABLE:
        return
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO games (game_id, started_at, num_players, player_names) VALUES (?,?,?,?)",
            (game_id, datetime.now().isoformat(), num_players, json.dumps(player_names))
        )
        con.commit()
        con.close()
    except Exception:
        pass

def db_record_turn(game_id, turn_number, player_idx, player_name,
                   word, word_starts_with, rec_source, new_words_saved,
                   results_with_source):
    """Insert a turn row and its recommendation rows."""
    if not DB_AVAILABLE:
        return None
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute(
            """INSERT INTO turns
               (game_id, turn_number, player_idx, player_name, word, word_starts_with,
                rec_source, new_words_saved, played_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (game_id, turn_number, player_idx, player_name, word, word_starts_with,
             rec_source, ",".join(new_words_saved) if new_words_saved else "",
             datetime.now().isoformat())
        )
        turn_id = cur.lastrowid
        for slot_idx, (label, word_rec, source) in enumerate(results_with_source, start=1):
            cur.execute(
                "INSERT INTO recommendations (turn_id, slot, label, word, source) VALUES (?,?,?,?,?)",
                (turn_id, slot_idx, label, word_rec, source)
            )
        cur.execute(
            "UPDATE games SET total_turns = total_turns + 1, status = 'ongoing' WHERE game_id = ?",
            (game_id,)
        )
        con.commit()
        con.close()
        return turn_id
    except Exception:
        return None

def db_finish_game(game_id):
    if not DB_AVAILABLE:
        return
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "UPDATE games SET ended_at = ?, status = 'finished' WHERE game_id = ?",
            (datetime.now().isoformat(), game_id)
        )
        con.commit()
        con.close()
    except Exception:
        pass

def db_record_invalid(game_id, turn_number, player_idx, player_name, word_tried, prev_word):
    """Record a failed kamus attempt for analytics."""
    if not DB_AVAILABLE:
        return
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            """INSERT INTO invalid_attempts
               (game_id, turn_number, player_idx, player_name, word_tried, prev_word, attempted_at)
               VALUES (?,?,?,?,?,?,?)""",
            (game_id, turn_number, player_idx, player_name,
             word_tried, prev_word, datetime.now().isoformat())
        )
        con.commit()
        con.close()
    except Exception:
        pass

# ─── Load & Cache Dataset ────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_word_set():
    if not os.path.exists(WORDLIST_PATH):
        return set()
    with open(WORDLIST_PATH, "r", encoding="utf-8") as f:
        return {line.strip().upper() for line in f if line.strip() and line.strip().isalpha()}

word_set = load_word_set()

def save_word_to_dataset(word: str) -> bool:
    w = word.strip().upper()
    if not w or not w.isalpha() or w in word_set:
        return False
    word_set.add(w)
    try:
        with open(WORDLIST_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n{w.lower()}")
        return True
    except Exception:
        return False

# ─── Dataset Lookup ──────────────────────────────────────────────────────────
def find_words_by_prefix(prefix: str, used_words: set) -> list:
    p = prefix.upper()
    candidates = [w for w in word_set if w.startswith(p) and w not in used_words and len(w) > len(p)]
    random.shuffle(candidates)
    return candidates[:10]

def get_recommendations_from_dataset(last_word: str, used_words: set):
    lw = last_word.upper()
    char_1 = lw[-1]
    char_2 = lw[-2:] if len(lw) >= 2 else char_1
    char_3 = lw[-3:] if len(lw) >= 3 else char_2
    prefixes = [char_1, char_2, char_3]
    labels   = ["1 huruf terakhir", "2 huruf terakhir", "3 huruf terakhir"]
    results  = []
    for label, prefix in zip(labels, prefixes):
        hits = find_words_by_prefix(prefix, used_words)
        results.append((label, hits[0] if hits else None, "DATASET"))
    return results  # list of (label, word_or_None, source)

# ─── AI Fallback ─────────────────────────────────────────────────────────────
def get_recommendations_from_ai(last_word: str, used_words: set):
    lw = last_word.upper()
    char_1 = lw[-1]
    char_2 = lw[-2:] if len(lw) >= 2 else char_1
    char_3 = lw[-3:] if len(lw) >= 3 else char_2
    used_str = ", ".join(sorted(used_words)) if used_words else "kosong"

    prompt = f"""Kata terakhir: "{lw}"
Kata yang sudah dipakai (TIDAK BOLEH direkomendasikan): [{used_str}]

Berikan 3 rekomendasi kata dasar Bahasa Indonesia.

Aturan WAJIB:
- 1 HURUF: kata berawalan huruf "{char_1}".
- 2 HURUF: kata berawalan "{char_2}". Jika TIDAK ADA, tulis: tidak ada kata
- 3 HURUF: kata berawalan "{char_3}". Jika TIDAK ADA, tulis: tidak ada kata
- DILARANG mengganti awalan. Tulis "tidak ada kata" jika kosong.
- Kata TIDAK BOLEH ada di daftar yang sudah dipakai.

Format wajib (balas HANYA 3 baris ini):
1 HURUF: [kata atau "tidak ada kata"]
2 HURUF: [kata atau "tidak ada kata"]
3 HURUF: [kata atau "tidak ada kata"]"""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"ERROR: {e}"

def parse_ai_response(raw_text: str) -> list:
    labels = ["1 huruf terakhir", "2 huruf terakhir", "3 huruf terakhir"]
    lines  = [l.strip() for l in raw_text.strip().splitlines() if l.strip()]
    results = []
    for i, line in enumerate(lines[:3]):
        word  = line.split(":", 1)[-1].strip() if ":" in line else line.strip()
        label = labels[i] if i < len(labels) else f"Opsi {i+1}"
        w = word.upper() if word.lower() not in ("tidak ada kata", "") else None
        results.append((label, w, "AI"))
    while len(results) < 3:
        results.append((labels[len(results)], None, "AI"))
    return results

def get_recommendations(last_word: str, used_words: set):
    """
    Dataset-first then AI fallback.
    Returns (results: list[(label, word, source)], used_ai: bool, newly_saved: list[str])
    """
    results = get_recommendations_from_dataset(last_word, used_words)
    missing = [i for i, (_, w, _) in enumerate(results) if w is None]
    used_ai, newly_saved = False, []

    if missing:
        raw = get_recommendations_from_ai(last_word, used_words)
        if not raw.startswith("ERROR"):
            ai_results = parse_ai_response(raw)
            used_ai = True
            for i in missing:
                if i < len(ai_results):
                    label, ai_word, _ = ai_results[i]
                    if ai_word:
                        results[i] = (results[i][0], ai_word, "AI")
                        if save_word_to_dataset(ai_word):
                            newly_saved.append(ai_word)

    return results, used_ai, newly_saved

# ─── Render Recommendations ──────────────────────────────────────────────────
# Vivid colors that pop on dark backgrounds
REC_COLORS = ["#7c83ff", "#34d399", "#fb923c"]

def render_recommendations(results: list):
    source_icons = {"DATASET": "📚", "AI": "🤖"}
    html = '<div style="display:flex;flex-direction:column;gap:12px;margin-top:10px;">'
    for i, (label, word, source) in enumerate(results[:3]):
        color = REC_COLORS[i] if i < len(REC_COLORS) else "#aaa"
        icon  = source_icons.get(source, "")
        delay = f"{i * 0.12:.2f}s"
        if not word:
            html += (
                f'<div class="rec-card" style="'
                f'background:#1a1a30;border-left:4px solid #2d2d50;'
                f'border-radius:10px;padding:12px 18px;'
                f'color:#444;font-style:italic;font-size:0.9rem;'
                f'animation-delay:{delay};">'
                f'<span style="font-size:0.7rem;display:block;margin-bottom:4px;color:#333;">{label}</span>'
                f'tidak ada kata</div>'
            )
        else:
            html += (
                f'<div class="rec-card" style="'
                f'--glow:{color}55;'
                f'background:linear-gradient(135deg,{color}14,{color}08);'
                f'border-left:5px solid {color};'
                f'border-radius:10px;padding:14px 20px;'
                f'color:{color};font-weight:800;font-size:1.25rem;letter-spacing:2.5px;'
                f'box-shadow:0 0 18px {color}33, inset 0 0 30px {color}08;'
                f'animation-delay:{delay};">'
                f'<span style="font-size:0.7rem;font-weight:500;display:block;'
                f'margin-bottom:5px;opacity:0.65;letter-spacing:0.5px;">{icon} {label}</span>'
                f'{word}</div>'
            )
    html += '</div>'
    return html

# ─── Helpers ──────────────────────────────────────────────────────────────────
# Neon-bright palette visible on dark backgrounds
PLAYER_COLORS = [
    "#7c83ff",  # indigo
    "#34d399",  # emerald
    "#fb923c",  # orange
    "#c084fc",  # purple
    "#f472b6",  # pink
    "#38bdf8",  # sky
    "#facc15",  # yellow
    "#4ade80",  # green
]

def player_color(idx: int) -> str:
    return PLAYER_COLORS[idx % len(PLAYER_COLORS)]

def get_valid_starts(last_word: str) -> list[str]:
    """Return list of valid starting strings (1, 2, 3 last letters)."""
    lw = last_word.upper()
    starts = [lw[-1]]
    if len(lw) >= 2: starts.append(lw[-2:])
    if len(lw) >= 3: starts.append(lw[-3:])
    return starts  # e.g. ["H", "AH", "JAH"]

def validate_word_input(word: str, last_word: str, used_words: set) -> list[str]:
    """Return list of error strings (empty = valid)."""
    errors = []
    if not word:
        errors.append("Kata tidak boleh kosong.")
        return errors
    if word in used_words:
        errors.append(f"Kata **{word}** sudah pernah dipakai!")
        return errors
    if last_word:
        valid_starts = get_valid_starts(last_word)
        if not any(word.startswith(s) for s in valid_starts):
            starts_display = " / ".join(f"**{s}**" for s in valid_starts)
            errors.append(f"Kata harus diawali salah satu dari: {starts_display}")
    return errors

def is_valid_kamus(word: str) -> bool:
    """Check whether the word exists in the loaded KBBI dataset."""
    return word.upper() in word_set

def which_start_used(word: str, last_word: str) -> str:
    """Return which valid start the word used ('1', '2', or '3')."""
    lw = last_word.upper()
    if len(lw) >= 3 and word.startswith(lw[-3:]):
        return "3"
    if len(lw) >= 2 and word.startswith(lw[-2:]):
        return "2"
    return "1"

# ─── Session State ────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "game_started":      False,
        "game_ended":        False,
        "game_id":           None,
        "num_players":       2,
        "player_names":      [],
        "current_player_idx":0,
        "last_word":         None,
        "turn_number":       0,
        "used_words":        set(),
        "history":           [],
        "words_added_to_db": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Pengaturan")
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = None

    if api_key and api_key != "your_api_key_here":
        try:
            genai.configure(api_key=api_key)
            st.success("✅ API Key berhasil dimuat!")
        except Exception:
            st.error("❌ API Key invalid.")
    else:
        st.warning("⚠️ API Key belum dikonfigurasi.")

    st.markdown("---")
    st.markdown(f"📚 **Dataset**: {len(word_set):,} kata")
    if st.session_state.words_added_to_db > 0:
        st.success(f"➕ {st.session_state.words_added_to_db} kata baru disimpan ke dataset")

    if st.session_state.game_started and not st.session_state.game_ended:
        st.markdown("---")
        st.markdown("### 👥 Pemain")
        for i, name in enumerate(st.session_state.player_names):
            color  = player_color(i)
            marker = " 🎯" if i == st.session_state.current_player_idx else ""
            st.markdown(
                f'<span style="color:{color};font-weight:700;">●</span> {name}{marker}',
                unsafe_allow_html=True
            )
        st.markdown(f"*Game ID:* `{st.session_state.game_id[:8]}...`")
        st.markdown("---")
        if st.button("🏁 Akhiri Game", use_container_width=True):
            db_finish_game(st.session_state.game_id)
            st.session_state.game_ended = True
            st.rerun()

    st.markdown("---")
    if st.button("🔄 Game Baru", use_container_width=True, type="primary"):
        if st.session_state.get("game_id") and not st.session_state.get("game_ended"):
            db_finish_game(st.session_state.game_id)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if st.session_state.used_words:
        st.markdown("---")
        st.markdown("### 📋 Kata Terpakai:")
        st.write(", ".join(sorted(st.session_state.used_words)))

    st.markdown("---")
    st.markdown("### 📜 Aturan")
    st.markdown("Kata kamu **boleh** diawali:")
    st.markdown("- Huruf **terakhir** kata sebelumnya")
    st.markdown("- **2 huruf terakhir** kata sebelumnya")
    st.markdown("- **3 huruf terakhir** kata sebelumnya")
    st.markdown("Kata yang sudah dipakai **tidak bisa** digunakan lagi.")

# ─── Title ────────────────────────────────────────────────────────────────────
st.markdown('<p class="game-title">🔗 Sambung Kata</p>', unsafe_allow_html=True)
st.markdown('<p class="game-subtitle">Game kata berantai — sambung dengan 1, 2, atau 3 huruf terakhir!</p>', unsafe_allow_html=True)

# ─── Setup Screen ─────────────────────────────────────────────────────────────
if not st.session_state.game_started:
    st.markdown('<div class="setup-card">', unsafe_allow_html=True)
    st.markdown("### 🎮 Pengaturan Game")

    num_players = st.slider("Jumlah Pemain", min_value=2, max_value=8, value=2, step=1)

    st.markdown("**Nama Pemain** *(opsional)*")
    num_cols    = min(num_players, 4)
    name_cols   = st.columns(num_cols)
    player_names_input = []
    for i in range(num_players):
        col = name_cols[i % num_cols]
        with col:
            color = player_color(i)
            name  = st.text_input(
                f"Pemain {i+1}",
                value=f"Pemain {i+1}",
                key=f"name_input_{i}",
                label_visibility="collapsed",
                placeholder=f"Pemain {i+1}"
            )
            st.markdown(
                f'<div style="height:4px;background:{color};border-radius:2px;margin-top:-10px;margin-bottom:8px;"></div>',
                unsafe_allow_html=True
            )
            player_names_input.append(name.strip() or f"Pemain {i+1}")

    st.markdown('</div>', unsafe_allow_html=True)

    if not api_key:
        st.warning("⚠️ API Key belum dikonfigurasi. Rekomendasi hanya dari dataset lokal.")

    if st.button("▶️ Mulai Game!", use_container_width=True, type="primary"):
        gid = str(uuid.uuid4())
        db_create_game(gid, num_players, player_names_input)
        st.session_state.game_started      = True
        st.session_state.game_id           = gid
        st.session_state.num_players       = num_players
        st.session_state.player_names      = player_names_input
        st.session_state.current_player_idx = 0
        st.session_state.last_word         = None
        st.session_state.turn_number       = 0
        st.session_state.used_words        = set()
        st.session_state.history           = []
        st.rerun()

# ─── Active Game ──────────────────────────────────────────────────────────────
else:
    # Render history
    for msg in st.session_state.history:
        with st.chat_message(msg.get("role", "user")):
            if msg.get("is_recommendation"):
                p_idx   = msg.get("player_idx", 0)
                p_name  = msg.get("for_player", "Pemain berikutnya")
                color   = player_color(p_idx)
                st.markdown(
                    f'<span class="player-badge" style="background:{color}22;color:{color};">🎯 Rekomendasi untuk {p_name}</span>',
                    unsafe_allow_html=True
                )
                st.markdown(msg["html"], unsafe_allow_html=True)
                if msg.get("newly_saved"):
                    st.caption(f"➕ Kata baru disimpan ke dataset: {', '.join(msg['newly_saved'])}")
            else:
                st.markdown(msg["content"], unsafe_allow_html=True)

    # Turn indicator
    cur_idx   = st.session_state.current_player_idx
    cur_name  = st.session_state.player_names[cur_idx]
    cur_color = player_color(cur_idx)
    st.markdown(
        f'<div class="turn-indicator" style="background:linear-gradient(135deg,{cur_color},{cur_color}cc);">'
        f'🎯 Giliran: {cur_name}</div>',
        unsafe_allow_html=True
    )

    # Chain info: show valid starting options
    if st.session_state.last_word:
        lw     = st.session_state.last_word
        starts = get_valid_starts(lw)
        badges = "".join(
            f'<span class="start-badge" style="background:{cur_color}22;color:{cur_color};">{s}</span>'
            for s in starts
        )
        st.markdown(
            f'<div class="chain-info">'
            f'Kata terakhir: <strong>{lw}</strong><br>'
            f'Awalan yang valid: <div class="valid-starts">{badges}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Input form
    with st.form(f"turn_form_{cur_idx}_{len(st.session_state.history)}", clear_on_submit=True):
        if st.session_state.last_word:
            starts = get_valid_starts(st.session_state.last_word)
            placeholder = f"Awali dengan: {' / '.join(starts)}"
        else:
            placeholder = "Kata pertama bebas..."

        word_input = st.text_input(
            f"✍️ Kata {cur_name}",
            placeholder=placeholder,
        )
        submitted = st.form_submit_button("Mainkan →", use_container_width=True, type="primary")

    # End game button — visible in main area
    st.markdown(
        '<div style="margin-top:8px;text-align:center;">'
        '<span style="font-size:0.78rem;color:#555;">Sudah puas bermain?</span>'
        '</div>',
        unsafe_allow_html=True
    )
    if st.button("🏁 Akhiri Game & Lihat Hasil", use_container_width=True):
        db_finish_game(st.session_state.game_id)
        st.session_state.game_ended = True
        st.rerun()

    if submitted:
        word_clean = "".join(c for c in word_input if c.isalpha()).strip().upper()
        errors = validate_word_input(word_clean, st.session_state.last_word, st.session_state.used_words)

        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")

        elif not is_valid_kamus(word_clean):
            # Word passes letter rules but is NOT in KBBI dictionary → chain reset
            prev_word = st.session_state.last_word or "-"
            st.error(
                f"❌ **{word_clean}** tidak ditemukan dalam kamus! "
                f"Rantai kata direset — {cur_name} bisa memulai dengan kata bebas."
            )
            # Persist invalid attempt to DB for analytics
            db_record_invalid(
                game_id     = st.session_state.game_id,
                turn_number = st.session_state.turn_number,
                player_idx  = cur_idx,
                player_name = cur_name,
                word_tried  = word_clean,
                prev_word   = st.session_state.last_word,
            )
            # Log invalid attempt in history
            st.session_state.history.append({
                "role": "user",
                "content": (
                    f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">'
                    f'<span style="color:{cur_color};font-weight:700;font-size:0.85rem;'
                    f'background:{cur_color}18;padding:3px 12px;border-radius:20px;'
                    f'border:1px solid {cur_color}44;">{cur_name}</span>'
                    f'<span style="font-size:1.1rem;font-weight:700;color:#ef4444;'
                    f'text-decoration:line-through;letter-spacing:2px;opacity:0.7;">{word_clean}</span>'
                    f'<span style="font-size:0.72rem;color:#ef4444;background:#ef444418;'
                    f'padding:2px 10px;border-radius:12px;border:1px solid #ef44443a;">'
                    f'tidak valid — rantai reset</span>'
                    f'</div>'
                ),
            })
            # Reset chain so next attempt is constraint-free
            st.session_state.last_word = None
            st.rerun()
        else:
            # Determine which start was used
            start_used = which_start_used(word_clean, st.session_state.last_word) \
                         if st.session_state.last_word else "1"

            st.session_state.used_words.add(word_clean)
            st.session_state.last_word = word_clean
            st.session_state.turn_number += 1

            st.session_state.history.append({
                "role": "user",
                "content": (
                    f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">'
                    f'<span style="color:{cur_color};font-weight:700;font-size:0.85rem;'
                    f'background:{cur_color}18;padding:3px 12px;border-radius:20px;'
                    f'border:1px solid {cur_color}44;">{cur_name}</span>'
                    f'<span style="font-size:1.4rem;font-weight:800;letter-spacing:3px;'
                    f'color:#e0e0ff;text-shadow:0 0 12px {cur_color}66;">{word_clean}</span>'
                    f'<span style="font-size:0.72rem;color:{cur_color};background:{cur_color}18;'
                    f'padding:2px 10px;border-radius:12px;border:1px solid {cur_color}44;">'
                    f'awalan {start_used} huruf</span>'
                    f'</div>'
                ),
            })

            next_idx   = (cur_idx + 1) % st.session_state.num_players
            next_name  = st.session_state.player_names[next_idx]

            # Get recommendations
            with st.spinner(f"Menyusun rekomendasi untuk {next_name}..."):
                results, used_ai, newly_saved = get_recommendations(word_clean, st.session_state.used_words)

            if newly_saved:
                st.session_state.words_added_to_db += len(newly_saved)

            # Record turn to DB
            rec_source = ("MIXED" if used_ai and any(src == "DATASET" for _, _, src in results)
                          else "AI" if used_ai else "DATASET")
            db_record_turn(
                game_id         = st.session_state.game_id,
                turn_number     = st.session_state.turn_number,
                player_idx      = cur_idx,
                player_name     = cur_name,
                word            = word_clean,
                word_starts_with= start_used,
                rec_source      = rec_source,
                new_words_saved = newly_saved,
                results_with_source = results,
            )

            html       = render_recommendations(results)
            st.session_state.history.append({
                "role": "assistant",
                "is_recommendation": True,
                "for_player": next_name,
                "player_idx": next_idx,
                "html": html,
                "newly_saved": newly_saved,
            })

            st.session_state.current_player_idx = next_idx
            st.rerun()

# ─── End Game Summary Screen ────────────────────────────────────────────────
if st.session_state.game_ended:
    st.markdown(
        '<div style="text-align:center;padding:30px 0 10px;">'
        '<div style="font-size:3.5rem;">🏁</div>'
        '<div style="font-size:1.8rem;font-weight:800;color:#7c83ff;'
        'text-shadow:0 0 20px #7c83ff88;margin-top:8px;">Game Selesai!</div>'
        '<div style="color:#8892b0;margin-top:6px;">Data telah tersimpan ke database</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Stats row
    total_turns = st.session_state.turn_number
    total_words = len(st.session_state.used_words)
    num_p       = st.session_state.num_players
    c1, c2, c3 = st.columns(3)
    for col, label, val in [
        (c1, "Total Giliran", total_turns),
        (c2, "Total Kata",    total_words),
        (c3, "Jumlah Pemain", num_p),
    ]:
        with col:
            st.markdown(
                f'<div style="background:#1a1a2e;border:1px solid #2d2d5e;'
                f'border-radius:12px;padding:16px;text-align:center;'
                f'box-shadow:0 0 16px #7c83ff18;">'
                f'<div style="font-size:2rem;font-weight:800;color:#7c83ff;'
                f'text-shadow:0 0 12px #7c83ff66;">{val}</div>'
                f'<div style="font-size:0.8rem;color:#8892b0;margin-top:4px;">{label}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Per-player turn count
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 👥 Kontribusi Pemain")
    player_turns = {name: 0 for name in st.session_state.player_names}
    for msg in st.session_state.history:
        if not msg.get("is_recommendation"):
            # Count by matching player names in history
            pass
    # Pull from DB for accurate per-player count
    try:
        con  = sqlite3.connect(DB_PATH)
        rows = con.execute(
            "SELECT player_name, COUNT(*) FROM turns WHERE game_id=? GROUP BY player_name",
            (st.session_state.game_id,)
        ).fetchall()
        con.close()
        player_turn_counts = {r[0]: r[1] for r in rows}
    except Exception:
        player_turn_counts = {}

    cols = st.columns(min(num_p, 4))
    for i, name in enumerate(st.session_state.player_names):
        color = player_color(i)
        turns = player_turn_counts.get(name, 0)
        with cols[i % 4]:
            st.markdown(
                f'<div style="background:{color}0f;border:1px solid {color}44;'
                f'border-radius:10px;padding:12px 16px;text-align:center;'
                f'box-shadow:0 0 10px {color}22;">'
                f'<div style="color:{color};font-weight:800;font-size:1.05rem;'
                f'text-shadow:0 0 8px {color}66;">{name}</div>'
                f'<div style="font-size:1.6rem;font-weight:800;color:#e0e0ff;margin:4px 0;">{turns}</div>'
                f'<div style="font-size:0.72rem;color:#8892b0;">giliran dimainkan</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Word list
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📋 Semua Kata yang Dimainkan")
    words_sorted = sorted(st.session_state.used_words)
    word_tags = " ".join(
        f'<span style="background:#1e1e3a;border:1px solid #2d2d5e;'
        f'color:#c7c7e9;padding:4px 12px;border-radius:20px;font-size:0.85rem;'
        f'font-weight:600;letter-spacing:1px;">{w}</span>'
        for w in words_sorted
    )
    st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:8px;">{word_tags}</div>',
                unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🎮 Main Lagi", use_container_width=True, type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
