import json
import streamlit as st

st.set_page_config(
    page_title="Dicsőítő Repertoár", page_icon="🎸", layout="wide"
)


# 1. Gyorsítótárazott adatbetöltés (villámgyors működés)
@st.cache_data
def load_songs():
  with open("data/songs.json", "r", encoding="utf-8") as f:
    return json.load(f)


songs = load_songs()

# Session state inicializálása a koncertanyaghoz (setlist)
if "setlist" not in st.session_state:
  st.session_state.setlist = []

# --- OLDALSÁV: SZŰRŐK ---
st.sidebar.header("🔍 Dal keresése és szűrése")

search_query = st.sidebar.text_input(
    "Keresés címre vagy dalszövegre:", placeholder="pl. Óceánok, kegyelem..."
)

all_themes = sorted(list({theme for song in songs for theme in song["themes"]}))
selected_themes = st.sidebar.multiselect(
    "Tematika (szöveg alapján):", options=all_themes
)

all_origins = sorted(list({song["origin"] for song in songs}))
selected_origin = st.sidebar.multiselect("Eredet / Stílus:", options=all_origins)

all_keys = sorted(list({song["key"] for song in songs}))
selected_key = st.sidebar.multiselect("Hangnem:", options=all_keys)

# --- OLDALSÁV: ÉLŐ RÁDIÓK ---
st.sidebar.divider()
st.sidebar.subheader("📻 Élő Dicsőítő Rádiók (USA)")
st.sidebar.caption("Ingyenes 0-24 online stream inspirációhoz:")
st.sidebar.link_button(
    "🎵 Air1 Worship Now",
    "https://air1.com",
    use_container_width=True,
)
st.sidebar.link_button(
    "❤️ K-LOVE Radio", "https://klove.com", use_container_width=True
)

# --- SZŰRÉSI LOGIKA ---
filtered_songs = []
for song in songs:
  if search_query:
    q = search_query.lower()
    if (
        q not in song["title"].lower()
        and q not in song["artist"].lower()
        and q not in song["lyrics"].lower()
    ):
      continue

  if selected_themes:
    if not all(t in song["themes"] for t in selected_themes):
      continue

  if selected_origin and song["origin"] not in selected_origin:
    continue

  if selected_key and song["key"] not in selected_key:
    continue

  filtered_songs.append(song)

# --- FŐ FELÜLET (FÜLEK) ---
st.title("🎸 Dicsőítő Repertoár & Setlist Tervező")

tab1, tab2 = st.tabs([
    f"📚 Dalbank ({len(filtered_songs)} találat)",
    f"📋 Koncertanyag / Setlist ({len(st.session_state.setlist)})",
])

# === 1. FÜL: DALBANK ===
with tab1:
  if not filtered_songs:
    st.info(
        "Nincs a szűrési feltételeknek megfelelő dal. Próbálj meg kevesebb"
        " szűrőt beállítani!"
    )
  else:
    for song in filtered_songs:
      with st.expander(
          f"**{song['title']}** – {song['artist']} | 🎵 {song['key']} | 🏷️"
          f" {', '.join(song['themes'])}"
      ):
        col1, col2 = st.columns([3, 2])

        with col1:
          st.subheader("Dalszöveg")
          st.text(song["lyrics"])

        with col2:
          st.subheader("Média és Kotta")
          st.markdown(f"**Hangnem:** {song['key']} | **Tempó:** {song['bpm']} BPM")

          if song.get("sheet_music_url"):
            st.link_button(
                "🎼 Kotta megnyitása",
                song["sheet_music_url"],
                use_container_width=True,
            )

          if song.get("youtube_url"):
            st.video(song["youtube_url"])

          is_in_setlist = any(
              s["id"] == song["id"] for s in st.session_state.setlist
          )
          if is_in_setlist:
            st.success("✅ Már benne van a koncertanyagban")
          else:
            if st.button(
                "➕ Hozzáadás a koncertanyaghoz",
                key=f"add_{song['id']}",
                use_container_width=True,
            ):
              st.session_state.setlist.append(song)
              st.rerun()

# === 2. FÜL: KONCERTANYAG / SETLIST ===
with tab2:
  st.subheader("Összeállított dallista")

  if not st.session_state.setlist:
    st.info(
        "Még üres a koncertanyagod. A Dalbank fülön tudsz dalokat hozzáadni!"
    )
  else:
    export_lines = ["KONCERTANYAG / DICSŐÍTŐ SETLIST\n" + "=" * 35 + "\n"]

    for idx, item in enumerate(st.session_state.setlist):
      c1, c2, c3, c4 = st.columns([4, 4, 1, 1])
      with c1:
        st.markdown(
            f"**{idx + 1}. {item['title']}** ({item['artist']}) –"
            f" *{item['key']}*"
        )
      with c2:
        note = st.text_input(
            "Megjegyzés",
            key=f"note_{item['id']}",
            placeholder="pl. Lassú átkötés, ima...",
            label_visibility="collapsed",
        )
      with c3:
        if idx > 0 and st.button("⬆️", key=f"up_{item['id']}"):
          st.session_state.setlist[idx], st.session_state.setlist[idx - 1] = (
              st.session_state.setlist[idx - 1],
              st.session_state.setlist[idx],
          )
          st.rerun()
      with c4:
        if st.button("🗑️", key=f"del_{item['id']}"):
          st.session_state.setlist.pop(idx)
          st.rerun()

      note_text = f" | Megjegyzés: {note}" if note else ""
      export_lines.append(
          f"{idx + 1}. {item['title']} - {item['artist']} [{item['key']},"
          f" {item['bpm']} BPM]{note_text}\n   YouTube:"
          f" {item.get('youtube_url', 'Nincs')}\n   Kotta:"
          f" {item.get('sheet_music_url', 'Nincs')}\n"
      )

    st.divider()

    final_text = "\n".join(export_lines)
    col_exp1, col_exp2 = st.columns([2, 1])
    with col_exp1:
      st.download_button(
          label="📥 Koncertanyag letöltése (.txt) a zenekarnak",
          data=final_text,
          file_name="koncertanyag_setlist.txt",
          mime="text/plain",
          type="primary",
      )
    with col_exp2:
      if st.button("🧹 Teljes lista törlése"):
        st.session_state.setlist = []
        st.rerun()
