import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="AI Sambung Kata", page_icon="📝", layout="centered")

# --- UI Styles ---
st.markdown("""
<style>
    .game-title { text-align: center; color: #2e7d32; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 2.5rem; margin-bottom: 0px;}
    .game-subtitle { text-align: center; color: #666; font-family: 'Inter', sans-serif; font-size: 1.1rem; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="game-title">📝 Sambung Kata AI</p>', unsafe_allow_html=True)
st.markdown('<p class="game-subtitle">Lawan Gemini AI dalam permainan kata tak terbatas!</p>', unsafe_allow_html=True)

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    # Mengambil API key dari Streamlit Secrets (untuk deployment awan)
    # Jika berjalan lokal, ini akan membaca dari .streamlit/secrets.toml
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = None

    if api_key and api_key != "your_api_key_here":
        try:
            genai.configure(api_key=api_key)
            st.success("✅ API Key berhasil dimuat dari Secrets/sistem!")
        except Exception as e:
            st.error("❌ API Key invalid.")
    else:
        st.warning("⚠️ API Key belum dikonfigurasi. Pastikan mengatur st.secrets saat deploy.")
    
    st.markdown("---")
    st.markdown("### 📜 Aturan Main:")
    st.markdown("1. Mainkan 1 kata saja.")
    st.markdown("2. Kata selanjutnya **diawali dengan huruf terakhir** dari kata musuh.")
    st.markdown("3. **Tidak boleh** memakai kata yang sudah dipakai sebelumnya pada sesi game yang sama.")
    
    st.markdown("---")
    if st.button("🔄 Reset Permainan", use_container_width=True, type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- Initialize Session State ---
if "history" not in st.session_state:
    st.session_state.history = []
if "used_words" not in st.session_state:
    st.session_state.used_words = set()
if "current_ai_words" not in st.session_state:
    st.session_state.current_ai_words = []
if "game_over" not in st.session_state:
    st.session_state.game_over = False

# --- API Functions ---
def get_ai_responses(last_word, used_words_list):
    char_1 = last_word[-1].upper()
    char_2 = last_word[-2:].upper() if len(last_word) >= 2 else char_1
    char_3 = last_word[-3:].upper() if len(last_word) >= 3 else char_2
    used_str = ", ".join(used_words_list)
    
    prompt = f"""Kata terakhir dari pemain adalah: "{last_word.upper()}".

Tugasmu memberikan 3 jawaban kata dasar Bahasa Indonesia sekaligus sebagai balasan. Aturannya:
1. Kata TIDAK BOLEH ada di daftar kata yang sudah dipakai ini: [{used_str}].
2. Format yang HARUS diberikan:
   1 HURUF: [Kata yang berawalan "{char_1}"]
   2 HURUF: [Kata yang berawalan "{char_2}"] (Jika sangat sulit/tidak ada, ganti pakai awalan "{char_1}")
   3 HURUF: [Kata yang berawalan "{char_3}"] (Jika sangat sulit/tidak ada, ganti pakai awalan "{char_1}")

Contoh Jika Pemain="KUCING":
1 HURUF: GAJAH
2 HURUF: NGAMUK
3 HURUF: INGGRIS

Berikan HANYA 3 baris jawaban di atas tanpa basa-basi, tanpa penjelasan tambahan."""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        text = response.text.strip().upper()
        
        words = []
        for line in text.splitlines():
            if ":" in line:
                part = line.split(":", 1)[1]
            else:
                part = line
            w = "".join(c for c in part if c.isalpha() or c.isspace()).strip().split()
            if w:
                words.append(w[0])
            
        return text.replace('\n', '\n\n'), words
    except Exception as e:
        return f"ERROR: {e}", []

# --- Main UI ---
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["word"])

if st.session_state.game_over:
    st.error("🏁 Permainan Berakhir! Silakan tekan tombol 'Reset Permainan' di sidebar untuk mulai ulang.")
else:
    if not api_key:
        st.info("👈 Silakan masukkan API Key Google Gemini Anda di sidebar sebelah kiri untuk mulai permainan.")
    else:
        if st.session_state.current_ai_words:
            allowed_chars = list(set([w[-1].upper() for w in st.session_state.current_ai_words if w]))
            last_char_msg = " ATAU ".join(allowed_chars)
            st.info(f"Giliran Anda! Kata selanjutnya bebas berawalan huruf: **{last_char_msg}**")
        else:
            st.success("Babak Pertama! Giliran Anda, ketik kata apa saja untuk memulai permainan.")

        user_input = st.chat_input("Ketikkan tebakan kata Anda di sini...")
        
        if user_input:
            # clean punctuation
            word = "".join(c for c in user_input if c.isalpha() or c.isspace()).strip().upper()
            
            # --- PLAYER VALIDATION ---
            if " " in word:
                st.error("⚠️ Masukkan hanya 1 kata (tanpa kalimat/spasi).")
                st.stop()
            elif word in st.session_state.used_words:
                st.error(f"❌ Kata '{word}' sudah dipakai di game ini! Kalian tidak boleh memakai kata berulang. Anda kalah.")
                st.session_state.history.append({"role": "user", "word": f"~~{word}~~ (KATA SUDAH DIPAKAI)"})
                st.session_state.game_over = True
                st.rerun()
            elif st.session_state.current_ai_words:
                allowed_chars = list(set([w[-1].upper() for w in st.session_state.current_ai_words if w]))
                if not any(word.startswith(c) for c in allowed_chars):
                    st.error(f"❌ Kata '{word}' tidak berawalan salah satu dari {', '.join(allowed_chars)}! Anda kalah.")
                    st.session_state.history.append({"role": "user", "word": f"~~{word}~~ (SALAH HURUF AWAL)"})
                    st.session_state.game_over = True
                    st.rerun()
            
            # Input valid
            st.session_state.used_words.add(word)
            st.session_state.history.append({"role": "user", "word": f"**Anda:** {word}"})
            
            # --- ENEMY (AI) GILIRAN ---
            with st.spinner("Giliran Musuh (AI) memikirkan 3 kata..."):
                raw_text, ai_words_list = get_ai_responses(word, list(st.session_state.used_words))
                
                if not ai_words_list or raw_text.startswith("ERROR"):
                    st.error("Terjadi masalah pada server API. Mainkan kembali.")
                    st.stop()
                else:
                    st.session_state.history.append({"role": "assistant", "word": f"**Lawan AI:**\n\n{raw_text}"})
                    st.session_state.current_ai_words = []
                    
                    for aw in ai_words_list:
                        st.session_state.used_words.add(aw)
                        st.session_state.current_ai_words.append(aw)
                
            st.rerun()
