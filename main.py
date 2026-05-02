import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "gui":
        # Remove "gui" from argv so Gradio doesn't see it
        share = "--share" in sys.argv
        sys.argv = [sys.argv[0]]
        from app.gui import launch_gui
        launch_gui(share=share)
    else:
        # CLI mode: pass remaining args (if any) or interactive
        if len(sys.argv) > 1 and sys.argv[1] != "gui":
            from app.cli import cli_args_mode
            cli_args_mode()
        else:
            from app.cli import interactive_mode
            interactive_mode()


if __name__ == "__main__":
    main()
