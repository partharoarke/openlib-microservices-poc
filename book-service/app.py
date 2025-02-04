from fastapi import FastAPI, HTTPException, Query
import psycopg2
import os
from typing import Optional, List

app = FastAPI()

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        dbname=os.getenv("POSTGRES_DB", "openlib_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "password")
    )

@app.get("/books/search")
def search_books(
    isbn: Optional[str] = Query(None, description="Search by ISBN"),
    title: Optional[str] = Query(None, description="Search by title"),
    author: Optional[str] = Query(None, description="Search by author")
):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Base query against the materialized view
    query = """
        SELECT isbn, edition_key, edition_title, publish_date, work_key, work_title, author_key, author_name
        FROM book_search_view
    """
    conditions = []
    params = []
    
    if isbn:
        conditions.append("isbn ILIKE %s")
        params.append(f"%{isbn}%")
    if title:
        # Search in both edition_title and work_title
        conditions.append("(edition_title ILIKE %s OR work_title ILIKE %s)")
        params.extend([f"%{title}%", f"%{title}%"])
    if author:
        conditions.append("author_name ILIKE %s")
        params.append(f"%{author}%")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # For debugging:
    print("Executing query:", query, params)
    
    try:
        cur.execute(query, params)
        rows = cur.fetchall()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No books found matching your criteria")
    
    # Map the results to a list of dictionaries
    books = []
    for row in rows:
        books.append({
            "isbn": row[0],
            "edition_key": row[1],
            "edition_title": row[2],
            "publish_date": row[3],
            "work_key": row[4],
            "work_title": row[5],
            "author_key": row[6],
            "author_name": row[7]
        })
    
    return books

