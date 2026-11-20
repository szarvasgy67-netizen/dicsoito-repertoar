from collections import Counter
import json
import unicodedata
from bs4 import BeautifulSoup
import requests
import streamlit as st
import streamlit.components.v1 as components

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


def external_open_button(label, url, bg_color="#FF0000"):
  """A klasszikus zongorás appban bevált components.html alapú, blokkolásmentes külső megnyitó gomb."""
  safe_url = url.replace('"', "%22").replace("'", "%27")
  html_code = f"""
    <div style="margin: 0; padding: 0;">
        <button onclick="window.open('{safe_url}', '_blank', 'noopener,noreferrer')"
                style="width: 100%; padding: 10px 14px; background-color: {bg_color}; color: white;
                       border: none; border-radius: 8px; font-family: sans-serif; font-size: 14px;
                       font-weight: 600; cursor: pointer;">
            {label}
        </button>
    </div>
    """
  components.html(html_code, height=46)


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
    "📊 Amerikai Rádiós Toplisták (Air1 & K-LOVE)",
])

# === 1. FÜL: DALBANK ===
with tab1:
  if not filtered_songs:
    st.warning(
        "Ezzel a szűrési feltétellel nincs dal a listában. Próbálj meg kevesebb"
        " szűrőt beállítani!"
    )
  else:
    st.caption(f"Szűrt lista: **{len(filtered_songs)} dal**")

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
          external_open_button(
              "▶️ Megnyitás YouTube-on", yt_url, bg_color="#FF0000"
          )
          external_open_button(
              "🔍 További verziók a YouTube-on",
              yt_search_url,
              bg_color="#333333",
          )
        else:
          external_open_button(
              f"▶️ {song['title']} a YouTube-on",
              yt_search_url,
              bg_color="#FF0000",
          )

        sheet_url = song.get("sheet_music_url", "").strip()
        if sheet_url:
          external_open_button(
              "🎼 Kotta megnyitása", sheet_url, bg_color="#1E3A8A"
          )
        else:
          chord_search_url = build_google_search_url(
              f"{search_str} chords lyrics"
          )
          external_open_button(
              "🎼 Kotta / Akkord keresése",
              chord_search_url,
              bg_color="#1E3A8A",
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
@st.cache_data(ttl=3600)
def fetch_us_christian_radio_data():
  """Amerikai Streamlit szerverről (USA IP) dinamikusan lekéri a friss keresztény rádiós és toplistás adatokat."""
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  results = {"air1": [], "klove": [], "itunes_christian": []}

  # 1. Air1 playlist lekérése USA szerverről
  try:
    url_air1 = (
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
    r = requests.get(url_air1, headers=headers, timeout=8)
    if r.status_code == 200:
      soup = BeautifulSoup(r.text, "html.parser")
      for row in soup.select("table.tablelist-schedule tr"):
        cols = [c.get_text(" ", strip=True) for c in row.find_all("td")]
        if len(cols) >= 2 and " - " in cols:
          results["air1"].append(cols)
  except Exception:
    pass

  # 2. K-LOVE playlist lekérése USA szerverről
  try:
    url_klove = (
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
    r = requests.get(url_klove, headers=headers, timeout=8)
    if r.status_code == 200:
      soup = BeautifulSoup(r.text, "html.parser")
      for row in soup.select("table.tablelist-schedule tr"):
        cols = [c.get_text(" ", strip=True) for c in row.find_all("td")]
        if len(cols) >= 2 and " - " in cols:
          results["klove"].append(cols)
  except Exception:
    pass

  # 3. Apple Music / iTunes USA Christian & Gospel Top 50 élő JSON feed
  try:
    url_itunes = (
        "https:"
        + s
        + s
        + "://apple.com"
        + s
        + "us"
        + s
        + "rss"
        + s
        + "topsongs"
        + s
        + "limit=50"
        + s
        + "genre=22"
        + s
        + "json"
    )
    r = requests.get(url_itunes, headers=headers, timeout=8)
    if r.status_code == 200:
      data = r.json()
      entries = data.get("feed", {}).get("entry", [])
      for entry in entries:
        title = entry.get("im:name", {}).get("label", "")
        artist = entry.get("im:artist", {}).get("label", "")
        if title and artist:
          results["itunes_christian"].append(f"{artist} - {title}")
  except Exception:
    pass

  return results


# === 3. FÜL: DINAMIKUS AMERIKAI RÁDIÓS TOPLISTÁK ===
with tab3:
  st.subheader("📻 Élő Amerikai Keresztény Rádiós & Toplista Adatok")
  st.caption(
      "Mivel az alkalmazás amerikai szerveren fut, közvetlenül lekéri a friss"
      " USA keresztény rádiós (Air1, K-LOVE) és slágerlistás adatokat –"
      " európai tiltás nélkül!"
  )

  col_btn1, col_btn2 = st.columns()
  with col_btn1:
    if st.button("🔄 Adatok frissítése most", use_container_width=True):
      st.cache_data.clear()
      st.rerun()

  with st.spinner("Amerikai keresztény rádiós listák lekérése..."):
    radio_data = fetch_us_christian_radio_data()

  source_options = {}
  if radio_data["air1"]:
    source_options[
        f"🎵 Air1 Worship Now – Friss adáslista ({len(radio_data['air1'])} dal)"
    ] = radio_data["air1"]
  if radio_data["klove"]:
    source_options[
        f"❤️ K-LOVE Radio – Friss adáslista ({len(radio_data['klove'])} dal)"
    ] = radio_data["klove"]
  if radio_data["itunes_christian"]:
    source_options[
        "🏆 USA Christian & Gospel Top 50"
        f" ({len(radio_data['itunes_christian'])} dal)"
    ] = radio_data["itunes_christian"]

  if not source_options:
    st.warning(
        "A külső rádiós szerverek most lassabban válaszolnak. Nyomj a"
        " 'Frissítés' gombra, vagy használd a lenti saját statisztikát!"
    )
  else:
    selected_source = st.selectbox(
        "Válassz élő adatforrást:", list(source_options.keys())
    )
    active_list = source_options[selected_source]

    parsed_items = []
    artist_counts = Counter()

    for row in active_list:
      if " - " in row:
        art, tit = row.split(" - ", 1)
        art, tit = art.strip(), tit.strip()
        artist_counts[art] += 1
        parsed_items.append((art, tit, row))

    top_artists = [f"{a} ({c} dal)" for a, c in artist_counts.most_common()]
    selected_radio_artist = st.selectbox(
        "Szűrés zenekarra az élő listában:",
        ["Összes zenekar"] + top_artists,
    )

    if selected_radio_artist != "Összes zenekar":
      target_artist = selected_radio_artist.rsplit(" (", 1)
      display_items = [
          item for item in parsed_items if item == target_artist
      ]
    else:
      display_items = parsed_items

    st.divider()
    d_col1, d_col2 = st.columns([1.5, 1])

    with d_col1:
      st.markdown(f"#### 🎶 Dalok a listában ({len(display_items)} találat)")
      seen_songs = Counter((art, tit) for art, tit, _ in display_items)

      for (art, tit), play_count in seen_songs.most_common(40):
        full_label = f"{art} – {tit}"
        norm_title = normalize_match(tit)

        matched_song = None
        for db_song in songs:
          db_title = normalize_match(db_song["title"])
          title_words = [w for w in norm_title.split() if len(w) > 3]
          if title_words and all(w in db_title for w in title_words[:3]):
            matched_song = db_song
            break

        with st.container(border=True):
          m1, m2 = st.columns([3, 1.3])
          with m1:
            count_badge = (
                f" *(lejátszva: {play_count}x)*" if play_count > 1 else ""
            )
            st.markdown(f"**{full_label}**{count_badge}")
            if matched_song:
              st.caption(
                  f"✅ **Megvan a dalbankban (#{matched_song['id']})** | 🎵"
                  f" {matched_song['key']} | 🏷️"
                  f" {', '.join(matched_song['themes'])}"
              )
            else:
              st.caption("🆕 Új dal (még nincs a dalbankban)")
          with m2:
            # Ugyanaz a blokkolásmentes components.html gomb, mint az 1. fülön!
            external_open_button(
                "▶️ YouTube",
                build_yt_search_url(f"{art} {tit}"),
                bg_color="#FF0000",
            )

    with d_col2:
      st.markdown("#### 🎸 Zenekarok rangsora ebben a listában")
      for art_name, cnt in artist_counts.most_common(20):
        st.markdown(f"- **{art_name}**: {cnt} lejátszás / dal")

  st.divider()

  # Saját Repertoár Statisztika
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
