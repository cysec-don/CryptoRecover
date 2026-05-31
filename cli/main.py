"""
CryptoRecover - Command Line Interface
========================================
Full-featured CLI for crypto wallet recovery operations.
Now powered by the advanced bruteforce engine with CPF, PVP, LWO, HCP,
SWP, AWD, CWP, EGS, and checkpoint/resume support.
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
from core.bruteforce_engine import (
    BruteforceEngine,
    BruteforceConfig,
    BruteforceResult,
    RecoveryMode,
    SearchStrategy,
)
from core.address_derivation import (
    AddressMatcher, AddressType, mnemonic_to_seed as mnemonic_to_seed_v2,
    generate_addresses,
)
from core.checksum_filter import find_valid_last_words
from core.candidate_generators import ContextualWordPredictor
from core.gpu_accelerator import detect_gpu_backends, get_cpu_info
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
    speed = progress.get("rate_per_second", 0) or progress.get("attempts_per_second", 0)
    found = progress.get("found", 0)

    sys.stdout.write(
        f"\r  [{status.upper()}] Attempts: {format_number(attempts)} | "
        f"Speed: {speed:.0f}/s | Elapsed: {format_time(elapsed)}"
        f"{' | Found: ' + str(found) if found else ''}"
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


def cmd_bruteforce(args):
    """Advanced bruteforce recovery using the new engine"""
    print("\n" + "=" * 80)
    print("  ADVANCED BRUTEFORCE RECOVERY ENGINE")
    print("  Techniques: CPF | PVP | LWO | HCP | SWP | AWD | CWP | EGS")
    print("=" * 80)

    if args.mode == "seed":
        _bruteforce_seed(args)
    elif args.mode == "passphrase":
        _bruteforce_passphrase(args)
    elif args.mode == "password":
        _bruteforce_password(args)
    else:
        print("  ERROR: Specify --mode seed|passphrase|password")
        return


def _bruteforce_seed(args):
    """Advanced seed phrase bruteforce"""
    known_words = []
    missing_positions = []

    if args.mnemonic:
        parts = args.mnemonic.split()
        for i, part in enumerate(parts):
            if part in ("?", "???", "*"):
                missing_positions.append(i)
            else:
                known_words.append(part)
    elif args.known_words:
        known_words = args.known_words.split(",")
        if args.missing_positions:
            missing_positions = [int(p) for p in args.missing_positions.split(",")]
        else:
            print("  ERROR: --missing-positions required with --known-words")
            return
    else:
        print("  ERROR: Provide --mnemonic with ? for unknown words")
        return

    seed_length = args.seed_length or (len(known_words) + len(missing_positions))
    num_missing = len(missing_positions)

    # Display analysis
    print(f"\n  Seed Length: {seed_length} words")
    print(f"  Missing Positions: {missing_positions} ({num_missing} words)")
    print(f"  Known Words: {len(known_words)}")

    # Check if last position is missing for LWO
    last_missing = (seed_length - 1) in missing_positions
    if last_missing and num_missing == 1:
        valid_words = find_valid_last_words(known_words, seed_length - 1)
        print(f"\n  [LWO] Last-Word Optimization: Only {len(valid_words)} valid candidates (vs 2048)")
        print(f"  [LWO] Speedup: {2048 // len(valid_words)}x")
    elif last_missing:
        lwo_factor = 128 if seed_length == 12 else 8
        total = 2048 ** (num_missing - 1) * lwo_factor
        print(f"\n  [HCP+LWO] Combined optimization: {format_number(total)} candidates")
        print(f"  [HCP+LWO] Speedup: {2048 // lwo_factor}x vs full enumeration")

    # Estimate time
    estimate = BruteforceEngine.estimate_recovery_time(
        num_missing, seed_length, last_missing,
        hash_rate=1500.0,
    )
    print(f"\n  Search Space: {format_number(estimate['total_candidates'])} total")
    print(f"  After Checksum Filter: {format_number(estimate['valid_after_checksum'])} valid")
    print(f"  Checksum Pruning: {estimate['checksum_pruning_ratio']}")
    print(f"  Estimated Time: {estimate['estimated_time']} (at {estimate['hash_rate_used']:.0f} H/s)")

    # Show available strategies
    strategies = BruteforceEngine.list_strategies(num_missing, seed_length, last_missing)
    print(f"\n  Available Strategies:")
    for s in strategies:
        marker = " <-- RECOMMENDED" if s['recommended'] else ""
        print(f"    - {s['name']}: {s['description']}{marker}")

    # Detect hardware
    print(f"\n  Hardware Detection:")
    cpu_info = get_cpu_info()
    print(f"    CPU: {cpu_info.device_name} ({cpu_info.compute_units} cores)")
    gpu_backends = detect_gpu_backends()
    if gpu_backends:
        for gpu in gpu_backends:
            print(f"    GPU: {gpu.device_name} ({gpu.estimated_hash_rate:.0f} H/s est.)")
    else:
        print(f"    GPU: None detected (install pyopencl for GPU support)")

    if args.dry_run:
        print("\n  [DRY RUN] No actual recovery performed.")
        return

    # Parse strategy
    strategy_map = {
        "auto": SearchStrategy.AUTO,
        "lwo": SearchStrategy.LWO,
        "hcp": SearchStrategy.HCP,
        "statistical": SearchStrategy.STATISTICAL,
        "full": SearchStrategy.FULL,
        "markov": SearchStrategy.MARKOV,
        "cwp": SearchStrategy.CWP,
    }
    strategy = strategy_map.get(args.strategy, SearchStrategy.AUTO)

    # Parse target addresses
    target_addresses = []
    if args.target_address:
        target_addresses = [args.target_address]
    if args.target_addresses_file:
        try:
            with open(args.target_addresses_file, 'r') as f:
                target_addresses.extend(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            print(f"  ERROR: Target addresses file not found: {args.target_addresses_file}")
            return

    # Build config
    config = BruteforceConfig(
        mode=RecoveryMode.SEED_PHRASE,
        target_addresses=target_addresses,
        seed_length=seed_length,
        known_words=known_words,
        missing_positions=missing_positions,
        seed_standard=args.seed_standard or "BIP39",
        strategy=strategy,
        prioritize_common=not args.no_prioritize,
        num_threads=args.threads or 0,
        use_gpu=not args.no_gpu,
        max_attempts=args.max_attempts or 0,
        checkpoint_interval=args.checkpoint_interval or 60.0,
        resume_from=args.resume or None,
        coin=args.coin or "BTC",
        callback=cli_progress_callback,
        callback_interval=100,
        seedrecover_path=args.seedrecover or None,
        btcrecover_path=args.btcrecover or None,
        bitcoin_core_path=args.bitcoin_core or None,
    )

    print(f"\n  Starting advanced bruteforce recovery...")
    print(f"  Strategy: {strategy.value} | GPU: {'enabled' if config.use_gpu else 'disabled'}")
    print()

    engine = BruteforceEngine(config)
    result = engine.run()

    print()
    _print_bruteforce_result(result)

    if args.save_result and result.success:
        path = save_recovery_result(result)
        print(f"  Result saved to: {path}")


def _bruteforce_passphrase(args):
    """Advanced passphrase bruteforce"""
    if not args.mnemonic:
        print("  ERROR: --mnemonic is required for passphrase recovery")
        return

    known_words = args.mnemonic.split()
    target_addresses = []
    if args.target_address:
        target_addresses = [args.target_address]

    passphrase_candidates = []
    if args.passphrase_list:
        passphrase_candidates = args.passphrase_list.split(",")

    config = BruteforceConfig(
        mode=RecoveryMode.PASSPHRASE,
        target_addresses=target_addresses,
        known_words=known_words,
        passphrase_candidates=passphrase_candidates,
        partial_passphrase=args.partial_passphrase or "",
        passphrase_dict_files=[args.passphrase_file] if args.passphrase_file else [],
        coin=args.coin or "BTC",
        num_threads=args.threads or 0,
        use_gpu=not args.no_gpu,
        callback=cli_progress_callback,
        seedrecover_path=args.seedrecover or None,
    )

    print(f"\n  Starting advanced passphrase recovery...")
    print(f"  Seed: {args.mnemonic[:30]}... ({len(known_words)} words)")
    print(f"  Targets: {len(target_addresses)} addresses")
    print()

    engine = BruteforceEngine(config)
    result = engine.run()

    print()
    _print_bruteforce_result(result)


def _bruteforce_password(args):
    """Advanced password bruteforce"""
    if not args.wallet_file:
        print("  ERROR: --wallet-file is required")
        return

    password_candidates = []
    if args.password_list:
        password_candidates = args.password_list.split(",")

    config = BruteforceConfig(
        mode=RecoveryMode.PASSWORD,
        wallet_file=args.wallet_file,
        target_addresses=[],
        password_candidates=password_candidates,
        password_dict_files=[args.password_dict] if args.password_dict else [],
        num_threads=args.threads or 0,
        use_gpu=not args.no_gpu,
        callback=cli_progress_callback,
        btcrecover_path=args.btcrecover or None,
    )

    print(f"\n  Starting advanced password recovery...")
    print()

    engine = BruteforceEngine(config)
    result = engine.run()

    print()
    _print_bruteforce_result(result)


def cmd_predict_words(args):
    """Use Contextual Word Prediction to suggest similar BIP39 words"""
    print("\n" + "=" * 80)
    print("  CONTEXTUAL WORD PREDICTION (CWP)")
    print("=" * 80)

    wordlist = get_bip39_wordlist()
    predictor = ContextualWordPredictor(wordlist)

    word = args.word
    max_distance = args.max_distance or 3
    max_results = args.max_results or 50

    print(f"\n  Input word: '{word}'")
    print(f"  Max edit distance: {max_distance}")

    similar = predictor.predict_similar_words(word, max_distance, max_results)

    print(f"\n  Similar BIP39 words ({len(similar)} found):")
    for i, w in enumerate(similar[:30]):
        in_wordlist = " [VALID]" if w in wordlist else ""
        print(f"    {i+1:3d}. {w}{in_wordlist}")
    if len(similar) > 30:
        print(f"    ... and {len(similar) - 30} more")

    # If the word is in the wordlist, note it
    if word in wordlist:
        print(f"\n  Note: '{word}' IS a valid BIP39 word.")
    else:
        print(f"\n  Note: '{word}' is NOT a valid BIP39 word.")
        # Find closest matches
        closest = similar[:5]
        print(f"  Closest BIP39 matches: {closest}")

    print("=" * 80 + "\n")


def cmd_estimate(args):
    """Estimate recovery time for a given scenario"""
    print("\n" + "=" * 80)
    print("  RECOVERY TIME ESTIMATOR")
    print("=" * 80)

    num_missing = args.missing_words
    seed_length = args.seed_length or 12
    last_missing = args.last_missing or False

    estimate = BruteforceEngine.estimate_recovery_time(
        num_missing, seed_length, last_missing
    )

    print(f"\n  Scenario: {num_missing} missing word(s) in {seed_length}-word seed")
    print(f"  Last position missing: {'Yes' if last_missing else 'No'}")
    print(f"\n  Search Space:")
    print(f"    Total candidates:       {format_number(estimate['total_candidates'])}")
    print(f"    After checksum filter:  {format_number(estimate['valid_after_checksum'])}")
    print(f"    Checksum pruning:       {estimate['checksum_pruning_ratio']}")

    # Show estimates for different hardware
    print(f"\n  Estimated Recovery Time:")
    for label, rate in [("CPU (1 core)", 1500), ("CPU (8 cores)", 12000),
                         ("GPU (RTX 3060)", 100000), ("GPU (RTX 4090)", 400000),
                         ("GPU Cluster (4x RTX 4090)", 1600000)]:
        est = BruteforceEngine.estimate_recovery_time(num_missing, seed_length, last_missing, rate)
        print(f"    {label:30s}: {est['estimated_time']}")

    # Show available strategies
    strategies = BruteforceEngine.list_strategies(num_missing, seed_length, last_missing)
    print(f"\n  Recommended Strategies:")
    for s in strategies:
        marker = " <-- BEST" if s['recommended'] else ""
        print(f"    - {s['name']}: {s['description']}{marker}")
        print(f"      Candidates: {s['candidates']} | Time: {s['estimated_time']}")

    print("=" * 80 + "\n")


def cmd_benchmark(args):
    """Benchmark hardware for wallet recovery"""
    print("\n" + "=" * 80)
    print("  HARDWARE BENCHMARK")
    print("=" * 80)

    # CPU info
    cpu = get_cpu_info()
    print(f"\n  CPU: {cpu.device_name}")
    print(f"  Cores: {cpu.compute_units}")
    print(f"  Estimated hash rate: {cpu.estimated_hash_rate:.0f} H/s")

    # GPU detection
    gpus = detect_gpu_backends()
    if gpus:
        for gpu in gpus:
            print(f"\n  GPU: {gpu.device_name}")
            print(f"  Compute Units: {gpu.compute_units}")
            print(f"  Memory: {gpu.global_memory_mb} MB")
            print(f"  Estimated hash rate: {gpu.estimated_hash_rate:.0f} H/s")
    else:
        print(f"\n  GPU: None detected")
        print(f"  (Install pyopencl: pip install pyopencl)")

    # Run benchmark
    if not args.skip_benchmark:
        print(f"\n  Running benchmark ({args.duration}s)...")
        accelerator = GPUAccelerator(AcceleratorConfig())
        accelerator.initialize()
        results = accelerator.benchmark(duration_seconds=args.duration)
        print(f"\n  Results:")
        for backend, rate in results.items():
            print(f"    {backend}: {rate:.0f} PBKDF2 derivations/sec")

        # Translate to seed recovery rates
        print(f"\n  Estimated Recovery Rates (12-word seed, 1 missing word):")
        for backend, rate in results.items():
            # With LWO, only 128 candidates, checksum pass rate ~100%
            lwo_time = 128 / rate if rate > 0 else float('inf')
            # Without LWO, 2048 candidates, 128 pass checksum
            no_lwo_time = 2048 / rate if rate > 0 else float('inf')
            print(f"    {backend}:")
            print(f"      With LWO: 128 candidates in {lwo_time:.3f}s")
            print(f"      Without LWO: 2048 candidates in {no_lwo_time:.3f}s")

        accelerator.cleanup()

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

    try:
        seed_bytes = mnemonic_to_seed_v2(args.mnemonic, passphrase)
        from core.address_derivation import seed_to_master_key
        master = seed_to_master_key(seed_bytes)

        print(f"\n  Master Seed (hex): {seed_bytes.hex()[:32]}...{seed_bytes.hex()[-32:]}")

        # Generate addresses for all types
        addrs = generate_addresses(master, num_addresses=args.count or 5, coin=args.coin or "BTC")

        for addr_type, addresses in addrs.items():
            type_name = {"p2pkh": "Legacy (P2PKH)", "p2sh_p2wpkh": "Nested SegWit (P2SH-P2WPKH)",
                        "p2wpkh": "Native SegWit (P2WPKH)", "p2tr": "Taproot (P2TR)"}.get(addr_type, addr_type)
            print(f"\n  {type_name}:")
            for i, addr in enumerate(addresses):
                print(f"    [{i}] {addr}")
    except Exception as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 80 + "\n")


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
        # Suggest alternatives
        predictor = ContextualWordPredictor(wordlist)
        for w in invalid_words:
            similar = predictor.predict_similar_words(w, max_distance=2, max_results=5)
            if similar:
                print(f"    Did you mean: {similar[:5]}?")

    if len(words) in [12, 15, 18, 21, 24]:
        is_valid = validate_bip39_checksum(words)
        print(f"  BIP39 Checksum: {'VALID' if is_valid else 'INVALID'}")
        if not is_valid:
            print(f"  One or more words may be incorrect or out of order.")
    else:
        print(f"  Warning: Non-standard word count ({len(words)}). BIP39 uses 12/15/18/21/24 words.")

    # Check for last-word validity
    if len(words) in [12, 15, 18, 21, 24]:
        all_but_last = words[:-1]
        valid_last = find_valid_last_words(all_but_last, len(words) - 1, wordlist)
        if words[-1] in valid_last:
            print(f"  Last word: Valid ({len(valid_last)} valid options for this position)")
        else:
            print(f"  Last word: INVALID (valid options: {valid_last[:10]}...)")

    print("=" * 80 + "\n")


def cmd_interactive(args):
    """Launch interactive recovery wizard"""
    print("\n" + "=" * 80)
    print("  CryptoRecover - Interactive Recovery Wizard")
    print("  Advanced Engine: CPF | PVP | LWO | HCP | SWP | AWD | CWP | EGS")
    print("=" * 80)
    print()
    print("  What do you need to recover?")
    print("  1. Missing words from a seed phrase (Advanced Bruteforce)")
    print("  2. BIP39 passphrase (25th word)")
    print("  3. Wallet file password")
    print("  4. Validate a seed phrase")
    print("  5. Generate addresses from a seed phrase")
    print("  6. Predict similar BIP39 words")
    print("  7. Estimate recovery time")
    print("  8. Benchmark hardware")
    print("  9. List supported wallets")
    print("  10. List login technologies")
    print()

    choice = input("  Select option (1-10): ").strip()

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
            mnemonic=mnemonic, passphrase=passphrase, coin="BTC", count=5
        ))
    elif choice == "6":
        word = input("  Enter word to find similar BIP39 words: ").strip()
        cmd_predict_words(argparse.Namespace(word=word, max_distance=3, max_results=50))
    elif choice == "7":
        missing = int(input("  Number of missing words: ").strip() or "1")
        length = int(input("  Seed length (12/15/18/21/24): ").strip() or "12")
        last = input("  Is the last position missing? (y/N): ").strip().lower() == "y"
        cmd_estimate(argparse.Namespace(
            missing_words=missing, seed_length=length, last_missing=last
        ))
    elif choice == "8":
        cmd_benchmark(argparse.Namespace(skip_benchmark=False, duration=3))
    elif choice == "9":
        cmd_list_wallets(argparse.Namespace(coin=None, seed_type=None, login_tech=None))
    elif choice == "10":
        cmd_list_login_techs(argparse.Namespace())
    else:
        print("  Invalid option.")


def _interactive_seed_recovery():
    """Interactive seed phrase recovery"""
    print("\n  --- Seed Phrase Recovery Wizard ---\n")
    print("  Enter your seed phrase with ? for each missing/unknown word.")
    print("  Example: abandon ? ? about above absent absorb abstract absurd abuse access accident")
    mnemonic = input("\n  Seed phrase: ").strip()

    if not mnemonic:
        print("  No seed phrase entered. Exiting.")
        return

    target_address = input("  Target address (optional, press Enter to skip): ").strip() or None

    args = argparse.Namespace(
        mode="seed",
        mnemonic=mnemonic,
        known_words=None,
        missing_positions=None,
        seed_length=None,
        seed_standard="BIP39",
        target_address=target_address,
        target_addresses_file=None,
        strategy="auto",
        no_prioritize=False,
        no_gpu=False,
        threads=0,
        max_attempts=0,
        checkpoint_interval=60,
        resume=None,
        coin="BTC",
        seedrecover=None,
        btcrecover=None,
        bitcoin_core=None,
        dry_run=False,
        save_result=True,
    )
    cmd_bruteforce(args)


def _interactive_passphrase_recovery():
    """Interactive passphrase recovery"""
    print("\n  --- Passphrase Recovery Wizard ---\n")
    mnemonic = input("  Enter your complete seed phrase: ").strip()
    if not mnemonic:
        print("  No seed phrase entered. Exiting.")
        return

    target_address = input("  Target address (required for verification): ").strip()
    if not target_address:
        print("  Target address is required. Exiting.")
        return

    args = argparse.Namespace(
        mode="passphrase",
        mnemonic=mnemonic,
        target_address=target_address,
        passphrase_list=None,
        passphrase_file=None,
        partial_passphrase=None,
        coin="BTC",
        threads=0,
        no_gpu=False,
        seedrecover=None,
        dry_run=False,
        save_result=True,
    )
    cmd_bruteforce(args)


def _interactive_password_recovery():
    """Interactive password recovery"""
    print("\n  --- Password Recovery Wizard ---\n")
    wallet_file = input("  Enter wallet file path: ").strip()
    if not wallet_file:
        print("  No wallet file entered. Exiting.")
        return

    args = argparse.Namespace(
        mode="password",
        wallet_file=wallet_file,
        password_list=None,
        password_dict=None,
        threads=0,
        no_gpu=False,
        btcrecover=None,
        dry_run=False,
        save_result=True,
    )
    cmd_bruteforce(args)


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


def _print_bruteforce_result(result: BruteforceResult):
    """Print advanced bruteforce result"""
    print("\n" + "=" * 80)
    print("  BRUTEFORCE RECOVERY RESULT")
    print("=" * 80)

    if result.success:
        print(f"\n  *** RECOVERY SUCCESSFUL ***\n")
        print(f"  Found Value: {result.found_value}")
        print(f"  Recovery Mode: {result.mode.value}")
        print(f"  Strategy Used: {result.strategy_used}")
        if result.found_address:
            print(f"  Matched Address: {result.found_address}")
        if result.found_address_type:
            print(f"  Address Type: {result.found_address_type}")
        if result.seed_hex:
            print(f"  Seed (hex): {result.seed_hex[:32]}...")
        if result.passphrase:
            print(f"  Passphrase: '{result.passphrase}'")
        print(f"  Attempts: {format_number(result.attempts)}")
        print(f"  Time Elapsed: {format_time(result.time_elapsed)}")
        print(f"  Speed: {result.rate_per_second:.1f} attempts/sec")
    else:
        print(f"\n  Recovery FAILED\n")
        print(f"  Status: {result.status.value}")
        print(f"  Strategy Used: {result.strategy_used}")
        print(f"  Error: {result.error_message or 'Unknown'}")
        print(f"  Attempts: {format_number(result.attempts)}")
        print(f"  Time Elapsed: {format_time(result.time_elapsed)}")

    # Pipeline statistics
    if result.pipeline_stats:
        print(f"\n  Pipeline Statistics:")
        stats = result.pipeline_stats
        total = stats.candidates_entered or 1
        print(f"    Candidates entered:      {stats.candidates_entered:,}")
        print(f"    Passed checksum:         {stats.passed_checksum:,} ({100*stats.passed_checksum/total:.1f}%)")
        print(f"    Passed PBKDF2:           {stats.passed_seed_derivation:,} ({100*stats.passed_seed_derivation/total:.1f}%)")
        print(f"    Pruning efficiency:      {stats.pruning_efficiency:.1f}% eliminated before PBKDF2")
        print(f"    Time in checksum:        {stats.time_in_checksum:.3f}s")
        print(f"    Time in PBKDF2:          {stats.time_in_seed:.3f}s")

    print("\n" + "=" * 80 + "\n")


# ==============================================================================
# MAIN CLI ENTRY POINT
# ==============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser"""
    parser = argparse.ArgumentParser(
        prog="cryptorecover",
        description="CryptoRecover - Advanced Cryptocurrency Wallet Recovery Tool\n"
                    "Techniques: CPF | PVP | LWO | HCP | SWP | AWD | CWP | EGS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Advanced bruteforce with all optimizations
  cryptorecover bruteforce --mode seed --mnemonic "abandon ? ? about above absent absorb abstract absurd abuse access accident"

  # Bruteforce with target address verification
  cryptorecover bruteforce --mode seed --mnemonic "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon ?" --target-address bc1q...

  # Estimate recovery time
  cryptorecover estimate --missing-words 2 --seed-length 12

  # Predict similar BIP39 words
  cryptorecover predict-words --word abandn

  # Generate addresses from seed
  cryptorecover generate-addresses --mnemonic "abandon ability able about..."

  # Benchmark hardware
  cryptorecover benchmark

  # Interactive wizard
  cryptorecover interactive
        """
    )

    parser.add_argument("--version", action="version", version="CryptoRecover v2.0.0")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- bruteforce (new advanced engine) ---
    p_bf = subparsers.add_parser("bruteforce", help="Advanced bruteforce recovery engine")
    p_bf.add_argument("--mode", required=True, choices=["seed", "passphrase", "password"],
                       help="Recovery mode")
    p_bf.add_argument("--mnemonic", "-m", help="Seed phrase with ? for unknown words")
    p_bf.add_argument("--known-words", help="Known words, comma-separated")
    p_bf.add_argument("--missing-positions", help="Positions of missing words (0-indexed)")
    p_bf.add_argument("--seed-length", type=int, help="Expected seed length")
    p_bf.add_argument("--seed-standard", default="BIP39", choices=["BIP39", "Electrum", "SLIP39"])
    p_bf.add_argument("--target-address", "-a", help="Target address for verification")
    p_bf.add_argument("--target-addresses-file", help="File with target addresses")
    p_bf.add_argument("--strategy", default="auto",
                       choices=["auto", "lwo", "hcp", "statistical", "full", "markov", "cwp"],
                       help="Search strategy (default: auto)")
    p_bf.add_argument("--no-prioritize", action="store_true", help="Don't prioritize common words")
    p_bf.add_argument("--no-gpu", action="store_true", help="Disable GPU acceleration")
    p_bf.add_argument("--threads", "-t", type=int, default=0, help="Number of threads (0=auto)")
    p_bf.add_argument("--max-attempts", type=int, default=0, help="Max attempts (0=unlimited)")
    p_bf.add_argument("--checkpoint-interval", type=float, default=60, help="Auto-save interval (seconds)")
    p_bf.add_argument("--resume", help="Resume from checkpoint file")
    p_bf.add_argument("--coin", default="BTC", help="Coin type (default: BTC)")
    # Passphrase options
    p_bf.add_argument("--passphrase-list", help="Passphrase candidates, comma-separated")
    p_bf.add_argument("--passphrase-file", help="Passphrase candidates file")
    p_bf.add_argument("--partial-passphrase", help="Partial passphrase hint")
    # Password options
    p_bf.add_argument("--wallet-file", "-w", help="Wallet file path")
    p_bf.add_argument("--password-list", help="Password candidates, comma-separated")
    p_bf.add_argument("--password-dict", help="Password dictionary file")
    # External tools
    p_bf.add_argument("--btcrecover", help="Path to btcrecover.py")
    p_bf.add_argument("--seedrecover", help="Path to seedrecover.py")
    p_bf.add_argument("--bitcoin-core", help="Path to bitcoin-cli")
    p_bf.add_argument("--dry-run", action="store_true", help="Show estimate without running")
    p_bf.add_argument("--save-result", action="store_true", help="Save result to file")

    # --- estimate (new) ---
    p_est = subparsers.add_parser("estimate", help="Estimate recovery time")
    p_est.add_argument("--missing-words", type=int, required=True, help="Number of missing words")
    p_est.add_argument("--seed-length", type=int, default=12, help="Seed length (default: 12)")
    p_est.add_argument("--last-missing", action="store_true", help="Last position is missing")

    # --- predict-words (new) ---
    p_pred = subparsers.add_parser("predict-words", help="Predict similar BIP39 words")
    p_pred.add_argument("--word", required=True, help="Word to find similar BIP39 words for")
    p_pred.add_argument("--max-distance", type=int, default=3, help="Max edit distance")
    p_pred.add_argument("--max-results", type=int, default=50, help="Max results")

    # --- benchmark (new) ---
    p_bench = subparsers.add_parser("benchmark", help="Benchmark hardware")
    p_bench.add_argument("--duration", type=int, default=3, help="Benchmark duration (seconds)")
    p_bench.add_argument("--skip-benchmark", action="store_true", help="Only detect hardware")

    # --- list-wallets ---
    p_list = subparsers.add_parser("list-wallets", help="List all supported wallets")
    p_list.add_argument("--coin", help="Filter by coin")
    p_list.add_argument("--seed-type", help="Filter by seed type")
    p_list.add_argument("--login-tech", help="Filter by login technology")

    # --- list-login-techs ---
    subparsers.add_parser("list-login-techs", help="List all login technologies")

    # --- validate ---
    p_val = subparsers.add_parser("validate", help="Validate a seed phrase")
    p_val.add_argument("--mnemonic", "-m", required=True, help="Seed phrase to validate")

    # --- generate-addresses ---
    p_gen = subparsers.add_parser("generate-addresses", help="Generate addresses from seed")
    p_gen.add_argument("--mnemonic", "-m", required=True, help="Seed phrase")
    p_gen.add_argument("--passphrase", help="BIP39 passphrase")
    p_gen.add_argument("--coin", default="BTC", help="Coin type")
    p_gen.add_argument("--count", type=int, default=5, help="Addresses per type")

    # --- interactive ---
    subparsers.add_parser("interactive", help="Launch interactive recovery wizard")

    return parser


def main():
    """Main CLI entry point"""
    ensure_dirs()

    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    if getattr(args, 'debug', False):
        logging.basicConfig(level=logging.DEBUG)
    elif getattr(args, 'verbose', False):
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Route to command
    if args.command == "bruteforce":
        cmd_bruteforce(args)
    elif args.command == "estimate":
        cmd_estimate(args)
    elif args.command == "predict-words":
        cmd_predict_words(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "list-wallets":
        cmd_list_wallets(args)
    elif args.command == "list-login-techs":
        cmd_list_login_techs(args)
    elif args.command == "validate":
        cmd_validate_seed(args)
    elif args.command == "generate-addresses":
        cmd_generate_addresses(args)
    elif args.command == "interactive":
        cmd_interactive(args)
    else:
        parser.print_help()
        print("\n  Tip: Use 'cryptorecover interactive' for a guided recovery wizard.")
        print("  New: 'cryptorecover bruteforce' for the advanced engine with all optimizations.")


if __name__ == "__main__":
    main()
