import json
import unicodedata
import streamlit as st

st.set_page_config(
    page_title="Dicsőítő Repertoár & Setlist Tervező",
    page_icon="🎸",
    layout="wide",
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


def clean_query(text):
  nfkd = unicodedata.normalize("NFKD", str(text))
  ascii_text = "".join([c for c in nfkd if c.isalnum() or c == " "])
  return "+".join(ascii_text.split())


s = chr(47)
q_mark = chr(63)
eq = chr(61)


def build_yt_search_url(query_text):
  q = clean_query(query_text)
  return (
      "https:"
      + s
      + s
      + "www.youtube.com"
      + s
      + "results"
      + q_mark
      + "search_query"
      + eq
      + q
  )


def build_google_search_url(query_text):
  q = clean_query(query_text)
  return "https:" + s + s + "://google.com" + s + "search" + q_mark + "q" + eq + q


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
    "https:" + s + s + "://air1.com" + s + "listen",
    use_container_width=True,
)
st.sidebar.link_button(
    "❤️ K-LOVE Radio",
    "https:" + s + s + "://klove.com" + s + "listen",
    use_container_width=True,
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

# --- FŐ FELÜLET ---
st.title("🎸 Dicsőítő Repertoár & Setlist Tervező")
st.markdown(
    f"Jelenleg **{len(songs)} keresztény dicséret** érhető el a dalbankban –"
    " tematika, előadó és hangnem szerint szűrhetően."
)

tab1, tab2 = st.tabs([
    f"📚 Dalbank ({len(filtered_songs)} találat)",
    f"📋 Koncertanyag / Setlist ({len(st.session_state.setlist)})",
])

# === 1. FÜL: DALBANK ===
with tab1:
  if not filtered_songs:
    st.warning(
        "Ezzel a szűrési feltétellel nincs dal a listában. Próbálj meg kevesebb"
        " szűrőt beállítani!"
    )
  else:
    st.caption(f"Találatok száma: **{len(filtered_songs)} dal**")

    # Ugyanaz a tiszta legördülő választó, mint a klasszikus zenei appban (nincs görgetési gond!)
    song_options = {
        f"#{song['id']} | {song['title']} – {song['artist']} ({song['key']})": (
            song
        )
        for song in filtered_songs
    }
    selected_label = st.selectbox(
        "Válassz egy dalt a listából:", list(song_options.keys())
    )
    song = song_options[selected_label]

    st.divider()

    # Dal fejléc adatai
    c_head1, c_head2, c_head3 = st.columns((3, 1, 1))
    with c_head1:
      st.subheader(f"{song['title']}")
      st.markdown(
          f"**Előadó / Forrás:** {song['artist']} | **Stílus:**"
          f" {song['origin']}"
      )
    with c_head2:
      st.metric("Hangnem", song["key"])
    with c_head3:
      st.metric("Tempó", f"{song['bpm']} BPM")

    themes_str = " • ".join([f"🏷️ {t}" for t in song["themes"]])
    st.info(f"**Tematika:** {themes_str}")

    # Két oszlopos elrendezés: Dalszöveg + Média / Kotta / Setlist
    col1, col2 = st.columns([1.3, 1])

    with col1:
      st.markdown("### 📜 Dalszöveg")
      with st.container(border=True):
        st.text(song["lyrics"])

    with col2:
      st.markdown("### 🎧 Meghallgatás & Kotta")
      with st.container(border=True):
        search_str = f"{song['title']} {song['artist']}"
        yt_search_url = build_yt_search_url(search_str)
        yt_url = song.get("youtube_url", "").strip()

        # Pontosan ugyanaz a logika, mint a tegnapi klasszikus zenei appban!
        if "watch" + q_mark + "v" + eq in yt_url or "youtu.be" + s in yt_url:
          st.video(yt_url)
          st.link_button(
              "▶️ Megnyitás YouTube-on", yt_url, use_container_width=True
          )
          st.link_button(
              "🔍 További verziók a YouTube-on",
              yt_search_url,
              use_container_width=True,
          )
        else:
          st.link_button(
              f"🔍 {song['title']} a YouTube-on",
              yt_search_url,
              use_container_width=True,
              type="primary",
          )

        sheet_url = song.get("sheet_music_url", "").strip()
        if sheet_url:
          st.link_button(
              "🎼 Kotta megnyitása", sheet_url, use_container_width=True
          )
        else:
          chord_search_url = build_google_search_url(
              f"{search_str} chords lyrics"
          )
          st.link_button(
              "🎼 Kotta / Akkord keresése",
              chord_search_url,
              use_container_width=True,
          )

      st.markdown("### 📋 Koncertanyag")
      is_in_setlist = any(
          item["id"] == song["id"] for item in st.session_state.setlist
      )
      if is_in_setlist:
        st.success("✅ Ez a dal már szerepel a koncertanyagodban!")
      else:
        if st.button(
            "➕ Hozzáadás a koncertanyaghoz",
            key=f"add_{song['id']}",
            use_container_width=True,
            type="primary",
        ):
          st.session_state.setlist.append(song)
          st.rerun()

# === 2. FÜL: KONCERTANYAG / SETLIST ===
with tab2:
  st.subheader("Összeállított dallista")

  if not st.session_state.setlist:
    st.info(
        "Még üres a koncertanyagod. A Dalbank fülön válassz ki egy dalt, és"
        " kattints a '➕ Hozzáadás a koncertanyaghoz' gombra!"
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
      yt_link = item.get("youtube_url") or build_yt_search_url(
          f"{item['title']} {item['artist']}"
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
