import pytest

from app import tasks


def test_research_task_interface_is_available() -> None:
    if tasks.celery_app is None:
        with pytest.raises(RuntimeError):
            tasks.run_research.delay("query-1", 1, 1)
    else:
        assert tasks.run_research.name == "app.tasks.run_research"
        assert hasattr(tasks.run_research, "delay")
