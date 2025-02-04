FROM apache/airflow:2.10.4 
USER root

# Install additional packages if needed
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python dependencies
COPY requirements.txt /tmp/requirements.txt

# Switch back to airflow user
USER airflow

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the dags over
COPY dags/ /opt/airflow/dags/

