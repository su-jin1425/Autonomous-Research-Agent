from prometheus_client import Counter, Gauge, Histogram

RESEARCH_RUNS = Counter(
    "research_runs_total",
    "Total research workflow executions",
    ["status"],
)

RETRIEVAL_COUNT = Counter(
    "research_retrieval_documents_total",
    "Total retrieved documents",
)

RESEARCH_LATENCY = Histogram(
    "research_execution_seconds",
    "Research workflow execution duration",
)

VECTOR_SEARCH_LATENCY = Histogram(
    "vector_search_seconds",
    "Vector search duration",
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    [
        "method",
        "endpoint",
        "status",
    ],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
)

HTTP_REQUEST_ERRORS_TOTAL = Counter(
    "http_request_errors_total",
    "Total HTTP request errors",
    [
        "method",
        "endpoint",
    ],
)

ACTIVE_RESEARCH_JOBS = Gauge(
    "active_research_jobs",
    "Currently running research jobs",
)

FAILED_RESEARCH_JOBS = Counter(
    "failed_research_jobs_total",
    "Total failed research jobs",
)

VECTORSTORE_SIZE = Gauge(
    "vectorstore_documents_total",
    "Total indexed vector documents",
)

REDIS_QUEUE_SIZE = Gauge(
    "redis_queue_size",
    "Current Redis queue size",
)

DATABASE_QUERY_DURATION = Histogram(
    "database_query_duration_seconds",
    "Database query duration",
)

DATABASE_CONNECTIONS = Gauge(
    "database_connections_active",
    "Active database connections",
)

WEBSOCKET_CONNECTIONS = Gauge(
    "websocket_connections_active",
    "Active websocket connections",
)

REPORTS_GENERATED = Counter(
    "reports_generated_total",
    "Total generated reports",
)

AUTH_LOGINS = Counter(
    "auth_login_total",
    "Total successful logins",
)

AUTH_REGISTRATIONS = Counter(
    "auth_registration_total",
    "Total successful registrations",
)

SOURCE_VALIDATION_SCORE = Histogram(
    "source_validation_score",
    "Source quality score distribution",
    buckets=(
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
    ),
)
