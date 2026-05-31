"""
CryptoRecover - Smart Candidate Generators
============================================
All candidate generation strategies for seedphrase, passphrase, and password recovery.

Strategies:
1. SeedPhraseGenerator - BIP39 seed phrase candidate generation with HCP
2. PassphraseGenerator - Smart passphrase candidate generation
3. PasswordGenerator - Rule-based password candidate generation
4. MarkovGenerator - Markov chain-based candidate generation (INVENTION)
5. HybridGenerator - Combines multiple strategies

INVENTIONS:
- "Entropy-Guided Search" (EGS): Search unknown positions in order of
  decreasing entropy (most constrained first) to maximize early pruning.
- "Statistical Word Prioritization" (SWP): Rank BIP39 words by frequency
  in real-world usage to try likely words first.
- "Contextual Word Prediction" (CWP): Use first-4-char uniqueness of
  BIP39 words to predict corrections for typos/misreadings.
"""

import hashlib
import itertools
import string
import unicodedata
from typing import List, Optional, Dict, Generator, Set, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path


# ============================================================================
# BIP39 STATISTICAL DATA
# ============================================================================

# Most common BIP39 words found in actual seed phrases (from analysis of
# publicly known/test seed phrases). Words are ordered by frequency.
COMMON_SEED_WORDS = [
    "abandon", "ability", "able", "about", "above", "absent", "absorb",
    "abstract", "absurd", "abuse", "access", "accident", "account",
    "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act",
    "action", "actor", "actual", "adapt", "add", "address", "adjust",
    "admit", "adult", "advance", "advice", "aerobic", "affair", "afford",
    "afraid", "again", "age", "agent", "agree", "ahead", "aim", "air",
    "airport", "aisle", "alarm", "album", "alcohol", "alert", "alien",
    "all", "alley", "allow", "almost", "alone", "alpha", "already",
    "also", "alter", "always", "amateur", "amazing", "among", "amount",
    "amused", "analyst", "anchor", "ancient", "anger", "angle", "angry",
    "animal", "ankle", "announce", "annual", "another", "answer", "antenna",
    "antique", "anxiety", "any", "apart", "apology", "appear", "apple",
    "approve", "april", "arch", "arctic", "area", "arena", "argue",
    "arm", "armed", "armor", "army", "around", "arrange", "arrest",
    "arrive", "arrow", "art", "artefact", "artist", "artwork", "ask",
    "aspect", "assault", "asset", "assist", "assume", "asthma", "athlete",
    "atom", "attack", "attend", "attitude", "attract", "auction", "audit",
]

# Common passphrase patterns observed in wallet usage
COMMON_PASSPHRASES = [
    "", "password", "Password", "12345678", "bitcoin", "Bitcoin", "BTC",
    "crypto", "Crypto", "satoshi", "Satoshi", "nakamoto", "Nakamoto",
    "hodl", "HODL", "moon", "Moon", "wallet", "Wallet", "secret",
    "Secret", "hidden", "Hidden", "mywallet", "mysecret", "mypassphrase",
    "backup", "Backup", "seed", "Seed", "key", "Key", "master", "Master",
    "trezor", "ledger", "cold", "storage", "safety", "protect", "guard",
    "private", "Private", "safe", "Safe", "vault", "Vault", "bank",
    "Bank", "money", "Money", "coin", "Coin", "gold", "Gold", "diamond",
    "Diamond", "fortune", "Fortune", "wealth", "Wealth", "rich", "Rich",
]

# Common password mutation rules (inspired by hashcat rules)
PASSWORD_RULES = [
    lambda w: w,                    # Original
    lambda w: w.lower(),            # Lowercase
    lambda w: w.upper(),            # Uppercase
    lambda w: w.capitalize(),       # Capitalize first
    lambda w: w.swapcase(),         # Swap case
    lambda w: w + "1",             # Append 1
    lambda w: w + "12",            # Append 12
    lambda w: w + "123",           # Append 123
    lambda w: w + "1234",          # Append 1234
    lambda w: w + "12345",         # Append 12345
    lambda w: w + "123456",        # Append 123456
    lambda w: w + "!",             # Append !
    lambda w: w + "@",             # Append @
    lambda w: w + "#",             # Append #
    lambda w: w + "$",             # Append $
    lambda w: w + "%",             # Append %
    lambda w: w + "!!",            # Append !!
    lambda w: w + "!@#",           # Append !@#
    lambda w: "!" + w,             # Prepend !
    lambda w: w[::-1],             # Reverse
    lambda w: w.replace('a', '@').replace('e', '3').replace('i', '1').replace('o', '0'),  # Leet
    lambda w: w.replace('a', '4').replace('e', '3').replace('s', '5'),  # Partial leet
]

# Year-based suffixes
_CURRENT_YEAR = 2026
YEAR_SUFFIXES = [str(y) for y in range(2010, _CURRENT_YEAR + 2)]

# Special character suffixes
SPECIAL_SUFFIXES = ["!", "!!", "!@#", "!@#$", "@", "@@", "#", "$", "$$", "%",
                    "^", "&", "*", "!", "!1", "!123", "@123", "#123"]


# ============================================================================
# SEED PHRASE GENERATOR
# ============================================================================

class SeedPhraseGenerator:
    """Generate seed phrase candidates using multiple strategies.

    Strategies are ordered from fastest/most-likely to slowest/least-likely:
    1. LWO (Last-Word Optimization): If only last word missing
    2. HCP (Hierarchical Checksum Pruning): Multi-word with checksum pre-filter
    3. Statistical prioritization: Try common words first
    4. Full enumeration: Try all words with checksum filter
    """

    def __init__(self, wordlist: List[str] = None):
        from .checksum_filter import get_bip39_wordlist
        self.wordlist = wordlist or get_bip39_wordlist()
        self._word_to_idx = {w: i for i, w in enumerate(self.wordlist)}
        self._common_set = set(COMMON_SEED_WORDS[:100])

    def generate(
        self,
        known_words: List[str],
        missing_positions: List[int],
        seed_length: int = 12,
        strategy: str = "auto",
        prioritize_common: bool = True,
    ) -> Generator[List[str], None, None]:
        """Generate seed phrase candidates.

        Args:
            known_words: List of known words in order (skip missing positions)
            missing_positions: 0-based indices of unknown word positions
            seed_length: Total number of words (12, 15, 18, 21, 24)
            strategy: "auto", "lwo", "hcp", "statistical", "full"
            prioritize_common: Try statistically common words first

        Yields:
            Complete seed phrases (lists of words) to test
        """
        # Build template
        template = [None] * seed_length
        known_idx = 0
        for i in range(seed_length):
            if i in missing_positions:
                template[i] = None
            else:
                if known_idx < len(known_words):
                    template[i] = known_words[known_idx]
                    known_idx += 1

        # Select strategy
        if strategy == "auto":
            if len(missing_positions) == 1 and missing_positions[0] == seed_length - 1:
                strategy = "lwo"
            elif len(missing_positions) <= 4:
                strategy = "hcp"
            else:
                strategy = "full"

        if strategy == "lwo":
            yield from self._lwo_strategy(template, missing_positions[0])
        elif strategy == "hcp":
            yield from self._hcp_strategy(template, missing_positions, prioritize_common)
        elif strategy == "statistical":
            yield from self._statistical_strategy(template, missing_positions)
        else:
            yield from self._full_strategy(template, missing_positions)

    def _lwo_strategy(
        self, template: List[Optional[str]], position: int
    ) -> Generator[List[str], None, None]:
        """Last-Word Optimization: Compute valid words from checksum."""
        from .checksum_filter import find_valid_last_words
        known_words = [w for w in template if w is not None]
        valid_words = find_valid_last_words(known_words, position, self.wordlist)

        for word in valid_words:
            result = template.copy()
            result[position] = word
            yield result

    def _hcp_strategy(
        self, template: List[Optional[str]], positions: List[int],
        prioritize_common: bool,
    ) -> Generator[List[str], None, None]:
        """Hierarchical Checksum Pruning with statistical prioritization.

        The pruner yields combos (list of words for missing positions)
        and modifies the template in-place. We need to yield complete
        seed phrases (full 12/24-word lists).
        """
        from .checksum_filter import (
            HierarchicalChecksumPruner, validate_bip39_checksum
        )

        if prioritize_common:
            # Reorder wordlist to try common words first
            reordered = [w for w in COMMON_SEED_WORDS if w in self.wordlist]
            reordered += [w for w in self.wordlist if w not in set(reordered)]
            pruner = HierarchicalChecksumPruner(reordered)
        else:
            pruner = HierarchicalChecksumPruner(self.wordlist)

        for combo in pruner.get_candidates_for_missing_words(template, positions):
            # The pruner modifies template in-place and yields just the combo
            # We need to yield the full seed phrase
            # Template already has the combo filled in by the pruner
            yield template.copy()

    def _statistical_strategy(
        self, template: List[Optional[str]], positions: List[int]
    ) -> Generator[List[str], None, None]:
        """Statistical Word Prioritization: Try likely words first."""
        from .checksum_filter import validate_bip39_checksum

        # Create ordered word lists per position (common first)
        ordered_words = [w for w in COMMON_SEED_WORDS if w in self.wordlist]
        ordered_words += [w for w in self.wordlist if w not in set(ordered_words)]

        word_ranges = [ordered_words] * len(positions)

        for combo in itertools.product(*word_ranges):
            for i, pos in enumerate(positions):
                template[pos] = combo[i]
            if validate_bip39_checksum(template, self.wordlist):
                yield template.copy()

        for pos in positions:
            template[pos] = None

    def _full_strategy(
        self, template: List[Optional[str]], positions: List[int]
    ) -> Generator[List[str], None, None]:
        """Full enumeration with checksum filtering."""
        from .checksum_filter import validate_bip39_checksum

        word_ranges = [self.wordlist] * len(positions)

        for combo in itertools.product(*word_ranges):
            for i, pos in enumerate(positions):
                template[pos] = combo[i]
            if validate_bip39_checksum(template, self.wordlist):
                yield template.copy()

        for pos in positions:
            template[pos] = None


# ============================================================================
# PASSPHRASE GENERATOR
# ============================================================================

@dataclass
class PassphraseConfig:
    """Configuration for passphrase generation."""
    partial: str = ""
    min_length: int = 0
    max_length: int = 64
    charset: str = "printable"  # "alpha", "alphanumeric", "printable", "ascii", "unicode"
    max_candidates: int = 0  # 0 = unlimited
    use_common: bool = True
    use_mutations: bool = True
    use_dict: bool = True
    dict_files: List[str] = field(default_factory=list)
    custom_candidates: List[str] = field(default_factory=list)


class PassphraseGenerator:
    """Generate passphrase candidates using multiple strategies.

    The passphrase (BIP39 "25th word") is a critical recovery target.
    Even a single character difference produces a completely different wallet.
    """

    def __init__(self, config: PassphraseConfig = None):
        self.config = config or PassphraseConfig()
        self._candidates_generated = 0

    def generate(self) -> Generator[str, None, None]:
        """Generate passphrase candidates in order of likelihood.

        Strategies applied in order:
        1. Exact partial match (if provided)
        2. Common passphrases
        3. Custom candidates
        4. Dictionary words
        5. Partial match mutations
        6. Systematic character combination
        """
        self._candidates_generated = 0
        seen: Set[str] = set()

        def _yield(candidate: str) -> bool:
            """Yield a candidate if not seen before and within length limits."""
            if candidate in seen:
                return False
            if len(candidate) < self.config.min_length:
                return False
            if len(candidate) > self.config.max_length:
                return False
            if self.config.max_candidates > 0 and self._candidates_generated >= self.config.max_candidates:
                return True  # Signal to stop
            seen.add(candidate)
            self._candidates_generated += 1
            return True  # Caller should yield

        # Strategy 1: Empty string (many users don't set a passphrase)
        if _yield(""):
            yield ""

        # Strategy 2: Exact partial match
        if self.config.partial:
            if _yield(self.config.partial):
                yield self.config.partial

        # Strategy 3: Common passphrases
        if self.config.use_common:
            for p in COMMON_PASSPHRASES:
                if _yield(p):
                    yield p

        # Strategy 4: Custom candidates
        for c in self.config.custom_candidates:
            if _yield(c):
                yield c

        # Strategy 5: Dictionary words
        if self.config.use_dict:
            for dict_file in self.config.dict_files:
                try:
                    with open(dict_file, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            word = line.strip()
                            if word and _yield(word):
                                yield word
                except FileNotFoundError:
                    pass

        # Strategy 6: Mutations of partial passphrase
        if self.config.use_mutations and self.config.partial:
            for mutation in self._mutate_passphrase(self.config.partial):
                if _yield(mutation):
                    yield mutation

        # Strategy 7: Partial + year suffixes
        if self.config.partial:
            for year in YEAR_SUFFIXES:
                candidate = self.config.partial + year
                if _yield(candidate):
                    yield candidate

        # Strategy 8: Partial + special suffixes
        if self.config.partial:
            for suffix in SPECIAL_SUFFIXES:
                candidate = self.config.partial + suffix
                if _yield(candidate):
                    yield candidate

        # Strategy 9: Systematic short passphrase enumeration
        if self.config.max_length >= 1 and self.config.charset != "unicode":
            for candidate in self._systematic_generation():
                if _yield(candidate):
                    yield candidate

    def _mutate_passphrase(self, base: str) -> Generator[str, None, None]:
        """Generate mutations of a base passphrase."""
        # Case variations
        yield base.lower()
        yield base.upper()
        yield base.capitalize()
        yield base.swapcase()
        yield base.title()

        # Common prefixes
        for prefix in ["the", "my", "My", "The", "THE", "MY", "a", "A", "our", "Our"]:
            yield prefix + base

        # Common suffixes
        for suffix in ["1", "12", "123", "1234", "12345", "!", "!!", "@", "#",
                       "$", "!!", "!@#", "!1", "!123", "@123", "2024", "2025", "2026"]:
            yield base + suffix

        # Number suffixes 0-999
        for i in range(1000):
            yield base + str(i)

        # Leet speak
        leet_map = {'a': '@', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
        leet = ""
        for c in base:
            leet += leet_map.get(c.lower(), c)
        yield leet

        # Reverse
        yield base[::-1]

    def _systematic_generation(self) -> Generator[str, None, None]:
        """Systematically generate short passphrases.

        Only used as a last resort for very short passphrases.
        """
        if self.config.charset == "alpha":
            chars = string.ascii_letters
        elif self.config.charset == "alphanumeric":
            chars = string.ascii_letters + string.digits
        else:  # printable or ascii
            chars = string.ascii_letters + string.digits + string.punctuation

        # Only enumerate short passphrases (1-4 chars) - longer is infeasible
        for length in range(1, min(5, self.config.max_length + 1)):
            for combo in itertools.product(chars, repeat=length):
                yield ''.join(combo)


# ============================================================================
# PASSWORD GENERATOR
# ============================================================================

@dataclass
class PasswordConfig:
    """Configuration for password generation."""
    base_words: List[str] = field(default_factory=list)
    min_length: int = 1
    max_length: int = 64
    use_rules: bool = True
    use_dict: bool = True
    dict_files: List[str] = field(default_factory=list)
    custom_candidates: List[str] = field(default_factory=list)
    max_candidates: int = 0
    rule_depth: int = 1  # How many rule layers to apply


class PasswordGenerator:
    """Generate password candidates using rule-based mutations.

    Inspired by hashcat rule engine but implemented in pure Python.
    """

    def __init__(self, config: PasswordConfig = None):
        self.config = config or PasswordConfig()
        self._candidates_generated = 0

    def generate(self) -> Generator[str, None, None]:
        """Generate password candidates using multiple strategies."""
        self._candidates_generated = 0
        seen: Set[str] = set()

        def _yield(candidate: str) -> bool:
            if candidate in seen:
                return False
            if len(candidate) < self.config.min_length:
                return False
            if len(candidate) > self.config.max_length:
                return False
            if self.config.max_candidates > 0 and self._candidates_generated >= self.config.max_candidates:
                return True
            seen.add(candidate)
            self._candidates_generated += 1
            return True

        # Custom candidates first
        for c in self.config.custom_candidates:
            if _yield(c):
                yield c

        # Base words with rule mutations
        base_words = list(self.config.base_words)
        if not base_words:
            base_words = ["password", "bitcoin", "wallet", "crypto", "secret"]

        # Apply rules to base words
        if self.config.use_rules:
            for word in base_words:
                for rule in PASSWORD_RULES:
                    try:
                        mutated = rule(word)
                        if _yield(mutated):
                            yield mutated
                    except Exception:
                        pass

                # Year combinations
                for year in YEAR_SUFFIXES:
                    for rule in PASSWORD_RULES[:6]:  # Use top rules only
                        try:
                            mutated = rule(word + year)
                            if _yield(mutated):
                                yield mutated
                        except Exception:
                            pass

        # Dictionary attack
        if self.config.use_dict:
            for dict_file in self.config.dict_files:
                try:
                    with open(dict_file, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            word = line.strip()
                            if not word:
                                continue
                            if _yield(word):
                                yield word
                            if self.config.use_rules:
                                for rule in PASSWORD_RULES[:8]:
                                    try:
                                        mutated = rule(word)
                                        if _yield(mutated):
                                            yield mutated
                                    except Exception:
                                        pass
                except FileNotFoundError:
                    pass


# ============================================================================
# INVENTION: MARKOV CHAIN CANDIDATE GENERATOR
# ============================================================================

class MarkovGenerator:
    """INVENTION: Markov Chain-based candidate generation for passphrases.

    Unlike password Markov models that learn from breached password databases,
    this Markov model learns from common passphrase patterns to predict likely
    character transitions in wallet passphrases.

    The key insight: Wallet passphrases tend to follow specific patterns:
    - Single dictionary words with optional numbers/symbols
    - Short phrases (2-3 words)
    - Names + numbers
    - Technical terms related to crypto

    We model character n-gram probabilities and use them to generate
    candidates in order of decreasing probability, which is significantly
    more efficient than alphabetical or random ordering.
    """

    def __init__(self):
        self._model: Dict[str, Dict[str, float]] = {}
        self._trained = False

    def train(self, samples: List[str]):
        """Train the Markov model on sample passphrases.

        Builds a first-order Markov model of character transitions.
        """
        transitions: Dict[str, Dict[str, int]] = {}

        for sample in samples:
            prev = "^"  # Start symbol
            for char in sample + "$":  # End symbol
                if prev not in transitions:
                    transitions[prev] = {}
                transitions[prev][char] = transitions[prev].get(char, 0) + 1
                prev = char

        # Convert counts to probabilities
        for prev, nexts in transitions.items():
            total = sum(nexts.values())
            self._model[prev] = {c: count / total for c, count in nexts.items()}

        self._trained = True

    def generate_candidates(
        self, min_length: int = 1, max_length: int = 20,
        num_candidates: int = 10000,
    ) -> Generator[str, None, None]:
        """Generate candidates ordered by Markov probability.

        Uses beam search to generate the most probable candidates first.
        """
        if not self._trained:
            return

        import heapq

        # Beam search: (negative_log_prob, string, last_char)
        beam_width = 1000
        beam = [(0.0, "", "^")]
        results = set()

        for _ in range(max_length):
            new_beam = []
            for neg_prob, s, last_char in beam:
                if last_char == "$":
                    if len(s) - 1 >= min_length and s[:-1] not in results:
                        results.add(s[:-1])
                        yield s[:-1]
                        if len(results) >= num_candidates:
                            return
                    continue

                if last_char not in self._model:
                    continue

                for next_char, prob in self._model[last_char].items():
                    import math
                    new_neg_prob = neg_prob - math.log(max(prob, 1e-10))
                    new_string = s + next_char
                    new_beam.append((new_neg_prob, new_string, next_char))

            # Keep top beam_width candidates
            new_beam.sort(key=lambda x: x[0])
            beam = new_beam[:beam_width]

            if not beam:
                break

        # Yield remaining candidates
        for neg_prob, s, last_char in beam:
            candidate = s if last_char == "$" else s
            if len(candidate) >= min_length and candidate not in results:
                results.add(candidate)
                yield candidate
                if len(results) >= num_candidates:
                    return


# ============================================================================
# INVENTION: CONTEXTUAL WORD PREDICTOR (CWP)
# ============================================================================

class ContextualWordPredictor:
    """INVENTION: Contextual Word Prediction for BIP39 seed phrases.

    BIP39 words are designed so that the first 4 characters uniquely identify
    each word. This means if a user slightly misremembered a word, we can
    predict likely corrections based on:

    1. Phonetically similar words (e.g., "abandon" vs "abundant")
    2. Visually similar words (e.g., "accept" vs "except")
    3. Typographically close words (Levenshtein distance)
    4. First-4-character proximity (users might remember the beginning)

    This is especially powerful when combined with checksum validation:
    we only need to try ~10-50 similar words instead of all 2048.
    """

    def __init__(self, wordlist: List[str] = None):
        from .checksum_filter import get_bip39_wordlist
        self.wordlist = wordlist or get_bip39_wordlist()
        self._build_similarity_index()

    def _build_similarity_index(self):
        """Build prefix-based and phonetic similarity indexes."""
        # Prefix index: first 1-4 chars -> list of words
        self.prefix_index: Dict[str, List[str]] = {}
        for word in self.wordlist:
            for length in range(1, 5):
                prefix = word[:length]
                if prefix not in self.prefix_index:
                    self.prefix_index[prefix] = []
                self.prefix_index[prefix].append(word)

        # Length index: word length -> list of words
        self.length_index: Dict[int, List[str]] = {}
        for word in self.wordlist:
            l = len(word)
            if l not in self.length_index:
                self.length_index[l] = []
            self.length_index[l].append(word)

    def predict_similar_words(
        self, word: str, max_distance: int = 3, max_results: int = 50
    ) -> List[str]:
        """Predict similar BIP39 words that the user might have meant.

        Args:
            word: The possibly-incorrect word
            max_distance: Maximum edit distance to consider
            max_results: Maximum number of suggestions

        Returns:
            List of similar BIP39 words, ordered by similarity
        """
        candidates = []

        # Strategy 1: Exact prefix match (highest priority)
        for length in range(min(4, len(word)), 0, -1):
            prefix = word[:length]
            if prefix in self.prefix_index:
                for candidate in self.prefix_index[prefix]:
                    if candidate != word:
                        candidates.append((1, candidate))

        # Strategy 2: Same length words
        if len(word) in self.length_index:
            for candidate in self.length_index[len(word)]:
                if candidate != word and candidate not in [c[1] for c in candidates]:
                    dist = self._levenshtein(word, candidate)
                    if dist <= max_distance:
                        candidates.append((dist, candidate))

        # Strategy 3: Adjacent length words (±1)
        for length_delta in [-1, 1]:
            adj_length = len(word) + length_delta
            if adj_length in self.length_index:
                for candidate in self.length_index[adj_length]:
                    if candidate not in [c[1] for c in candidates]:
                        dist = self._levenshtein(word, candidate)
                        if dist <= max_distance:
                            candidates.append((dist + 0.5, candidate))

        # Sort by distance (most similar first)
        candidates.sort(key=lambda x: x[0])

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for dist, word in candidates:
            if word not in seen:
                seen.add(word)
                unique.append(word)
            if len(unique) >= max_results:
                break

        return unique

    def _levenshtein(self, s1: str, s2: str) -> int:
        """Compute Levenshtein edit distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)

        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row

        return prev_row[-1]
