```markdown
# ShelfMatch

Aplicație de recomandări de cărți și predicție a ritmului de citire, pe baza istoricului personal de lectură.

## Funcționalități

- **Bibliotecă personală** — căutare cărți prin Google Books API, cu adăugare automată a copertei, autorului, genului și numărului de pagini
- **Recomandări** — sugestii de cărți noi bazate pe genurile cu rating mediu cel mai mare din istoric
- **Predicție ritm de citire** — estimează câte zile ar dura o carte nouă, pe baza ritmului mediu (pagini/zi) calculat per gen
- **Dashboard** — statistici agregate: rating mediu și ritm de citire per gen

## Tech stack

- **Backend**: Python, FastAPI, SQLAlchemy
- **Bază de date**: PostgreSQL
- **Frontend**: Streamlit
- **API extern**: Google Books API

## Structură

```
shelfmatch/
  backend/
    app/
      main.py
      database.py
      models.py
      schemas.py
      crud.py
      google_books.py
      routers/
        books.py
        recommendations.py
        stats.py
  frontend/
    streamlit_app.py
  db/
    schema.sql
  render.yaml
```

## Setup local

### 1. Bază de date

```bash
psql -h localhost -U postgres -c "CREATE DATABASE shelfmatch;"
psql -h localhost -U postgres -d shelfmatch -f db/schema.sql
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
cp .env.example .env         # completează DATABASE_URL și, opțional, GOOGLE_BOOKS_API_KEY
uvicorn app.main:app --reload
```

API disponibil la `http://localhost:8000`, documentație interactivă la `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Interfață disponibilă la `http://localhost:8501`.

## Variabile de mediu

`backend/.env`:

```
DATABASE_URL=postgresql://postgres:PAROLA@localhost:5432/shelfmatch
GOOGLE_BOOKS_API_KEY=
```

`GOOGLE_BOOKS_API_KEY` e opțională — fără ea, API-ul funcționează dar cu o limită de request-uri mai mică.

## Deploy

**Backend + bază de date**: Render, folosind `render.yaml` (Blueprint) pentru configurare automată a serviciului web și a bazei PostgreSQL.

**Frontend**: Streamlit Community Cloud, cu variabila `API_URL` setată în Secrets către URL-ul public al backend-ului.

