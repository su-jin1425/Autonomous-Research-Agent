from dataclasses import dataclass, field


@dataclass(slots=True)
class RetrievedDocument:
    url: str
    title: str | None
    content: str
    score: float = 0.0
    metadata: dict[str, str | int | float] = field(default_factory=dict)


@dataclass(slots=True)
class DocumentChunk:
    id: str
    text: str
    metadata: dict[str, str | int | float]
