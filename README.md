# 104 Job Crawler & Data API

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)
![Celery](https://img.shields.io/badge/Celery-5.x-brightgreen.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.1xx-green.svg)

This is a high-performance, scalable, and distributed crawler system designed specifically for fetching job data from the **104.com.tw** job portal. It transforms raw data into structured information, stores it in a relational database, and serves it via a RESTful API.

## System Architecture

The system is designed based on a message-driven, producer-consumer pattern, fully containerized with Docker. For a detailed visual representation of the components and their interactions, please refer to the PlantUML file:

[**`system_architecture.puml`**](./system_architecture.puml)

This file can be rendered using online tools or IDE extensions (e.g., PlantUML for VS Code) to generate a clear architectural diagram.

## The Story: From Setup to Data

This guide will walk you through the entire process, from setting up the environment to querying the final, structured job data.

### Prologue: Setting the Stage

Before we begin, our system needs its configuration. All settings are managed in a single `.env` file.

**Action**: Create a `.env` file in the project root. Use the following template, replacing placeholder values as needed.

```env
# .env

# ==================================
# ====== Database (MySQL)      ======
# ==================================
MYSQL_ROOT_PASSWORD=your_strong_root_password
MYSQL_DATABASE=job_data
MYSQL_USER=user
MYSQL_PASSWORD=password
MYSQL_HOST=mysql
MYSQL_PORT=3306

# ==================================
# ====== Message Broker (RabbitMQ) ======
# ==================================
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672

# ==================================
# ====== 104 Crawler Parameters  ======
# ==================================
# Job category code (e.g., 2007000000 for Software/Engineering)
# Find this in the 104.com.tw URL or reference `crawler/project_data/104_人力銀行_jobcat_json.txt`
JOBCAT_CODE=2007000000

# Keywords to search for (comma-separated, no spaces)
KEYWORDS=Python,Golang,Java,Backend,DevOps

# Max pages to crawl per keyword
MAX_PAGES=100

# Sort order (15: by relevance, 16: by update date)
ORDER_SETTING=15
```

### Act I: Awakening the System

With the configuration in place, we can bring all services to life. This single command builds the necessary Docker images and starts all services (database, message broker, workers, etc.) in the background.

**Action**: Run the following command.

```bash
docker compose up --build -d
```

At this point, the system is running and waiting for instructions. The Celery workers are idle, connected to the message broker, and ready to accept tasks.

### Act II: The Data Harvest

Our data collection is a three-part process. Each part is a `producer` that sends a specific task to the workers.

**1. Gathering the Categories (Optional, but recommended for first run)**

First, we need to understand the job landscape. This producer fetches all job category definitions from 104.com.tw and stores them in our database (`tb_category`).

**Action**: Execute the category producer.
```bash
docker compose run --rm producer-category
```

**2. Collecting the Leads (URLs)**

Next, based on the `JOBCAT_CODE` and `KEYWORDS` in your `.env` file, we'll gather the URLs for all relevant job postings. This producer sends tasks to the workers, which then scrape the search result pages and save unique URLs into the `tb_urls` table.

**Action**: Execute the URL producer.
```bash
docker compose run --rm producer-urls
```

**3. Uncovering the Details**

With a list of URLs, we can now fetch the detailed information for each job. This producer reads from the `tb_urls` table and creates a task for each URL. Workers then hit the 104 API, parse the JSON response, and save the structured data into the `tb_jobs` table.

**Action**: Execute the job details producer.
```bash
docker compose run --rm producer-job-details
```

### Act III: Accessing the Treasure

Once the harvest is complete, the structured data resides in our MySQL database. The FastAPI service provides a clean, fast, and documented way to access it.

**Action**: Use any HTTP client or your browser to query the data.

-   **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
-   **API Root**: [http://localhost:8000/](http://localhost:8000/)

**Example Query (using `curl` and `jq` for pretty-printing):**

*To find the first 5 jobs with "Python" in the title:*
```bash
curl -s "http://localhost:8000/jobs/?title=Python&limit=5" | jq
```

*To find jobs from companies with "新加坡商" in their name:*
```bash
curl -s "http://localhost:8000/jobs/?company_name=新加坡商" | jq
```

## Epilogue: Monitoring and Shutdown

Throughout the process, you can monitor the system's health and progress.

| Service                 | URL                                     | Credentials                           |
| ----------------------- | --------------------------------------- | ------------------------------------- |
| **Job Data API (Swagger)**| [http://localhost:8000/docs](http://localhost:8000/docs)      | -                                     |
| **Flower (Celery Monitor)** | [http://localhost:5555](http://localhost:5555)           | -                                     |
| **RabbitMQ Management** | [http://localhost:15672](http://localhost:15672)      | `guest` / `guest`                     |
| **phpMyAdmin**          | [http://localhost:8080](http://localhost:8080)           | Server: `mysql`, User/Pass from `.env`|

When your work is done, you can shut down the entire system.

-   **To stop all services**:
    ```bash
    docker compose down
    ```

-   **To stop services and PERMANENTLY DELETE all data** (database, message queues):
    ```bash
    docker compose down -v
    ```
