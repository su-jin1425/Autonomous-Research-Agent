from __future__ import annotations

import re

from app.core.config import get_settings


class ResearchPlanner:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def create_plan(
        self,
        *,
        query: str,
        max_depth: int,
    ) -> dict:
        normalized = re.sub(
            r"\s+",
            " ",
            query,
        ).strip()

        sub_questions = self._generate_sub_questions(normalized)

        search_tasks = self._generate_search_tasks(
            normalized,
            max_depth=max_depth,
        )

        return {
            "objective": normalized,
            "sub_questions": sub_questions,
            "search_tasks": search_tasks,
            "knowledge_gaps": [],
            "confidence_score": 0.0,
        }

    def _generate_sub_questions(
        self,
        query: str,
    ) -> list[str]:
        return [
            f"What is {query}?",
            f"How does {query} work?",
            f"What are the benefits of {query}?",
            f"What are the risks of {query}?",
            f"What are industry best practices for {query}?",
        ]

    def _generate_search_tasks(
        self,
        query: str,
        *,
        max_depth: int,
    ) -> list[str]:
        candidates = [
            query,
            f"{query} overview",
            f"{query} latest research",
            f"{query} evidence",
            f"{query} risks",
            f"{query} opportunities",
            f"{query} industry analysis",
            f"{query} best practices",
        ]

        if any(
            keyword in query.lower()
            for keyword in {
                "ai",
                "llm",
                "agent",
                "automation",
                "machine learning",
            }
        ):
            candidates.extend(
                [
                    f"{query} architecture",
                    f"{query} implementation patterns",
                    f"{query} deployment strategy",
                ]
            )

        unique_tasks: list[str] = []
        seen: set[str] = set()

        for task in candidates:
            normalized = task.lower()

            if normalized in seen:
                continue

            seen.add(normalized)
            unique_tasks.append(task)

        return unique_tasks[: max(max_depth * 3, 3)]
