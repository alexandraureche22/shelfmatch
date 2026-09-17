-- ShelfMatch — schema PostgreSQL

CREATE TABLE users (
    id             SERIAL PRIMARY KEY,
    email          VARCHAR(255) UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    created_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE books (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    author          VARCHAR(255),
    genre           VARCHAR(100),
    pages           INTEGER,
    google_books_id VARCHAR(50) UNIQUE,
    cover_url       TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TYPE reading_status AS ENUM ('wishlist', 'reading', 'finished');

CREATE TABLE user_books (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id        INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    rating         SMALLINT CHECK (rating BETWEEN 1 AND 5),
    date_started   DATE,
    date_finished  DATE,
    status         reading_status NOT NULL DEFAULT 'wishlist',
    created_at     TIMESTAMP DEFAULT NOW(),
    CHECK (date_finished IS NULL OR date_started IS NULL OR date_finished >= date_started)
);

CREATE INDEX idx_user_books_status ON user_books(status);
CREATE INDEX idx_user_books_book_id ON user_books(book_id);
CREATE INDEX idx_user_books_user_id ON user_books(user_id);
CREATE INDEX idx_books_genre ON books(genre);

-- View de referință: statistici globale pe gen (toți utilizatorii la un loc).
-- Aplicația folosește, în schimb, o interogare per-utilizator (vezi crud.py).
CREATE VIEW genre_stats AS
SELECT
    b.genre,
    COUNT(*)                                                      AS books_finished,
    ROUND(AVG(ub.rating)::numeric, 2)                             AS avg_rating,
    ROUND(AVG(
        b.pages::numeric / NULLIF(ub.date_finished - ub.date_started, 0)
    )::numeric, 2)                                                AS avg_pages_per_day
FROM user_books ub
JOIN books b ON b.id = ub.book_id
WHERE ub.status = 'finished'
  AND ub.date_started IS NOT NULL
  AND ub.date_finished IS NOT NULL
GROUP BY b.genre;

INSERT INTO books (title, author, genre, pages, google_books_id) VALUES
('A little life', 'Hanya Yanagihara', 'Fiction', 412, 'B1xXX'),
('Caraval', 'Stephanie Garber', 'Fantasy', 443, 'B2xXX'),
('The picture of Dorian Gray', 'Oscar Wilde', 'Fiction', 328, 'B3xXX');

-- ---------- Prieteni ----------
CREATE TYPE friendship_status AS ENUM ('pending', 'accepted');

CREATE TABLE friendships (
    id             SERIAL PRIMARY KEY,
    requester_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    addressee_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status         friendship_status NOT NULL DEFAULT 'pending',
    created_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE (requester_id, addressee_id),
    CHECK (requester_id != addressee_id)
);

CREATE INDEX idx_friendships_requester ON friendships(requester_id);
CREATE INDEX idx_friendships_addressee ON friendships(addressee_id);

-- ---------- Challenge-uri lunare ----------
CREATE TYPE challenge_visibility AS ENUM ('public', 'friends');

CREATE TABLE challenges (
    id             SERIAL PRIMARY KEY,
    creator_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,  -- NULL = challenge oficial ShelfMatch
    title          VARCHAR(255) NOT NULL,
    description    TEXT,
    month          VARCHAR(7) NOT NULL,  -- format 'YYYY-MM'
    visibility     challenge_visibility NOT NULL DEFAULT 'friends',
    created_at     TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_challenges_month ON challenges(month);

-- Câteva challenge-uri oficiale, vizibile tuturor
INSERT INTO challenges (creator_id, title, description, month, visibility) VALUES
(NULL, 'Read a Classic', 'Choose a book considered a classic of literature, published at least 50 years ago.', '2026-01', 'public'),
(NULL, 'New Author for You', 'Read a book by an author you haven''t read before.', '2026-02', 'public'),
(NULL, 'Non-Fiction', 'Read a non-fiction book: history, science, biography or essay.', '2026-03', 'public');


-- ---------- Completarea challenge-urilor ----------
CREATE TABLE challenge_completions (
    id             SERIAL PRIMARY KEY,
    challenge_id   INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_book_id   INTEGER NOT NULL REFERENCES user_books(id) ON DELETE CASCADE,
    created_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE (challenge_id, user_id)
);

CREATE INDEX idx_completions_challenge ON challenge_completions(challenge_id);