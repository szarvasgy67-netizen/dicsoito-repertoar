from collections import Counter
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


def normalize_match(text):
  nfkd = unicodedata.normalize("NFKD", str(text).lower())
  return "".join([c for c in nfkd if c.isalnum() or c == " "]).strip()


s = chr(47)
q_mark = chr(63)
eq = chr(61)


def build_yt_search_url(query_text):
  q = clean_query(query_text)
  return (
      "https:"
      + s
      + s
      + "://youtube.com"
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

# Látható visszajelzés, ha a bal oldali szűrő aktív!
if search_query or selected_themes or selected_origin or selected_key:
  st.success(
      f"🎯 **Szűrés aktív:** {len(filtered_songs)} dal felel meg a bal"
      " oldalon megadott feltételeknek (nézd a **📚 Dalbank** fület)!"
  )
else:
  st.markdown(
      f"Jelenleg **{len(songs)} keresztény dicséret** érhető el a dalbankban"
      " – a bal oldali szűrőkkel tudsz válogatni."
  )

tab1, tab2, tab3 = st.tabs([
    f"📚 Dalbank ({len(filtered_songs)} találat)",
    f"📋 Koncertanyag / Setlist ({len(st.session_state.setlist)})",
    "📊 Rádiós Trendek & Lista Elemző",
])

# === 1. FÜL: DALBANK ===
with tab1:
  if not filtered_songs:
    st.warning(
        "Ezzel a szűrési feltétellel nincs dal a listában. Próbálj meg kevesebb"
        " szűrőt beállítani!"
    )
  else:
    st.caption(
        f"Szűrt lista: **{len(filtered_songs)} dal** (válassz az alábbi"
        " legördülő menüből):"
    )

    song_options = {
        f"#{song['id']} | {song['title']} – {song['artist']} ({song['key']})": (
            song
        )
        for song in filtered_songs
    }
    selected_label = st.selectbox(
        "Válassz egy dalt a szűrt listából:", list(song_options.keys())
    )
    song = song_options[selected_label]

    st.divider()

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
# === 3. FÜL: RÁDIÓS TRENDEK & LISTA ELEMZŐ ===
with tab3:
  st.subheader("📻 Amerikai Keresztény Rádiók Lejátszási Listái & Trendek")
  st.markdown(
      "Az alábbi gombok közvetlenül az **Air1 Worship Now** és a **K-LOVE**"
      " csatornák elmúlt napokban/hetekben játszott dalainak listáját nyitják"
      " meg (Európából is elérhető felületen):"
  )

  # Európából is blokkolás nélkül működő közvetlen lejátszási lista linkek (chr(47) trükkel)
  air1_pl_url = (
      "https:"
      + s
      + s
      + "onlineradiobox.com"
      + s
      + "us"
      + s
      + "air1"
      + s
      + "playlist"
      + s
  )
  klove_pl_url = (
      "https:"
      + s
      + s
      + "onlineradiobox.com"
      + s
      + "us"
      + s
      + "klove"
      + s
      + "playlist"
      + s
  )
  worship_charts_url = build_google_search_url(
      "Air1 Worship Now recently played songs playlist"
  )

  r_col1, r_col2, r_col3 = st.columns(3)
  with r_col1:
    st.link_button(
        "🎵 Air1 Worship – Lejátszási lista (7 nap)",
        air1_pl_url,
        use_container_width=True,
        type="primary",
    )
  with r_col2:
    st.link_button(
        "❤️ K-LOVE – Lejátszási lista (7 nap)",
        klove_pl_url,
        use_container_width=True,
        type="primary",
    )
  with r_col3:
    st.link_button(
        "🔍 Air1 / K-LOVE Top Listák keresése",
        worship_charts_url,
        use_container_width=True,
    )

  st.divider()

  # 2. Copy-Paste Lejátszási Lista Elemző
  st.markdown("### 📋 Rádiós Lejátszási Lista Gyors-Elemző")
  st.caption(
      "Nyisd meg a fenti Air1 vagy K-LOVE lejátszási listát, jelöld ki a"
      " dalokat (Ctrl+C), másold ide (Ctrl+V), és a program kigyűjti a"
      " zenekarokat, a gyakoriságot és összeveti a saját dalbankoddal!"
  )

  pasted_playlist = st.text_area(
      "Másold ide a rádiós lejátszási listát (soronként pl. 'Előadó - Dal címe'"
      " vagy '14:20 Előadó - Dal címe'):",
      height=180,
      placeholder=(
          "Példa:\n18:15 Elevation Worship - Praise\n18:10 Brandon Lake -"
          " Gratitude\n18:05 Phil Wickham - Living Hope\n17:58 Elevation"
          " Worship - Praise\n17:52 Hillsong Worship - What A Beautiful Name"
      ),
  )

  if pasted_playlist.strip():
    raw_lines = [
        line.strip() for line in pasted_playlist.splitlines() if line.strip()
    ]
    song_entries = []
    artists_counter = Counter()

    for line in raw_lines:
      sep = " - " if " - " in line else (" – " if " – " in line else None)
      if sep:
        parts = line.split(sep, 1)
        part_a, part_b = parts[0].strip(), parts[1].strip()
        if len(part_a) > 6 and part_a[:2].isdigit() and ":" in part_a[:6]:
          part_a = part_a.split(" ", 1)[-1].strip()
        artists_counter[part_a] += 1
        song_entries.append(f"{part_a} – {part_b}")
      elif len(line) > 3 and not line.isdigit():
        song_entries.append(line)

    song_counts = Counter(song_entries)

    st.success(
        f"Feldolgozva: **{len(song_entries)} lejátszás**, **{len(song_counts)}"
        " különböző dal**!"
    )

    an_col1, an_col2 = st.columns([1.4, 1])

    with an_col1:
      st.markdown("#### 🏆 Legtöbbet játszott dalok & Dalbank egyezés")
      for entry, count in song_counts.most_common(30):
        norm_entry = normalize_match(entry)
        matched_song = None
        for db_song in songs:
          db_title = normalize_match(db_song["title"])
          title_words = [w for w in db_title.split() if len(w) > 3]
          if title_words and all(w in norm_entry for w in title_words[:3]):
            matched_song = db_song
            break

        with st.container(border=True):
          m1, m2 = st.columns([3, 1.2])
          with m1:
            st.markdown(f"**{entry}** *(lejátszva: {count}x)*")
            if matched_song:
              st.caption(
                  f"✅ **Megvan a dalbankban (#{matched_song['id']})** | 🎵"
                  f" {matched_song['key']} | 🏷️"
                  f" {', '.join(matched_song['themes'])}"
              )
            else:
              st.caption("🆕 Új dal (még nincs a dalbankban)")
          with m2:
            st.link_button(
                "▶️ YouTube",
                build_yt_search_url(entry),
                use_container_width=True,
            )

    with an_col2:
      st.markdown("#### 🎸 Zenekarok megoszlása a listában")
      if artists_counter:
        for artist_name, a_count in artists_counter.most_common(20):
          st.markdown(f"- **{artist_name}**: {a_count} lejátszás")
      else:
        st.info(
            "Ha 'Előadó - Dal címe' formátumban másolod be a listát, itt"
            " zenekaronként is összesíti!"
        )

  st.divider()

  # 3. Saját Repertoár Statisztika (Zenekaronként és Tematikánként)
  st.markdown(
      f"### 📈 Saját Repertoár Statisztika ({len(songs)} dal bontása)"
  )
  stat_col1, stat_col2 = st.columns(2)

  with stat_col1:
    st.markdown("#### Top Előadók / Források a dalbankodban")
    db_artists = Counter(song["artist"] for song in songs)
    for artist, cnt in db_artists.most_common(15):
      st.markdown(f"- **{artist}**: {cnt} dal")

  with stat_col2:
    st.markdown("#### Tematikák megoszlása a dalbankodban")
    db_themes = Counter(t for song in songs for t in song["themes"])
    for theme, cnt in db_themes.most_common(15):
      st.markdown(f"- **🏷️ {theme}**: {cnt} dal")
