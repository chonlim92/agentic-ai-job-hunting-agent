import pytest
from unittest.mock import patch, MagicMock

from app.react_agent import build_react_agent, run_react


class TestReActAgent:
    """Tests for the ReAct agent module."""

    @patch("app.react_agent.ChatOpenAI")
    def test_build_react_agent_returns_compiled_graph(self, mock_llm):
        """Test that build_react_agent returns a runnable graph."""
        mock_llm.return_value = MagicMock()
        mock_llm.return_value.bind_tools.return_value = MagicMock()
        agent = build_react_agent()
        assert agent is not None

    @patch("app.react_agent.build_react_agent")
    def test_run_react_calls_agent(self, mock_build):
        """Test that run_react invokes the agent and returns a string."""
        mock_agent = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Analysis result"
        mock_agent.invoke.return_value = {"messages": [mock_message]}
        mock_build.return_value = mock_agent

        result = run_react("data/cv.pdf", ["https://example.com/job/1"])
        assert result == "Analysis result"
        mock_agent.invoke.assert_called_once()

    @patch("app.react_agent.build_react_agent")
    def test_run_react_passes_multiple_links(self, mock_build):
        """Test that multiple job links are included in the message."""
        mock_agent = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Result"
        mock_agent.invoke.return_value = {"messages": [mock_message]}
        mock_build.return_value = mock_agent

        links = ["https://example.com/job/1", "https://example.com/job/2"]
        run_react("cv.pdf", links)

        call_args = mock_agent.invoke.call_args
        state = call_args[0][0]
        msg_content = state["messages"][0].content
        for link in links:
            assert link in msg_content
