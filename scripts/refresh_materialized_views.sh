#!/bin/sh
psql -h localhost -d openlib_db -U postgres -c "REFRESH MATERIALIZED VIEW book_search_view;"

