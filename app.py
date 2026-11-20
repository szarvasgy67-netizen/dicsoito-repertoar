from collections import Counter
import json
import unicodedata
import urllib.parse
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
  return " ".join(ascii_text.split())


def normalize_match(text):
  nfkd = unicodedata.normalize("NFKD", str(text).lower())
  return "".join([c for c in nfkd if c.isalnum() or c == " "]).strip()


def build_yt_search_url(query_text):
  q = urllib.parse.urlencode({"search_query": clean_query(query_text)})
  return "https://youtube.com?" + q


def build_google_search_url(query_text):
  q = urllib.parse.urlencode({"q": clean_query(query_text)})
  return "https://google.com?" + q


songs = load_songs()
if "setlist" not in st.session_state:
  st.session_state.setlist = []

st.sidebar.header("🔍 Dal keresése és szűrése")
search_query = st.sidebar.text_input(
    "Keresés címre, előadóra vagy szövegre:",
    placeholder="pl. Óceánok, Hillsong, kegyelem...",
)

all_artists = sorted(list({song["artist"] for song in songs}))
selected_artists = st.sidebar.multiselect("Előadó:", options=all_artists)

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
  if selected_artists and song["artist"] not in selected_artists:
    continue
  if selected_themes and not all(t in song["themes"] for t in selected_themes):
    continue
  if selected_origin and song["origin"] not in selected_origin:
    continue
  if selected_key and song["key"] not in selected_key:
    continue
  filtered_songs.append(song)

st.title("🎸 Dicsőítő Repertoár & Setlist Tervező")
if (
    search_query
    or selected_artists
    or selected_themes
    or selected_origin
    or selected_key
):
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
        raw_yt = song.get("youtube_url", "").strip()
        is_valid_video = "watch?v=" in raw_yt or "youtu.be/" in raw_yt

        if is_valid_video:
          st.video(raw_yt)
          st.link_button(
              "▶️ Megnyitás YouTube-on", raw_yt, use_container_width=True
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

        raw_sheet = song.get("sheet_music_url", "").strip()
        if raw_sheet.startswith("http"):
          st.link_button(
              "🎼 Kotta megnyitása", raw_sheet, use_container_width=True
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
      raw_item_yt = item.get("youtube_url", "").strip()
      yt_link = (
          raw_item_yt
          if ("watch?v=" in raw_item_yt or "youtu.be/" in raw_item_yt)
          else build_yt_search_url(f"{item['title']} {item['artist']}")
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
  st.subheader("📻 Amerikai Rádiós Toplisták & Lista Elemző")
  st.caption(
      "Azonnal elérhető amerikai keresztény rádiós (Air1 / K-LOVE) slágerek"
      " és saját lista-elemző – külső szerverhiba nélkül!"
  )

  preset_radio_list = "\n".join([
      "Elevation Worship - Praise",
      "Brandon Lake - Gratitude",
      "Phil Wickham - Living Hope",
      "Hillsong Worship - What A Beautiful Name",
      "Bethel Music - Goodness of God",
      "Sinach - Way Maker",
      "Kari Jobe - The Blessing",
      "Elevation Worship - Graves Into Gardens",
      "Cory Asbury - Reckless Love",
      "Hillsong United - Oceans",
      "Lauren Daigle - You Say",
      "Maverick City Music - Promises",
      "Elevation Worship - O Come to the Altar",
      "Pat Barrett - Build My Life",
      "Phil Wickham - Battle Belongs",
      "Chris Tomlin - Good Good Father",
      "Matt Redman - 10,000 Reasons",
      "Hillsong Worship - King of Kings",
      "Bethel Music - Raise A Hallelujah",
      "Casting Crowns - Only Jesus",
      "Hillsong Worship - Who You Say I Am",
      "Elevation Worship - Do It Again",
      "Bethel Music - No Longer Slaves",
      "Chris Tomlin - How Great Is Our God",
      "All Sons & Daughters - Great Are You Lord",
      "Elevation Worship - Worthy",
      "Phil Wickham - This Is Amazing Grace",
      "Hillsong United - Another In The Fire",
      "Cody Carnes - Christ Be Magnified",
      "Matt Maher - Lord I Need You",
  ])

  if "radio_input" not in st.session_state:
    st.session_state.radio_input = preset_radio_list

  b_col1, b_col2 = st.columns(2)
  with b_col1:
    if st.button(
        "🎵 Air1 / K-LOVE Top 30 betöltése", use_container_width=True
    ):
      st.session_state.radio_input = preset_radio_list
      st.rerun()
  with b_col2:
    if st.button("🧹 Szövegmező törlése", use_container_width=True):
      st.session_state.radio_input = ""
      st.rerun()

  st.info(
      "💡 **Használat:** Keress rá a neten egy friss dicsőítő toplistára,"
      " töröld ki a lenti dobozt, és másold be a dalokat **Előadó - Dal címe**"
      " formátumban (kötőjellel elválasztva). Utána nyomj **Ctrl+Enter**-t"
      " (vagy kattints a dobozon kívülre), és a program azonnal elemzi és"
      " megkeresi őket YouTube-on!"
  )

  user_list = st.text_area(
      "Elemezhető dallista (bármilyen listát bemásolhatsz 'Előadó - Dal címe'"
      " formátumban):",
      key="radio_input",
      height=160,
  )

  if user_list.strip():
    parsed_items, artist_counts = [], Counter()
    for line in user_list.splitlines():
      line = line.strip()
      sep = " - " if " - " in line else (" – " if " – " in line else None)
      if sep:
        parts = line.split(sep, 1)
        art, tit = parts.strip(), parts.strip()
        artist_counts[art] += 1
        parsed_items.append((art, tit))

    top_artists = [f"{a} ({c})" for a, c in artist_counts.most_common()]
    sel_art = st.selectbox(
        "Szűrés zenekarra a listában:", ["Összes zenekar"] + top_artists
    )
    if sel_art != "Összes zenekar":
      target = sel_art.rsplit(" (", 1)
      display_items = [x for x in parsed_items if x == target]
    else:
      display_items = parsed_items

    st.divider()
    d_col1, d_col2 = st.columns((1.5, 1))
    with d_col1:
      st.markdown(f"#### 🎶 Dalok a listában ({len(display_items)} találat)")
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
        st.markdown(f"- **{art_name}**: {cnt} dal")

  st.divider()
  st.markdown(f"### 📈 Saját Repertoár Statisztika ({len(songs)} dal)")
  sc1, sc2 = st.columns(2)
  with sc1:
    for a, c in Counter(s["artist"] for s in songs).most_common(15):
      st.markdown(f"- **{a}**: {c} dal")
  with sc2:
    for t, c in Counter(t for s in songs for t in s["themes"]).most_common(15):
      st.markdown(f"- **🏷️ {t}**: {c} dal")
