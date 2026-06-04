from app.agents.prompts import RESEARCH_SYNTHESIS_PROMPT
from app.core.config import get_settings
from app.vectorstore.base import VectorHit


class ReasoningAgent:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def synthesize(self, *, query: str, evidence: list[VectorHit]) -> dict:
        llm_result = await self._try_llm_synthesis(query=query, evidence=evidence)
        if llm_result:
            return llm_result
        return self._deterministic_synthesis(query=query, evidence=evidence)

    async def _try_llm_synthesis(self, *, query: str, evidence: list[VectorHit]) -> dict | None:
        if not self.settings.openai_api_key:
            return None
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI
        except ImportError:
            return None

        prompt = ChatPromptTemplate.from_template(RESEARCH_SYNTHESIS_PROMPT.template)
        model = ChatOpenAI(model=self.settings.llm_model, api_key=self.settings.openai_api_key, temperature=0.2)
        evidence_text = self._format_evidence(evidence)
        response = await (prompt | model).ainvoke({"query": query, "evidence": evidence_text})
        return {
            "executive_summary": response.content,
            "key_findings": [],
            "risks": ["LLM output should be reviewed before external use"],
            "citations": self._citations(evidence),
            "reasoning_steps": [
                "Query decomposed into search tasks",
                "Sources retrieved and embedded",
                "Top semantic matches synthesized against the original query",
            ],
            "model": self.settings.llm_model,
        }

    def _deterministic_synthesis(self, *, query: str, evidence: list[VectorHit]) -> dict:
        top_hits = evidence[:5]
        findings = []
        for hit in top_hits:
            title = hit.metadata.get("title") or "Untitled source"
            url = hit.metadata.get("url") or ""
            excerpt = hit.text[:420].strip()
            findings.append({"source": str(title), "url": str(url), "finding": excerpt, "score": round(hit.score, 4)})

        if findings:
            summary = f"Research for '{query}' found {len(findings)} semantically relevant evidence chunks."
        else:
            summary = f"No high-confidence evidence was retrieved for '{query}'."
        return {
            "executive_summary": summary,
            "key_findings": findings,
            "risks": [
                "Search engine availability and website access affect retrieval quality",
                "Fallback synthesis is extractive and should be reviewed for final publication",
            ],
            "citations": self._citations(evidence),
            "reasoning_steps": [
                "Generated focused search tasks from the user query",
                "Collected web evidence and extracted page content where possible",
                "Indexed chunks into the vector store",
                "Ranked evidence by semantic similarity",
                "Generated a citation-aware structured report",
            ],
            "model": "deterministic-fallback",
        }

    def _format_evidence(self, evidence: list[VectorHit]) -> str:
        lines = []
        for index, hit in enumerate(evidence, start=1):
            url = hit.metadata.get("url", "")
            lines.append(f"[{index}] score={hit.score:.3f} url={url}\n{hit.text}")
        return "\n\n".join(lines)

    def _citations(self, evidence: list[VectorHit]) -> list[dict[str, str | float]]:
        citations = []
        seen: set[str] = set()
        for hit in evidence:
            url = str(hit.metadata.get("url", ""))
            if not url or url in seen:
                continue
            seen.add(url)
            citations.append(
                {
                    "url": url,
                    "title": str(hit.metadata.get("title", "")),
                    "score": round(hit.score, 4),
                }
            )
        return citations

