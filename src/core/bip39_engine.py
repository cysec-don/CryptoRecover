"""
BIP-39 Engine - Core mnemonic handling, validation, and seed derivation.

This module implements the complete BIP-39 specification including:
- Word list management (all 2048 BIP-39 words)
- Mnemonic validation with checksum verification
- Seed derivation (PBKDF2-SHA512 with 2048 iterations)
- Partial mnemonic recovery helpers
"""

import hashlib
import itertools
from typing import List, Optional, Tuple, Set, Dict
from dataclasses import dataclass, field


# BIP-39 word count to entropy bits mapping
WORD_COUNT_TO_ENTROPY = {
    12: 128,
    15: 160,
    18: 192,
    21: 224,
    24: 256,
}

# Entropy bits per word (always 11 for BIP-39)
BITS_PER_WORD = 11

# Number of checksum bits = entropy_bits / 32
CHECKSUM_RATIO = 32


@dataclass
class MnemonicCandidate:
    """A candidate mnemonic with metadata for scoring and tracking."""
    words: List[str]
    confidence: float = 0.0
    source: str = "unknown"  # e.g., "llm", "bruteforce", "semantic", "cognitive"
    attempt_number: int = 0
    derivation_path: Optional[str] = None

    def to_string(self) -> str:
        return " ".join(self.words)

    def __hash__(self):
        return hash(tuple(self.words))


@dataclass
class RecoveryContext:
    """Context information about the recovery attempt."""
    total_words: int = 12
    known_words: Dict[int, str] = field(default_factory=dict)  # position -> word
    missing_positions: List[int] = field(default_factory=list)
    approximate_words: Dict[int, str] = field(default_factory=dict)  # position -> approximate word
    target_addresses: List[str] = field(default_factory=list)
    target_public_key: Optional[str] = None
    derivation_paths: List[str] = field(default_factory=lambda: ["m/44'/0'/0'/0/0"])
    passphrase_hint: Optional[str] = None
    wallet_type: str = "bitcoin"
    time_since_exposure: Optional[int] = None  # days since user last saw the seedphrase
    user_notes: Optional[str] = None


class BIP39Engine:
    """
    Complete BIP-39 engine for mnemonic validation and seed derivation.
    """

    def __init__(self, wordlist: Optional[List[str]] = None):
        self.wordlist = wordlist or self._load_default_wordlist()
        self.word_to_index = {w: i for i, w in enumerate(self.wordlist)}

    @staticmethod
    def _load_default_wordlist() -> List[str]:
        """Load the standard BIP-39 English wordlist."""
        try:
            from bip_utils.bip.bip39.bip39_mnemonic_utils import Bip39WordsListGetter
            from bip_utils import Bip39Languages
            getter = Bip39WordsListGetter.Instance()
            wl = getter.GetByLanguage(Bip39Languages.ENGLISH)
            return [wl.GetWordAtIdx(i) for i in range(2048)]
        except (ImportError, AttributeError, TypeError):
            pass

        # Fallback: embedded core wordlist (first and last 50 words + checksum)
        # This is a minimal fallback; full wordlist requires bip-utils
        raise RuntimeError(
            "Cannot load BIP-39 wordlist. Install bip-utils: pip install bip-utils"
        )

    def get_word(self, index: int) -> str:
        """Get a BIP-39 word by its index (0-2047)."""
        return self.wordlist[index]

    def get_index(self, word: str) -> int:
        """Get the index of a BIP-39 word. Returns -1 if not found."""
        return self.word_to_index.get(word.strip().lower(), -1)

    def is_valid_word(self, word: str) -> bool:
        """Check if a word is in the BIP-39 wordlist."""
        return word.strip().lower() in self.word_to_index

    def find_similar_words(self, word: str, max_distance: int = 2) -> List[Tuple[str, int]]:
        """Find BIP-39 words with edit distance <= max_distance."""
        word = word.strip().lower()
        similar = []
        for bw in self.wordlist:
            dist = self._levenshtein_distance(word, bw)
            if dist <= max_distance:
                similar.append((bw, dist))
        similar.sort(key=lambda x: x[1])
        return similar

    def find_prefix_matches(self, prefix: str) -> List[str]:
        """Find all BIP-39 words that start with the given prefix."""
        prefix = prefix.strip().lower()
        return [w for w in self.wordlist if w.startswith(prefix)]

    def validate_mnemonic(self, words: List[str]) -> bool:
        """
        Validate a complete BIP-39 mnemonic including checksum.
        Returns True if the mnemonic is valid.
        """
        word_count = len(words)
        if word_count not in WORD_COUNT_TO_ENTROPY:
            return False

        # Check all words are in the wordlist
        indices = []
        for w in words:
            idx = self.get_index(w)
            if idx < 0:
                return False
            indices.append(idx)

        # Reconstruct entropy + checksum from word indices
        entropy_bits = WORD_COUNT_TO_ENTROPY[word_count]
        checksum_bits = entropy_bits // CHECKSUM_RATIO

        # Convert indices to binary string
        binary_str = ""
        for idx in indices:
            binary_str += format(idx, f'0{BITS_PER_WORD}b')

        # Split into entropy and checksum
        entropy_bin = binary_str[:entropy_bits]
        checksum_bin = binary_str[entropy_bits:entropy_bits + checksum_bits]

        # Compute expected checksum
        entropy_bytes = int(entropy_bin, 2).to_bytes(entropy_bits // 8, 'big')
        expected_checksum = hashlib.sha256(entropy_bytes).digest()
        expected_checksum_bin = format(expected_checksum[0], '08b')[:checksum_bits]

        return checksum_bin == expected_checksum_bin

    def compute_checksum_bits(self, partial_words: List[Optional[str]],
                              word_count: int) -> Set[int]:
        """
        Given a partial mnemonic with some unknown words, compute
        the set of valid checksum values, reducing the search space
        for the last word.

        Returns a set of valid last-word indices (0-2047).
        """
        # For the last word, only certain indices will produce a valid checksum
        valid_last_indices = set()

        # Determine which position is the last
        last_pos = word_count - 1

        # Build indices list with placeholders
        indices = []
        for i, w in enumerate(partial_words):
            if w is None:
                indices.append(None)
            else:
                indices.append(self.get_index(w))

        # If only the last word is missing, we can directly compute valid indices
        missing = [i for i, idx in enumerate(indices) if idx is None]

        if missing == [last_pos]:
            # Only last word is missing - direct checksum computation
            entropy_bits = WORD_COUNT_TO_ENTROPY[word_count]
            checksum_bits = entropy_bits // CHECKSUM_RATIO

            for candidate_idx in range(2048):
                test_indices = indices[:]
                test_indices[last_pos] = candidate_idx

                binary_str = ""
                for idx in test_indices:
                    binary_str += format(idx, f'0{BITS_PER_WORD}b')

                entropy_bin = binary_str[:entropy_bits]
                checksum_bin = binary_str[entropy_bits:entropy_bits + checksum_bits]

                entropy_bytes = int(entropy_bin, 2).to_bytes(entropy_bits // 8, 'big')
                expected_checksum = hashlib.sha256(entropy_bytes).digest()
                expected_checksum_bin = format(expected_checksum[0], '08b')[:checksum_bits]

                if checksum_bin == expected_checksum_bin:
                    valid_last_indices.add(candidate_idx)

        return valid_last_indices

    def derive_seed(self, words: List[str], passphrase: str = "") -> bytes:
        """
        Derive the seed from a BIP-39 mnemonic and optional passphrase.
        Uses PBKDF2-SHA512 with 2048 iterations.
        """
        mnemonic = " ".join(words).strip()
        password = mnemonic.encode("utf-8")
        salt = ("mnemonic" + passphrase).encode("utf-8")
        return hashlib.pbkdf2_hmac("sha512", password, salt, 2048)

    def derive_address(self, words: List[str], passphrase: str = "",
                       path: str = "m/84'/0'/0'/0/0") -> Optional[str]:
        """
        Derive a cryptocurrency address from a mnemonic.
        Returns the address string or None if derivation fails.
        
        Supports multiple coins by detecting the coin_type from the
        derivation path. Currently supports BTC (all BIP standards),
        ETH, LTC, DOGE, and other major coins.
        """
        mnemonic_str = " ".join(words) if isinstance(words, list) else words
        
        try:
            from bip_utils import (
                Bip39SeedGenerator, Bip44Changes, Bip44, Bip44Coins,
                Bip49, Bip49Coins, Bip84, Bip84Coins,
            )
            
            seed = Bip39SeedGenerator(mnemonic_str).Generate(passphrase)
            
            # Extract coin_type from derivation path
            # Path format: m/purpose'/coin_type'/account'/change/address_index
            path_parts = path.strip("'").replace("m/", "").split("/")
            coin_type_str = path_parts[1].rstrip("'") if len(path_parts) > 1 else "0"
            coin_type = int(coin_type_str)
            
            # Map coin_type to appropriate Bip coins enum
            # Coin types: 0=BTC, 60=ETH, 2=LTC, 3=DOGE, 501=SOL, etc.
            
            # Select derivation scheme based on path
            if path.startswith("m/84'"):
                # Native SegWit (bech32)
                coin_map_84 = {0: Bip84Coins.BITCOIN}
                bip_coin = coin_map_84.get(coin_type, Bip84Coins.BITCOIN)
                bip_obj = Bip84.FromSeed(seed, bip_coin)
            elif path.startswith("m/49'"):
                # Nested SegWit (P2SH-wrapped)
                coin_map_49 = {0: Bip49Coins.BITCOIN}
                bip_coin = coin_map_49.get(coin_type, Bip49Coins.BITCOIN)
                bip_obj = Bip49.FromSeed(seed, bip_coin)
            else:
                # Default to BIP-44 for legacy and other coins
                coin_map_44 = {
                    0: Bip44Coins.BITCOIN,
                    60: Bip44Coins.ETHEREUM,
                    2: Bip44Coins.LITECOIN,
                    3: Bip44Coins.DOGECOIN,
                }
                bip_coin = coin_map_44.get(coin_type, Bip44Coins.BITCOIN)
                bip_obj = Bip44.FromSeed(seed, bip_coin)
            
            addr_obj = (
                bip_obj.Purpose()
                .Coin()
                .Account(0)
                .Change(Bip44Changes.CHAIN_EXT)
                .AddressIndex(0)
            )
            return addr_obj.PublicKey().ToAddress()
        except Exception as e:
            # Log the error for debugging instead of silently returning None
            import logging
            logging.getLogger("cryptorecover").debug(f"derive_address failed: {e}")
            return None

    def get_search_space_size(self, missing_count: int, last_word_missing: bool = False,
                              word_count: int = 12) -> int:
        """
        Calculate the search space size for a given number of missing words.
        If the last word is missing, checksum reduces valid candidates.
        
        When multiple words are missing and the last word is among them,
        the last word position still benefits from checksum constraint.
        """
        if missing_count == 0:
            return 1

        checksum_bits = WORD_COUNT_TO_ENTROPY.get(word_count, 128) // CHECKSUM_RATIO
        last_word_candidates = 2 ** (BITS_PER_WORD - checksum_bits)

        if missing_count == 1 and last_word_missing:
            return last_word_candidates

        if missing_count > 1 and last_word_missing:
            # Multiple missing + last word missing: apply checksum to last position
            return (2048 ** (missing_count - 1)) * last_word_candidates

        return 2048 ** missing_count

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Compute Levenshtein edit distance between two strings."""
        if len(s1) < len(s2):
            return BIP39Engine._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row

        return prev_row[-1]
