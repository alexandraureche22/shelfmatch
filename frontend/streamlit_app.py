import os
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="ShelfMatch", page_icon="☕", layout="wide")

# Local: rămâne localhost. Pe Streamlit Cloud: setezi API_URL în Settings → Secrets.
try:
    API_URL = st.secrets["API_URL"]
except Exception:
    API_URL = os.getenv("API_URL", "http://localhost:8000")

# ---------- Temă custom (paletă cafea/piele, variantă deschisă și cozy) ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');

:root {
    --cream: #FAF5EE;
    --card: #FFFFFF;
    --camel: #C6B39A;
    --boho: #7D694E;
    --rubine: #8C5A5C;
    --text-dark: #3E2E26;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: var(--cream);
    color: var(--text-dark);
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--text-dark) !important;
}

p, span, label, .stMarkdown, .stCaption {
    color: var(--text-dark) !important;
}

/* Tab-uri */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    border-bottom: 1px solid var(--camel);
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    color: var(--boho);
    font-weight: 600;
    padding: 10px 22px;
    border-radius: 10px 10px 0 0;
}
.stTabs [aria-selected="true"] {
    background-color: var(--camel) !important;
    color: var(--text-dark) !important;
}

/* Butoane */
.stButton > button, .stFormSubmitButton > button {
    background-color: var(--boho);
    color: var(--cream) !important;
    border: none;
    border-radius: 8px;
    padding: 0.55em 1.6em;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background-color: var(--rubine);
    color: var(--cream) !important;
}

/* Input-uri */
.stTextInput input, .stDateInput input {
    background-color: var(--card) !important;
    color: var(--text-dark) !important;
    border: 1px solid var(--camel) !important;
    border-radius: 8px;
}
.stSelectbox div[data-baseweb="select"] > div {
    background-color: var(--card) !important;
    border: 1px solid var(--camel) !important;
    border-radius: 8px;
    color: var(--text-dark) !important;
}

/* Carduri (containere cu border) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: var(--card);
    border: 1px solid #EDE2D3;
    border-radius: 14px;
    padding: 8px;
    box-shadow: 0 2px 8px rgba(125, 105, 78, 0.08);
}

/* Tabel */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

st.title("☕ ShelfMatch")


def api_get(path, **kwargs):
    """GET sigur către backend: arată eroarea clar în loc să crape aplicația."""
    try:
        resp = requests.get(f"{API_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError:
        try:
            detail = resp.json().get("detail", "Eroare la server.")
        except Exception:
            detail = "Eroare la server."
        st.error(detail)
        return None
    except requests.exceptions.RequestException:
        st.error(f"Nu pot contacta backend-ul la {API_URL}. Rulează `uvicorn`?")
        return None

tab_library, tab_recommend, tab_dashboard = st.tabs(["Bibliotecă", "Recomandări", "Dashboard"])

# ---------- TAB: Bibliotecă ----------
with tab_library:
    st.subheader("Caută și adaugă o carte")
    query = st.text_input("Titlu sau autor")

    if query:
        results = api_get("/books/search", params={"q": query})
        if results:
            for book in results:
                with st.container(border=True):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if book.get("cover_url"):
                            st.image(book["cover_url"], width=80)
                    with col2:
                        st.write(f"**{book['title']}** — {book.get('author', 'necunoscut')}")
                        st.caption(f"{book.get('genre', 'gen necunoscut')} · {book.get('pages', '?')} pagini")

                        with st.form(key=f"log_{book['google_books_id']}"):
                            status = st.selectbox("Status", ["wishlist", "reading", "finished"], key=f"status_{book['google_books_id']}")
                            rating = st.slider("Rating", 1, 5, 3, key=f"rating_{book['google_books_id']}")
                            date_started = st.date_input("Dată început", value=None, key=f"start_{book['google_books_id']}")
                            date_finished = st.date_input("Dată sfârșit", value=None, key=f"end_{book['google_books_id']}")
                            submitted = st.form_submit_button("Adaugă în bibliotecă")

                            if submitted:
                                book_resp = requests.post(f"{API_URL}/books/", json=book).json()
                                entry = {
                                    "book_id": book_resp["id"],
                                    "rating": rating if status == "finished" else None,
                                    "date_started": str(date_started) if date_started else None,
                                    "date_finished": str(date_finished) if date_finished else None,
                                    "status": status,
                                }
                                requests.post(f"{API_URL}/books/log", json=entry)
                                st.success(f"'{book['title']}' adăugată!")
        elif results == []:
            st.info("Niciun rezultat găsit.")

    st.divider()
    st.subheader("Cărțile tale")
    my_books = api_get("/books/mine")
    if my_books:
        df = pd.json_normalize(my_books)
        st.dataframe(df[["book.title", "book.author", "book.genre", "status", "rating", "date_started", "date_finished"]])
    else:
        st.info("Nu ai încă nicio carte adăugată.")

# ---------- TAB: Recomandări ----------
with tab_recommend:
    st.subheader("Ce ar trebui să citești în continuare")
    if st.button("Generează recomandări"):
        recs = api_get("/recommendations/")
        if recs is not None and not recs:
            st.warning("Adaugă cel puțin câteva cărți citite (cu rating) ca să pot genera recomandări.")
        for r in (recs or []):
            with st.container(border=True):
                col1, col2 = st.columns([1, 4])
                with col1:
                    if r.get("cover_url"):
                        st.image(r["cover_url"], width=80)
                with col2:
                    st.write(f"**{r['title']}** — {r.get('author', 'necunoscut')}")
                    st.caption(f"{r.get('genre', '')} · {r.get('pages', '?')} pagini")
                    if r.get("estimated_days_to_read"):
                        st.write(f"⏱️ Estimare: ~{r['estimated_days_to_read']} zile la ritmul tău")

# ---------- TAB: Dashboard ----------
with tab_dashboard:
    st.subheader("Statistici pe genuri")
    stats = api_get("/stats/genres")
    if stats:
        df = pd.DataFrame(stats)
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(df, x="genre", y="avg_pages_per_day", title="Ritm mediu (pagini/zi) pe gen",
                          color_discrete_sequence=["#7D694E"])
            fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                font_color="#3E2E26", title_font_color="#3E2E26")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(df, x="genre", y="avg_rating", title="Rating mediu pe gen",
                          color_discrete_sequence=["#8C5A5C"])
            fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                font_color="#3E2E26", title_font_color="#3E2E26")
            st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(df)
    else:
        st.info("Nu sunt încă suficiente date pentru statistici.")