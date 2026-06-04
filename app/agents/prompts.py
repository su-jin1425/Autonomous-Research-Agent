from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    template: str


RESEARCH_SYNTHESIS_PROMPT = PromptTemplate(
    name="research_synthesis",
    template=(
        "You are an autonomous research analyst. Use only the supplied evidence. "
        "Return concise findings, cite source URLs, flag weak evidence, and avoid unsupported claims.\n\n"
        "Research question: {query}\n\nEvidence:\n{evidence}\n\n"
        "Produce: executive_summary, key_findings, risks, citations."
    ),
)


QUERY_DECOMPOSITION_PROMPT = PromptTemplate(
    name="query_decomposition",
    template=(
        "Break the research question into focused search tasks. "
        "Question: {query}\nReturn short search tasks only."
    ),
)

