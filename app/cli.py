import argparse
import os

from app.react_agent import run_react
from app.rewoo_agent import run_rewoo


def _langsmith_available() -> bool:
    """Check if LangSmith API key is configured in environment."""
    return bool(os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY"))


def _set_langsmith_tracing(enabled: bool):
    """Enable or disable LangSmith tracing via environment variables."""
    if enabled and _langsmith_available():
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    else:
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"


def interactive_mode():
    """Run the agent in interactive CLI mode with prompts."""
    print("=" * 60)
    print("  Job Hunting Agent - CLI Mode")
    print("=" * 60)

    # Select agent mode
    print("\nSelect agent mode:")
    print("  1) ReAct")
    print("  2) ReWOO")
    mode = input("Enter choice [1/2]: ").strip()
    while mode not in ("1", "2"):
        mode = input("Invalid choice. Enter 1 or 2: ").strip()
    agent_mode = "react" if mode == "1" else "rewoo"

    # LangSmith tracing
    if _langsmith_available():
        ls_choice = input("\nEnable LangSmith tracing? [y/N]: ").strip().lower()
        _set_langsmith_tracing(ls_choice == "y")
    else:
        _set_langsmith_tracing(False)

    # CV path
    cv_path = input("\nEnter path to your CV file (.pdf, .docx, .doc): ").strip()
    while not os.path.isfile(cv_path):
        cv_path = input("File not found. Enter a valid path: ").strip()

    # Job links
    print("\nEnter job posting URLs (one per line, empty line to finish):")
    job_links = []
    while True:
        link = input("  > ").strip()
        if not link:
            break
        job_links.append(link)

    if not job_links:
        print("No job links provided. Exiting.")
        return

    print(f"\nRunning {agent_mode.upper()} agent...")
    print("-" * 60)

    if agent_mode == "react":
        result = run_react(cv_path, job_links)
    else:
        result = run_rewoo(cv_path, job_links)

    print("\n" + "=" * 60)
    print("  RESULT")
    print("=" * 60)
    print(result)

    # Option to save result
    save = input("\nSave result to file? [y/N]: ").strip().lower()
    if save == "y":
        output_path = input("Enter output file path [result.txt]: ").strip() or "result.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Result saved to {output_path}")


def cli_args_mode():
    """Parse command-line arguments and run the agent."""
    parser = argparse.ArgumentParser(
        description="Job Hunting Agent - Analyze your CV against job postings"
    )
    parser.add_argument(
        "--mode", choices=["react", "rewoo"], required=True,
        help="Agent mode: react or rewoo"
    )
    parser.add_argument(
        "--cv", required=True,
        help="Path to your CV file (.pdf, .docx, .doc)"
    )
    parser.add_argument(
        "--jobs", nargs="+", required=True,
        help="One or more job posting URLs"
    )
    parser.add_argument(
        "--output", default=None,
        help="Save result to this file path"
    )
    parser.add_argument(
        "--langsmith", action="store_true", default=False,
        help="Enable LangSmith tracing (requires API key in .env)"
    )

    args = parser.parse_args()

    # Configure LangSmith
    _set_langsmith_tracing(args.langsmith)

    if not os.path.isfile(args.cv):
        print(f"Error: CV file not found: {args.cv}")
        return

    print(f"Running {args.mode.upper()} agent...")

    if args.mode == "react":
        result = run_react(args.cv, args.jobs)
    else:
        result = run_rewoo(args.cv, args.jobs)

    print("\n" + result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\nResult saved to {args.output}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cli_args_mode()
    else:
        interactive_mode()
