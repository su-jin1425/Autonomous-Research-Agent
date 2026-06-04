from app.retrieval.documents import RetrievedDocument
from app.services.source_validation import SourceValidator


def test_source_validator_scores_https_structured_source_higher() -> None:
    validator = SourceValidator()
    weak = RetrievedDocument(url="http://example.com", title=None, content="short", score=0.1)
    strong = RetrievedDocument(
        url="https://agency.gov/report",
        title="Research Report",
        content=" ".join(["evidence"] * 300),
        score=0.9,
    )

    assert validator.score(strong) > validator.score(weak)

