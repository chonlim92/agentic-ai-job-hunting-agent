import os
import re
from typing import List, TypedDict, Literal

from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import traceable

from app.tools import extract_cv_text, job_posting_scraper


class ReWOO(TypedDict):
    task: str
    plan_string: str
    steps: List
    results: dict
    result: str


PLANNER_PROMPT = """For the following task, make plans that can solve the problem step by step. For each plan, indicate
which external tool together with tool input to retrieve evidence. You can store the evidence into a
variable #E that can be called by later tools. (Plan, #E1, Plan, #E2, Plan, ...) Use the following format:
Plan: Explain the plan.
#E1 = TOOL[tool-input]

Plan: Explain the plan for the next step
#E2 = TOOL[tool-input]


Allowed TOOLs:
1) LLM[input]    – Let the language model reason
2) CV[input]     – The tool extract_cv_text, input = local path
3) JobPost[input]– The tool job_posting_scraper, input = a job-url

Do not invent any other tool names.
Begin!

Task: {task}
"""

SOLVER_PROMPT = """
Solve the following task or problem. To solve the problem, we have made step-by-step Plan and
retrieved corresponding Evidence to each Plan. Use them with caution since long evidence might
contain irrelevant information.

{plan_block}

Now solve the question or task according to provided Evidence above. Respond with the answer
directly with no extra words.

Task: {task}
Response:
"""

PLAN_REGEX = r"Plan:\s*(.+?)\s*(#E\d+)\s*=\s*(\w+)\[(.+?)\]"


def build_rewoo_agent(model_name: str = "gpt-4.1-mini"):
    """
    Build and return a compiled ReWOO agent graph with memory.

    Args:
        model_name: The OpenAI model to use.

    Returns:
        Compiled LangGraph runnable with memory checkpointer.
    """
    llm = ChatOpenAI(model=model_name)

    @traceable(name="Planner Node")
    def planner_node(state: ReWOO):
        task = state['task']
        raw_plan = llm.invoke(PLANNER_PROMPT.format(task=task)).content
        steps = re.findall(PLAN_REGEX, raw_plan, flags=re.S)
        return ReWOO(plan_string=raw_plan, steps=steps)

    def _current_index(state: ReWOO):
        done = len(state.get("results", {}))
        total = len(state['steps'])
        return None if done >= total else done

    @traceable(name="Executor Node")
    def executor_node(state: ReWOO):
        current_index = _current_index(state)
        if current_index is None:
            return {}

        plan_text, step_name, tool_name, tool_input = state['steps'][current_index]

        for k, v in state.get("results", {}).items():
            if tool_name == "LLM" and k in tool_input:
                tool_input = tool_input.replace(k, v)

        if tool_name == "LLM":
            out = llm.invoke(tool_input).content
        elif tool_name == "CV":
            out = extract_cv_text.invoke(tool_input)
        elif tool_name == "JobPost":
            out = job_posting_scraper.invoke(tool_input)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

        results = dict(state.get("results", {}))
        results[step_name] = str(out)
        return ReWOO(results=results)

    @traceable(name="Solver Node")
    def solver_node(state: ReWOO):
        lines = []
        for plan_text, step_name, tool_name, tool_input in state['steps']:
            evidence = state['results'][step_name]
            lines.append(f"Plan: {plan_text}\nEvidence: {evidence}\n")

        prompt = SOLVER_PROMPT.format(
            plan_block='\n'.join(lines), task=state['task']
        )
        answer = llm.invoke(prompt).content.strip()
        return ReWOO(result=answer)

    def router(state: ReWOO) -> Literal["solver", "executor"]:
        return "solver" if _current_index(state) is None else "executor"

    graph = StateGraph(ReWOO)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("solver", solver_node)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_conditional_edges(source="executor", path=router)
    graph.add_edge("solver", END)

    memory = InMemorySaver()
    return graph.compile(checkpointer=memory)


def run_rewoo(cv_path: str, job_links: list[str], thread_id: str = "rewoo_thread_1") -> str:
    """
    Run the ReWOO agent with a CV and job links.

    Args:
        cv_path: Path to the CV file.
        job_links: List of job posting URLs.
        thread_id: Thread ID for memory persistence.

    Returns:
        The final agent response as a string.
    """
    agent = build_rewoo_agent()
    config = {"configurable": {"thread_id": thread_id}}

    links_text = "\n".join(job_links)
    task = f"""
Can you take a look at my CV at the location "{cv_path}" and tell me how well it matches the requirements for the following jobs:

{links_text}

Tell me which one is the most suitable for my experience and skills, and what improvements I can make to my CV to increase my chances of getting an interview for that job.
"""

    request = ReWOO(
        task=task,
        plan_string="",
        steps=[],
        results={},
        result=""
    )

    result = agent.invoke(request, config=config)
    return result['result']
