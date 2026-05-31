"""
CryptoRecover - Progressive Verification Pipeline (PVP)
=========================================================
Multi-stage verification with increasing computational cost per stage.
This is the key innovation that makes bruteforce recovery feasible by
eliminating invalid candidates at the cheapest possible stage.

Pipeline stages:
Stage 1: BIP39 Checksum Validation (~0.001ms per candidate)
    → Eliminates 93.75%+ candidates for free
Stage 2: PBKDF2-SHA512 Seed Derivation (~8-15ms per candidate on CPU)
    → Produces 64-byte seed from mnemonic + passphrase
Stage 3: BIP32 Master Key Derivation (~0.5ms per candidate)
    → Derive master extended key from seed
Stage 4: First Address Generation (~2ms per candidate)
    → Derive first receive address using BIP44/49/84/86
Stage 5: Address Matching with Bloom Filter (~0.001ms per candidate)
    → Fast probabilistic check against target addresses
Stage 6: Exact Address Verification (~0.001ms per candidate)
    → Definitive check, only reached for bloom filter hits

INVENTION: "Progressive Verification Pipeline" (PVP) - By ordering verification
stages from cheapest to most expensive, and by eliminating candidates at the
earliest possible stage, we achieve massive speedups. For 12-word seeds with
1 missing word: Stage 1 alone eliminates 93.75% of candidates, saving ~94%
of PBKDF2 computations.

Combined with HCP (Hierarchical Checksum Pruning), we never even generate
candidates that would fail Stage 1, saving even more time.
"""

import hashlib
import time
import logging
from typing import List, Optional, Dict, Tuple, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from .address_derivation import (
    AddressMatcher, AddressType, mnemonic_to_seed, seed_to_master_key,
    generate_address, derive_first_address, check_seed_against_targets,
    COIN_CONFIG, DERIVATION_PATHS,
)
from .checksum_filter import validate_bip39_checksum, get_bip39_wordlist

logger = logging.getLogger(__name__)


# ============================================================================
# PIPELINE STAGES
# ============================================================================

class PipelineStage(Enum):
    """Verification pipeline stages, ordered by cost."""
    CHECKSUM = 1          # ~0.001ms - BIP39 checksum validation
    SEED_DERIVATION = 2   # ~8-15ms - PBKDF2-SHA512 (2048 iterations)
    MASTER_KEY = 3        # ~0.5ms - BIP32 master key derivation
    ADDRESS_DERIVATION = 4  # ~2ms - HD wallet address derivation
    BLOOM_FILTER = 5      # ~0.001ms - Probabilistic address match
    EXACT_MATCH = 6       # ~0.001ms - Definitive address verification


@dataclass
class PipelineStats:
    """Statistics for the progressive verification pipeline."""
    candidates_entered: int = 0
    passed_checksum: int = 0
    passed_seed_derivation: int = 0
    passed_master_key: int = 0
    passed_address_derivation: int = 0
    passed_bloom_filter: int = 0
    exact_matches: int = 0
    time_in_checksum: float = 0.0
    time_in_seed: float = 0.0
    time_in_master_key: float = 0.0
    time_in_address: float = 0.0
    time_in_matching: float = 0.0

    def summary(self) -> str:
        """Return a human-readable summary of pipeline statistics."""
        total = self.candidates_entered or 1
        lines = [
            f"Pipeline Statistics:",
            f"  Candidates entered:      {self.candidates_entered:,}",
            f"  Passed checksum:         {self.passed_checksum:,} ({100*self.passed_checksum/total:.2f}%)",
            f"  Passed seed derivation:  {self.passed_seed_derivation:,} ({100*self.passed_seed_derivation/total:.2f}%)",
            f"  Passed master key:       {self.passed_master_key:,} ({100*self.passed_master_key/total:.2f}%)",
            f"  Passed address deriv:    {self.passed_address_derivation:,} ({100*self.passed_address_derivation/total:.2f}%)",
            f"  Passed bloom filter:     {self.passed_bloom_filter:,} ({100*self.passed_bloom_filter/total:.2f}%)",
            f"  Exact matches:           {self.exact_matches:,}",
            f"",
            f"  Time in checksum:        {self.time_in_checksum:.3f}s",
            f"  Time in seed derivation: {self.time_in_seed:.3f}s",
            f"  Time in master key:      {self.time_in_master_key:.3f}s",
            f"  Time in address deriv:   {self.time_in_address:.3f}s",
            f"  Time in matching:        {self.time_in_matching:.3f}s",
        ]
        return "\n".join(lines)

    @property
    def pruning_efficiency(self) -> float:
        """Percentage of candidates eliminated before expensive stages."""
        if self.candidates_entered == 0:
            return 0.0
        return 100.0 * (1.0 - self.passed_seed_derivation / self.candidates_entered)


@dataclass
class VerificationResult:
    """Result of verifying a candidate through the pipeline."""
    passed: bool
    matched: bool
    stage_reached: PipelineStage
    seed_phrase: Optional[str] = None
    passphrase: Optional[str] = None
    seed_hex: Optional[str] = None
    matched_address: Optional[str] = None
    address_type: Optional[str] = None
    derivation_path: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# PROGRESSIVE VERIFICATION PIPELINE
# ============================================================================

class ProgressiveVerificationPipeline:
    """INVENTION: Progressive Verification Pipeline (PVP)

    Multi-stage candidate verification that eliminates invalid candidates
    at the cheapest possible stage, dramatically reducing total computation.

    Key principle: Fail fast, fail cheap.
    - Checksum is ~10000x cheaper than PBKDF2
    - PBKDF2 is ~5x cheaper than full address derivation
    - Bloom filter check is ~1000x cheaper than exact comparison

    By ordering stages from cheapest to most expensive, we achieve
    maximum efficiency with minimum wasted computation.
    """

    def __init__(
        self,
        target_addresses: List[str] = None,
        addr_types: List[str] = None,
        coin: str = "BTC",
        num_addresses: int = 5,
        passphrase: str = "",
        wordlist: List[str] = None,
    ):
        """Initialize the verification pipeline.

        Args:
            target_addresses: List of target addresses to match against
            addr_types: Address types to derive (P2PKH, P2SH-P2WPKH, P2WPKH, P2TR)
            coin: Cryptocurrency symbol
            num_addresses: Number of addresses to derive per type
            passphrase: Known passphrase (empty string if none)
            wordlist: BIP39 wordlist
        """
        self.target_addresses = target_addresses or []
        self.addr_types = addr_types or [AddressType.P2WPKH, AddressType.P2PKH, AddressType.P2SH_P2WPKH]
        self.coin = coin
        self.num_addresses = num_addresses
        self.passphrase = passphrase
        self.wordlist = wordlist or get_bip39_wordlist()

        # Build address matcher with bloom filter
        self.matcher = AddressMatcher(self.target_addresses) if self.target_addresses else None
        self.has_targets = bool(self.target_addresses)

        self.stats = PipelineStats()

    def verify(self, words: List[str]) -> VerificationResult:
        """Run a candidate through the full verification pipeline.

        Args:
            words: Complete seed phrase (list of words)

        Returns:
            VerificationResult with details of how far the candidate got
        """
        self.stats.candidates_entered += 1
        seed_phrase = " ".join(words)

        # Stage 1: BIP39 Checksum Validation
        t0 = time.perf_counter()
        checksum_valid = validate_bip39_checksum(words, self.wordlist)
        self.stats.time_in_checksum += time.perf_counter() - t0
        if not checksum_valid:
            return VerificationResult(
                passed=False, matched=False,
                stage_reached=PipelineStage.CHECKSUM,
                seed_phrase=seed_phrase,
                error="Checksum failed"
            )
        self.stats.passed_checksum += 1

        # Stage 2: PBKDF2-SHA512 Seed Derivation
        t0 = time.perf_counter()
        try:
            seed_bytes = mnemonic_to_seed(seed_phrase, self.passphrase)
            seed_hex = seed_bytes.hex()
        except Exception as e:
            return VerificationResult(
                passed=True, matched=False,
                stage_reached=PipelineStage.SEED_DERIVATION,
                seed_phrase=seed_phrase,
                error=f"Seed derivation failed: {e}"
            )
        self.stats.passed_seed_derivation += 1
        self.stats.time_in_seed += time.perf_counter() - t0

        # If no target addresses, a valid checksum + seed derivation is enough
        if not self.has_targets:
            return VerificationResult(
                passed=True, matched=True,
                stage_reached=PipelineStage.EXACT_MATCH,
                seed_phrase=seed_phrase,
                seed_hex=seed_hex,
            )

        # Stage 3: BIP32 Master Key Derivation
        t0 = time.perf_counter()
        try:
            master = seed_to_master_key(seed_bytes)
        except ValueError as e:
            return VerificationResult(
                passed=True, matched=False,
                stage_reached=PipelineStage.MASTER_KEY,
                seed_phrase=seed_phrase,
                seed_hex=seed_hex,
                error=f"Master key derivation failed: {e}"
            )
        self.stats.passed_master_key += 1
        self.stats.time_in_master_key += time.perf_counter() - t0

        # Stage 4-6: Address derivation + bloom filter + exact match
        t0 = time.perf_counter()
        for addr_type in self.addr_types:
            for i in range(self.num_addresses):
                try:
                    addr = generate_address(master, addr_type, self.coin, 0, i)
                except Exception:
                    continue

                if not addr:
                    continue

                self.stats.passed_address_derivation += 1

                if self.matcher:
                    # Stage 5: Bloom filter check
                    if self.matcher.quick_check(addr):
                        self.stats.passed_bloom_filter += 1

                        # Stage 6: Exact match
                        if self.matcher.matches(addr):
                            self.stats.exact_matches += 1
                            self.stats.time_in_matching += time.perf_counter() - t0
                            return VerificationResult(
                                passed=True, matched=True,
                                stage_reached=PipelineStage.EXACT_MATCH,
                                seed_phrase=seed_phrase,
                                passphrase=self.passphrase or None,
                                seed_hex=seed_hex,
                                matched_address=addr,
                                address_type=addr_type,
                                derivation_path=DERIVATION_PATHS.get(addr_type, "").format(
                                    slip44=COIN_CONFIG.get(self.coin, COIN_CONFIG["BTC"])[5],
                                    index=i
                                ),
                            )

        self.stats.time_in_matching += time.perf_counter() - t0
        return VerificationResult(
            passed=True, matched=False,
            stage_reached=PipelineStage.EXACT_MATCH,
            seed_phrase=seed_phrase,
            seed_hex=seed_hex,
        )

    def verify_seed_only(self, words: List[str]) -> VerificationResult:
        """Fast verification that only checks checksum + seed derivation.
        Used when we don't have target addresses and just need valid seeds.
        """
        self.stats.candidates_entered += 1
        seed_phrase = " ".join(words)

        # Stage 1: Checksum
        if not validate_bip39_checksum(words, self.wordlist):
            return VerificationResult(
                passed=False, matched=False,
                stage_reached=PipelineStage.CHECKSUM,
                seed_phrase=seed_phrase,
            )
        self.stats.passed_checksum += 1

        # Stage 2: Seed derivation
        try:
            seed_bytes = mnemonic_to_seed(seed_phrase, self.passphrase)
            seed_hex = seed_bytes.hex()
        except Exception as e:
            return VerificationResult(
                passed=True, matched=False,
                stage_reached=PipelineStage.SEED_DERIVATION,
                seed_phrase=seed_phrase,
                error=str(e),
            )

        self.stats.passed_seed_derivation += 1
        return VerificationResult(
            passed=True, matched=True,
            stage_reached=PipelineStage.SEED_DERIVATION,
            seed_phrase=seed_phrase,
            seed_hex=seed_hex,
        )

    def verify_passphrase(
        self, seed_phrase: str, passphrase_candidate: str
    ) -> VerificationResult:
        """Verify a passphrase candidate against a known seed phrase.

        This is the pipeline for passphrase recovery: we already know
        the seed phrase, we just need to find the passphrase that
        generates the target addresses.
        """
        self.stats.candidates_entered += 1

        # For passphrase recovery, there's no checksum stage
        # Stage 2: Seed derivation with passphrase
        t0 = time.perf_counter()
        try:
            seed_bytes = mnemonic_to_seed(seed_phrase, passphrase_candidate)
            seed_hex = seed_bytes.hex()
        except Exception as e:
            return VerificationResult(
                passed=False, matched=False,
                stage_reached=PipelineStage.SEED_DERIVATION,
                error=str(e),
            )
        self.stats.passed_seed_derivation += 1
        self.stats.time_in_seed += time.perf_counter() - t0

        if not self.has_targets:
            return VerificationResult(
                passed=True, matched=True,
                stage_reached=PipelineStage.SEED_DERIVATION,
                passphrase=passphrase_candidate,
                seed_hex=seed_hex,
            )

        # Stage 3: Master key
        t0 = time.perf_counter()
        try:
            master = seed_to_master_key(seed_bytes)
        except ValueError:
            return VerificationResult(
                passed=True, matched=False,
                stage_reached=PipelineStage.MASTER_KEY,
                passphrase=passphrase_candidate,
                seed_hex=seed_hex,
            )
        self.stats.passed_master_key += 1
        self.stats.time_in_master_key += time.perf_counter() - t0

        # Stage 4-6: Address derivation + matching
        t0 = time.perf_counter()
        for addr_type in self.addr_types:
            for i in range(self.num_addresses):
                try:
                    addr = generate_address(master, addr_type, self.coin, 0, i)
                except Exception:
                    continue
                if not addr:
                    continue

                self.stats.passed_address_derivation += 1
                if self.matcher and self.matcher.matches(addr):
                    self.stats.exact_matches += 1
                    self.stats.time_in_matching += time.perf_counter() - t0
                    return VerificationResult(
                        passed=True, matched=True,
                        stage_reached=PipelineStage.EXACT_MATCH,
                        passphrase=passphrase_candidate,
                        seed_hex=seed_hex,
                        matched_address=addr,
                        address_type=addr_type,
                    )

        self.stats.time_in_matching += time.perf_counter() - t0
        return VerificationResult(
            passed=True, matched=False,
            stage_reached=PipelineStage.EXACT_MATCH,
            passphrase=passphrase_candidate,
            seed_hex=seed_hex,
        )

    def get_stats(self) -> PipelineStats:
        """Return current pipeline statistics."""
        return self.stats

    def reset_stats(self):
        """Reset pipeline statistics."""
        self.stats = PipelineStats()
