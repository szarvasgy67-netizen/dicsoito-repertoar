import json
import math
import urllib.parse
import streamlit as st

st.set_page_config(
    page_title="Dicsőítő Repertoár", page_icon="🎸", layout="wide"
)

# Görgetősáv kényszerítése, hogy sose tűnjön el a Streamlit keretben
st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"], .main {
            overflow-y: auto !important;
            height: auto !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def load_songs():
  with open("data/songs.json", "r", encoding="utf-8") as f:
    content = f.read()
  try:
    return json.loads(content)
  except json.JSONDecodeError as e:
    st.error(
        f"⚠️ Hiba a data/songs.json fájlban a **{e.lineno}. sorban** (a"
        f" {e.colno}. karakternél): {e.msg}"
    )
    st.stop()


def build_clean_query(title, artist):
  raw = f"{title} {artist}"
  for ch in ["/", "(", ")", ".", ","]:
    raw = raw.replace(ch, " ")
  return " ".join(raw.split())


songs = load_songs()

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
    # Lapozó (25 dal oldalanként a gyors böngészéshez)
    items_per_page = 25
    total_pages = max(1, math.ceil(len(filtered_songs) / items_per_page))

    if total_pages > 1:
      page = st.number_input(
          f"Oldal kiválasztása (1 – {total_pages}. oldal, oldalanként"
          f" {items_per_page} dal):",
          min_value=1,
          max_value=total_pages,
          value=1,
          step=1,
      )
    else:
      page = 1

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    visible_songs = filtered_songs[start_idx:end_idx]

    for song in visible_songs:
      with st.expander(
          f"**{song['id']}. {song['title']}** – {song['artist']} | 🎵"
          f" {song['key']} | 🏷️ {', '.join(song['themes'])}"
      ):
        col1, col2 = st.columns([1.2, 1])

        with col1:
          st.subheader("Dalszöveg")
          st.text(song["lyrics"])

        with col2:
          st.subheader("Média és Kotta")
          st.markdown(f"**Hangnem:** {song['key']} | **Tempó:** {song['bpm']} BPM")

          clean_query = build_clean_query(song["title"], song["artist"])
          search_term = urllib.parse.quote_plus(clean_query)
          chord_search_term = urllib.parse.quote_plus(
              f"{clean_query} chords lyrics"
          )

          # Kotta gomb
          sheet_url = (
              song.get("sheet_music_url")
              or f"https://google.com{chord_search_term}"
          )
          sheet_label = (
              "🎼 Kotta megnyitása"
              if song.get("sheet_music_url")
              else "🎼 Kotta / Akkord keresése"
          )
          st.link_button(sheet_label, sheet_url, use_container_width=True)

          # Megbízható YouTube gomb (új lapon nyílik, így sosem tiltja le a kiadó)
          yt_search_url = (
              f"https://youtube.com{search_term}"
          )
          if song.get("youtube_url"):
            st.link_button(
                "▶️ Lejátszás YouTube-on (új lapon)",
                song["youtube_url"],
                use_container_width=True,
                type="primary",
            )
            st.link_button(
                "🔍 Másik verzió keresése YouTube-on",
                yt_search_url,
                use_container_width=True,
            )
          else:
            st.link_button(
                "▶️ Meghallgatás YouTube-on",
                yt_search_url,
                use_container_width=True,
                type="primary",
            )

          # Hozzáadás a setlisthez
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
      c1, c2, c3, c4 = st.columns()
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
      clean_item_query = build_clean_query(item["title"], item["artist"])
      yt_link = item.get(
          "youtube_url"
      ) or "https://youtube.com" + urllib.parse.quote_plus(
          clean_item_query
      )
      export_lines.append(
          f"{idx + 1}. {item['title']} - {item['artist']} [{item['key']},"
          f" {item['bpm']} BPM]{note_text}\n   YouTube: {yt_link}\n"
      )

    st.divider()

    final_text = "\n".join(export_lines)
    col_exp1, col_exp2 = st.columns()
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
