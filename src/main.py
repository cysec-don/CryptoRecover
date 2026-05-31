"""
CryptoRecover - AI-Enhanced Crypto Wallet Recovery Application

Entry point for the application.
"""

import sys
import asyncio


def main():
    """Main entry point for CryptoRecover."""
    if len(sys.argv) > 1 and sys.argv[1] == "--tui":
        # Launch TUI
        from .gui.tui import run_tui
        run_tui()
    else:
        # Launch CLI
        from .cli.app import main as cli_main
        cli_main()


def run_cli():
    """Launch CLI directly."""
    from .cli.app import main
    main()


def run_tui():
    """Launch TUI directly."""
    from .gui.tui import run_tui as _run_tui
    _run_tui()


if __name__ == "__main__":
    main()
