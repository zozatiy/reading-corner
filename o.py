import sqlite3, json, random, datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Reading Corner", page_icon="📚", layout="wide")
DB = "books_en.db"
from books_data import BOOKS
from ar_books1 import AR1
from ar_books2 import AR2
from ui_text import GENRE_AR, LEVEL_AR, STATUS_AR, T

AR = {**AR1, **AR2}

ar_mode = True  # set below from the sidebar


def t(k):
    return T[k][0 if ar_mode else 1]


def G(x):
    return GENRE_AR.get(x, x) if ar_mode else x


def L(x):
    return LEVEL_AR.get(x, x) if ar_mode else x


def S(x):
    return STATUS_AR.get(x, x) if ar_mode else x


def btitle(b):
    return b["title_ar"] if ar_mode and b["title_ar"] else b["title"]


def bsyn(b):
    return b["synopsis_ar"] if ar_mode and b["synopsis_ar"] else b["synopsis"]


# ---------- database ----------
def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def run(sql, args=(), fetch=True):
    c = conn()
    cur = c.execute(sql, args)
    rows = cur.fetchall() if fetch else None
    c.commit()
    c.close()
    return rows


def init_db():
    c = conn()
    c.execute("""CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY, title TEXT UNIQUE, author TEXT, genre TEXT,
        level TEXT, min_age INTEGER, isbn TEXT, synopsis TEXT)""")
    for col in ("title_ar", "synopsis_ar"):  # upgrade older databases
        try:
            c.execute(f"ALTER TABLE books ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    c.execute("""CREATE TABLE IF NOT EXISTS shelf(
        reader TEXT, book_id INTEGER, status TEXT, rating INTEGER, review TEXT,
        UNIQUE(reader, book_id))""")
    c.executemany(
        "INSERT OR IGNORE INTO books(title,author,genre,level,min_age,isbn,synopsis) VALUES(?,?,?,?,?,?,?)", BOOKS)
    for en, (tar, sar) in AR.items():
        c.execute("UPDATE books SET title_ar=?, synopsis_ar=? WHERE title=?", (tar, sar, en))
    c.commit()
    c.close()


def cover(isbn):
    return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"


def speak_widget(text, rate, lang_code):
    components.html(f"""
    <div style="text-align:center">
    <button id="p" style="background:#8B5E3C;color:#FFF8E7;border:none;border-radius:8px;padding:10px 20px;font-size:16px">{t('listen')}</button>
    <button id="s" style="background:#B8893B;color:#fff;border:none;border-radius:8px;padding:10px 20px;font-size:16px;margin:0 8px">{t('stop')}</button>
    </div>
    <script>
    const txt = {json.dumps(text)};
    document.getElementById('p').onclick = () => {{
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(txt);
      u.lang = '{lang_code}'; u.rate = {rate}; u.pitch = 1.05;
      speechSynthesis.speak(u);
    }};
    document.getElementById('s').onclick = () => speechSynthesis.cancel();
    </script>""", height=70)


def card(key):
    try:
        return st.container(key=key)
    except TypeError:  # very old Streamlit
        return st.container(border=True)


def show(rows, prefix):
    if not rows:
        st.info(t("none"))
        return
    for start in range(0, len(rows), 4):
        cols = st.columns(4)
        for j, b in enumerate(rows[start:start + 4]):
            with cols[j]:
                with card(f"card_{prefix}{b['id']}"):
                    st.image(cover(b["isbn"]), use_container_width=True)
                    st.markdown(f"**{btitle(b)}**  \n*{b['author']}*")
                    st.caption(f"{G(b['genre'])} · {L(b['level'])} · {t('age')} {b['min_age']}+")
                    with st.expander(t("synopsis")):
                        st.write(bsyn(b))
                    if st.button(t("add_shelf"), key=f"{prefix}{b['id']}"):
                        run("INSERT OR IGNORE INTO shelf VALUES(?,?,?,?,?)",
                            (reader, b["id"], "Want to read", None, ""), fetch=False)
                        st.toast(f"{t('added')}: {btitle(b)}")
        st.markdown('<div class="plank"></div>', unsafe_allow_html=True)


init_db()

# ---------- language + sidebar ----------
lang = st.sidebar.radio("Language / اللغة", ["العربية", "English"], horizontal=True)
ar_mode = lang == "العربية"
reader = st.sidebar.text_input(t("name"), t("guest")).strip() or t("guest")
st.sidebar.caption(t("name_hint"))

# ---------- style ----------
direction = "rtl" if ar_mode else "ltr"
SPINE_COLORS = ["#7B2D26", "#2F4F4F", "#B8893B", "#4B3621", "#1F3A5F",
                "#6B4E71", "#8B5E3C", "#355E3B", "#9C4A1A", "#3B2F63"]
spines = "".join(
    f'<span style="height:{30 + (i * 7) % 22}px;width:{14 + (i * 5) % 12}px;'
    f'background:linear-gradient(90deg,rgba(0,0,0,.28),{SPINE_COLORS[i % 10]} 30%,'
    f'{SPINE_COLORS[i % 10]} 70%,rgba(0,0,0,.32))"></span>' for i in range(36))

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Playfair+Display:wght@500;700&display=swap');
.stApp {
  background-color:#EAD9B5;
  background-image:
    radial-gradient(ellipse at top, rgba(255,247,222,.95), rgba(210,183,135,.55)),
    repeating-linear-gradient(0deg, rgba(110,75,40,.05) 0 2px, transparent 2px 5px);
  color:#3E2A1C; direction:__DIR__;
}
.stApp p, .stApp label, .stMarkdown, .stCaption, h1, h2, h3, h4, button, input, textarea,
[data-baseweb="tab"] {font-family:'Amiri','Playfair Display',Georgia,serif !important;}
.stApp p, .stApp label {font-size:1.12rem;}
h2, h3 {color:#4A2C17; border-bottom:2px solid #CDB27A; padding-bottom:4px;
        font-family:'Playfair Display','Amiri',Georgia,serif !important;}
.hero {background:linear-gradient(180deg,#4A2C17,#2E1A0D); border:3px solid #B8893B; border-radius:8px;
  box-shadow:0 8px 20px rgba(40,20,5,.5), inset 0 0 0 5px #2E1A0D, inset 0 0 0 6px #B8893B;
  text-align:center; padding:26px 10px 18px; margin:0 0 4px;}
.hero h1 {color:#F1D58A; letter-spacing:2px; margin:0; font-size:2.7rem; border:none;
  font-family:'Playfair Display','Amiri',Georgia,serif !important; text-shadow:0 2px 0 #1B0F06;}
.hero p {color:#E9D9B0; margin:6px 0 0; font-style:italic; font-size:1.2rem;}
.orn {color:#B8893B; letter-spacing:12px; font-size:1.1rem;}
.spines {display:flex; align-items:flex-end; justify-content:center; gap:2px; margin-top:14px;}
.spines span {border-radius:2px 2px 0 0; display:inline-block; border-top:2px solid rgba(255,220,150,.45);}
.plank {height:16px; background:linear-gradient(180deg,#A06F3C,#6B4423 60%,#4B2E16); border-radius:3px;
  box-shadow:0 9px 12px rgba(40,20,5,.40); margin:2px 0 28px;}
[class*="st-key-card_"] {background:linear-gradient(180deg,#FFF9E8,#F5E7C2); border:1px solid #CDB27A;
  border-left:10px solid #6B3E21; border-radius:4px 10px 10px 4px; box-shadow:3px 6px 12px rgba(60,35,10,.32);
  padding:12px 12px 8px; margin-bottom:6px;}
[class*="st-key-card_"] img {border-radius:3px; box-shadow:0 4px 9px rgba(0,0,0,.40);}
.stTabs [data-baseweb="tab-list"] {gap:5px; border-bottom:3px solid #6B3E21; flex-wrap:wrap;}
.stTabs [data-baseweb="tab"] {background:#E0CC9C; border:1px solid #B79B63; border-bottom:none;
  border-radius:9px 9px 0 0; padding:8px 14px; height:auto;}
.stTabs [data-baseweb="tab"] p {color:#4A2C17; font-size:1.15rem; margin:0;}
.stTabs [aria-selected="true"] {background:#5B3A29;}
.stTabs [aria-selected="true"] p {color:#F1D58A;}
.stTabs [data-baseweb="tab-highlight"] {background:#B8893B;}
.stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"]>button {
  background:linear-gradient(180deg,#8B5E3C,#5B3A29); border:1px solid #B8893B; border-radius:6px;}
.stButton>button p, .stDownloadButton>button p, [data-testid="stFormSubmitButton"]>button p {color:#F7E7B6;}
.stButton>button:hover, .stDownloadButton>button:hover {background:#B8893B; border-color:#5B3A29;}
[data-testid="stExpander"] {background:#FFF6DC; border:1px solid #CDB27A; border-radius:6px;}
[data-testid="stMetric"] {background:#FFF6DC; border:1px solid #CDB27A; border-radius:8px; padding:10px 14px;}
[data-baseweb="input"], [data-baseweb="select"]>div, [data-baseweb="textarea"] {
  background:#FFF9E8 !important; border-color:#C9AE78 !important;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#4A2C17,#2E1A0D); border-right:3px solid #B8893B;}
[data-testid="stSidebar"] label p, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] .stMarkdown p {color:#F1E3BE !important;}
</style>
<div class="hero">
  <div class="orn">❦ ❦ ❦</div>
  <h1>📚 __APP__</h1>
  <p>__TAG__</p>
  <div class="spines">__SPINES__</div>
</div>
<div class="plank"></div>
"""
st.markdown(STYLE.replace("__DIR__", direction).replace("__APP__", t("app"))
            .replace("__TAG__", t("tagline")).replace("__SPINES__", spines), unsafe_allow_html=True)

tabs = st.tabs([t(k) for k in ("tab_home", "tab_search", "tab_foryou", "tab_genre",
                               "tab_shelf", "tab_listen", "tab_stats", "tab_add")])
LEVELS = ["Beginner", "Intermediate", "Advanced"]
STATUSES = ["Want to read", "Reading", "Finished"]
genres = [r[0] for r in run("SELECT DISTINCT genre FROM books ORDER BY genre")]

# ---------- Home ----------
with tabs[0]:
    all_books = run("SELECT * FROM books ORDER BY id")
    botd = all_books[datetime.date.today().toordinal() % len(all_books)]
    st.subheader(t("botd"))
    with card("card_botd"):
        c1, c2 = st.columns([1, 3])
        c1.image(cover(botd["isbn"]), use_container_width=True)
        c2.markdown(f"### {btitle(botd)}\n*{botd['author']}* · {G(botd['genre'])} · {L(botd['level'])}")
        c2.write(bsyn(botd))
    st.markdown('<div class="plank"></div>', unsafe_allow_html=True)

    st.subheader(t("surprise"))
    if st.button(t("surprise_btn")):
        st.session_state["surprise"] = random.choice(all_books)["id"]
    if "surprise" in st.session_state:
        show(run("SELECT * FROM books WHERE id=?", (st.session_state["surprise"],)), "sur")

    st.subheader(t("top"))
    top = run("""SELECT b.*, AVG(s.rating) AS avg_r, COUNT(s.rating) AS n FROM books b
                 JOIN shelf s ON s.book_id=b.id WHERE s.rating IS NOT NULL
                 GROUP BY b.id ORDER BY avg_r DESC, n DESC LIMIT 4""")
    if top:
        show(top, "top")
    else:
        st.caption(t("no_ratings"))

# ---------- Search ----------
with tabs[1]:
    q = st.text_input(t("search_ph"))
    f1, f2, f3 = st.columns(3)
    g = f1.multiselect(t("f_genre"), genres, format_func=G)
    lv = f2.multiselect(t("f_level"), LEVELS, format_func=L)
    sort_opts = {"title": t("s_title"), "author": t("s_author"), "age": t("s_age"), "level": t("s_level")}
    order = f3.selectbox(t("sort"), list(sort_opts), format_func=lambda k: sort_opts[k])
    like = f"%{q}%"
    ar_genre_hits = [k for k, v in GENRE_AR.items() if q and q in v]
    sql = "SELECT * FROM books WHERE (title LIKE ? OR author LIKE ? OR genre LIKE ? OR title_ar LIKE ?"
    args = [like, like, like, like]
    if ar_genre_hits:
        sql += f" OR genre IN ({','.join('?' * len(ar_genre_hits))})"
        args += ar_genre_hits
    sql += ")"
    if g:
        sql += f" AND genre IN ({','.join('?' * len(g))})"
        args += g
    if lv:
        sql += f" AND level IN ({','.join('?' * len(lv))})"
        args += lv
    sql += {"title": " ORDER BY title", "author": " ORDER BY author",
            "age": " ORDER BY min_age, title",
            "level": " ORDER BY CASE level WHEN 'Beginner' THEN 1 WHEN 'Intermediate' THEN 2 ELSE 3 END, title"}[order]
    res = run(sql, args)
    st.caption(f"{t('found')} {len(res)}")
    show(res, "s")
    if res:
        df = pd.DataFrame([dict(r) for r in res])[["title", "title_ar", "author", "genre", "level", "min_age"]]
        st.download_button(t("export"), df.to_csv(index=False).encode("utf-8-sig"), "books.csv", "text/csv")

# ---------- For You ----------
with tabs[2]:
    c1, c2 = st.columns(2)
    age = c1.number_input(t("your_age"), 5, 100, 14)
    level = c2.selectbox(t("your_level"), LEVELS, format_func=L)
    with st.expander(t("unsure")):
        st.write(t("level_help"))
    show(run("SELECT * FROM books WHERE min_age<=? AND level=? ORDER BY title", (age, level)), "fy")

# ---------- By Genre ----------
with tabs[3]:
    picked = st.multiselect(t("pick_genres"), genres, format_func=G, key="gpick")
    if picked:
        marks = ",".join("?" * len(picked))
        show(run(f"SELECT * FROM books WHERE genre IN ({marks}) ORDER BY genre, title", picked), "g")
    else:
        st.info(t("pick_one"))

# ---------- My Shelf ----------
with tabs[4]:
    st.subheader(f"{t('shelf_of')} {reader}")
    rows = run("""SELECT b.*, s.status, s.rating, s.review FROM shelf s
                  JOIN books b ON b.id=s.book_id WHERE s.reader=? ORDER BY b.title""", (reader,))
    if not rows:
        st.info(t("empty_shelf"))
    else:
        done = sum(1 for r in rows if r["status"] == "Finished")
        st.progress(done / len(rows), text=t("progress").format(d=done, n=len(rows)))
        for r in rows:
            with card(f"card_shelf{r['id']}"):
                a, b_ = st.columns([1, 4])
                a.image(cover(r["isbn"]), use_container_width=True)
                with b_:
                    st.markdown(f"**{btitle(r)}** — *{r['author']}*")
                    status = st.selectbox(t("status"), STATUSES, index=STATUSES.index(r["status"]),
                                          format_func=S, key=f"st{r['id']}")
                    rating = st.slider(t("rating"), 1, 5, r["rating"] or 3, key=f"rt{r['id']}")
                    review = st.text_area(t("review"), r["review"] or "", key=f"rv{r['id']}")
                    k1, k2 = st.columns(2)
                    if k1.button(t("save"), key=f"sv{r['id']}"):
                        run("UPDATE shelf SET status=?, rating=?, review=? WHERE reader=? AND book_id=?",
                            (status, rating, review, reader, r["id"]), fetch=False)
                        st.toast(t("saved"))
                    if k2.button(t("remove"), key=f"rm{r['id']}"):
                        run("DELETE FROM shelf WHERE reader=? AND book_id=?", (reader, r["id"]), fetch=False)
                        st.rerun()
        liked = [r["genre"] for r in rows if (r["rating"] or 0) >= 4]
        if liked:
            fav = max(set(liked), key=liked.count)
            st.subheader(f"{t('because')} {G(fav)}")
            show(run("""SELECT * FROM books WHERE genre=? AND id NOT IN
                        (SELECT book_id FROM shelf WHERE reader=?) LIMIT 4""", (fav, reader)), "rec")

# ---------- Listen ----------
with tabs[5]:
    rows = run("SELECT * FROM books ORDER BY title")
    by_id = {r["id"]: r for r in rows}
    bid = st.selectbox(t("choose_book"), list(by_id), format_func=lambda i: btitle(by_id[i]))
    b = by_id[bid]
    c1, c2 = st.columns([1, 3])
    c1.image(cover(b["isbn"]), use_container_width=True)
    with c2:
        st.markdown(f"**{btitle(b)}** — *{b['author']}*")
        st.write(bsyn(b))
        rate = st.slider(t("speed"), 0.6, 1.3, 0.9, 0.1)
        if ar_mode:
            speak_widget(f"{btitle(b)}. {bsyn(b)}", rate, "ar-SA")
        else:
            speak_widget(f"{b['title']}, by {b['author']}. {b['synopsis']}", rate, "en-US")

# ---------- Stats ----------
with tabs[6]:
    df = pd.DataFrame([dict(r) for r in run("SELECT * FROM books")])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(t("m_books"), len(df))
    m2.metric(t("m_authors"), df["author"].nunique())
    m3.metric(t("m_genres"), df["genre"].nunique())
    m4.metric(t("m_shelves"), run("SELECT COUNT(*) FROM shelf")[0][0])
    st.subheader(t("c_genre"))
    gc = df["genre"].value_counts()
    gc.index = [G(x) for x in gc.index]
    st.bar_chart(gc)
    st.subheader(t("c_level"))
    lc = df["level"].value_counts().reindex(LEVELS)
    lc.index = [L(x) for x in lc.index]
    st.bar_chart(lc)
    st.subheader(t("c_status"))
    stt = pd.DataFrame([dict(r) for r in run("SELECT status, COUNT(*) AS n FROM shelf GROUP BY status")])
    if not stt.empty:
        stt["status"] = stt["status"].map(S)
        st.bar_chart(stt.set_index("status"))
    else:
        st.caption(t("no_shelf"))

# ---------- Add Book ----------
with tabs[7]:
    st.subheader(t("add_title"))
    with st.form("add"):
        nt = st.text_input(t("f_title"))
        na = st.text_input(t("f_author"))
        ng = st.text_input(t("f_genre2"))
        c1, c2 = st.columns(2)
        nl = c1.selectbox(t("your_level"), LEVELS, format_func=L)
        nage = c2.number_input(t("s_age"), 5, 100, 12)
        nisbn = st.text_input(t("f_isbn"))
        nsyn = st.text_area(t("f_syn"))
        if st.form_submit_button(t("f_btn")):
            if nt and na and ng and nsyn:
                run("INSERT OR IGNORE INTO books(title,author,genre,level,min_age,isbn,synopsis) VALUES(?,?,?,?,?,?,?)",
                    (nt, na, ng, nl, nage, nisbn.strip(), nsyn), fetch=False)
                st.success(t("f_ok"))
            else:
                st.warning(t("f_warn"))
