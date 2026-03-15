import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Rekomendasi Kata AI", page_icon="📝", layout="centered")

st.markdown("""
<style>
    .game-title { text-align: center; color: #2e7d32; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 2.5rem; margin-bottom: 0px;}
    .game-subtitle { text-align: center; color: #666; font-family: 'Inter', sans-serif; font-size: 1.1rem; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="game-title">📝 Rekomendasi Sambung Kata</p>', unsafe_allow_html=True)
st.markdown('<p class="game-subtitle">Masukkan kata Anda & kata lawan, AI akan merekomendasikan jawaban!</p>', unsafe_allow_html=True)

# --- Sidebar ---
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
    st.markdown("### 📜 Cara Penggunaan")
    st.markdown("1. Masukkan kata yang **Anda mainkan**.")
    st.markdown("2. Masukkan kata yang **lawan mainkan**.")
    st.markdown("3. AI merekomendasikan 3 kata untuk giliran Anda berikutnya.")
    st.markdown("4. Kata yang sudah dipakai **tidak akan muncul** di rekomendasi.")

    st.markdown("---")
    if st.button("🔄 Reset Sesi", use_container_width=True, type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if "used_words" in st.session_state and st.session_state.used_words:
        st.markdown("---")
        st.markdown("### 📋 Kata Terpakai:")
        st.write(", ".join(sorted(st.session_state.used_words)))

# --- Session State ---
if "history" not in st.session_state:
    st.session_state.history = []
if "used_words" not in st.session_state:
    st.session_state.used_words = set()

# --- AI Function ---
def get_recommendations(opponent_word, used_words_set):
    char_1 = opponent_word[-1].upper()
    char_2 = opponent_word[-2:].upper() if len(opponent_word) >= 2 else char_1
    char_3 = opponent_word[-3:].upper() if len(opponent_word) >= 3 else char_2
    used_str = ", ".join(sorted(used_words_set)) if used_words_set else "kosong"

    prompt = f"""Kata terakhir lawan: "{opponent_word.upper()}"
Kata yang sudah dipakai (TIDAK BOLEH direkomendasikan): [{used_str}]

Berikan 3 rekomendasi kata dasar Bahasa Indonesia untuk menjawab kata lawan.

Aturan WAJIB:
- 1 HURUF: berikan 1 kata yang berawalan huruf "{char_1}".
- 2 HURUF: berikan 1 kata yang berawalan "{char_2}". Jika TIDAK ADA kata Bahasa Indonesia yang berawalan "{char_2}", tulis: "tidak ada kata".
- 3 HURUF: berikan 1 kata yang berawalan "{char_3}". Jika TIDAK ADA kata Bahasa Indonesia yang berawalan "{char_3}", tulis: "tidak ada kata".
- DILARANG mengganti awalan ke huruf lain jika tidak ada kata yang sesuai. Harus ditulis "tidak ada kata".
- Kata rekomendasi TIDAK BOLEH ada di daftar yang sudah dipakai.

Format wajib:
1 HURUF: [kata atau "tidak ada kata"]
2 HURUF: [kata atau "tidak ada kata"]
3 HURUF: [kata atau "tidak ada kata"]

Balas HANYA dengan 3 baris di atas. Tanpa penjelasan."""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"ERROR: {e}"

def render_recommendations(raw_text):
    """Parse AI response and render colored recommendation cards."""
    colors = ["#2e7d32", "#1565c0", "#e65100"]  # hijau, biru, oranye
    labels = ["1 huruf terakhir", "2 huruf terakhir", "3 huruf terakhir"]
    lines = [l.strip() for l in raw_text.strip().splitlines() if l.strip()]

    cards_html = '<div style="display:flex; flex-direction:column; gap:10px; margin-top:8px;">'
    for i, line in enumerate(lines[:3]):
        # Ambil kata setelah ":"
        word = line.split(":", 1)[-1].strip() if ":" in line else line.strip()
        color = colors[i] if i < len(colors) else "#555"
        label = labels[i] if i < len(labels) else ""

        if word.lower() == "tidak ada kata" or not word:
            cards_html += f'''
            <div style="
                background:#f0f0f0; border-left:4px solid #bbb;
                border-radius:8px; padding:10px 16px;
                color:#999; font-style:italic; font-size:0.9rem;">
                <span style="font-size:0.75rem; display:block; margin-bottom:2px;">{label}</span>
                tidak ada kata
            </div>'''
        else:
            cards_html += f'''
            <div style="
                background:{color}18; border-left:4px solid {color};
                border-radius:8px; padding:10px 16px;
                color:{color}; font-weight:700; font-size:1.1rem; letter-spacing:1px;">
                <span style="font-size:0.75rem; font-weight:400; display:block; margin-bottom:2px; opacity:0.8;">{label}</span>
                {word}
            </div>'''
    cards_html += '</div>'
    return cards_html

# --- Main UI ---
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        if msg.get("is_recommendation"):
            st.markdown("**Rekomendasi untuk Anda:**")
            st.markdown(render_recommendations(msg["content"]), unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

if not api_key:
    st.info("👈 Masukkan API Key di sidebar untuk mulai.")
else:
    st.markdown("---")
    with st.form("input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            my_word = st.text_input("✋ Kata Anda", placeholder="Misal: GAJAH")
        with col2:
            opp_word = st.text_input("⚔️ Kata Lawan", placeholder="Misal: HARIMAU")

        submitted = st.form_submit_button("Dapatkan Rekomendasi →", use_container_width=True, type="primary")

    if submitted:
        my_word_clean = "".join(c for c in my_word if c.isalpha()).strip().upper()
        opp_word_clean = "".join(c for c in opp_word if c.isalpha()).strip().upper()

        errors = []
        if not my_word_clean:
            errors.append("Kata Anda tidak boleh kosong.")
        elif " " in my_word_clean:
            errors.append("Kata Anda harus 1 kata saja.")
        elif my_word_clean in st.session_state.used_words:
            errors.append(f"Kata '**{my_word_clean}**' sudah pernah dipakai!")

        if not opp_word_clean:
            errors.append("Kata Lawan tidak boleh kosong.")
        elif " " in opp_word_clean:
            errors.append("Kata Lawan harus 1 kata saja.")
        elif opp_word_clean in st.session_state.used_words:
            errors.append(f"Kata lawan '**{opp_word_clean}**' sudah pernah dipakai!")

        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
        else:
            # Tambahkan ke riwayat dan used_words
            st.session_state.used_words.add(my_word_clean)
            st.session_state.used_words.add(opp_word_clean)

            st.session_state.history.append({
                "role": "user",
                "content": f"**Anda:** {my_word_clean} → **Lawan:** {opp_word_clean}"
            })

            with st.spinner("AI menyusun rekomendasi..."):
                result = get_recommendations(opp_word_clean, st.session_state.used_words)

            st.session_state.history.append({
                "role": "assistant",
                "content": result,
                "is_recommendation": True
            })

            st.rerun()
