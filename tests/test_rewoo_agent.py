import pytest
from unittest.mock import patch, MagicMock

from app.rewoo_agent import build_rewoo_agent, run_rewoo, PLAN_REGEX


class TestReWOOAgent:
    """Tests for the ReWOO agent module."""

    @patch("app.rewoo_agent.ChatOpenAI")
    def test_build_rewoo_agent_returns_compiled_graph(self, mock_llm):
        """Test that build_rewoo_agent returns a runnable graph."""
        mock_llm.return_value = MagicMock()
        agent = build_rewoo_agent()
        assert agent is not None

    def test_plan_regex_parses_valid_plan(self):
        """Test that the regex correctly parses a plan output."""
        import re
        plan_text = """Plan: Extract CV text from the file.
#E1 = CV[data/cv_sample.pdf]

Plan: Scrape the job posting for details.
#E2 = JobPost[https://linkedin.com/jobs/view/123]

Plan: Compare CV against job requirements.
#E3 = LLM[Compare #E1 with #E2 and provide analysis]
"""
        matches = re.findall(PLAN_REGEX, plan_text, flags=re.S)
        assert len(matches) == 3
        assert matches[0][1] == "#E1"
        assert matches[0][2] == "CV"
        assert matches[1][2] == "JobPost"
        assert matches[2][2] == "LLM"

    @patch("app.rewoo_agent.build_rewoo_agent")
    def test_run_rewoo_calls_agent(self, mock_build):
        """Test that run_rewoo invokes the agent and returns a string."""
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"result": "Final analysis"}
        mock_build.return_value = mock_agent

        result = run_rewoo("data/cv.pdf", ["https://example.com/job/1"])
        assert result == "Final analysis"
        mock_agent.invoke.assert_called_once()

    @patch("app.rewoo_agent.build_rewoo_agent")
    def test_run_rewoo_passes_task_with_links(self, mock_build):
        """Test that job links are embedded in the task."""
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"result": "Result"}
        mock_build.return_value = mock_agent

        links = ["https://example.com/job/1", "https://example.com/job/2"]
        run_rewoo("cv.pdf", links)

        call_args = mock_agent.invoke.call_args
        request = call_args[0][0]
        for link in links:
            assert link in request["task"]
