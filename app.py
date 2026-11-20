import json
import math
import urllib.parse
import streamlit as st

st.set_page_config(
    page_title="Dicsőítő Repertoár", page_icon="🎸", layout="wide"
)

# Görgetősáv kényszerítése + natív HTML gombok stílusa
st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"], .main {
            overflow-y: auto !important;
            height: auto !important;
        }
        .ext-btn {
            display: block;
            width: 100%;
            padding: 0.55rem 1rem;
            margin-bottom: 0.5rem;
            border-radius: 0.5rem;
            text-align: center;
            text-decoration: none !important;
            font-weight: 600;
            font-size: 0.95rem;
            transition: opacity 0.2s;
        }
        .ext-btn:hover {
            opacity: 0.85;
        }
        .yt-btn {
            background-color: #FF0000;
            color: #FFFFFF !important;
        }
        .sheet-btn {
            background-color: #262730;
            color: #FFFFFF !important;
            border: 1px solid #4A4C5A;
        }
        .radio-btn {
            background-color: #1E3A8A;
            color: #FFFFFF !important;
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
  for ch in ["/", "(", ")", ".", ",", "&"]:
    raw = raw.replace(ch, " ")
  return " ".join(raw.split())


def make_yt_search_url(query_text):
  base = "https://" + "://youtube.com" + "/results"
  params = urllib.parse.urlencode({"search_query": query_text})
  return f"{base}?{params}"


def make_google_search_url(query_text):
  base = "https://" + "://google.com" + "/search"
  params = urllib.parse.urlencode({"q": query_text})
  return f"{base}?{params}"


def render_link_button(label, url, css_class="sheet-btn"):
  st.markdown(
      f'<a href="{url}" target="_top" rel="noopener noreferrer" class="ext-btn'
      f' {css_class}">{label}</a>',
      unsafe_allow_html=True,
  )


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
render_link_button(
    "🎵 Air1 Worship Now", "https://" + "://air1.com", "radio-btn"
)
render_link_button(
    "❤️ K-LOVE Radio", "https://" + "://klove.com", "radio-btn"
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

          # Kotta gomb (target="_top" + középső klikkel új lapon nyílik)
          sheet_url = song.get("sheet_music_url") or make_google_search_url(
              f"{clean_query} chords lyrics"
          )
          sheet_label = (
              "🎼 Kotta megnyitása"
              if song.get("sheet_music_url")
              else "🎼 Kotta / Akkord keresése"
          )
          render_link_button(sheet_label, sheet_url, "sheet-btn")

          # YouTube gomb (target="_top" + középső klikkel új lapon nyílik)
          yt_search_url = make_yt_search_url(clean_query)
          render_link_button(
              "▶️ Meghallgatás YouTube-on", yt_search_url, "yt-btn"
          )
          st.caption(
              "💡 Tipp: Kattints középső egérgombbal (görgetővel), hogy új lapon"
              " nyíljon meg!"
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
      yt_link = make_yt_search_url(clean_item_query)
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
