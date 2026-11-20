from collections import Counter
import json
import unicodedata
from bs4 import BeautifulSoup
import requests
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
    st.error(f"Hiba a data/songs.json fájlban a {e.lineno}. sorban: {e.msg}")
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


@st.cache_data(ttl=3600)
def fetch_us_christian_radio_data():
  headers = {"User-Agent": "Mozilla/5.0"}
  results = {"air1": [], "klove": [], "itunes": []}
  for key, slug in [("air1", "air1"), ("klove", "klove")]:
    try:
      u = (
          "https:"
          + s
          + s
          + "onlineradiobox.com"
          + s
          + "us"
          + s
          + slug
          + s
          + "playlist"
          + s
      )
      r = requests.get(u, headers=headers, timeout=8)
      if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        for row in soup.select("table.tablelist-schedule tr"):
          cols = [c.get_text(" ", strip=True) for c in row.find_all("td")]
          if len(cols) >= 2 and " - " in cols[1]:
            results[key].append(cols[1])
    except Exception:
      pass
  try:
    u_it = (
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
    r = requests.get(u_it, headers=headers, timeout=8)
    if r.status_code == 200:
      for entry in r.json().get("feed", {}).get("entry", []):
        t = entry.get("im:name", {}).get("label", "")
        a = entry.get("im:artist", {}).get("label", "")
        if t and a:
          results["itunes"].append(f"{a} - {t}")
  except Exception:
    pass
  return results
songs = load_songs()
if "setlist" not in st.session_state:
  st.session_state.setlist = []

st.sidebar.header("🔍 Dal keresése és szűrése")
search_query = st.sidebar.text_input(
    "Keresés címre vagy dalszövegre:", placeholder="pl. Óceánok, kegyelem..."
)
all_themes = sorted(list({theme for song in songs for theme in song["themes"]}))
selected_themes = st.sidebar.multiselect("Tematika:", options=all_themes)
all_origins = sorted(list({song["origin"] for song in songs}))
selected_origin = st.sidebar.multiselect("Eredet / Stílus:", options=all_origins)
all_keys = sorted(list({song["key"] for song in songs}))
selected_key = st.sidebar.multiselect("Hangnem:", options=all_keys)

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
  if selected_themes and not all(t in song["themes"] for t in selected_themes):
    continue
  if selected_origin and song["origin"] not in selected_origin:
    continue
  if selected_key and song["key"] not in selected_key:
    continue
  filtered_songs.append(song)

st.title("🎸 Dicsőítő Repertoár & Setlist Tervező")
if search_query or selected_themes or selected_origin or selected_key:
  st.success(
      f"🎯 Szűrés aktív: {len(filtered_songs)} dal felel meg a feltételeknek!"
  )
else:
  st.markdown(f"Jelenleg **{len(songs)} keresztény dicséret** érhető el.")

tab1, tab2, tab3 = st.tabs([
    f"📚 Dalbank ({len(filtered_songs)} találat)",
    f"📋 Koncertanyag / Setlist ({len(st.session_state.setlist)})",
    "📊 Amerikai Rádiós Toplisták (Air1 & K-LOVE)",
])

with tab1:
  if not filtered_songs:
    st.warning("Nincs találat a szűrésre.")
  else:
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

    c_head1, c_head2, c_head3 = st.columns((3, 1, 1))
    with c_head1:
      st.subheader(song["title"])
      st.markdown(
          f"**Előadó:** {song['artist']} | **Stílus:** {song['origin']}"
      )
    with c_head2:
      st.metric("Hangnem", song["key"])
    with c_head3:
      st.metric("Tempó", f"{song['bpm']} BPM")

    st.info(
        "**Tematika:** " + " • ".join([f"🏷️ {t}" for t in song["themes"]])
    )
    col1, col2 = st.columns((1.3, 1))

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
          )

        sheet_url = song.get("sheet_music_url", "").strip()
        if sheet_url:
          st.link_button(
              "🎼 Kotta megnyitása", sheet_url, use_container_width=True
          )
        else:
          st.link_button(
              "🎼 Kotta / Akkord keresése",
              build_google_search_url(f"{search_str} chords lyrics"),
              use_container_width=True,
          )

      st.markdown("### 📋 Koncertanyag")
      if any(item["id"] == song["id"] for item in st.session_state.setlist):
        st.success("✅ Már benne van a koncertanyagban!")
      elif st.button(
          "➕ Hozzáadás a koncertanyaghoz",
          key=f"add_{song['id']}",
          use_container_width=True,
          type="primary",
      ):
        st.session_state.setlist.append(song)
        st.rerun()

with tab2:
  st.subheader("Összeállított dallista")
  if not st.session_state.setlist:
    st.info("Még üres a koncertanyagod.")
  else:
    export_lines = ["KONCERTANYAG / DICSŐÍTŐ SETLIST\n" + "=" * 35 + "\n"]
    for idx, item in enumerate(st.session_state.setlist):
      c1, c2, c3, c4 = st.columns((3, 2, 0.5, 0.5))
      with c1:
        st.markdown(
            f"**{idx + 1}. {item['title']}** ({item['artist']}) –"
            f" *{item['key']}*"
        )
      with c2:
        note = st.text_input(
            "Megjegyzés",
            key=f"note_{item['id']}",
            placeholder="pl. Átkötés, ima...",
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
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
      st.download_button(
          "📥 Koncertanyag letöltése (.txt)",
          "\n".join(export_lines),
          "koncertanyag_setlist.txt",
          "text/plain",
          type="primary",
      )
    with col_exp2:
      if st.button("🧹 Teljes lista törlése"):
        st.session_state.setlist = []
        st.rerun()
with tab3:
  st.subheader("📻 Élő Amerikai Keresztény Rádiós & Toplista Adatok")
  if st.button("🔄 Adatok frissítése most"):
    st.cache_data.clear()
    st.rerun()

  radio_data = fetch_us_christian_radio_data()
  source_options = {}
  if radio_data["air1"]:
    source_options[
        f"🎵 Air1 Worship Now – Adáslista ({len(radio_data['air1'])} dal)"
    ] = radio_data["air1"]
  if radio_data["klove"]:
    source_options[
        f"❤️ K-LOVE Radio – Adáslista ({len(radio_data['klove'])} dal)"
    ] = radio_data["klove"]
  if radio_data["itunes"]:
    source_options[
        f"🏆 USA Christian & Gospel Top 50 ({len(radio_data['itunes'])} dal)"
    ] = radio_data["itunes"]

  if not source_options:
    st.warning("A külső rádiós szerverek most nem válaszoltak.")
  else:
    selected_source = st.selectbox(
        "Válassz élő adatforrást:", list(source_options.keys())
    )
    active_list = source_options[selected_source]
    parsed_items, artist_counts = [], Counter()
    for row in active_list:
      if " - " in row:
        art, tit = [x.strip() for x in row.split(" - ", 1)]
        artist_counts[art] += 1
        parsed_items.append((art, tit))

    top_artists = [f"{a} ({c})" for a, c in artist_counts.most_common()]
    sel_art = st.selectbox(
        "Szűrés zenekarra:", ["Összes zenekar"] + top_artists
    )
    if sel_art != "Összes zenekar":
      target = sel_art.rsplit(" (", 1)
      display_items = [x for x in parsed_items if x == target]
    else:
      display_items = parsed_items

    st.divider()
    d_col1, d_col2 = st.columns((1.5, 1))
    with d_col1:
      st.markdown(f"#### 🎶 Dalok ({len(display_items)} találat)")
      for (art, tit), cnt in Counter(display_items).most_common(40):
        norm_t = normalize_match(tit)
        matched = next(
            (
                s_db
                for s_db in songs
                if any(
                    w in normalize_match(s_db["title"])
                    for w in norm_t.split()
                    if len(w) > 3
                )
            ),
            None,
        )
        with st.container(border=True):
          m1, m2 = st.columns((3, 1.2))
          with m1:
            st.markdown(
                f"**{art} – {tit}**" + (f" *({cnt}x)*" if cnt > 1 else "")
            )
            if matched:
              st.caption(
                  f"✅ Megvan (#{matched['id']}) | 🎵 {matched['key']} | 🏷️"
                  f" {', '.join(matched['themes'])}"
              )
            else:
              st.caption("🆕 Új dal")
          with m2:
            st.link_button(
                "▶️ YouTube",
                build_yt_search_url(f"{art} {tit}"),
                use_container_width=True,
            )

    with d_col2:
      st.markdown("#### 🎸 Zenekarok rangsora")
      for art_name, cnt in artist_counts.most_common(20):
        st.markdown(f"- **{art_name}**: {cnt}")

  st.divider()
  st.markdown(f"### 📈 Saját Repertoár Statisztika ({len(songs)} dal)")
  sc1, sc2 = st.columns(2)
  with sc1:
    for a, c in Counter(s["artist"] for s in songs).most_common(15):
      st.markdown(f"- **{a}**: {c} dal")
  with sc2:
    for t, c in Counter(t for s in songs for t in s["themes"]).most_common(15):
      st.markdown(f"- **🏷️ {t}**: {c} dal")

