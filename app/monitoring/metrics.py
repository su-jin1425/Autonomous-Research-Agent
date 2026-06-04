from prometheus_client import Counter, Histogram


RESEARCH_RUNS = Counter("research_runs_total", "Total research executions", ["status"])
RETRIEVAL_COUNT = Counter("research_retrieval_documents_total", "Total retrieved documents")
RESEARCH_LATENCY = Histogram("research_execution_seconds", "Research execution duration")
VECTOR_SEARCH_LATENCY = Histogram("vector_search_seconds", "Vector search duration")

