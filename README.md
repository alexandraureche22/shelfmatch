# ShelfMatch

Aplicație de recomandări de cărți + predicție a ritmului de citire, pe baza istoricului tău.

## Structură

```
shelfmatch/
├── backend/          # FastAPI
│   └── app/
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── crud.py
│       ├── google_books.py
│       └── routers/
├── frontend/         # Streamlit
├── db/
│   └── schema.sql
└── README.md
```

## Setup local (VS Code)

1. **PostgreSQL** — instalează local sau folosește Docker:
   ```bash
   docker run --name shelfmatch-db -e POSTGRES_PASSWORD=parola -e POSTGRES_DB=shelfmatch -p 5432:5432 -d postgres
   ```

2. **Rulează schema**:
   ```bash
   psql -h localhost -U postgres -d shelfmatch -f db/schema.sql
   ```

3. **Backend**:
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # Mac/Linux
   pip install -r requirements.txt
   cp .env.example .env         # completează DATABASE_URL
   uvicorn app.main:app --reload
   ```
   → API disponibil la `http://localhost:8000`, documentație interactivă la `http://localhost:8000/docs`

4. **Frontend** (terminal nou):
   ```bash
   cd frontend
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```
   → Dashboard la `http://localhost:8501`

## Deschidere în VS Code

```bash
code shelfmatch
```

Recomandat: extensiile Python (Microsoft) și SQLTools (pentru a naviga direct în baza de date din editor).

## Publicare pe GitHub

\`\`\`bash
cd shelfmatch
git init
git add .
git commit -m "Initial commit: ShelfMatch backend + frontend"
git branch -M main
git remote add origin https://github.com/<user>/shelfmatch.git
git push -u origin main
\`\`\`

## Deploy (ca să ai un link live, nu doar cod)

**Backend + DB pe Render:**
1. render.com → New → Blueprint → conectezi repo-ul GitHub. `render.yaml` din proiect configurează automat serviciul web + baza PostgreSQL.
2. După primul deploy, rulezi `db/schema.sql` pe baza de date de pe Render (din Render Dashboard → shelfmatch-db → Connect → copiezi comanda `psql` și rulezi `\i db/schema.sql`).
3. Notează URL-ul public al API-ului (ceva de forma `https://shelfmatch-api.onrender.com`).

**Frontend pe Streamlit Community Cloud:**
1. share.streamlit.io → New app → conectezi repo-ul, alegi `frontend/streamlit_app.py` ca entry point.
2. Settings → Secrets → adaugi:
   \`\`\`
   API_URL = "https://shelfmatch-api.onrender.com"
   \`\`\`
3. Deploy — primești un link public gen `https://shelfmatch.streamlit.app`.

Link-ul ăsta îl pui în CV, nu doar "vezi codul pe GitHub".
