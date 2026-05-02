import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import MessagesState, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import traceable

from app.tools import extract_cv_text, job_posting_scraper


SYS_MSG = SystemMessage(content="""
You are an expert career assistant that helps the user with questions related to jobs, careers, and applications.

Your key capabilities:
- You have access to the user's CV and can read its contents using the `extract_cv_text` tool.
- You can look up and extract details from job postings using the `job_posting_scraper`.
- You can compare the user's CV against one or more job postings to determine suitability and provide tailored advice.
- You can suggest improvements to the CV for better alignment with target roles.

When answering:
1. First, think step-by-step about the user's request.
2. If the task requires reading the CV, call the CV extraction tool before answering.
3. If the task involves evaluating job postings, call the job posting tool to gather accurate information before answering.
4. Compare and reason about the information before providing your final response.

Response format:
- Be clear, concise, and structured with bullet points or numbered lists.
- Use section headers when possible (e.g., "Strengths", "Weaknesses", "Recommendations").
- Support your statements with evidence from the CV or job postings.
- Avoid vague language—be specific and factual.

Constraints:
- Do not invent or guess details about the user's experience or job postings.
- Only use information available in the CV, job postings, or provided context.
- Keep your tone professional, friendly, and supportive.
""")


def build_react_agent(model_name: str = "gpt-4.1-mini"):
    """
    Build and return a compiled ReAct agent graph with memory.

    Args:
        model_name: The OpenAI model to use.

    Returns:
        Compiled LangGraph runnable with memory checkpointer.
    """
    llm = ChatOpenAI(model=model_name)
    tools = [extract_cv_text, job_posting_scraper]
    tools_node = ToolNode(tools=tools)
    agent = llm.bind_tools(tools=tools)

    @traceable(name=os.getenv("LANGSMITH_PROJECT", "ReAct Agent"))
    def assistant(state: MessagesState):
        return MessagesState(
            messages=[agent.invoke([SYS_MSG] + state["messages"])]
        )

    graph = StateGraph(MessagesState)
    graph.add_node("assistant", assistant)
    graph.add_node("tools", tools_node)
    graph.add_edge(START, "assistant")
    graph.add_conditional_edges(source="assistant", path=tools_condition)
    graph.add_edge("tools", "assistant")

    memory = InMemorySaver()
    return graph.compile(checkpointer=memory)


def run_react(cv_path: str, job_links: list[str], thread_id: str = "react_thread_1") -> str:
    """
    Run the ReAct agent with a CV and job links.

    Args:
        cv_path: Path to the CV file.
        job_links: List of job posting URLs.
        thread_id: Thread ID for memory persistence.

    Returns:
        The final agent response as a string.
    """
    agent = build_react_agent()
    config = {"configurable": {"thread_id": thread_id}}

    links_text = "\n".join(job_links)
    messages = [
        HumanMessage(content=f"""
Can you take a look at my CV at the location "{cv_path}" and tell me how well it matches the requirements for the following jobs:

{links_text}

Tell me which one is the most suitable for my experience and skills, and what improvements I can make to my CV to increase my chances of getting an interview for that job.
""")
    ]

    result = agent.invoke(MessagesState(messages=messages), config=config)
    return result["messages"][-1].content
