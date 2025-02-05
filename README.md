# Open Library ISBN Microservices POC

This repository demonstrates a **microservices-based** architecture for ingesting Open Library data, transforming it with **Airflow + Kafka**, storing it in **PostgreSQL**, and exposing it via **FastAPI** services. It includes:

- **Airflow DAGs** to parse and publish authors, works, and editions data.  
- **Kafka Consumers** to upsert data into PostgreSQL tables (authors, works, editions).  
- **Reference Tables** (`author_works`, `edition_isbns`) that link these entities.  
- **Materialized View** to facilitate consolidated book searches by ISBN, title, or author.  
- **Microservices** exposing REST endpoints for authors, works, and editions, plus a **book service** for unified search.

## Table of Contents
1. [Architecture Overview](#architecture-overview)  
2. [Repository Structure](#repository-structure)  
3. [Setup & Installation](#setup--installation)  
4. [Running the Pipeline](#running-the-pipeline)  
5. [Searching Books](#searching-books)  


---

## Architecture Overview

```
                   +-------------------+
                   |   Airflow DAGs    |
                   | (authors, works,  |
                   |  editions)        |
                   +--------+----------+
                            |
                            | Publishes messages to Kafka
                            V
+-----------+          +-----------------+         +---------------------+
|  Dump     |          |   Kafka Broker  | <----->|  Kafka Consumers    |
|  Files    |          | (Zookeeper +    |         | (author-service,    |
| (Authors, |  ----->  |  Kafka)         |         |  work-service,      |
|  Works,   |          +--------+--------+         |  edition-service)   |
|  Editions)|                   |                  +---------+-----------+
+-----------+                   |                            |
                                | Inserts data into           |
                                V                            |
                          +---------------+                  |
                          |  PostgreSQL   | <----------------+
                          | (authors,     |
                          |  works,       |
                          |  editions,    |
                          |  reftables)   |
                          +-------+-------+
                                  |
                                  | Materialized View
                                  V
                          +---------------+
                          |  Book Service |
                          | (FastAPI)     |
                          +---------------+
```

1. **Airflow** publishes records from data dump files to **Kafka**.  
2. **Kafka Consumers** (FastAPI microservices) read messages and insert/upsert into PostgreSQL.  
3. **Reference Tables** (`author_works`, `edition_isbns`) link authors-to-works and editions-to-ISBNs.  
4. A **Materialized View** merges data for simplified “book” search.  
5. The **book service** queries the view to allow searches by ISBN, title, or author.

---

## Repository Structure

A typical layout:

```
openlib_microservices_poc/
├── airflow/
│   ├── dags/
│   │   ├── openlib_publish_authors.py
│   │   ├── openlib_publish_works.py
│   │   ├── openlib_publish_editions.py
│   │   └── ...
│   ├── Dockerfile
│   └── ...
├── author-service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── work-service/
│   ├── app.py
│   ├── Dockerfile
│   └── ...
├── edition-service/
│   ├── app.py
│   ├── Dockerfile
│   └── ...
├── book-service/
│   ├── app.py
│   ├── Dockerfile
│   └── ...
├── scripts/
│   ├── populate_author_works.py
│   ├── populate_edition_isbns.py
│   └── ...
├── config/
│   ├── init.sql
│   └── ...
├── data/dumps
│   ├── ol_dump_editions_trunc.txt
│   └── ...
├── docker-compose.yml
└── README.md
```

- **airflow/dags/**: Airflow DAGs for authors, works, editions ingestion.  
- **\*-service/**: Each microservice (author, work, edition, and book).  
- **scripts/**: Helper scripts (populating reference tables, data transformations).  
- **config/init.sql**: DB init script that creates tables.  
- **docker-compose.yml**: Orchestrates all containers (PostgreSQL, Kafka, Airflow, microservices).

---

## Setup & Installation

1. **Clone the Repo**:
   ```bash
   git clone https://github.com/partharoarke/openlib_microservices_poc.git
   cd openlib_microservices_poc
   ```

2. **Configure Environment**:
   - Copy or create a `.env` file defining variables like `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, etc.
   - If you have custom Python dependencies, ensure each microservice has a `requirements.txt` or that you install them in your Dockerfiles.

3. **Initialize Database**:
   - The container runs `/docker-entrypoint-initdb.d/init.sql` from `config/init.sql` on startup, creating tables.  
   - You can modify or add additional SQL scripts if needed.

4. **Build & Start Containers**:
   ```bash
   docker compose build
   docker compose up -d
   ```
   This will spin up:
   - **PostgreSQL** (with tables created by `init.sql`)
   - **Kafka + Zookeeper**
   - **Airflow** (scheduler + webserver in standalone mode)
   - **Author/Work/Edition/Book services** (FastAPI containers)

5. **Check Services**:
   - **Airflow UI**: `http://localhost:8080` (username/password as defined or default).  
   - **Author-Service**: `http://localhost:5001/docs`  
   - **Edition-Service**: `http://localhost:5002/docs`
   - **Work-Service**: `http://localhost:5003/docs`    
   - **Book-Service**: `http://localhost:5005/docs`

---

## Running the Pipeline

1. **Add Data Dump Files**  
   - Place or copy truncated files (e.g., `ol_dump_authors_trunc.txt`, etc.) into `./data/dumps` so Airflow can detect them.
   - The scripts/truncate_data_dumps.py utility truncates the files from the source folder limiting the size to 100 edition entries for demo purposes as the files are large. 

2. **Trigger Airflow DAGs**  
   - In the **Airflow UI**, unpause/trigger DAGs like `openlib_publish_authors`, `openlib_publish_works`, `openlib_publish_editions`.  
   - These DAGs will:
     1. Wait for the dump file using a FileSensor.  
     2. Read each line, publish messages to Kafka.

3. **Kafka Consumers**  
   - Each microservice (author-service, work-service, edition-service) consumes messages from Kafka, upserting rows into PostgreSQL.

4. **Populate Reference Tables** (Optional)  
   - If you have scripts in `scripts/` (e.g., `populate_author_works.py`, `populate_edition_isbns.py`), run them manually or incorporate them into your DAG.  
   - **Refresh Materialized View** if you created one for consolidated search:
     ```sql
     REFRESH MATERIALIZED VIEW book_search_view;
     ```

5. **Verify Data**  
   - Inspect PostgreSQL tables.  
   - Check logs in your microservice containers to confirm data is inserted.  

---

## Searching Books

1. **Run the Book Service**  
   - By default, it’s mapped to `localhost:5005`.

2. **Endpoints**  
   - **`GET /books/search?isbn=...`**  
   - **`GET /books/search?title=...&author=...`**

3. **Example**  
   ```bash
   curl "http://localhost:5005/books/search?isbn=9781883823122"
   ```
   Or open in the browser to get JSON results. Alternatively, check `/docs` for interactive Swagger UI.

4. **Materialized View**  
   - The book service typically queries a materialized view (e.g., `book_search_view`) that joins authors, works, editions, etc.

---

## Thank You!

This POC showcases how to:

- **Ingest** and transform Open Library data  
- **Decouple** ingestion with Airflow + Kafka  
- **Store** structured + JSON data in PostgreSQL  
- **Expose** multiple microservices for authors, works, editions  
- **Join** data in a materialized view for unified book search

Feel free to open issues or pull requests if you have questions or enhancements!

---

## Possible Future Enhancements & Considerations for a production-ready application

1. **Massive-Scale Ingestion with Apache Spark or Beam**  
   - **Why:** While the current Airflow + Kafka pipeline handles moderate data volumes, truly massive Open Library dumps might benefit from a **distributed processing** framework.  
   - **What It Involves:**  
     - Using **Spark** or **Apache Beam** to parse and transform large JSON or TSV dumps in a cluster, then push the results into Kafka or directly into PostgreSQL.  
     - Integrating Spark/Beam jobs into Airflow via specialized operators (e.g., `SparkSubmitOperator`, `DataflowJavaOperator`, etc.).

2. **Advanced Search with Elasticsearch or OpenSearch**  
   - **Why:** PostgreSQL works well for relational queries and smaller text search. For richer features (fuzzy matching, scoring, faceting), **Elasticsearch** or **OpenSearch** can offer more sophisticated full-text search.  
   - **What It Involves:**  
     - Syncing updates from Kafka or PostgreSQL into an Elasticsearch index (via a dedicated consumer or Airflow DAG).  
     - A separate **book search microservice** that queries Elasticsearch for advanced querying.

3. **Kubernetes (K8s) or Docker Swarm for Orchestration**  
   - **Why:** Scaling beyond Docker Compose often requires a robust orchestrator.  
   - **What It Involves:**  
     - Packaging each microservice in Helm charts or K8s deployments.  
     - Managing persistent volumes for PostgreSQL and stateful services (Kafka, Zookeeper).

4. **DBT or Other Transformation Framework**  
   - **Why:** For organized SQL transformations and data modeling, a tool like **dbt** provides versioning, testing, and documentation of data models.  
   - **What It Involves:**  
     - Loading raw data into staging tables and using dbt to build incremental transformations.  
     - Centralizing logic for building materialized views and analytics.

5. **CI/CD Pipeline Enhancements**  
   - **Why:** Automated builds, tests, and deployments ensure consistency.  
   - **What It Involves:**  
     - Using **GitHub Actions**, **GitLab CI**, or **Jenkins** to build Docker images, run unit tests on DAGs/microservices, and deploy them to a staging environment.  
     - Automated integration tests that spin up Docker Compose or ephemeral K8s clusters to validate ingestion and API results.

6. **High-Availability & Scalability**  
   - **Why:** Production environments often require no single point of failure.  
   - **What It Involves:**  
     - Running Kafka and PostgreSQL in **cluster** mode (e.g., Patroni for Postgres, multiple brokers for Kafka).  
     - Load balancing and auto-scaling microservices in a container orchestrator.

7. **Enhanced Monitoring & Alerting**  
   - **Why:** Observability is crucial for diagnosing performance or ingestion bottlenecks.  
   - **What It Involves:**  
     - Using **Prometheus** + **Grafana** for real-time metrics (Kafka offsets, Airflow DAG success rates, Postgres queries).  
     - Slack or email alerts for pipeline failures, container crashes, or storage thresholds.

---

## License & Disclaimer

This project is released under the [MIT License](LICENSE). It is provided primarily for **educational and demonstrative purposes**, illustrating how to build an event-driven microservices architecture for ingesting and querying Open Library data.

**Note**: This repository and its maintainers are not affiliated with the Internet Archive or the Open Library project. All code and configurations are offered “as is” without warranty of any kind. Use and modify them at your own risk in accordance with the MIT License terms.

---

