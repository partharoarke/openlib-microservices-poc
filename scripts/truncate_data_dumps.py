#!/usr/bin/env python

import json

# Adjust these paths to point to your full dumps
EDITIONS_FILE = "/Users/partharoarke/Sandbox/openlibrary-data-dumps/ol_dump_editions_2025-01-08.txt"
WORKS_FILE    = "/Users/partharoarke/Sandbox/openlibrary-data-dumps/ol_dump_works_2025-01-08.txt"
AUTHORS_FILE  = "/Users/partharoarke/Sandbox/openlibrary-data-dumps/ol_dump_authors_2025-01-08.txt"

# Adjust these paths for output
TRUNC_EDITIONS_FILE = "../data/dumps/ol_dump_editions_trunc.txt"
TRUNC_WORKS_FILE    = "../data/dumps/ol_dump_works_trunc.txt"
TRUNC_AUTHORS_FILE  = "../data/dumps/ol_dump_authors_trunc.txt"

MAX_EDITIONS = 100

def main():
    editions = []
    needed_works = set()
    needed_authors = set()

    # Collect 100 editions
    with open(EDITIONS_FILE, "r", encoding="utf-8") as f_in:
        for line in f_in:
            cols = line.strip().split("\t")
            if len(cols) != 5:
                continue
            record_type, key, revision, file_timestamp, record_json = cols
            if record_type != "/type/edition":
                continue

            # Add edition to our list
            editions.append(line)
            
            # Parse the JSON to find references
            data = json.loads(record_json)
            
            # The 'works' array in an edition might be like: "works": [{"key": "/works/OLxxxxW"}]
            works_list = data.get("works", [])
            for w in works_list:
                w_key = w.get("key")
                if w_key:
                    needed_works.add(w_key)

            # The 'authors' array in an edition might be like: "authors": [{"key": "/authors/OLxxxxA"}]
            # Sometimes it's "authors" or "contributors" or might not exist.
            authors_list = data.get("authors", [])
            for a in authors_list:
                a_key = a.get("key")
                if a_key:
                    needed_authors.add(a_key)

            if len(editions) >= MAX_EDITIONS:
                break

    # Read the original large works file, keep only those matching needed_works
    retained_works_lines = {}
    with open(WORKS_FILE, "r", encoding="utf-8") as f_in:
        for line in f_in:
            cols = line.strip().split("\t")
            if len(cols) != 5:
                continue
            record_type, key, revision, file_timestamp, record_json = cols
            if record_type != "/type/work":
                continue
            if key in needed_works:
                retained_works_lines[key] = line

    # Parse each retained work to find authors
    # that might add more authors to needed_authors
    for key, line in retained_works_lines.items():
        cols = line.strip().split("\t")
        record_json = cols[4]
        data = json.loads(record_json)

        # "authors": [ { "author": {"key": "/authors/OLxxxA"}, ... } ]
        authors_list = data.get("authors", [])
        for author_obj in authors_list:
            author_info = author_obj.get("author")
            if author_info and author_info.get("key"):
                needed_authors.add(author_info["key"])

    # Read the big authors file, keep only those in needed_authors
    retained_authors_lines = {}
    with open(AUTHORS_FILE, "r", encoding="utf-8") as f_in:
        for line in f_in:
            cols = line.strip().split("\t")
            if len(cols) != 5:
                continue
            record_type, key, revision, file_timestamp, record_json = cols
            if record_type != "/type/author":
                continue

            if key in needed_authors:
                retained_authors_lines[key] = line

    # Write out truncated sets of everything
    with open(TRUNC_EDITIONS_FILE, "w", encoding="utf-8") as f_out:
        for line in editions:
            f_out.write(line)

    with open(TRUNC_WORKS_FILE, "w", encoding="utf-8") as f_out:
        for key, line in retained_works_lines.items():
            f_out.write(line)

    with open(TRUNC_AUTHORS_FILE, "w", encoding="utf-8") as f_out:
        for key, line in retained_authors_lines.items():
            f_out.write(line)

    print("Truncation complete!")
    print(f"Editions truncated: {len(editions)}")
    print(f"Works truncated: {len(retained_works_lines)}")
    print(f"Authors truncated: {len(retained_authors_lines)}")

if __name__ == "__main__":
    main()

