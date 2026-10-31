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


def show(rows, prefix):
    if not rows:
        st.info(t("none"))
        return
    cols = st.columns(4)
    for i, b in enumerate(rows):
        with cols[i % 4]:
            st.image(cover(b["isbn"]), use_container_width=True)
            st.markdown(f"**{btitle(b)}**  \n*{b['author']}*")
            st.caption(f"{G(b['genre'])} · {L(b['level'])} · {t('age')} {b['min_age']}+")
            with st.expander(t("synopsis")):
                st.write(bsyn(b))
            if st.button(t("add_shelf"), key=f"{prefix}{b['id']}"):
                run("INSERT OR IGNORE INTO shelf VALUES(?,?,?,?,?)",
                    (reader, b["id"], "Want to read", None, ""), fetch=False)
                st.toast(f"{t('added')}: {btitle(b)}")


init_db()

# ---------- language + sidebar ----------
lang = st.sidebar.radio("Language / اللغة", ["العربية", "English"], horizontal=True)
ar_mode = lang == "العربية"
reader = st.sidebar.text_input(t("name"), t("guest")).strip() or t("guest")
st.sidebar.caption(t("name_hint"))

# ---------- style ----------
direction = "rtl" if ar_mode else "ltr"
st.markdown(f"""
<style>
.stApp {{background:#FBF5E6; color:#4A3426; direction:{direction};}}
h1,h2,h3 {{font-family:Georgia,'Times New Roman',serif; color:#5B3A29;}}
.hero {{text-align:center; padding:10px 0 0 0;}}
.line {{height:3px; background:linear-gradient(90deg,transparent,#B8893B,transparent); margin:6px auto 18px auto; width:60%;}}
.stTabs [data-baseweb="tab"] {{font-family:Georgia,serif; font-size:17px;}}
.stButton>button {{background:#8B5E3C; color:#FFF8E7; border:none; border-radius:8px;}}
.stButton>button:hover {{background:#B8893B; color:#fff;}}
[data-testid="stSidebar"] {{background:#F3E8CC;}}
</style>
<div class="hero"><h1>📚 {t('app')}</h1><p><i>{t('tagline')}</i></p></div>
<div class="line"></div>
""", unsafe_allow_html=True)

tabs = st.tabs([t(k) for k in ("tab_home", "tab_search", "tab_foryou", "tab_genre",
                               "tab_shelf", "tab_listen", "tab_stats", "tab_add", "tab_about")])
LEVELS = ["Beginner", "Intermediate", "Advanced"]
STATUSES = ["Want to read", "Reading", "Finished"]
genres = [r[0] for r in run("SELECT DISTINCT genre FROM books ORDER BY genre")]

# ---------- Home ----------
with tabs[0]:
    all_books = run("SELECT * FROM books ORDER BY id")
    botd = all_books[datetime.date.today().toordinal() % len(all_books)]
    st.subheader(t("botd"))
    c1, c2 = st.columns([1, 3])
    c1.image(cover(botd["isbn"]), use_container_width=True)
    c2.markdown(f"### {btitle(botd)}\n*{botd['author']}* · {G(botd['genre'])} · {L(botd['level'])}")
    c2.write(bsyn(botd))

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
            with st.container(border=True):
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

# ---------- About ----------
with tabs[8]:
    st.subheader(t("about_h"))
    if ar_mode:
        st.markdown("""
ركن القراءة موقع مكتبة مبني بلغة Python وإطار Streamlit مع قاعدة بيانات SQLite، ومنشور على Streamlit Community Cloud.

**مصادر البيانات**
- **بيانات الكتب** (العنوان، المؤلف، النوع، النبذة): كتبها صاحب المشروع من معرفته العامة بالكتب المشهورة، والنبذات ملخصات قصيرة بصياغة جديدة وليست منقولة من أي موقع.
- **المستوى والعمر الأدنى**: تقديرات من صاحب المشروع للاسترشاد فقط، وليست تصنيفا رسميا.
- **صور الأغلفة**: تُحمَّل مباشرة من [Open Library Covers API](https://openlibrary.org/dev/docs/api/covers) باستخدام رقم ISBN لكل كتاب.
- **الصوت**: تقنية تحويل النص إلى كلام (Web Speech API) المدمجة في المتصفح، ولا تُخزَّن أي ملفات صوتية.
- **الترجمة العربية**: العناوين والنبذات العربية مكتوبة ضمن المشروع.

**قاعدة البيانات**
- جدول `books`: id, title, title_ar, author, genre, level, min_age, isbn, synopsis, synopsis_ar
- جدول `shelf`: reader, book_id, status, rating, review

**الأدوات**: Python, Streamlit, SQLite, pandas, GitHub, Streamlit Cloud.
""")
    else:
        st.markdown("""
Reading Corner is a web library built with Python and Streamlit, with a SQLite database, deployed on Streamlit Community Cloud.

**Data sources**
- **Book records** (title, author, genre, synopsis): written by the project author from general knowledge of well-known books. Synopses are short original summaries, not copied from any website.
- **Reading level and minimum age**: estimated by the author, as a guide only (not an official rating).
- **Cover images**: loaded live from the [Open Library Covers API](https://openlibrary.org/dev/docs/api/covers) using each book's ISBN.
- **Audio**: the browser's built-in Web Speech API (text-to-speech). No audio files are stored.
- **Arabic translation**: Arabic titles and synopses are written inside the project.

**Database**
- `books` table: id, title, title_ar, author, genre, level, min_age, isbn, synopsis, synopsis_ar
- `shelf` table: reader, book_id, status, rating, review

**Tools**: Python, Streamlit, SQLite, pandas, GitHub, Streamlit Cloud.
""")
