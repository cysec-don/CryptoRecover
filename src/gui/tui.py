"""
CryptoRecover TUI - Terminal User Interface using Textual.

A rich, interactive terminal UI for the crypto wallet recovery application.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Button, Input, Select, Static, Label, DataTable
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
import asyncio

from ..core.bip39_engine import BIP39Engine, RecoveryContext
from ..ai.llm_providers import LLMProviderFactory, ProviderType
from ..ai.candidate_generator import LLMCandidateGenerator
from ..bruteforce.enhanced_engine import EnhancedBruteforceEngine, RecoveryPhase


BANNER = """
[bold cyan]
  ██████╗██████╗ ██╗   ██╗███████╗██████╗ ███████╗███████╗ ██████╗
 ██╔════╝██╔══██╗╚██╗ ██╔╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔═══██╗
 ██║     ██████╔╝ ╚████╔╝ █████╗  ██████╔╝███████╗█████╗  ██║   ██║
 ██║     ██╔══██╗  ╚██╔╝  ██╔══╝  ██╔═══╝ ╚════██║██╔══╝  ██║   ██║
 ╚██████╗██║  ██║   ██║   ███████╗██║     ███████║███████╗╚██████╔╝
  ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝     ╚══════╝╚══════╝ ╚═════╝
[/bold cyan]
 [bold]AI-Enhanced Crypto Wallet Recovery Tool v1.0.0[/bold]
"""


class CryptoRecoverApp(App):
    """The main CryptoRecover TUI application."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #main-container {
        layout: horizontal;
        height: 1fr;
    }

    #sidebar {
        width: 30;
        dock: left;
        border-right: solid green;
        padding: 1;
    }

    #content {
        padding: 1;
        height: 1fr;
    }

    .panel {
        border: solid cyan;
        padding: 1;
        margin: 1;
    }

    Button {
        margin: 1;
        width: 100%;
    }

    Input {
        margin: 1 0;
    }

    Select {
        margin: 1 0;
    }

    #status-bar {
        dock: bottom;
        height: 3;
        background: $surface;
        padding: 0 1;
    }

    #progress-info {
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "start_recovery", "Recover"),
        Binding("p", "show_providers", "Providers"),
        Binding("w", "show_wallets", "Wallets"),
        Binding("d", "detect_local", "Detect Local"),
    ]

    TITLE = "CryptoRecover - AI-Enhanced Wallet Recovery"

    recovery_status: reactive[str] = reactive("Ready")
    current_phase: reactive[str] = reactive("Idle")
    candidates_checked: reactive[int] = reactive(0)

    def __init__(self):
        super().__init__()
        self.bip39 = BIP39Engine()
        self.llm_provider = None
        self.engine = None
        self._recovery_task = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main-container"):
            with Vertical(id="sidebar"):
                yield Static(BANNER)
                yield Label("Provider:")
                yield Select(
                    [(p["name"], p["id"]) for p in LLMProviderFactory.list_providers()],
                    value="ollama",
                    id="provider-select",
                )
                yield Label("API Key:")
                yield Input(placeholder="Leave empty for local providers", id="api-key-input", password=True)
                yield Label("Word Count:")
                yield Select(
                    [("12 words", 12), ("15 words", 15), ("18 words", 18),
                     ("21 words", 21), ("24 words", 24)],
                    value=12,
                    id="word-count-select",
                )
                yield Label("Known Words:")
                yield Input(placeholder="e.g., 0:abandon 5:crane", id="known-words-input")
                yield Label("Approximate Words:")
                yield Input(placeholder="e.g., 3:ocean 7:garden", id="approx-words-input")
                yield Label("Target Address:")
                yield Input(placeholder="Bitcoin/Ethereum address", id="address-input")
                yield Label("Days Since Exposure:")
                yield Input(placeholder="365", id="days-input")
                yield Button("🚀 Start Recovery", variant="success", id="start-btn")
                yield Button("🔍 Detect Local LLMs", variant="primary", id="detect-btn")
                yield Button("📋 List Wallets", variant="default", id="wallets-btn")
                yield Button("🤖 List AI Providers", variant="default", id="providers-btn")

            with VerticalScroll(id="content"):
                yield Static(
                    "[bold cyan]Welcome to CryptoRecover[/bold cyan]\n\n"
                    "This tool uses AI-enhanced bruteforce techniques to recover\n"
                    "lost or partially-remembered crypto wallet seedphrases.\n\n"
                    "[bold]5-Phase Recovery Strategy:[/bold]\n"
                    "  🤖 Phase 1: LLM-Guided Search\n"
                    "  🧠 Phase 2: Cognitive Graph Traversal\n"
                    "  📝 Phase 3: Semantic Cluster Search\n"
                    "  🎲 Phase 4: Probabilistic Ordered Search\n"
                    "  💪 Phase 5: Exhaustive Brute Force\n\n"
                    "[bold]Getting Started:[/bold]\n"
                    "  1. Select an AI provider from the sidebar\n"
                    "  2. Enter any known or approximate words\n"
                    "  3. Click 'Start Recovery' to begin\n\n"
                    "[dim]Press 'p' for providers, 'w' for wallets, 'd' to detect local LLMs[/dim]",
                    id="main-info",
                )

        with Horizontal(id="status-bar"):
            yield Label("Status: Ready", id="status-label")
            yield Label("Phase: Idle", id="phase-label")
            yield Label("Checked: 0", id="count-label")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-btn":
            self.action_start_recovery()
        elif event.button.id == "detect-btn":
            self.action_detect_local()
        elif event.button.id == "wallets-btn":
            self.action_show_wallets()
        elif event.button.id == "providers-btn":
            self.action_show_providers()

    def _watch_recovery_status(self, status: str) -> None:
        self.query_one("#status-label", Label).update(f"Status: {status}")

    def _watch_current_phase(self, phase: str) -> None:
        self.query_one("#phase-label", Label).update(f"Phase: {phase}")

    def _watch_candidates_checked(self, count: int) -> None:
        self.query_one("#count-label", Label).update(f"Checked: {count:,}")

    def action_start_recovery(self) -> None:
        """Start the recovery process."""
        provider_id = self.query_one("#provider-select", Select).value
        api_key = self.query_one("#api-key-input", Input).value or None
        word_count = self.query_one("#word-count-select", Select).value
        known_str = self.query_one("#known-words-input", Input).value
        approx_str = self.query_one("#approx-words-input", Input).value
        address = self.query_one("#address-input", Input).value
        days_str = self.query_one("#days-input", Input).value or "365"

        # Parse inputs
        known_words = {}
        if known_str:
            for pair in known_str.split():
                if ":" in pair:
                    pos, word = pair.split(":", 1)
                    known_words[int(pos)] = word.strip().lower()

        approx_words = {}
        if approx_str:
            for pair in approx_str.split():
                if ":" in pair:
                    pos, word = pair.split(":", 1)
                    approx_words[int(pos)] = word.strip().lower()

        missing = [i for i in range(word_count) if i not in known_words]

        context = RecoveryContext(
            total_words=word_count,
            known_words=known_words,
            missing_positions=missing,
            approximate_words=approx_words,
            target_addresses=[address] if address else [],
            time_since_exposure=int(days_str) if days_str.isdigit() else 365,
        )

        # Initialize provider
        try:
            overrides = {}
            if api_key:
                overrides["api_key"] = api_key
            self.llm_provider = LLMProviderFactory.create(provider_id, **overrides)
        except ValueError as e:
            self.query_one("#main-info", Static).update(
                f"[red]Error: {e}[/red]"
            )
            return

        llm_generator = LLMCandidateGenerator(self.llm_provider, self.bip39)
        self.engine = EnhancedBruteforceEngine(self.bip39, llm_generator)

        # Show search space estimate
        estimate = self.engine.get_search_space_estimate(context)
        self.query_one("#main-info", Static).update(
            f"[bold cyan]Recovery Started[/bold cyan]\n\n"
            f"Provider: {provider_id}\n"
            f"Missing words: {len(missing)}\n"
            f"Search space: {estimate['effective_search_space']:,}\n"
            f"Estimated time: {estimate['estimated_hours']:.2f} hours\n\n"
            f"[green]Running...[/green]"
        )

        self.recovery_status = "Running"
        self._recovery_task = asyncio.create_task(
            self._run_recovery(context)
        )

    async def _run_recovery(self, context: RecoveryContext) -> None:
        """Run the recovery in an async task."""
        phase_names = {
            RecoveryPhase.LLM_GUIDED: "🤖 LLM-Guided",
            RecoveryPhase.COGNITIVE: "🧠 Cognitive",
            RecoveryPhase.SEMANTIC: "📝 Semantic",
            RecoveryPhase.PROBABILISTIC: "🎲 Probabilistic",
            RecoveryPhase.EXHAUSTIVE: "💪 Exhaustive",
        }

        def callback(result):
            self.candidates_checked += 1
            if result.phase in phase_names:
                self.current_phase = phase_names[result.phase]

        result = await self.engine.recover(context, callback)

        if result:
            self.recovery_status = "Found!"
            self.query_one("#main-info", Static).update(
                f"[bold green]🎉 SEEDPHRASE RECOVERED! 🎉[/bold green]\n\n"
                f"{' '.join(result.words)}\n\n"
                f"Source: {result.source}\n"
                f"Confidence: {result.confidence:.2f}\n\n"
                f"[yellow]⚠ Store this securely![/yellow]"
            )
        else:
            self.recovery_status = "Failed"
            self.query_one("#main-info", Static).update(
                f"[bold red]Recovery Unsuccessful[/bold red]\n\n"
                f"Try: different provider, more hints, or target address."
            )

    def action_detect_local(self) -> None:
        """Detect local LLM providers."""
        results = LLMProviderFactory.detect_local_providers()
        lines = ["[bold cyan]Local Provider Detection[/bold cyan]\n"]
        for name, running in results.items():
            status = "[green]✓ Running[/green]" if running else "[red]✗ Not running[/red]"
            lines.append(f"  {name}: {status}")
        self.query_one("#main-info", Static).update("\n".join(lines))

    def action_show_wallets(self) -> None:
        """Show supported wallets."""
        from ..wallets.registry import get_all_wallets
        wallets = get_all_wallets()
        lines = [f"[bold cyan]Supported Wallets ({len(wallets)} total)[/bold cyan]\n"]

        # Group by type
        by_type = {}
        for wid, winfo in wallets.items():
            wtype = winfo.wallet_type.value
            if wtype not in by_type:
                by_type[wtype] = []
            by_type[wtype].append(winfo.name)

        for wtype, names in by_type.items():
            lines.append(f"\n[bold]{wtype.upper()}:[/bold]")
            for name in sorted(names):
                lines.append(f"  • {name}")

        self.query_one("#main-info", Static).update("\n".join(lines))

    def action_show_providers(self) -> None:
        """Show AI providers."""
        providers = LLMProviderFactory.list_providers()
        lines = [f"[bold cyan]AI/LLM Providers ({len(providers)} total)[/bold cyan]\n"]

        cloud = [p for p in providers if p["type"] == "cloud"]
        local = [p for p in providers if p["type"] == "local"]
        aggregator = [p for p in providers if p["type"] == "aggregator"]

        if cloud:
            lines.append("\n[bold]☁️ Cloud Providers:[/bold]")
            for p in cloud:
                lines.append(f"  • {p['id']}: {p['name']} (model: {p['default_model']})")

        if local:
            lines.append("\n[bold]🏠 Local Providers:[/bold]")
            for p in local:
                lines.append(f"  • {p['id']}: {p['name']} (port: {p['base_url'].split(':')[-1].split('/')[0]})")

        if aggregator:
            lines.append("\n[bold]🔀 Aggregators:[/bold]")
            for p in aggregator:
                lines.append(f"  • {p['id']}: {p['name']}")

        self.query_one("#main-info", Static).update("\n".join(lines))


def run_tui():
    """Launch the TUI application."""
    app = CryptoRecoverApp()
    app.run()
