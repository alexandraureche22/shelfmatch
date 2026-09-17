import os
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="ShelfMatch", page_icon="☕", layout="wide")

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

.stTextInput input, .stDateInput input, .stNumberInput input {
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

div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: var(--card);
    border: 1px solid #EDE2D3;
    border-radius: 14px;
    padding: 8px;
    box-shadow: 0 2px 8px rgba(125, 105, 78, 0.08);
}

[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"} if token else {}


@st.cache_data(ttl=15, show_spinner=False)
def _cached_get(path, token, params):
    """Rezultatul e ținut minte 15 secunde — request-uri identice nu mai lovesc backend-ul de fiecare dată."""
    headers = auth_headers(token)
    resp = requests.get(f"{API_URL}{path}", headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def api_get(path, **kwargs):
    """GET sigur către backend, cu token atașat automat și rezultat cache-uit."""
    token = st.session_state.get("token")
    params = kwargs.pop("params", None)
    try:
        return _cached_get(path, token, params)
    except requests.exceptions.HTTPError:
        try:
            resp = requests.get(f"{API_URL}{path}", headers=auth_headers(token), params=params)
            detail = resp.json().get("detail", "Server error.")
            status = resp.status_code
        except Exception:
            detail, status = "Server error.", None
        if status == 401:
            st.session_state.pop("token", None)
            st.session_state.pop("user_email", None)
        st.error(detail)
        return None
    except requests.exceptions.RequestException:
        st.error(f"Can't reach the backend at {API_URL}. Is `uvicorn` running?")
        return None


def api_send(method, path, json=None):
    """POST/PUT/DELETE sigur către backend. La succes, golește cache-ul de citire,
    ca datele afișate să fie mereu la zi imediat după o modificare."""
    token = st.session_state.get("token")
    try:
        resp = requests.request(method, f"{API_URL}{path}", json=json, headers=auth_headers(token))
        resp.raise_for_status()
        _cached_get.clear()
        return resp.json() if resp.content else {}
    except requests.exceptions.HTTPError:
        try:
            detail = resp.json().get("detail", "Server error.")
        except Exception:
            detail = "Server error."
        st.error(detail)
        return None
    except requests.exceptions.RequestException:
        st.error(f"Can't reach the backend at {API_URL}.")
        return None


# ---------- Autentificare ----------
if "token" not in st.session_state:
    st.title("☕ ShelfMatch")
    st.caption("Sign in or create an account to keep your progress saved.")

    tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign In")
            if submitted:
                result = api_send("POST", "/auth/login", json={"email": email, "password": password})
                if result:
                    st.session_state["token"] = result["access_token"]
                    st.session_state["user_email"] = result["user"]["email"]
                    st.rerun()

    with tab_register:
        with st.form("register_form"):
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_password")
            submitted = st.form_submit_button("Create Account")
            if submitted:
                result = api_send("POST", "/auth/register", json={"email": email, "password": password})
                if result:
                    st.session_state["token"] = result["access_token"]
                    st.session_state["user_email"] = result["user"]["email"]
                    st.rerun()

    st.stop()


# ---------- Aplicația (doar dacă ești logat) ----------
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.title("☕ ShelfMatch")
    st.caption(f"Signed in as {st.session_state.get('user_email', '')}")
with col_logout:
    st.write("")
    if st.button("Log Out"):
        st.session_state.pop("token", None)
        st.session_state.pop("user_email", None)
        st.rerun()

tab_library, tab_recommend, tab_dashboard, tab_feed, tab_friends, tab_challenges = st.tabs(
    ["Library", "Recommendations", "Dashboard", "Feed", "Friends", "Challenges"]
)

# ---------- TAB: Bibliotecă ----------
with tab_library:
    st.subheader("Search and add a book")
    query = st.text_input("Title or author")

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
                        st.write(f"**{book['title']}** — {book.get('author', 'unknown')}")
                        st.caption(f"{book.get('genre', 'unknown genre')} · {book.get('pages', '?')} pages")

                        with st.form(key=f"log_{book['google_books_id']}"):
                            status = st.selectbox("Status", ["wishlist", "reading", "finished"], key=f"status_{book['google_books_id']}")
                            rating = st.slider("Rating", 1, 5, 3, key=f"rating_{book['google_books_id']}")
                            date_started = st.date_input("Start date", value=None, key=f"start_{book['google_books_id']}")
                            date_finished = st.date_input("End date", value=None, key=f"end_{book['google_books_id']}")
                            submitted = st.form_submit_button("Add to library")

                            if submitted:
                                book_resp = api_send("POST", "/books/", json=book)
                                if book_resp:
                                    entry = {
                                        "book_id": book_resp["id"],
                                        "rating": rating if status == "finished" else None,
                                        "date_started": str(date_started) if date_started else None,
                                        "date_finished": str(date_finished) if date_finished else None,
                                        "status": status,
                                    }
                                    if api_send("POST", "/books/log", json=entry):
                                        st.success(f"'{book['title']}' added!")
        elif results == []:
            st.info("No results found.")

    st.divider()
    st.subheader("Your books")
    my_books = api_get("/books/mine")

    if my_books:
        for entry in my_books:
            book = entry["book"]
            with st.container(border=True):
                col1, col2 = st.columns([1, 4])
                with col1:
                    if book.get("cover_url"):
                        st.image(book["cover_url"], width=70)
                with col2:
                    st.write(f"**{book['title']}** — {book.get('author', 'unknown')}")
                    st.caption(f"{book.get('genre', '')} · status: {entry['status']}")

                    with st.expander("Edit / delete"):
                        with st.form(key=f"edit_{entry['id']}"):
                            new_status = st.selectbox(
                                "Status", ["wishlist", "reading", "finished"],
                                index=["wishlist", "reading", "finished"].index(entry["status"]),
                                key=f"edit_status_{entry['id']}",
                            )
                            new_rating = st.slider(
                                "Rating", 1, 5, entry["rating"] or 3, key=f"edit_rating_{entry['id']}"
                            )
                            new_start = st.date_input(
                                "Start date",
                                value=pd.to_datetime(entry["date_started"]).date() if entry["date_started"] else None,
                                key=f"edit_start_{entry['id']}",
                            )
                            new_finish = st.date_input(
                                "End date",
                                value=pd.to_datetime(entry["date_finished"]).date() if entry["date_finished"] else None,
                                key=f"edit_end_{entry['id']}",
                            )
                            col_save, col_delete = st.columns(2)
                            with col_save:
                                save = st.form_submit_button("Save")
                            with col_delete:
                                delete = st.form_submit_button("🗑️ Delete")

                            if save:
                                updates = {
                                    "status": new_status,
                                    "rating": new_rating if new_status == "finished" else entry["rating"],
                                    "date_started": str(new_start) if new_start else None,
                                    "date_finished": str(new_finish) if new_finish else None,
                                }
                                if api_send("PUT", f"/books/log/{entry['id']}", json=updates):
                                    st.success("Updated!")
                                    st.rerun()

                            if delete:
                                if api_send("DELETE", f"/books/log/{entry['id']}"):
                                    st.success("Removed from your library.")
                                    st.rerun()
    else:
        st.info("You haven't added any books yet.")

# ---------- TAB: Recomandări ----------
with tab_recommend:
    st.subheader("What to read next")
    if st.button("Generate recommendations"):
        recs = api_get("/recommendations/")
        if recs is not None and not recs:
            st.warning("Add a few finished books with ratings so I can generate recommendations.")
        for r in (recs or []):
            with st.container(border=True):
                col1, col2 = st.columns([1, 4])
                with col1:
                    if r.get("cover_url"):
                        st.image(r["cover_url"], width=80)
                with col2:
                    st.write(f"**{r['title']}** — {r.get('author', 'unknown')}")
                    st.caption(f"{r.get('genre', '')} · {r.get('pages', '?')} pages")
                    if r.get("estimated_days_to_read"):
                        st.write(f"⏱️ Estimate: ~{r['estimated_days_to_read']} days at your pace")

# ---------- TAB: Dashboard ----------
with tab_dashboard:
    st.subheader("Genre stats")
    stats = api_get("/stats/genres")
    if stats:
        df = pd.DataFrame(stats)
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(df, x="genre", y="avg_pages_per_day", title="Average pace (pages/day) by genre",
                          color_discrete_sequence=["#7D694E"])
            fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                font_color="#3E2E26", title_font_color="#3E2E26")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(df, x="genre", y="avg_rating", title="Average rating by genre",
                          color_discrete_sequence=["#8C5A5C"])
            fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                font_color="#3E2E26", title_font_color="#3E2E26")
            st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(df)
    else:
        st.info("Not enough data yet for stats.")

# ---------- TAB: Feed ----------
with tab_feed:
    st.subheader("What your friends are reading")
    feed = api_get("/feed/")
    if feed:
        for item in feed:
            with st.container(border=True):
                col1, col2 = st.columns([1, 4])
                with col1:
                    if item.get("cover_url"):
                        st.image(item["cover_url"], width=70)
                with col2:
                    verb = {"finished": "finished", "reading": "is reading"}.get(item["status"], item["status"])
                    st.write(f"**{item['user_email']}** {verb} **{item['book_title']}**")
                    if item.get("book_author"):
                        st.caption(f"by {item['book_author']}")
                    if item.get("rating"):
                        st.write("⭐" * item["rating"])
                    if item.get("date"):
                        st.caption(str(item["date"]))
    elif feed == []:
        st.info("Add some friends to see their reading activity here.")

# ---------- TAB: Friends ----------
with tab_friends:
    st.subheader("Add a friend")
    with st.form("add_friend_form"):
        friend_email = st.text_input("Friend's email")
        submitted = st.form_submit_button("Send friend request")
        if submitted and friend_email:
            if api_send("POST", "/friends/request", json={"email": friend_email}):
                st.success("Friend request sent!")

    st.divider()
    st.subheader("Pending requests")
    requests_in = api_get("/friends/requests")
    if requests_in:
        for req in requests_in:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(req["requester"]["email"])
            with col2:
                if st.button("Accept", key=f"accept_{req['id']}"):
                    if api_send("POST", f"/friends/accept/{req['id']}"):
                        st.success("Friend added!")
                        st.rerun()
    elif requests_in == []:
        st.caption("No pending requests.")

    st.divider()
    st.subheader("Your friends")
    friends_list = api_get("/friends/")
    if friends_list:
        for f in friends_list:
            st.write(f"• {f['email']}")
    elif friends_list == []:
        st.info("You haven't added any friends yet.")

# ---------- TAB: Challenges ----------
with tab_challenges:
    st.subheader("Create a monthly challenge")
    st.caption("Only visible to your friends.")
    with st.form("new_challenge_form"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        month = st.text_input("Month (YYYY-MM)", placeholder="2026-10")
        submitted = st.form_submit_button("Create challenge")
        if submitted and title and month:
            if api_send("POST", "/challenges/", json={"title": title, "description": description, "month": month}):
                st.success("Challenge created!")
                st.rerun()

    st.divider()
    st.subheader("Challenges")
    challenges_list = api_get("/challenges/")
    my_finished_books = [
        b for b in (api_get("/books/mine") or []) if b["status"] == "finished"
    ]

    if challenges_list:
        for c in challenges_list:
            with st.container(border=True):
                badge = "🌍 Official" if c["visibility"] == "public" else f"👥 by {c.get('creator_email', 'a friend')}"
                st.write(f"**{c['title']}** — {c['month']}")
                st.caption(badge)
                if c.get("description"):
                    st.write(c["description"])

                with st.expander("Mark as completed / see friends' picks"):
                    if my_finished_books:
                        options = {
                            f"{b['book']['title']} — {b['book'].get('author', 'unknown')}": b["id"]
                            for b in my_finished_books
                        }
                        chosen_label = st.selectbox(
                            "Which finished book completed this challenge?",
                            list(options.keys()),
                            key=f"complete_select_{c['id']}",
                        )
                        if st.button("Mark as completed", key=f"complete_btn_{c['id']}"):
                            if api_send("POST", f"/challenges/{c['id']}/complete", json={"user_book_id": options[chosen_label]}):
                                st.success("Marked as completed!")
                                st.rerun()
                    else:
                        st.caption("Finish a book first to mark this challenge as completed.")

                    completions = api_get(f"/challenges/{c['id']}/completions")
                    if completions:
                        st.write("**Friends who completed this:**")
                        for comp in completions:
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                if comp.get("cover_url"):
                                    st.image(comp["cover_url"], width=50)
                            with col2:
                                st.write(f"{comp['user_email']} — *{comp['book_title']}*")
    elif challenges_list == []:
        st.info("No challenges yet.")