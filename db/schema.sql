--ShelfMatch schema PostgreSQL

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
    book_id        INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    rating         SMALLINT CHECK (rating BETWEEN 1 AND 5),
    date_started   DATE,
    date_finished  DATE,
    status         reading_status NOT NULL DEFAULT 'wishlist',
    created_at     TIMESTAMP DEFAULT NOW(),
    CHECK (date_finished IS NULL OR date_started IS NULL OR date_finished >= date_started)
);

-- Indexuri pentru querurile de agregare
CREATE INDEX idx_user_books_status ON user_books(status);
CREATE INDEX idx_user_books_book_id ON user_books(book_id);
CREATE INDEX idx_books_genre ON books(genre);

-- View calculat: statistici pe gen (ritm de citire + preferință)
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

-- Date de test 
INSERT INTO books (title, author, genre, pages, google_books_id) VALUES
('Dune', 'Frank Herbert', 'Science Fiction', 412, 'B1xXX'),
('Sapiens', 'Yuval Noah Harari', 'Non-Fiction', 443, 'B2xXX'),
('1984', 'George Orwell', 'Dystopia', 328, 'B3xXX');

INSERT INTO user_books (book_id, rating, date_started, date_finished, status) VALUES
(1, 5, '2026-01-01', '2026-01-10', 'finished'),
(2, 4, '2026-01-15', '2026-01-30', 'finished'),
(3, 5, '2026-02-01', '2026-02-05', 'finished');
