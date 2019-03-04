/* Users */
IF NOT EXISTS(SELECT 1
FROM information_schema.tables
WHERE
    table_name = 'users' AND
    table_schema = 'public')
BEGIN
    CREATE TABLE users
    (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        hash TEXT NOT NULL
    );
END


/* Books */
IF NOT EXISTS(SELECT 1
FROM information_schema.tables
WHERE
    table_name = 'books' AND
    table_schema = 'public')
BEGIN
    CREATE TABLE books
    (
        id SERIAL PRIMARY KEY,
        isbn CHAR(10) NOT NULL,
        title VARCHAR NOT NULL,
        author VARCHAR NOT NULL,
        year CHAR(4) NOT NULL
    );
END


/* Reviews */
IF NOT EXISTS(SELECT 1
FROM information_schema.tables
WHERE
    table_name = 'reviews' AND
    table_schema = 'public')
BEGIN
    CREATE TABLE reviews
    (
        id SERIAL PRIMARY KEY,
        rating INTEGER NOT NULL,
        text TEXT,
        user_id INTEGER REFERENCES users,
        book_id INTEGER REFERENCES books
    );
END
