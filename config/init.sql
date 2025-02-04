-- Drop child tables first to avoid foreign key conflicts
DROP TABLE IF EXISTS author_works;
DROP TABLE IF EXISTS edition_isbns;
DROP TABLE IF EXISTS editions;
DROP TABLE IF EXISTS works;
DROP TABLE IF EXISTS authors;

-- Re-create the tables

CREATE TABLE authors (
    author_key TEXT PRIMARY KEY,         -- e.g., "/authors/OL10000031A"
    name TEXT,
    revision INT,
    last_modified TIMESTAMP,
    data JSONB                           -- raw JSON record from the dump
);

CREATE TABLE works (
    work_key TEXT PRIMARY KEY,           -- e.g., "/works/OL10000278W"
    title TEXT,
    revision INT,
    last_modified TIMESTAMP,
    data JSONB                           -- raw JSON record
);

CREATE TABLE editions (
    edition_key TEXT PRIMARY KEY,        -- e.g., "/books/OL10000299M"
    title TEXT,
    publish_date TEXT,
    revision INT,
    last_modified TIMESTAMP,
    work_key TEXT,                       -- foreign key referencing works(work_key)
    data JSONB,                          -- raw JSON record
    FOREIGN KEY (work_key) REFERENCES works(work_key)
);

CREATE TABLE edition_isbns (
    isbn TEXT PRIMARY KEY,               -- e.g., "9780108360688"
    edition_key TEXT,
    FOREIGN KEY (edition_key) REFERENCES editions(edition_key)
);

CREATE TABLE author_works (
    author_key TEXT,
    work_key TEXT,
    PRIMARY KEY (author_key, work_key),
    FOREIGN KEY (author_key) REFERENCES authors(author_key),
    FOREIGN KEY (work_key) REFERENCES works(work_key)
);

-- Create a materialized view for book searches.
CREATE MATERIALIZED VIEW IF NOT EXISTS book_search_view AS
SELECT
    ei.isbn,
    e.edition_key,
    e.title AS edition_title,
    e.publish_date,
    w.work_key,
    w.title AS work_title,
    a.author_key,
    a.name AS author_name,
    e.data AS edition_data,
    w.data AS work_data,
    a.data AS author_data
FROM edition_isbns ei
JOIN editions e ON e.edition_key = ei.edition_key
JOIN works w ON w.work_key = e.work_key
JOIN author_works aw ON aw.work_key = w.work_key
JOIN authors a ON a.author_key = aw.author_key;

