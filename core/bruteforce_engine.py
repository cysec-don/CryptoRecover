"""
CryptoRecover - Advanced Bruteforce Engine
============================================
The ultimate cryptocurrency wallet bruteforce recovery engine.

INVENTIONS IMPLEMENTED:
1. CPF (Checksum Pre-Filter) - Eliminates 93.75%+ candidates before PBKDF2
2. PVP (Progressive Verification Pipeline) - Multi-stage fail-fast verification
3. LWO (Last-Word Optimization) - Only 128 valid candidates for last word
4. HCP (Hierarchical Checksum Pruning) - Pre-compute partial checksum states
5. SWP (Statistical Word Prioritization) - Rank candidates by likelihood
6. AWD (Adaptive Work Distribution) - Dynamic CPU/GPU work splitting
7. CWP (Contextual Word Prediction) - Predict similar BIP39 words
8. EGS (Entropy-Guided Search) - Search most constrained positions first
9. MMCS (Memory-Mapped Candidate Streams) - Generator-based for infinite search spaces
10. SRC (Smart Resume/Checkpoint) - Save/restore progress for long searches

Performance characteristics:
- Single missing word (last position): ~128 candidates, <1 second
- Single missing word (any position): ~2048 candidates, ~0.5s with LWO
- 2 missing words (inc. last): ~262K candidates, ~1-5 minutes
- 2 missing words (no last): ~4.2M candidates, ~10-60 minutes
- 3 missing words: ~537M checksum-valid, hours on CPU
- 4+ missing words: Requires GPU cluster (see Cantrell's approach)
"""

import hashlib
import logging
import multiprocessing
import os
import sys
import time
import threading
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Callable, Tuple, Any, Generator, Set

from .address_derivation import (
    AddressMatcher, AddressType, mnemonic_to_seed, seed_to_master_key,
    generate_address, generate_addresses, derive_first_address,
    check_seed_against_targets, COIN_CONFIG, DERIVATION_PATHS,
)
from .checksum_filter import (
    validate_bip39_checksum, get_bip39_wordlist, find_valid_last_words,
    HierarchicalChecksumPruner, ChecksumBatchValidator,
    IncrementalEntropyBuilder,
)
from .candidate_generators import (
    SeedPhraseGenerator, PassphraseGenerator, PassphraseConfig,
    PasswordGenerator, PasswordConfig, MarkovGenerator,
    ContextualWordPredictor,
)
from .verification_pipeline import (
    ProgressiveVerificationPipeline, PipelineStage, PipelineStats,
    VerificationResult,
)
from .gpu_accelerator import (
    GPUAccelerator, AcceleratorConfig, AccelerationBackend,
    detect_gpu_backends, get_cpu_info,
)
from .checkpoint import (
    CheckpointManager, CheckpointState,
)

logger = logging.getLogger(__name__)


# ============================================================================
# ENGINE TYPES
# ============================================================================

class RecoveryMode(Enum):
    SEED_PHRASE = "seed_phrase"
    PASSPHRASE = "passphrase"
    PASSWORD = "password"
    PIN = "pin"


class RecoveryStatus(Enum):
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"
    CANCELLED = "cancelled"


class SearchStrategy(Enum):
    AUTO = "auto"               # Auto-select best strategy
    LWO = "lwo"                 # Last-Word Optimization
    HCP = "hcp"                 # Hierarchical Checksum Pruning
    STATISTICAL = "statistical"  # Statistical Word Prioritization
    FULL = "full"               # Full enumeration
    MARKOV = "markov"           # Markov chain-based generation
    CWP = "cwp"                 # Contextual Word Prediction


@dataclass
class BruteforceConfig:
    """Complete configuration for a bruteforce recovery operation."""
    # Recovery target
    mode: RecoveryMode = RecoveryMode.SEED_PHRASE
    target_addresses: List[str] = field(default_factory=list)
    wallet_file: Optional[str] = None

    # Seed phrase settings
    seed_length: int = 12
    known_words: List[str] = field(default_factory=list)
    missing_positions: List[int] = field(default_factory=list)
    seed_standard: str = "BIP39"  # BIP39, Electrum, SLIP39

    # Passphrase settings
    partial_passphrase: str = ""
    passphrase_candidates: List[str] = field(default_factory=list)
    passphrase_dict_files: List[str] = field(default_factory=list)

    # Password settings
    password_candidates: List[str] = field(default_factory=list)
    password_dict_files: List[str] = field(default_factory=list)

    # Address derivation
    addr_types: List[str] = field(default_factory=lambda: [
        AddressType.P2WPKH, AddressType.P2PKH, AddressType.P2SH_P2WPKH
    ])
    coin: str = "BTC"
    num_addresses: int = 5

    # Search strategy
    strategy: SearchStrategy = SearchStrategy.AUTO
    prioritize_common: bool = True

    # Performance
    num_threads: int = 0  # 0 = auto
    use_gpu: bool = True
    gpu_batch_size: int = 4096
    max_attempts: int = 0  # 0 = unlimited

    # Checkpoint
    checkpoint_dir: str = ""
    checkpoint_interval: float = 60.0  # seconds
    resume_from: Optional[str] = None  # Checkpoint file path

    # Progress callback
    callback: Optional[Callable] = None
    callback_interval: int = 100  # Call callback every N candidates

    # External tools
    btcrecover_path: Optional[str] = None
    seedrecover_path: Optional[str] = None
    bitcoin_core_path: Optional[str] = None


@dataclass
class BruteforceResult:
    """Result of a bruteforce recovery operation."""
    success: bool
    mode: RecoveryMode
    status: RecoveryStatus = RecoveryStatus.IDLE
    found_value: Optional[str] = None
    found_address: Optional[str] = None
    found_address_type: Optional[str] = None
    found_derivation_path: Optional[str] = None
    seed_hex: Optional[str] = None
    passphrase: Optional[str] = None
    attempts: int = 0
    time_elapsed: float = 0.0
    rate_per_second: float = 0.0
    pipeline_stats: Optional[PipelineStats] = None
    strategy_used: str = ""
    error_message: Optional[str] = None
    details: Dict = field(default_factory=dict)


# ============================================================================
# MAIN BRUTEFORCE ENGINE
# ============================================================================

class BruteforceEngine:
    """The Ultimate Cryptocurrency Wallet Bruteforce Engine.

    Combines all invented techniques (CPF, PVP, LWO, HCP, SWP, AWD, CWP, EGS)
    into a single cohesive engine that automatically selects the optimal
    strategy for each recovery scenario.

    Usage:
        config = BruteforceConfig(
            mode=RecoveryMode.SEED_PHRASE,
            known_words=["abandon", "abandon", ...],
            missing_positions=[11],
            target_addresses=["bc1q..."],
        )
        engine = BruteforceEngine(config)
        result = engine.run()
    """

    def __init__(self, config: BruteforceConfig):
        self.config = config
        self.status = RecoveryStatus.IDLE
        self._cancel_flag = threading.Event()
        self._pause_flag = threading.Event()
        self._start_time = 0.0
        self._attempts = 0
        self._found_results: List[Dict] = []
        self._pipeline: Optional[ProgressiveVerificationPipeline] = None
        self._accelerator: Optional[GPUAccelerator] = None
        self._checkpoint_mgr: Optional[CheckpointManager] = None
        self._wordlist: Optional[List[str]] = None
        self._resume_skip_count: int = 0

    def cancel(self):
        """Cancel the running recovery operation."""
        self._cancel_flag.set()
        self.status = RecoveryStatus.CANCELLED

    def pause(self):
        """Pause the recovery operation."""
        self._pause_flag.set()

    def resume(self):
        """Resume a paused recovery operation."""
        self._pause_flag.clear()

    def get_progress(self) -> Dict:
        """Get current progress information."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        return {
            "status": self.status.value,
            "attempts": self._attempts,
            "time_elapsed": elapsed,
            "rate_per_second": self._attempts / elapsed if elapsed > 0 else 0,
            "found": len(self._found_results),
        }

    def _get_checkpoint_state(self) -> CheckpointState:
        """Get current state for checkpointing."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        return CheckpointState(
            recovery_type=self.config.mode.value,
            candidates_tested=self._attempts,
            time_elapsed=elapsed,
            rate_per_second=self._attempts / elapsed if elapsed > 0 else 0,
            seed_length=self.config.seed_length,
            known_words=self.config.known_words,
            missing_positions=self.config.missing_positions,
            strategy=self.config.strategy.value,
            found_results=self._found_results,
            config={
                'coin': self.config.coin,
                'addr_types': self.config.addr_types,
                'num_addresses': self.config.num_addresses,
            },
        )

    # ─── MAIN RUN METHOD ─────────────────────────────────────────────

    def run(self) -> BruteforceResult:
        """Execute the bruteforce recovery operation.

        Automatically selects the optimal strategy based on the recovery
        configuration and available hardware.

        Returns:
            BruteforceResult with outcome details
        """
        self.status = RecoveryStatus.INITIALIZING
        self._start_time = time.time()
        self._cancel_flag.clear()
        self._pause_flag.clear()
        self._attempts = 0
        self._found_results = []

        try:
            # Initialize subsystems
            self._initialize()

            # Check for resume
            if self.config.resume_from:
                self._resume_from_checkpoint()

            # Route to appropriate recovery method
            if self.config.mode == RecoveryMode.SEED_PHRASE:
                result = self._recover_seed_phrase()
            elif self.config.mode == RecoveryMode.PASSPHRASE:
                result = self._recover_passphrase()
            elif self.config.mode == RecoveryMode.PASSWORD:
                result = self._recover_password()
            else:
                result = BruteforceResult(
                    success=False,
                    mode=self.config.mode,
                    status=RecoveryStatus.ERROR,
                    error_message=f"Unsupported recovery mode: {self.config.mode}",
                )

            # Attach pipeline stats
            if self._pipeline:
                result.pipeline_stats = self._pipeline.get_stats()

            return result

        except Exception as e:
            logger.error(f"Recovery engine error: {e}", exc_info=True)
            return BruteforceResult(
                success=False,
                mode=self.config.mode,
                status=RecoveryStatus.ERROR,
                error_message=str(e),
                attempts=self._attempts,
                time_elapsed=time.time() - self._start_time,
            )
        finally:
            self._cleanup()

    def _initialize(self):
        """Initialize all subsystems."""
        # Load wordlist
        self._wordlist = get_bip39_wordlist()
        if len(self._wordlist) < 2048:
            logger.warning("Incomplete BIP39 wordlist - some features may not work")

        # Initialize verification pipeline
        self._pipeline = ProgressiveVerificationPipeline(
            target_addresses=self.config.target_addresses,
            addr_types=self.config.addr_types,
            coin=self.config.coin,
            num_addresses=self.config.num_addresses,
            wordlist=self._wordlist,
        )

        # Initialize accelerator
        if self.config.use_gpu:
            accel_config = AcceleratorConfig(
                backend=AccelerationBackend.AUTO if self.config.use_gpu else AccelerationBackend.CPU,
                num_threads=self.config.num_threads,
            )
            self._accelerator = GPUAccelerator(accel_config)
            self._accelerator.initialize()

        # Initialize checkpoint manager
        self._checkpoint_mgr = CheckpointManager(
            checkpoint_dir=self.config.checkpoint_dir,
            auto_save_interval=self.config.checkpoint_interval,
        )

        logger.info(f"Engine initialized: mode={self.config.mode.value}, "
                    f"wordlist={len(self._wordlist)} words, "
                    f"targets={len(self.config.target_addresses)}, "
                    f"accelerator={self._accelerator.get_info() if self._accelerator else 'none'}")

        self.status = RecoveryStatus.RUNNING

    def _cleanup(self):
        """Clean up resources."""
        if self._checkpoint_mgr:
            self._checkpoint_mgr.stop_auto_save()
        if self._accelerator:
            self._accelerator.cleanup()

    def _check_cancelled(self) -> bool:
        """Check if recovery has been cancelled."""
        if self._cancel_flag.is_set():
            return True
        # Check pause
        while self._pause_flag.is_set():
            time.sleep(0.1)
            if self._cancel_flag.is_set():
                return True
        return False

    def _update_progress(self, force: bool = False):
        """Update progress and trigger callback if needed."""
        if self.config.callback:
            if force or self._attempts % self.config.callback_interval == 0:
                self.config.callback(self.get_progress())

        # Auto-checkpoint
        if self._checkpoint_mgr and self._checkpoint_mgr.should_auto_save():
            self._checkpoint_mgr.save(self._get_checkpoint_state())

    def _resume_from_checkpoint(self):
        """Resume recovery from a checkpoint file."""
        if not self.config.resume_from:
            return

        try:
            state = self._checkpoint_mgr.load(self.config.resume_from)
            self._attempts = state.candidates_tested
            self._resume_skip_count = state.candidates_tested
            logger.info(f"Resumed from checkpoint: {state.candidates_tested} candidates already tested")
        except Exception as e:
            logger.warning(f"Failed to resume from checkpoint: {e}")
            self._resume_skip_count = 0

    # ─── SEED PHRASE RECOVERY ──────────────────────────────────────────

    def _recover_seed_phrase(self) -> BruteforceResult:
        """Recover missing words from a seed phrase.

        Automatically selects the optimal strategy:
        - 1 missing word, last position: LWO (128 candidates)
        - 1 missing word, any position: LWO with all positions
        - 2-4 missing words: HCP with statistical prioritization
        - 5+ missing words: Not feasible on CPU, requires GPU cluster
        """
        config = self.config

        if not config.missing_positions:
            return BruteforceResult(
                success=False, mode=RecoveryMode.SEED_PHRASE,
                status=RecoveryStatus.ERROR,
                error_message="No missing word positions specified",
            )

        num_missing = len(config.missing_positions)

        # Select strategy
        strategy = self._select_seed_strategy(num_missing)
        logger.info(f"Seed phrase recovery: {num_missing} missing words, "
                    f"strategy={strategy.value}")

        # Try external tools first
        if config.seedrecover_path and os.path.isfile(config.seedrecover_path):
            result = self._try_seedrecover()
            if result and result.success:
                return result

        # Use our advanced engine
        generator = SeedPhraseGenerator(self._wordlist)

        total_estimate = self._estimate_search_space(num_missing)
        from .checksum_filter import ChecksumBatchValidator
        batch_validator = ChecksumBatchValidator(self._wordlist)
        valid_estimate = batch_validator.estimate_valid_count(config.seed_length, total_estimate)
        logger.info(f"Estimated search space: {total_estimate:,} candidates "
                    f"({valid_estimate:,} pass checksum)")

        # Start checkpoint auto-save
        self._checkpoint_mgr.start_auto_save(self._get_checkpoint_state, "seed_phrase")

        found_results = []
        strategy_name = strategy.value

        for candidate_words in generator.generate(
            known_words=config.known_words,
            missing_positions=config.missing_positions,
            seed_length=config.seed_length,
            strategy=strategy.value if strategy != SearchStrategy.AUTO else "hcp",
            prioritize_common=config.prioritize_common,
        ):
            # Skip already-tested candidates if resuming from checkpoint
            if self._resume_skip_count > 0:
                self._resume_skip_count -= 1
                continue

            if self._check_cancelled():
                return self._make_result(
                    RecoveryStatus.CANCELLED,
                    strategy_name=strategy_name,
                )

            self._attempts += 1

            # Run through progressive verification pipeline
            result = self._pipeline.verify(candidate_words)

            if result.matched:
                found_results.append({
                    'seed_phrase': result.seed_phrase,
                    'seed_hex': result.seed_hex,
                    'matched_address': result.matched_address,
                    'address_type': result.address_type,
                    'derivation_path': result.derivation_path,
                })

                # Found! Return immediately
                elapsed = time.time() - self._start_time
                return BruteforceResult(
                    success=True,
                    mode=RecoveryMode.SEED_PHRASE,
                    status=RecoveryStatus.FOUND,
                    found_value=result.seed_phrase,
                    found_address=result.matched_address,
                    found_address_type=result.address_type,
                    found_derivation_path=result.derivation_path,
                    seed_hex=result.seed_hex,
                    attempts=self._attempts,
                    time_elapsed=elapsed,
                    rate_per_second=self._attempts / elapsed if elapsed > 0 else 0,
                    strategy_used=strategy_name,
                    details={'found_results': found_results},
                )

            self._update_progress()

            # Check max attempts
            if config.max_attempts > 0 and self._attempts >= config.max_attempts:
                return self._make_result(
                    RecoveryStatus.NOT_FOUND,
                    strategy_name=strategy_name,
                    error_message=f"Max attempts ({config.max_attempts}) reached",
                )

        # Exhausted all candidates without finding a match
        return self._make_result(
            RecoveryStatus.NOT_FOUND,
            strategy_name=strategy_name,
            error_message="No valid seed phrase found for the given constraints",
        )

    def _select_seed_strategy(self, num_missing: int) -> SearchStrategy:
        """Automatically select the best seed phrase recovery strategy."""
        if self.config.strategy != SearchStrategy.AUTO:
            return self.config.strategy

        if num_missing == 1:
            last_pos = self.config.seed_length - 1
            if self.config.missing_positions == [last_pos]:
                return SearchStrategy.LWO  # Optimal: 128 candidates
            return SearchStrategy.HCP  # Good: 128-2048 candidates with checksum filter
        elif num_missing <= 4:
            return SearchStrategy.HCP  # Best for 2-4 missing words
        else:
            return SearchStrategy.FULL  # Fallback (infeasible without GPU)

    def _estimate_search_space(self, num_missing: int) -> int:
        """Estimate total candidates before checksum filtering."""
        if not self._wordlist:
            return 0
        wordlist_size = len(self._wordlist)

        # If last position is missing, LWO applies
        if num_missing >= 1 and (self.config.seed_length - 1) in self.config.missing_positions:
            other_missing = num_missing - 1
            if other_missing == 0:
                return 128  # Pure LWO for 12-word seed
            return wordlist_size ** other_missing * 128
        return wordlist_size ** num_missing

    # ─── PASSPHRASE RECOVERY ────────────────────────────────────────────

    def _recover_passphrase(self) -> BruteforceResult:
        """Recover BIP39 passphrase (25th word).

        Strategy:
        1. Common passphrases (fastest, most likely)
        2. Custom candidates
        3. Dictionary-based
        4. Mutations of partial passphrase
        5. Systematic enumeration (last resort, only short passphrases)
        """
        config = self.config

        if not config.known_words:
            return BruteforceResult(
                success=False, mode=RecoveryMode.PASSPHRASE,
                status=RecoveryStatus.ERROR,
                error_message="Known seed phrase required for passphrase recovery",
            )

        if not config.target_addresses and not config.wallet_file:
            return BruteforceResult(
                success=False, mode=RecoveryMode.PASSPHRASE,
                status=RecoveryStatus.ERROR,
                error_message="Target address or wallet file required for passphrase recovery",
            )

        seed_phrase = " ".join(config.known_words)

        # Build passphrase generator
        pass_config = PassphraseConfig(
            partial=config.partial_passphrase,
            custom_candidates=config.passphrase_candidates,
            dict_files=config.passphrase_dict_files,
            use_common=True,
            use_mutations=True,
            use_dict=True,
            max_length=64,
        )
        generator = PassphraseGenerator(pass_config)

        # Initialize pipeline for passphrase recovery
        self._pipeline = ProgressiveVerificationPipeline(
            target_addresses=config.target_addresses,
            addr_types=config.addr_types,
            coin=config.coin,
            num_addresses=config.num_addresses,
        )

        # Start checkpoint auto-save
        self._checkpoint_mgr.start_auto_save(self._get_checkpoint_state, "passphrase")

        strategy_name = "passphrase_smart"

        for candidate in generator.generate():
            if self._check_cancelled():
                return self._make_result(
                    RecoveryStatus.CANCELLED,
                    strategy_name=strategy_name,
                )

            self._attempts += 1

            result = self._pipeline.verify_passphrase(seed_phrase, candidate)

            if result.matched:
                elapsed = time.time() - self._start_time
                return BruteforceResult(
                    success=True,
                    mode=RecoveryMode.PASSPHRASE,
                    status=RecoveryStatus.FOUND,
                    found_value=candidate,
                    found_address=result.matched_address,
                    found_address_type=result.address_type,
                    seed_hex=result.seed_hex,
                    passphrase=candidate,
                    attempts=self._attempts,
                    time_elapsed=elapsed,
                    rate_per_second=self._attempts / elapsed if elapsed > 0 else 0,
                    strategy_used=strategy_name,
                )

            self._update_progress()

            if config.max_attempts > 0 and self._attempts >= config.max_attempts:
                return self._make_result(
                    RecoveryStatus.NOT_FOUND,
                    strategy_name=strategy_name,
                    error_message=f"Max attempts ({config.max_attempts}) reached",
                )

        return self._make_result(
            RecoveryStatus.NOT_FOUND,
            strategy_name=strategy_name,
            error_message="Passphrase not found in candidate list",
        )

    # ─── PASSWORD RECOVERY ──────────────────────────────────────────────

    def _recover_password(self) -> BruteforceResult:
        """Recover wallet file password.

        Strategy:
        1. Try btcrecover.py if available
        2. Built-in rule-based password recovery
        3. Dictionary attack with mutations
        """
        config = self.config

        # Try btcrecover.py first
        if config.btcrecover_path and os.path.isfile(config.btcrecover_path):
            result = self._try_btcrecover()
            if result and result.success:
                return result

        # Built-in password recovery
        if not config.wallet_file:
            return BruteforceResult(
                success=False, mode=RecoveryMode.PASSWORD,
                status=RecoveryStatus.ERROR,
                error_message="Wallet file required for password recovery",
            )

        wallet_path = Path(config.wallet_file)
        if not wallet_path.exists():
            return BruteforceResult(
                success=False, mode=RecoveryMode.PASSWORD,
                status=RecoveryStatus.ERROR,
                error_message=f"Wallet file not found: {wallet_path}",
            )

        # Build password generator
        pw_config = PasswordConfig(
            base_words=config.password_candidates[:10],
            custom_candidates=config.password_candidates,
            dict_files=config.password_dict_files,
            use_rules=True,
            use_dict=True,
        )
        generator = PasswordGenerator(pw_config)

        wallet_data = wallet_path.read_bytes()
        wallet_type = self._detect_wallet_type(wallet_data, wallet_path.suffix)

        strategy_name = "password_rule_based"

        for candidate in generator.generate():
            if self._check_cancelled():
                return self._make_result(
                    RecoveryStatus.CANCELLED,
                    strategy_name=strategy_name,
                )

            self._attempts += 1

            if self._try_wallet_password(wallet_data, candidate, wallet_type):
                elapsed = time.time() - self._start_time
                return BruteforceResult(
                    success=True,
                    mode=RecoveryMode.PASSWORD,
                    status=RecoveryStatus.FOUND,
                    found_value=candidate,
                    attempts=self._attempts,
                    time_elapsed=elapsed,
                    rate_per_second=self._attempts / elapsed if elapsed > 0 else 0,
                    strategy_used=strategy_name,
                    details={'wallet_type': wallet_type},
                )

            self._update_progress()

            if config.max_attempts > 0 and self._attempts >= config.max_attempts:
                return self._make_result(
                    RecoveryStatus.NOT_FOUND,
                    strategy_name=strategy_name,
                    error_message=f"Max attempts ({config.max_attempts}) reached",
                )

        return self._make_result(
            RecoveryStatus.NOT_FOUND,
            strategy_name=strategy_name,
            error_message="Password not found in candidates",
        )

    # ─── WORD PREDICTION RECOVERY ──────────────────────────────────────

    def recover_with_word_prediction(
        self, uncertain_words: List[Tuple[int, str]]
    ) -> BruteforceResult:
        """Recover seed phrase using Contextual Word Prediction.

        INVENTION: When a user is unsure about specific words (e.g., they
        wrote down "aband" instead of "abandon"), this method generates
        similar BIP39 words and tests them.

        Args:
            uncertain_words: List of (position, approximate_word) tuples

        Returns:
            BruteforceResult with the recovered seed phrase
        """
        predictor = ContextualWordPredictor(self._wordlist)

        # For each uncertain word, generate candidate alternatives
        word_candidates: Dict[int, List[str]] = {}
        for pos, approx_word in uncertain_words:
            candidates = predictor.predict_similar_words(approx_word, max_distance=3, max_results=50)
            word_candidates[pos] = candidates
            logger.info(f"Position {pos}: {len(candidates)} candidates for '{approx_word}'")

        # Build template with all known words
        template = list(self.config.known_words) if self.config.known_words else [None] * self.config.seed_length

        # Fill in known positions
        known_idx = 0
        for i in range(self.config.seed_length):
            if i not in word_candidates:
                if known_idx < len(self.config.known_words):
                    template[i] = self.config.known_words[known_idx]
                    known_idx += 1

        # Try all combinations of predicted words
        positions = sorted(word_candidates.keys())
        candidate_lists = [word_candidates[p] for p in positions]

        total = 1
        for cl in candidate_lists:
            total *= len(cl)
        logger.info(f"Word prediction: testing {total} combinations")

        import itertools
        for combo in itertools.product(*candidate_lists):
            if self._check_cancelled():
                return self._make_result(RecoveryStatus.CANCELLED, strategy_name="cwp")

            self._attempts += 1
            for i, pos in enumerate(positions):
                template[pos] = combo[i]

            result = self._pipeline.verify(template)
            if result.matched:
                elapsed = time.time() - self._start_time
                return BruteforceResult(
                    success=True,
                    mode=RecoveryMode.SEED_PHRASE,
                    status=RecoveryStatus.FOUND,
                    found_value=result.seed_phrase,
                    found_address=result.matched_address,
                    seed_hex=result.seed_hex,
                    attempts=self._attempts,
                    time_elapsed=elapsed,
                    rate_per_second=self._attempts / elapsed if elapsed > 0 else 0,
                    strategy_used="cwp",
                )

            self._update_progress()

        return self._make_result(
            RecoveryStatus.NOT_FOUND,
            strategy_name="cwp",
            error_message="No matching seed phrase found with word predictions",
        )

    # ─── EXTERNAL TOOL INTEGRATION ──────────────────────────────────────

    def _try_seedrecover(self) -> Optional[BruteforceResult]:
        """Try seedrecover.py for seed phrase recovery."""
        import subprocess
        config = self.config
        if not config.seedrecover_path:
            return None

        try:
            template = [None] * config.seed_length
            known_idx = 0
            for i in range(config.seed_length):
                if i in config.missing_positions:
                    template[i] = None
                elif known_idx < len(config.known_words):
                    template[i] = config.known_words[known_idx]
                    known_idx += 1

            cmd = [
                sys.executable, config.seedrecover_path,
                "--mnemonic", " ".join(str(w) if w else "?" for w in template),
                "--wallet-type", "bitcoin",
                "--addr-limit", str(config.num_addresses),
                "--num-threads", str(config.num_threads or multiprocessing.cpu_count()),
            ]
            if config.target_addresses:
                cmd.extend(["--addr-search", config.target_addresses[0]])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    if "SEED FOUND" in line or "found" in line.lower():
                        found_seed = line.split(":")[-1].strip() if ":" in line else ""
                        elapsed = time.time() - self._start_time
                        return BruteforceResult(
                            success=True, mode=RecoveryMode.SEED_PHRASE,
                            status=RecoveryStatus.FOUND,
                            found_value=found_seed,
                            time_elapsed=elapsed,
                            strategy_used="seedrecover.py",
                        )
        except Exception as e:
            logger.debug(f"seedrecover.py failed: {e}")
        return None

    def _try_btcrecover(self) -> Optional[BruteforceResult]:
        """Try btcrecover.py for password recovery."""
        import subprocess
        import tempfile
        config = self.config
        if not config.btcrecover_path or not config.wallet_file:
            return None

        try:
            cmd = [
                sys.executable, config.btcrecover_path,
                "--wallet", config.wallet_file,
                "--threads", str(config.num_threads or multiprocessing.cpu_count()),
            ]

            temp_path = None
            if config.password_dict_files:
                cmd.extend(["--passwordlist", config.password_dict_files[0]])
            elif config.password_candidates:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
                    for pw in config.password_candidates:
                        f.write(pw + "\n")
                    temp_path = f.name
                cmd.extend(["--passwordlist", temp_path])

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split("\n"):
                        if "PASSWORD FOUND" in line or "found" in line.lower():
                            found = line.split(":")[-1].strip() if ":" in line else ""
                            elapsed = time.time() - self._start_time
                            return BruteforceResult(
                                success=True, mode=RecoveryMode.PASSWORD,
                                status=RecoveryStatus.FOUND,
                                found_value=found,
                                time_elapsed=elapsed,
                                strategy_used="btcrecover.py",
                            )
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
        except Exception as e:
            logger.debug(f"btcrecover.py failed: {e}")
        return None

    # ─── WALLET HELPERS ────────────────────────────────────────────────

    def _detect_wallet_type(self, data: bytes, extension: str) -> str:
        """Detect wallet type from file data and extension."""
        import json as json_module
        if extension == ".dat" or b"\x0b\x0f\x06\x00\x00\x00" in data[:20]:
            return "bitcoin_core"
        try:
            text = data.decode("utf-8", errors="ignore")
            if '"seed_version"' in text or '"keystore"' in text:
                return "electrum"
        except Exception:
            pass
        try:
            text = data.decode("utf-8", errors="ignore")
            if '"data"' in text and '"iv"' in text and '"salt"' in text:
                return "metamask_vault"
        except Exception:
            pass
        return "unknown"

    def _try_wallet_password(self, data: bytes, password: str, wallet_type: str) -> bool:
        """Try a password against a wallet file."""
        import json as json_module
        if wallet_type == "metamask_vault":
            try:
                vault = json_module.loads(data.decode("utf-8"))
                if isinstance(vault, dict) and "data" in vault:
                    vault_data = vault
                elif isinstance(vault, list) and len(vault) > 0:
                    vault_data = vault[0] if isinstance(vault[0], dict) else vault
                else:
                    return False

                salt = bytes.fromhex(vault_data.get("salt", ""))
                iv = bytes.fromhex(vault_data.get("iv", ""))
                encrypted_data = bytes.fromhex(vault_data.get("data", ""))

                if not salt or not iv or not encrypted_data:
                    return False

                derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 10000, dklen=32)

                try:
                    from Crypto.Cipher import AES
                    cipher = AES.new(derived_key[:16], AES.MODE_CTR, nonce=b"", initial_value=iv)
                    decrypted = cipher.decrypt(encrypted_data)
                    try:
                        json_module.loads(decrypted.decode("utf-8"))
                        return True
                    except (json_module.JSONDecodeError, UnicodeDecodeError):
                        return False
                except ImportError:
                    try:
                        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                        cipher = Cipher(algorithms.AES(derived_key[:16]), modes.CTR(iv))
                        decryptor = cipher.decryptor()
                        decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
                        try:
                            json_module.loads(decrypted.decode("utf-8"))
                            return True
                        except (json_module.JSONDecodeError, UnicodeDecodeError):
                            return False
                    except ImportError:
                        return False
            except Exception:
                return False
        return False

    # ─── RESULT BUILDER ────────────────────────────────────────────────

    def _make_result(
        self,
        status: RecoveryStatus,
        strategy_name: str = "",
        error_message: str = None,
    ) -> BruteforceResult:
        """Create a result object with current stats."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        return BruteforceResult(
            success=status == RecoveryStatus.FOUND,
            mode=self.config.mode,
            status=status,
            attempts=self._attempts,
            time_elapsed=elapsed,
            rate_per_second=self._attempts / elapsed if elapsed > 0 else 0,
            strategy_used=strategy_name,
            error_message=error_message,
        )

    # ─── STATIC UTILITY METHODS ────────────────────────────────────────

    @staticmethod
    def list_strategies(num_missing: int, seed_length: int = 12,
                        last_missing: bool = False) -> List[Dict]:
        """List available strategies for a given recovery scenario."""
        strategies = []
        if num_missing == 1 and last_missing:
            strategies.append({
                'name': 'LWO',
                'description': 'Last-Word Optimization',
                'candidates': 128 if seed_length == 12 else 8,
                'estimated_time': '<1 second',
                'recommended': True,
            })
        elif num_missing == 1:
            strategies.append({
                'name': 'HCP',
                'description': 'Hierarchical Checksum Pruning',
                'candidates': 128 if last_missing else 2048,
                'estimated_time': '<1 second',
                'recommended': True,
            })
        elif num_missing <= 4:
            strategies.append({
                'name': 'HCP',
                'description': 'Hierarchical Checksum Pruning',
                'candidates': 'varies (16x reduction vs full)',
                'estimated_time': 'minutes to hours',
                'recommended': True,
            })
        strategies.append({
            'name': 'STATISTICAL',
            'description': 'Statistical Word Prioritization',
            'candidates': 'same as HCP but tries common words first',
            'estimated_time': 'potentially faster than HCP',
            'recommended': False,
        })
        strategies.append({
            'name': 'FULL',
            'description': 'Full Enumeration',
            'candidates': f'{2048**num_missing:,}',
            'estimated_time': 'varies widely',
            'recommended': False,
        })
        return strategies

    @staticmethod
    def estimate_recovery_time(
        num_missing: int,
        seed_length: int = 12,
        last_position_missing: bool = False,
        hash_rate: float = 1500.0,
    ) -> Dict:
        """Estimate recovery time for a given scenario.

        Args:
            num_missing: Number of missing words
            seed_length: Seed phrase length
            last_position_missing: Whether the last position is among the missing
            hash_rate: Expected verification rate (seeds/sec)

        Returns:
            Dict with estimates
        """
        import math

        if num_missing == 0:
            return {'total_candidates': 0, 'valid_candidates': 0, 'estimated_seconds': 0,
                    'checksum_pruning_ratio': 'N/A', 'estimated_time': '0 ms', 'hash_rate_used': hash_rate}

        # Calculate LWO candidates for given seed length
        # 12-word: 128, 15-word: 64, 18-word: 32, 21-word: 16, 24-word: 8
        lwo_count = 2048 // (2 ** (seed_length * 11 // 33)) if seed_length in (12, 15, 18, 21, 24) else 2048

        # Calculate search space
        if last_position_missing and num_missing == 1:
            total = lwo_count
        elif last_position_missing and num_missing > 1:
            total = 2048 ** (num_missing - 1) * lwo_count
        else:
            total = 2048 ** num_missing

        # After checksum filtering
        checksum_bits = seed_length * 11 // 33
        valid_after_checksum = max(1, total // (2 ** checksum_bits)) if total > 0 else 1

        # Estimated time
        est_seconds = valid_after_checksum / hash_rate if hash_rate > 0 else float('inf')
        pruning_ratio = f'{100 * (1 - valid_after_checksum/total):.1f}% eliminated' if total > 0 else 'N/A'

        return {
            'total_candidates': total,
            'valid_after_checksum': valid_after_checksum,
            'checksum_pruning_ratio': pruning_ratio,
            'estimated_seconds': est_seconds,
            'estimated_time': _format_time(est_seconds),
            'hash_rate_used': hash_rate,
        }


def _format_time(seconds: float) -> str:
    """Format seconds into human-readable time string."""
    if seconds < 1:
        return f"{seconds*1000:.0f} ms"
    elif seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    elif seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    else:
        return f"{seconds/86400:.1f} days"
