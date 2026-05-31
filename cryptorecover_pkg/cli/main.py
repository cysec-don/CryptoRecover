"""
CryptoRecover - Command Line Interface
========================================
Full-featured CLI for crypto wallet recovery operations.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

# Add parent to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.recovery_engine import (
    RecoveryEngine,
    RecoveryConfig,
    RecoveryResult,
    RecoveryType,
    RecoveryStatus,
    SeedStandard,
    RecoveryFlowOrchestrator,
    get_bip39_wordlist,
    validate_bip39_checksum,
    mnemonic_to_seed,
)
from wallets.wallet_database import (
    WALLETS,
    WalletInfo,
    SeedType,
    LoginTech,
    list_all_wallets,
    list_all_seed_types,
    list_all_login_techs,
    get_wallets_by_seed_type,
    get_wallets_by_coin,
    get_wallets_by_login_tech,
)
from utils.helpers import (
    format_time,
    format_number,
    estimate_recovery_time,
    calculate_seed_combinations,
    save_recovery_result,
    ensure_dirs,
    get_data_dir,
)


# ==============================================================================
# CLI PROGRESS CALLBACK
# ==============================================================================

def cli_progress_callback(progress: dict):
    """Display progress updates in the terminal"""
    status = progress.get("status", "unknown")
    attempts = progress.get("attempts", 0)
    elapsed = progress.get("time_elapsed", 0)
    speed = progress.get("attempts_per_second", 0)

    sys.stdout.write(
        f"\r  [{status.upper()}] Attempts: {format_number(attempts)} | "
        f"Speed: {speed:.0f}/s | Elapsed: {format_time(elapsed)}"
    )
    sys.stdout.flush()


# ==============================================================================
# CLI COMMANDS
# ==============================================================================

def cmd_list_wallets(args):
    """List all supported wallets"""
    print("\n" + "=" * 80)
    print("  SUPPORTED CRYPTO WALLETS DATABASE")
    print("=" * 80)

    filter_coin = getattr(args, 'coin', None)
    filter_seed = getattr(args, 'seed_type', None)
    filter_login = getattr(args, 'login_tech', None)

    wallets = list(WALLETS.values())

    if filter_coin:
        wallets = [w for w in wallets if any(filter_coin.upper() in c.upper() for c in w.supported_coins)]
        print(f"\n  Filtered by coin: {filter_coin}")

    if filter_seed:
        seed_enum = SeedType(filter_seed)
        wallets = [w for w in wallets if seed_enum in w.supported_seed_types]
        print(f"\n  Filtered by seed type: {filter_seed}")

    if filter_login:
        login_enum = LoginTech(filter_login)
        wallets = [w for w in wallets if login_enum in w.login_technologies]
        print(f"\n  Filtered by login tech: {filter_login}")

    for wallet in wallets:
        print(f"\n  {'─' * 76}")
        print(f"  Name: {wallet.name}")
        print(f"  Category: {', '.join(c.value for c in wallet.category)}")
        print(f"  Seed Types: {', '.join(s.value for s in wallet.supported_seed_types) or 'None (custodial)'}")
        print(f"  Seed Lengths: {', '.join(str(l) for l in wallet.seed_lengths) or 'N/A'}")
        print(f"  Passphrase Support: {'Yes' if wallet.supports_passphrase else 'No'}")
        print(f"  Login Technologies: {', '.join(t.value for t in wallet.login_technologies)}")
        print(f"  Derivation Paths: {', '.join(wallet.derivation_paths[:3])}")
        print(f"  Supported Coins: {', '.join(wallet.supported_coins[:5])}{'...' if len(wallet.supported_coins) > 5 else ''}")
        print(f"  Recovery Difficulty: {wallet.recovery_difficulty}")
        if wallet.wallet_file_format:
            print(f"  Wallet File: {wallet.wallet_file_format}")
        print(f"  Notes: {wallet.notes[:100]}{'...' if len(wallet.notes) > 100 else ''}")

    print(f"\n  Total wallets: {len(wallets)}")
    print("=" * 80 + "\n")


def cmd_list_login_techs(args):
    """List all login technologies"""
    from wallets.wallet_database import LOGIN_TECHNOLOGIES

    print("\n" + "=" * 80)
    print("  WALLET LOGIN TECHNOLOGIES")
    print("=" * 80)

    for tech, info in LOGIN_TECHNOLOGIES.items():
        print(f"\n  {'─' * 76}")
        print(f"  Name: {info['name']}")
        print(f"  Description: {info['description']}")
        if info.get('word_counts'):
            print(f"  Word Counts: {', '.join(str(w) for w in info['word_counts'])}")
        if info.get('standards'):
            print(f"  Standards: {', '.join(info['standards'])}")
        if info.get('recovery_tools'):
            print(f"  Recovery Tools: {', '.join(info['recovery_tools'])}")
        print(f"  Difficulty: {info['difficulty']}")

    print("\n" + "=" * 80 + "\n")


def cmd_recover_seed(args):
    """Recover missing seed phrase words"""
    print("\n" + "=" * 80)
    print("  SEED PHRASE RECOVERY")
    print("=" * 80)

    known_words = []
    missing_positions = []

    if args.mnemonic:
        parts = args.mnemonic.split()
        for i, part in enumerate(parts):
            if part == "?" or part == "???" or part == "*":
                missing_positions.append(i)
            else:
                known_words.append(part)
    elif args.known_words:
        known_words = args.known_words.split(",")
        if args.missing_positions:
            missing_positions = [int(p) for p in args.missing_positions.split(",")]
        else:
            print("  ERROR: --missing-positions is required when using --known-words")
            return
    else:
        print("  ERROR: Provide seed phrase with ? for missing words, or --known-words and --missing-positions")
        return

    seed_length = args.seed_length or (len(known_words) + len(missing_positions))

    print(f"\n  Seed Standard: {args.seed_standard}")
    print(f"  Seed Length: {seed_length} words")
    print(f"  Known Words: {len(known_words)}")
    print(f"  Missing Positions: {missing_positions}")

    wordlist = get_bip39_wordlist()
    total = calculate_seed_combinations(len(missing_positions), len(wordlist))
    print(f"  Total Combinations: {format_number(total)}")
    print(f"  Estimated Time: {estimate_recovery_time(total)}")

    if args.dry_run:
        print("\n  [DRY RUN] No actual recovery performed.")
        return

    if not args.skip_confirm:
        response = input("\n  Proceed with recovery? (y/N): ")
        if response.lower() != "y":
            print("  Recovery cancelled.")
            return

    config = RecoveryFlowOrchestrator.create_recovery_config(
        RecoveryType.SEED_PHRASE,
        seed_standard=SeedStandard(args.seed_standard),
        seed_length=seed_length,
        known_words=known_words,
        missing_word_positions=missing_positions,
        target_address=args.target_address,
        derivation_path=args.derivation_path,
        coin=args.coin,
        num_threads=args.threads,
        btcrecover_path=args.btcrecover,
        seedrecover_path=args.seedrecover,
        bitcoin_core_path=args.bitcoin_core,
        callback=cli_progress_callback,
    )

    print(f"\n  Starting recovery with {config.num_threads} threads...")
    print(f"  External tools: seedrecover={'Yes' if config.seedrecover_path else 'No'}, "
          f"btcrecover={'Yes' if config.btcrecover_path else 'No'}, "
          f"bitcoin-core={'Yes' if config.bitcoin_core_path else 'No'}")
    print()

    result = RecoveryFlowOrchestrator.run_recovery_flow(config)

    print()  # New line after progress
    _print_result(result)

    if args.save_result:
        path = save_recovery_result(result)
        print(f"  Result saved to: {path}")


def cmd_recover_passphrase(args):
    """Recover BIP39 passphrase"""
    print("\n" + "=" * 80)
    print("  PASSPHRASE RECOVERY (BIP39 25th Word)")
    print("=" * 80)

    if not args.mnemonic:
        print("  ERROR: --mnemonic is required for passphrase recovery")
        return

    known_words = args.mnemonic.split()
    print(f"\n  Seed Phrase: {args.mnemonic[:30]}... ({len(known_words)} words)")
    print(f"  Target Address: {args.target_address or 'Not specified'}")

    candidates = []
    if args.passphrase_list:
        candidates = args.passphrase_list.split(",")
    if args.passphrase_file:
        with open(args.passphrase_file, "r", encoding="utf-8", errors="ignore") as f:
            candidates.extend(line.strip() for line in f if line.strip())

    print(f"  Passphrase Candidates: {len(candidates)}")
    print(f"  Partial Passphrase: {args.partial_passphrase or 'None'}")

    if args.dry_run:
        print("\n  [DRY RUN] No actual recovery performed.")
        return

    config = RecoveryFlowOrchestrator.create_recovery_config(
        RecoveryType.PASSPHRASE,
        known_words=known_words,
        passphrase_candidates=candidates,
        partial_passphrase=args.partial_passphrase or "",
        target_address=args.target_address,
        derivation_path=args.derivation_path,
        coin=args.coin,
        num_threads=args.threads,
        seedrecover_path=args.seedrecover,
        bitcoin_core_path=args.bitcoin_core,
        callback=cli_progress_callback,
    )

    print(f"\n  Starting passphrase recovery...")
    print()

    result = RecoveryFlowOrchestrator.run_recovery_flow(config)

    print()
    _print_result(result)

    if args.save_result:
        path = save_recovery_result(result)
        print(f"  Result saved to: {path}")


def cmd_recover_password(args):
    """Recover wallet file password"""
    print("\n" + "=" * 80)
    print("  PASSWORD RECOVERY")
    print("=" * 80)

    if not args.wallet_file:
        print("  ERROR: --wallet-file is required for password recovery")
        return

    wallet_path = Path(args.wallet_file)
    if not wallet_path.exists():
        print(f"  ERROR: Wallet file not found: {args.wallet_file}")
        return

    print(f"\n  Wallet File: {args.wallet_file}")
    print(f"  File Size: {wallet_path.stat().st_size} bytes")

    candidates = []
    if args.password_list:
        candidates = args.password_list.split(",")
    if args.password_file:
        with open(args.password_file, "r", encoding="utf-8", errors="ignore") as f:
            candidates.extend(line.strip() for line in f if line.strip())

    print(f"  Password Candidates: {len(candidates)}")

    if args.dry_run:
        print("\n  [DRY RUN] No actual recovery performed.")
        return

    config = RecoveryFlowOrchestrator.create_recovery_config(
        RecoveryType.PASSWORD,
        wallet_file=args.wallet_file,
        password_candidates=candidates,
        password_dict_file=args.password_dict,
        num_threads=args.threads,
        btcrecover_path=args.btcrecover,
        callback=cli_progress_callback,
    )

    print(f"\n  Starting password recovery...")
    print(f"  External tool: btcrecover={'Yes' if config.btcrecover_path else 'No (built-in only)'}")
    print()

    result = RecoveryFlowOrchestrator.run_recovery_flow(config)

    print()
    _print_result(result)

    if args.save_result:
        path = save_recovery_result(result)
        print(f"  Result saved to: {path}")


def cmd_validate_seed(args):
    """Validate a seed phrase"""
    print("\n" + "=" * 80)
    print("  SEED PHRASE VALIDATION")
    print("=" * 80)

    words = args.mnemonic.split()
    print(f"\n  Words: {len(words)}")

    wordlist = get_bip39_wordlist()
    invalid_words = [w for w in words if w not in wordlist]
    if invalid_words:
        print(f"  Invalid BIP39 words found: {invalid_words}")
        print(f"  SUGGESTION: Check spelling. These might be the incorrect words.")

    if len(words) in [12, 15, 18, 21, 24]:
        is_valid = validate_bip39_checksum(words)
        print(f"  BIP39 Checksum: {'VALID ✓' if is_valid else 'INVALID ✗'}")
        if not is_valid:
            print(f"  One or more words may be incorrect or out of order.")
    else:
        print(f"  Warning: Non-standard word count ({len(words)}). BIP39 uses 12/15/18/21/24 words.")

    print("=" * 80 + "\n")


def cmd_generate_addresses(args):
    """Generate addresses from a seed phrase"""
    print("\n" + "=" * 80)
    print("  ADDRESS GENERATION")
    print("=" * 80)

    if not args.mnemonic:
        print("  ERROR: --mnemonic is required")
        return

    words = args.mnemonic.split()
    passphrase = args.passphrase or ""

    print(f"\n  Seed: {args.mnemonic[:30]}... ({len(words)} words)")
    print(f"  Passphrase: {'Yes' if passphrase else 'No'}")
    print(f"  Derivation Path: {args.derivation_path or 'Default'}")

    try:
        seed_bytes = mnemonic_to_seed(args.mnemonic, passphrase)
        seed_hex = seed_bytes.hex()
        print(f"\n  Master Seed (hex): {seed_hex[:32]}...{seed_hex[-32:]}")
        print(f"\n  NOTE: Full address generation requires bip32utils or hdwallet library.")
        print(f"  Install with: pip install bip32utils")
    except Exception as e:
        print(f"  Error: {e}")

    print("=" * 80 + "\n")


def cmd_interactive(args):
    """Launch interactive recovery wizard"""
    print("\n" + "=" * 80)
    print("  CryptoRecover - Interactive Recovery Wizard")
    print("=" * 80)
    print()
    print("  This wizard will guide you through the recovery process step by step.")
    print()

    # Step 1: What do you need to recover?
    print("  What do you need to recover?")
    print("  1. Missing words from a seed phrase")
    print("  2. BIP39 passphrase (25th word)")
    print("  3. Wallet file password")
    print("  4. Validate a seed phrase")
    print("  5. Generate addresses from a seed phrase")
    print("  6. List supported wallets")
    print("  7. List login technologies")
    print()

    choice = input("  Select option (1-7): ").strip()

    if choice == "1":
        _interactive_seed_recovery()
    elif choice == "2":
        _interactive_passphrase_recovery()
    elif choice == "3":
        _interactive_password_recovery()
    elif choice == "4":
        mnemonic = input("  Enter seed phrase: ").strip()
        cmd_validate_seed(argparse.Namespace(mnemonic=mnemonic))
    elif choice == "5":
        mnemonic = input("  Enter seed phrase: ").strip()
        passphrase = input("  Enter passphrase (or leave empty): ").strip()
        cmd_generate_addresses(argparse.Namespace(
            mnemonic=mnemonic, passphrase=passphrase, derivation_path=None
        ))
    elif choice == "6":
        cmd_list_wallets(argparse.Namespace(coin=None, seed_type=None, login_tech=None))
    elif choice == "7":
        cmd_list_login_techs(argparse.Namespace())
    else:
        print("  Invalid option.")


def _interactive_seed_recovery():
    """Interactive seed phrase recovery"""
    print("\n  ─── Seed Phrase Recovery Wizard ───\n")

    print("  Enter your seed phrase with ? for each missing/unknown word.")
    print("  Example: abandon ? ? about above absent absorb abstract absurd abuse access accident")
    mnemonic = input("\n  Seed phrase: ").strip()

    if not mnemonic:
        print("  No seed phrase entered. Exiting.")
        return

    target_address = input("  Target address (optional, press Enter to skip): ").strip() or None
    seed_standard = input("  Seed standard [BIP39/Electrum] (default: BIP39): ").strip() or "BIP39"

    threads = input("  Number of threads (default: auto): ").strip()
    threads = int(threads) if threads.isdigit() else 0

    args = argparse.Namespace(
        mnemonic=mnemonic,
        known_words=None,
        missing_positions=None,
        seed_length=None,
        seed_standard=seed_standard,
        target_address=target_address,
        derivation_path=None,
        coin="BTC",
        threads=threads,
        btcrecover=None,
        seedrecover=None,
        bitcoin_core=None,
        dry_run=False,
        skip_confirm=True,
        save_result=True,
    )
    cmd_recover_seed(args)


def _interactive_passphrase_recovery():
    """Interactive passphrase recovery"""
    print("\n  ─── Passphrase Recovery Wizard ───\n")

    mnemonic = input("  Enter your complete seed phrase: ").strip()
    if not mnemonic:
        print("  No seed phrase entered. Exiting.")
        return

    target_address = input("  Target address (required for verification): ").strip()
    if not target_address:
        print("  Target address is required for passphrase recovery. Exiting.")
        return

    has_candidates = input("  Do you have passphrase candidates? (y/N): ").strip().lower()
    passphrase_list = None
    partial_passphrase = None

    if has_candidates == "y":
        passphrase_list = input("  Enter candidates separated by commas: ").strip()
    else:
        partial_passphrase = input("  Enter partial passphrase hint (or press Enter): ").strip() or None

    args = argparse.Namespace(
        mnemonic=mnemonic,
        target_address=target_address,
        passphrase_list=passphrase_list,
        passphrase_file=None,
        partial_passphrase=partial_passphrase,
        derivation_path=None,
        coin="BTC",
        threads=0,
        seedrecover=None,
        bitcoin_core=None,
        dry_run=False,
        save_result=True,
    )
    cmd_recover_passphrase(args)


def _interactive_password_recovery():
    """Interactive password recovery"""
    print("\n  ─── Password Recovery Wizard ───\n")

    wallet_file = input("  Enter wallet file path: ").strip()
    if not wallet_file:
        print("  No wallet file entered. Exiting.")
        return

    has_candidates = input("  Do you have password candidates? (y/N): ").strip().lower()
    password_list = None
    password_dict = None

    if has_candidates == "y":
        password_list = input("  Enter candidates separated by commas: ").strip()
    else:
        dict_path = input("  Enter password dictionary file path (or press Enter): ").strip()
        if dict_path:
            password_dict = dict_path

    args = argparse.Namespace(
        wallet_file=wallet_file,
        password_list=password_list,
        password_file=None,
        password_dict=password_dict,
        threads=0,
        btcrecover=None,
        dry_run=False,
        save_result=True,
    )
    cmd_recover_password(args)


# ==============================================================================
# RESULT DISPLAY
# ==============================================================================

def _print_result(result: RecoveryResult):
    """Print recovery result in a formatted way"""
    print("\n" + "=" * 80)
    print("  RECOVERY RESULT")
    print("=" * 80)

    if result.success:
        print(f"\n  *** RECOVERY SUCCESSFUL ***\n")
        print(f"  Found: {result.found_value}")
        print(f"  Recovery Type: {result.recovery_type.value}")
        print(f"  Attempts: {format_number(result.attempts)}")
        print(f"  Time Elapsed: {format_time(result.time_elapsed)}")
        print(f"  Speed: {result.attempts_per_second:.1f} attempts/sec")
        if result.details:
            print(f"  Details:")
            for k, v in result.details.items():
                print(f"    {k}: {v}")
    else:
        print(f"\n  Recovery FAILED\n")
        print(f"  Status: {result.status.value}")
        print(f"  Error: {result.error_message or 'Unknown'}")
        print(f"  Attempts: {format_number(result.attempts)}")
        print(f"  Time Elapsed: {format_time(result.time_elapsed)}")

    print("\n" + "=" * 80 + "\n")


# ==============================================================================
# MAIN CLI ENTRY POINT
# ==============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser"""
    parser = argparse.ArgumentParser(
        prog="cryptorecover",
        description="CryptoRecover - Cryptocurrency Wallet Recovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all supported wallets
  cryptorecover list-wallets

  # Recover missing seed words (use ? for unknown words)
  cryptorecover recover-seed --mnemonic "abandon ? ? about above absent absorb abstract absurd abuse access accident"

  # Recover with target address verification
  cryptorecover recover-seed --mnemonic "abandon ? ? about above absent absorb abstract absurd abuse access accident" --target-address 1A1zP1...

  # Recover BIP39 passphrase
  cryptorecover recover-passphrase --mnemonic "abandon ability able..." --target-address 1A1zP1... --partial-passphrase "my"

  # Recover wallet password
  cryptorecover recover-password --wallet-file wallet.dat --password-list "password1,password2,password3"

  # Validate a seed phrase
  cryptorecover validate --mnemonic "abandon ability able about above absent absorb abstract absurd abuse access accident"

  # Interactive wizard mode
  cryptorecover interactive
        """
    )

    parser.add_argument("--version", action="version", version="CryptoRecover v1.0.0")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ─── list-wallets ───────────────────────────────────────────────────
    p_list = subparsers.add_parser("list-wallets", help="List all supported wallets")
    p_list.add_argument("--coin", help="Filter by coin (e.g., BTC, ETH)")
    p_list.add_argument("--seed-type", help="Filter by seed type (e.g., BIP39, Electrum)")
    p_list.add_argument("--login-tech", help="Filter by login technology")

    # ─── list-login-techs ───────────────────────────────────────────────
    subparsers.add_parser("list-login-techs", help="List all login technologies")

    # ─── recover-seed ──────────────────────────────────────────────────
    p_seed = subparsers.add_parser("recover-seed", help="Recover missing seed phrase words")
    p_seed.add_argument("--mnemonic", "-m", help="Seed phrase with ? for unknown words")
    p_seed.add_argument("--known-words", help="Known words, comma-separated")
    p_seed.add_argument("--missing-positions", help="Positions of missing words (0-indexed, comma-separated)")
    p_seed.add_argument("--seed-length", type=int, help="Expected seed length (12/24)")
    p_seed.add_argument("--seed-standard", default="BIP39", choices=["BIP39", "Electrum", "SLIP39", "Monero"])
    p_seed.add_argument("--target-address", "-a", help="Target address for verification")
    p_seed.add_argument("--derivation-path", help="BIP32 derivation path")
    p_seed.add_argument("--coin", default="BTC", help="Coin type (default: BTC)")
    p_seed.add_argument("--threads", "-t", type=int, default=0, help="Number of threads (0=auto)")
    p_seed.add_argument("--btcrecover", help="Path to btcrecover.py")
    p_seed.add_argument("--seedrecover", help="Path to seedrecover.py")
    p_seed.add_argument("--bitcoin-core", help="Path to bitcoin-cli")
    p_seed.add_argument("--dry-run", action="store_true", help="Show estimate without running")
    p_seed.add_argument("--skip-confirm", action="store_true", help="Skip confirmation prompt")
    p_seed.add_argument("--save-result", action="store_true", help="Save result to file")

    # ─── recover-passphrase ────────────────────────────────────────────
    p_pass = subparsers.add_parser("recover-passphrase", help="Recover BIP39 passphrase")
    p_pass.add_argument("--mnemonic", "-m", required=True, help="Complete seed phrase")
    p_pass.add_argument("--target-address", "-a", help="Target address for verification")
    p_pass.add_argument("--passphrase-list", help="Passphrase candidates, comma-separated")
    p_pass.add_argument("--passphrase-file", help="File with passphrase candidates")
    p_pass.add_argument("--partial-passphrase", help="Partial passphrase hint")
    p_pass.add_argument("--derivation-path", help="BIP32 derivation path")
    p_pass.add_argument("--coin", default="BTC", help="Coin type (default: BTC)")
    p_pass.add_argument("--threads", "-t", type=int, default=0, help="Number of threads")
    p_pass.add_argument("--seedrecover", help="Path to seedrecover.py")
    p_pass.add_argument("--bitcoin-core", help="Path to bitcoin-cli")
    p_pass.add_argument("--dry-run", action="store_true", help="Show estimate without running")
    p_pass.add_argument("--save-result", action="store_true", help="Save result to file")

    # ─── recover-password ──────────────────────────────────────────────
    p_pwd = subparsers.add_parser("recover-password", help="Recover wallet file password")
    p_pwd.add_argument("--wallet-file", "-w", required=True, help="Path to wallet file")
    p_pwd.add_argument("--password-list", help="Password candidates, comma-separated")
    p_pwd.add_argument("--password-file", help="File with password candidates")
    p_pwd.add_argument("--password-dict", help="Password dictionary file")
    p_pwd.add_argument("--threads", "-t", type=int, default=0, help="Number of threads")
    p_pwd.add_argument("--btcrecover", help="Path to btcrecover.py")
    p_pwd.add_argument("--dry-run", action="store_true", help="Show estimate without running")
    p_pwd.add_argument("--save-result", action="store_true", help="Save result to file")

    # ─── validate ──────────────────────────────────────────────────────
    p_val = subparsers.add_parser("validate", help="Validate a seed phrase")
    p_val.add_argument("--mnemonic", "-m", required=True, help="Seed phrase to validate")

    # ─── generate-addresses ────────────────────────────────────────────
    p_gen = subparsers.add_parser("generate-addresses", help="Generate addresses from seed")
    p_gen.add_argument("--mnemonic", "-m", required=True, help="Seed phrase")
    p_gen.add_argument("--passphrase", help="BIP39 passphrase")
    p_gen.add_argument("--derivation-path", help="BIP32 derivation path")

    # ─── interactive ───────────────────────────────────────────────────
    subparsers.add_parser("interactive", help="Launch interactive recovery wizard")

    return parser


def main():
    """Main CLI entry point"""
    ensure_dirs()

    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif getattr(args, 'verbose', False):
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Route to command
    if args.command == "list-wallets":
        cmd_list_wallets(args)
    elif args.command == "list-login-techs":
        cmd_list_login_techs(args)
    elif args.command == "recover-seed":
        cmd_recover_seed(args)
    elif args.command == "recover-passphrase":
        cmd_recover_passphrase(args)
    elif args.command == "recover-password":
        cmd_recover_password(args)
    elif args.command == "validate":
        cmd_validate_seed(args)
    elif args.command == "generate-addresses":
        cmd_generate_addresses(args)
    elif args.command == "interactive":
        cmd_interactive(args)
    else:
        parser.print_help()
        print("\n  Tip: Use 'cryptorecover interactive' for a guided recovery wizard.")


if __name__ == "__main__":
    main()
