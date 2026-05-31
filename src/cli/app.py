"""
CryptoRecover CLI - AI-Enhanced Crypto Wallet Recovery Tool

A comprehensive command-line interface for recovering seedphrases,
passphrases, and passwords using AI-enhanced bruteforce techniques.
"""

import asyncio
import click
import json
import time
import sys
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

from ..core.bip39_engine import BIP39Engine, RecoveryContext
from ..ai.llm_providers import LLMProviderFactory, ProviderType
from ..ai.candidate_generator import LLMCandidateGenerator, MultiProviderConsensus
from ..bruteforce.enhanced_engine import (
    EnhancedBruteforceEngine, ValidationResult, RecoveryPhase
)
from ..wallets.registry import (
    get_all_wallets, get_wallets_by_type, get_wallets_supporting_coin,
    get_all_auth_methods, WalletType
)

console = Console()


def print_banner():
    """Print the application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ██████╗██████╗ ██╗   ██╗███████╗██████╗ ███████╗███████╗ ██████╗  ║
║  ██╔════╝██╔══██╗╚██╗ ██╔╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔═══██╗ ║
║  ██║     ██████╔╝ ╚████╔╝ █████╗  ██████╔╝███████╗█████╗  ██║   ██║ ║
║  ██║     ██╔══██╗  ╚██╔╝  ██╔══╝  ██╔═══╝ ╚════██║██╔══╝  ██║   ██║ ║
║  ╚██████╗██║  ██║   ██║   ███████╗██║     ███████║███████╗╚██████╔╝ ║
║   ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝     ╚══════╝╚══════╝ ╚═════╝  ║
║                                                                      ║
║          AI-Enhanced Crypto Wallet Recovery Tool v1.0.0              ║
║          "Reimagine Bruteforce. Invent the Future."                  ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")


# ============================================================
# CLI Commands
# ============================================================

@click.group()
@click.version_option(version="1.0.0", prog_name="cryptorecover")
def cli():
    """CryptoRecover - AI-Enhanced Crypto Wallet Recovery Tool"""
    pass


@cli.command()
def wallets():
    """List all supported crypto wallets."""
    print_banner()
    all_wallets = get_all_wallets()

    # Group by type
    by_type = {}
    for wid, winfo in all_wallets.items():
        wtype = winfo.wallet_type.value
        if wtype not in by_type:
            by_type[wtype] = []
        by_type[wtype].append((wid, winfo))

    for wtype, wallets_list in by_type.items():
        table = Table(title=f"\n{wtype.upper()} Wallets", show_lines=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Coins", style="yellow", max_width=40)
        table.add_column("Seed Format", style="magenta")
        table.add_column("Words", style="blue")
        table.add_column("Passphrase", style="red")
        table.add_column("Auth Methods", style="white", max_width=35)

        for wid, winfo in wallets_list:
            table.add_row(
                wid,
                winfo.name,
                ", ".join(winfo.supported_coins[:5]) + ("..." if len(winfo.supported_coins) > 5 else ""),
                winfo.seed_format.value,
                "/".join(str(w) for w in winfo.word_counts),
                "✓" if winfo.supports_passphrase else "✗",
                ", ".join(m.value for m in winfo.auth_methods),
            )

        console.print(table)

    console.print(f"\n[bold green]Total: {len(all_wallets)} wallets supported[/bold green]")


@cli.command()
def auth_methods():
    """List all authentication methods used by crypto wallets."""
    print_banner()
    methods = get_all_auth_methods()

    table = Table(title="Authentication Methods", show_lines=True)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")

    for m in methods:
        table.add_row(m["id"], m["name"], m["description"])

    console.print(table)


@cli.command()
def providers():
    """List all available AI/LLM providers."""
    print_banner()
    provider_list = LLMProviderFactory.list_providers()

    # Group by type
    by_type = {}
    for p in provider_list:
        ptype = p["type"]
        if ptype not in by_type:
            by_type[ptype] = []
        by_type[ptype].append(p)

    for ptype, provs in by_type.items():
        table = Table(title=f"\n{ptype.upper()} Providers", show_lines=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Base URL", style="yellow")
        table.add_column("Default Model", style="magenta")
        table.add_column("API Key Required", style="red")
        table.add_column("OpenAI Compatible", style="blue")

        for p in provs:
            table.add_row(
                p["id"],
                p["name"],
                p["base_url"],
                p["default_model"],
                "Yes" if p["requires_api_key"] else "No",
                "✓" if p["openai_compatible"] else "✗",
            )

        console.print(table)

    console.print(f"\n[bold green]Total: {len(provider_list)} AI providers supported[/bold green]")


@cli.command()
@click.option("--detect", is_flag=True, help="Auto-detect running local LLM providers")
def detect_local(detect):
    """Detect locally running AI providers."""
    print_banner()

    if detect:
        console.print("\n[yellow]Scanning for local LLM providers...[/yellow]")
        results = LLMProviderFactory.detect_local_providers()

        table = Table(title="Local Provider Detection Results")
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="green")

        for name, running in results.items():
            status = "[green]✓ Running[/green]" if running else "[red]✗ Not Running[/red]"
            table.add_row(name, status)

        console.print(table)
    else:
        console.print("[yellow]Use --detect flag to scan for local providers[/yellow]")


@cli.command()
@click.option("--provider", "-p", default="ollama", help="AI provider to use")
@click.option("--api-key", "-k", default=None, help="API key for cloud providers")
@click.option("--model", "-m", default=None, help="Model to use (overrides default)")
@click.option("--words", "-w", default=12, type=int, help="Number of words in seedphrase")
@click.option("--known", "-kn", default=None, help="Known words as position:word pairs (e.g., '0:abandon 3:ability')")
@click.option("--approximate", "-a", default=None, help="Approximate words as position:word pairs")
@click.option("--address", "-addr", default=None, help="Target Bitcoin address")
@click.option("--passphrase-hint", "-ph", default=None, help="Hint about the passphrase")
@click.option("--wallet", "-wl", default=None, help="Wallet type (e.g., metamask, ledger_nano_x)")
@click.option("--days-since", "-d", default=None, type=int, help="Days since you last saw the seedphrase")
@click.option("--notes", "-n", default=None, help="Any additional notes about the seedphrase")
@click.option("--max-attempts", default=1000000, type=int, help="Maximum number of candidates to try")
def recover(provider, api_key, model, words, known, approximate, address,
            passphrase_hint, wallet, days_since, notes, max_attempts):
    """Start an AI-enhanced seedphrase recovery session."""
    print_banner()

    console.print(Panel(
        "[bold cyan]AI-Enhanced Seedphrase Recovery[/bold cyan]\n\n"
        "This tool uses advanced AI and novel bruteforce techniques to recover\n"
        "lost or partially-remembered seedphrases. The recovery process uses\n"
        "5 phases:\n\n"
        "  [green]Phase 1:[/green] LLM-Guided Search (AI predicts likely words)\n"
        "  [green]Phase 2:[/green] Cognitive Graph Traversal (memory modeling)\n"
        "  [green]Phase 3:[/green] Semantic Cluster Search (meaning-based)\n"
        "  [green]Phase 4:[/green] Probabilistic Ordered Search\n"
        "  [green]Phase 5:[/green] Exhaustive Brute Force (last resort)\n",
        title="Recovery Engine",
        border_style="cyan",
    ))

    # Parse known words
    known_words = {}
    if known:
        for pair in known.split():
            pos, word = pair.split(":")
            known_words[int(pos)] = word.strip().lower()

    # Parse approximate words
    approx_words = {}
    if approximate:
        for pair in approximate.split():
            pos, word = pair.split(":")
            approx_words[int(pos)] = word.strip().lower()

    # Determine missing positions
    missing = [i for i in range(words) if i not in known_words]

    # Build target addresses
    target_addresses = []
    if address:
        target_addresses.append(address)

    # Build recovery context
    context = RecoveryContext(
        total_words=words,
        known_words=known_words,
        missing_positions=missing,
        approximate_words=approx_words,
        target_addresses=target_addresses,
        passphrase_hint=passphrase_hint,
        time_since_exposure=days_since,
        user_notes=notes,
    )

    # Display recovery context
    context_table = Table(title="Recovery Context")
    context_table.add_column("Parameter", style="cyan")
    context_table.add_column("Value", style="green")

    context_table.add_row("Total Words", str(words))
    context_table.add_row("Known Words", str(len(known_words)))
    context_table.add_row("Missing Words", str(len(missing)))
    context_table.add_row("Approximate Words", str(len(approx_words)))
    context_table.add_row("Target Address", address or "Not provided")
    context_table.add_row("AI Provider", provider)
    context_table.add_row("Passphrase Hint", passphrase_hint or "None")
    context_table.add_row("Days Since Exposure", str(days_since) if days_since else "Unknown")

    console.print(context_table)

    # Initialize BIP-39 engine
    console.print("\n[yellow]Initializing BIP-39 engine...[/yellow]")
    try:
        bip39 = BIP39Engine()
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Install bip-utils: pip install bip-utils[/yellow]")
        return

    # Initialize AI provider
    console.print(f"[yellow]Connecting to AI provider: {provider}...[/yellow]")

    overrides = {}
    if api_key:
        overrides["api_key"] = api_key
    if model:
        overrides["model"] = model

    try:
        llm_provider = LLMProviderFactory.create(provider, **overrides)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    # Check provider health
    with console.status("Checking provider connectivity..."):
        is_healthy = asyncio.run(llm_provider.health_check())

    if is_healthy:
        console.print(f"[green]✓ {provider} is connected and ready[/green]")
    else:
        console.print(f"[yellow]⚠ {provider} might not be reachable. Continuing anyway...[/yellow]")

    # Initialize LLM candidate generator
    llm_generator = LLMCandidateGenerator(llm_provider, bip39)

    # Initialize enhanced bruteforce engine
    engine = EnhancedBruteforceEngine(bip39, llm_generator)

    # Show search space estimate
    estimate = engine.get_search_space_estimate(context)
    console.print(Panel(
        f"[bold]Search Space Analysis[/bold]\n\n"
        f"  Raw search space:         {estimate['raw_search_space']:,}\n"
        f"  Effective search space:   {estimate['effective_search_space']:,}\n"
        f"  Reduction factor:         {estimate['reduction_factor']:,.1f}x\n"
        f"  Estimated time:           {estimate['estimated_hours']:.2f} hours\n"
        f"  Has AI assistance:        {'✓' if estimate['has_llm'] else '✗'}\n"
        f"  Has approximate words:    {'✓' if estimate['has_approximate_words'] else '✗'}\n"
        f"  Checksum constrained:     {'✓' if estimate['checksum_constrained'] else '✗'}",
        title="Search Space Estimate",
        border_style="yellow",
    ))

    # Start recovery
    console.print("\n[bold green]Starting recovery...[/bold green]\n")

    phase_names = {
        RecoveryPhase.LLM_GUIDED: "🤖 LLM-Guided Search",
        RecoveryPhase.COGNITIVE: "🧠 Cognitive Graph Traversal",
        RecoveryPhase.SEMANTIC: "📝 Semantic Cluster Search",
        RecoveryPhase.PROBABILISTIC: "🎲 Probabilistic Ordered Search",
        RecoveryPhase.EXHAUSTIVE: "💪 Exhaustive Brute Force",
    }

    current_phase = [None]
    candidate_count = [0]
    valid_count = [0]
    start_time = time.time()

    def progress_callback(result: ValidationResult):
        candidate_count[0] += 1
        if result.is_valid_checksum:
            valid_count[0] += 1

        if result.phase != current_phase[0]:
            current_phase[0] = result.phase
            phase_name = phase_names.get(result.phase, str(result.phase))
            console.print(f"\n[bold cyan]▸ Entering Phase: {phase_name}[/bold cyan]")

        # Print progress periodically
        if candidate_count[0] % 100 == 0:
            elapsed = time.time() - start_time
            rate = candidate_count[0] / elapsed if elapsed > 0 else 0
            console.print(
                f"  [dim]Candidates: {candidate_count[0]:,} | "
                f"Valid checksums: {valid_count[0]:,} | "
                f"Rate: {rate:.0f}/sec | "
                f"Elapsed: {elapsed:.1f}s[/dim]"
            )

    try:
        result = asyncio.run(engine.recover(context, progress_callback, max_attempts))
    except KeyboardInterrupt:
        console.print("\n[yellow]Recovery interrupted by user.[/yellow]")
        stats = engine.get_stats()
        console.print(f"  Candidates tried: {stats['total_candidates']:,}")
        console.print(f"  Time elapsed: {stats['time_elapsed']:.1f}s")
        return

    elapsed = time.time() - start_time
    stats = engine.get_stats()

    if result:
        console.print(Panel(
            f"[bold green]🎉 SEEDPHRASE RECOVERED! 🎉[/bold green]\n\n"
            f"  [bold]Words:[/bold] {' '.join(result.words)}\n"
            f"  [bold]Confidence:[/bold] {result.confidence:.2f}\n"
            f"  [bold]Source:[/bold] {result.source}\n"
            f"  [bold]Time:[/bold] {elapsed:.1f} seconds\n"
            f"  [bold]Candidates tried:[/bold] {stats['total_candidates']:,}\n\n"
            f"[yellow]⚠ IMPORTANT: Store this seedphrase securely and never share it![/yellow]",
            title="Recovery Successful",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold red]Recovery Unsuccessful[/bold red]\n\n"
            f"  Candidates tried: {stats['total_candidates']:,}\n"
            f"  Valid checksums: {stats['valid_checksums']:,}\n"
            f"  Time elapsed: {elapsed:.1f}s\n\n"
            f"[yellow]Suggestions:[/yellow]\n"
            f"  • Try a different AI provider (use 'providers' command)\n"
            f"  • Add more approximate words to narrow the search\n"
            f"  • Increase --max-attempts for longer searches\n"
            f"  • Provide a target address with --address\n"
            f"  • Try multiple providers with consensus mode",
            title="Recovery Result",
            border_style="red",
        ))


@cli.command()
@click.option("--providers-list", "-p", default="ollama", help="Comma-separated list of providers for consensus")
@click.option("--api-keys", "-k", default=None, help="Comma-separated API keys (in same order as providers)")
@click.option("--words", "-w", default=12, type=int, help="Number of words in seedphrase")
@click.option("--approximate", "-a", default=None, help="Approximate words as position:word pairs")
@click.option("--address", "-addr", default=None, help="Target Bitcoin address")
@click.option("--days-since", "-d", default=None, type=int, help="Days since you last saw the seedphrase")
def consensus(providers_list, api_keys, words, approximate, address, days_since):
    """Use multiple AI providers with consensus voting for higher accuracy."""
    print_banner()

    console.print(Panel(
        "[bold cyan]Multi-Provider Consensus Recovery[/bold cyan]\n\n"
        "This mode queries multiple AI providers simultaneously and uses\n"
        "consensus voting to improve suggestion quality. Words suggested\n"
        "by multiple providers get boosted confidence scores.\n",
        title="Consensus Mode",
        border_style="magenta",
    ))

    # Parse providers
    provider_names = [p.strip() for p in providers_list.split(",")]
    keys = api_keys.split(",") if api_keys else [None] * len(provider_names)

    if len(keys) < len(provider_names):
        keys.extend([None] * (len(provider_names) - len(keys)))

    # Initialize BIP-39 engine
    bip39 = BIP39Engine()

    # Initialize providers
    llm_providers = []
    for name, key in zip(provider_names, keys):
        try:
            overrides = {}
            if key:
                overrides["api_key"] = key
            provider = LLMProviderFactory.create(name, **overrides)
            llm_providers.append(provider)
            console.print(f"[green]✓ {name} initialized[/green]")
        except ValueError as e:
            console.print(f"[red]✗ {name}: {e}[/red]")

    if not llm_providers:
        console.print("[red]No providers available. Aborting.[/red]")
        return

    # Initialize consensus engine
    consensus_engine = MultiProviderConsensus(llm_providers, bip39)

    # Parse approximate words
    approx_words = {}
    if approximate:
        for pair in approximate.split():
            pos, word = pair.split(":")
            approx_words[int(pos)] = word.strip().lower()

    missing = [i for i in range(words) if i not in approx_words]

    # Build context
    context = RecoveryContext(
        total_words=words,
        known_words={},
        missing_positions=missing,
        approximate_words=approx_words,
        target_addresses=[address] if address else [],
        time_since_exposure=days_since,
    )

    # Get consensus suggestions for each missing position
    console.print("\n[bold yellow]Querying multiple providers for consensus...[/bold yellow]\n")

    for pos in missing[:5]:  # Limit to first 5 positions
        with console.status(f"Getting suggestions for position {pos}..."):
            suggestions = asyncio.run(
                consensus_engine.suggest_with_consensus(context, pos, top_k=10)
            )

        if suggestions:
            table = Table(title=f"Consensus Suggestions for Position {pos}")
            table.add_column("Word", style="cyan")
            table.add_column("Confidence", style="green")
            table.add_column("Providers", style="yellow")
            table.add_column("Reasoning", style="white", max_width=50)

            for s in suggestions:
                table.add_row(
                    s.word,
                    f"{s.confidence:.2f}",
                    s.provider,
                    s.reasoning[:80] + "..." if len(s.reasoning) > 80 else s.reasoning,
                )

            console.print(table)
        else:
            console.print(f"[yellow]No suggestions for position {pos}[/yellow]")


@cli.command()
@click.option("--provider", "-p", default="ollama", help="AI provider to use")
@click.option("--api-key", "-k", default=None, help="API key")
@click.option("--hints", "-h", default=None, help="User hints as key:value pairs (e.g., 'name:John pet:Fluffy year:2019')")
@click.option("--top-k", "-t", default=50, type=int, help="Number of password candidates")
def password(provider, api_key, hints, top_k):
    """Generate likely password/passphrase candidates using AI."""
    print_banner()

    # Parse hints
    user_hints = {}
    if hints:
        for pair in hints.split():
            key, value = pair.split(":", 1)
            user_hints[key.strip()] = value.strip()

    if not user_hints:
        console.print("[yellow]No hints provided. Please use --hints to provide context.[/yellow]")
        console.print("[dim]Example: --hints 'name:John pet:Fluffy hobby:gaming year:2019 birthday:jan15'[/dim]")
        return

    # Display hints
    table = Table(title="User Hints")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    for k, v in user_hints.items():
        table.add_row(k, v)
    console.print(table)

    # Initialize provider
    overrides = {}
    if api_key:
        overrides["api_key"] = api_key

    try:
        llm_provider = LLMProviderFactory.create(provider, **overrides)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    # Initialize engine
    bip39 = BIP39Engine()
    generator = LLMCandidateGenerator(llm_provider, bip39)

    # Generate candidates
    console.print(f"\n[yellow]Generating password candidates using {provider}...[/yellow]")

    candidates = asyncio.run(generator.generate_password_candidates(user_hints, top_k))

    if candidates:
        table = Table(title="Password Candidates")
        table.add_column("#", style="dim")
        table.add_column("Password", style="cyan bold")
        table.add_column("Confidence", style="green")
        table.add_column("Bar", style="blue")

        for i, (pw, conf) in enumerate(candidates, 1):
            bar = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))
            table.add_row(str(i), pw, f"{conf:.2f}", bar)

        console.print(table)
    else:
        console.print("[yellow]No candidates generated. Try different hints or provider.[/yellow]")


@cli.command()
def interactive():
    """Start an interactive recovery session with step-by-step guidance."""
    print_banner()

    console.print(Panel(
        "[bold cyan]Interactive Recovery Session[/bold cyan]\n\n"
        "This wizard will guide you through the recovery process step by step.\n"
        "You'll be asked about your wallet, what you remember, and which\n"
        "AI provider to use.\n",
        title="Welcome",
        border_style="green",
    ))

    # Step 1: Wallet type
    console.print("\n[bold]Step 1: What type of wallet are you recovering?[/bold]")
    console.print("  1. Hardware wallet (Ledger, Trezor, etc.)")
    console.print("  2. Software wallet (MetaMask, Trust Wallet, etc.)")
    console.print("  3. Exchange account (Binance, Coinbase, etc.)")
    console.print("  4. Don't know / Other")

    wallet_choice = Prompt.ask("Select", choices=["1", "2", "3", "4"], default="2")

    wallet_type_map = {"1": "hardware", "2": "software", "3": "exchange", "4": "unknown"}
    selected_type = wallet_type_map[wallet_choice]

    # Step 2: What you remember
    console.print("\n[bold]Step 2: What do you remember about your seedphrase?[/bold]")
    word_count = Prompt.ask("Number of words", choices=["12", "15", "18", "21", "24"], default="12")

    known = Prompt.ask("Do you know any exact words? (e.g., '0:abandon 5:crane')", default="")
    approx = Prompt.ask("Do you remember any words approximately? (e.g., '3:ocean 7:garden')", default="")

    # Step 3: AI Provider
    console.print("\n[bold]Step 3: Choose your AI provider[/bold]")
    console.print("  [dim]Local providers (free, private):[/dim]")
    console.print("    ollama    - Ollama (recommended for local)")
    console.print("    lm-studio - LM Studio")
    console.print("    llama-cpp - llama.cpp server")
    console.print("  [dim]Cloud providers (fast, powerful):[/dim]")
    console.print("    openai    - OpenAI GPT-4o")
    console.print("    deepseek  - DeepSeek (cheapest)")
    console.print("    groq      - Groq (fastest)")
    console.print("    anthropic - Anthropic Claude")
    console.print("    openrouter- OpenRouter (access to all models)")

    provider = Prompt.ask("Select provider", default="ollama")
    api_key = Prompt.ask("API key (leave empty for local providers)", default="")

    # Step 4: Target info
    console.print("\n[bold]Step 4: Target information (optional but helpful)[/bold]")
    address = Prompt.ask("Known wallet address (if any)", default="")
    days_since = Prompt.ask("How many days since you last saw the seedphrase?", default="365")
    notes = Prompt.ask("Any additional notes or hints?", default="")

    # Step 5: Confirm and start
    console.print("\n[bold]Step 5: Confirm and start recovery[/bold]")
    console.print(f"  Wallet type: {selected_type}")
    console.print(f"  Word count: {word_count}")
    console.print(f"  Known words: {known or 'None'}")
    console.print(f"  Approximate words: {approx or 'None'}")
    console.print(f"  AI provider: {provider}")
    console.print(f"  Target address: {address or 'Not provided'}")

    if not Confirm.ask("\nStart recovery?", default=True):
        console.print("[yellow]Recovery cancelled.[/yellow]")
        return

    # Build and execute recovery
    from click.testing import CliRunner
    runner = CliRunner()

    args = [
        "--provider", provider,
        "--words", word_count,
        "--max-attempts", "1000000",
    ]

    if known:
        args.extend(["--known", known])
    if approx:
        args.extend(["--approximate", approx])
    if address:
        args.extend(["--address", address])
    if api_key:
        args.extend(["--api-key", api_key])
    if days_since:
        args.extend(["--days-since", days_since])
    if notes:
        args.extend(["--notes", notes])

    # Run the recover command
    recover_args = {k: v for k, v in zip(args[::2], args[1::2])}
    # Direct call to recover function
    console.print("\n[bold green]Starting recovery...[/bold green]")
    asyncio.run(_run_interactive_recovery(
        provider, api_key or None, int(word_count),
        known, approx, address, int(days_since), notes
    ))


async def _run_interactive_recovery(provider, api_key, words, known_str, approx_str,
                                      address, days_since, notes):
    """Run the actual recovery from interactive mode."""
    bip39 = BIP39Engine()

    # Parse known words
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

    missing = [i for i in range(words) if i not in known_words]

    context = RecoveryContext(
        total_words=words,
        known_words=known_words,
        missing_positions=missing,
        approximate_words=approx_words,
        target_addresses=[address] if address else [],
        time_since_exposure=days_since,
        user_notes=notes or None,
    )

    # Initialize provider
    overrides = {}
    if api_key:
        overrides["api_key"] = api_key

    try:
        llm_provider = LLMProviderFactory.create(provider, **overrides)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    llm_generator = LLMCandidateGenerator(llm_provider, bip39)
    engine = EnhancedBruteforceEngine(bip39, llm_generator)

    # Show estimate
    estimate = engine.get_search_space_estimate(context)
    console.print(f"\n[cyan]Search space: {estimate['effective_search_space']:,} candidates[/cyan]")
    console.print(f"[cyan]Estimated time: {estimate['estimated_hours']:.2f} hours[/cyan]")

    start_time = time.time()
    count = [0]

    def callback(result: ValidationResult):
        count[0] += 1
        if count[0] % 50 == 0:
            elapsed = time.time() - start_time
            rate = count[0] / elapsed if elapsed > 0 else 0
            console.print(
                f"  [dim]Checked: {count[0]:,} | Rate: {rate:.0f}/sec | "
                f"Elapsed: {elapsed:.1f}s[/dim]"
            )

    result = await engine.recover(context, callback)

    elapsed = time.time() - start_time

    if result:
        console.print(Panel(
            f"[bold green]🎉 SEEDPHRASE RECOVERED! 🎉[/bold green]\n\n"
            f"  {' '.join(result.words)}\n\n"
            f"  Time: {elapsed:.1f}s | Source: {result.source}\n\n"
            f"[yellow]⚠ Store this securely and never share it![/yellow]",
            title="Success",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold red]Recovery Unsuccessful[/bold red]\n\n"
            f"  Candidates: {count[0]:,} | Time: {elapsed:.1f}s\n\n"
            f"Try: different provider, more approximate words, or target address.",
            title="Result",
            border_style="red",
        ))


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
