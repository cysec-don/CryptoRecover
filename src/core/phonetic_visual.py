"""
Phonetic and Visual Similarity Maps for BIP-39 Words.

This module provides pre-computed similarity matrices and lookup tables
that enable the "Cognitive Graph Traversal" and "Temporal Decay Modeling"
novel techniques. It maps how humans misremember, mishear, or mistype
BIP-39 words based on phonetic, visual, and cognitive similarity.
"""

from typing import Dict, List, Tuple, Set
from collections import defaultdict
import functools


class PhoneticMapper:
    """
    Maps phonetic similarity between BIP-39 words.
    Based on Soundex, Metaphone, and custom phonetic rules for English.
    """

    # Common phonetic confusion pairs
    PHONETIC_GROUPS = {
        's': ['s', 'z', 'c'],
        'k': ['k', 'c', 'q', 'ch'],
        'f': ['f', 'ph', 'v'],
        'j': ['j', 'g', 'dge'],
        't': ['t', 'd', 'th'],
        'p': ['p', 'b'],
        'm': ['m', 'n'],
        'l': ['l', 'r'],
        'w': ['w', 'v', 'u'],
        'i': ['i', 'e', 'y'],
        'o': ['o', 'u', 'ow'],
        'a': ['a', 'e', 'ah'],
    }

    # BIP-39 words that sound similar
    SOUND_ALIKE_GROUPS = [
        # Two-syllable words with similar rhythm
        {"accept", "except", "access"},
        {"affect", "effect"},
        {"alter", "after"},
        {"anchor", "anger"},
        {"bless", "bliss", "press"},
        {"brave", "grave", "crave"},
        {"burden", "garden", "pardon"},
        {"canvas", "census"},
        {"castle", "cattle", "battle"},
        {"center", "enter", "chapter"},
        {"chimney", "timber"},
        {"circle", "surface"},
        {"clinic", "clinic"},
        {"colony", "company"},
        {"crop", "drop", "shop"},
        {"damage", "manage"},
        {"differ", "filter"},
        {"dinosaur", "discuss"},
        {"draft", "craft", "drift"},
        {"enable", "unable"},
        {"exotic", "exotic"},
        {"fiscal", "physical"},
        {"float", "boat", "coat"},
        {"gaze", "glaze", "graze"},
        {"gravel", "travel"},
        {"harvest", "harness"},
        {"inhale", "unveil"},
        {"isolate", "insulate"},
        {"jelly", "july"},
        {"kitten", "mitten"},
        {"labor", "neighbor"},
        {"lawn", "yawn"},
        {"margin", "marine"},
        {"midnight", "might"},
        {"muscle", "muzzle"},
        {"napkin", "jacket"},
        {"obtain", "contain"},
        {"ocean", "notion"},
        {"parent", "present"},
        {"peanut", "pilot"},
        {"plunge", "bungle"},
        {"pulse", "false"},
        {"rapid", "rival"},
        {"recipe", "receipt"},
        {"robin", "ribbon"},
        {"saddle", "candle", "handle"},
        {"senior", "signal"},
        {"slender", "tender"},
        {"socket", "pocket", "rocket"},
        {"stomach", "attack"},
        {"surface", "service"},
        {"symbol", "simple"},
        {"thunder", "tender"},
        {"tobacco", "potato"},
        {"unfold", "untold"},
        {"vintage", "village"},
        {"wheat", "sweat", "treat"},
        {"zero", "hero"},
    ]

    def __init__(self):
        self._similarity_cache: Dict[Tuple[str, str], float] = {}

    def soundex(self, word: str) -> str:
        """Compute American Soundex code for a word."""
        if not word:
            return ""

        word = word.upper()
        soundex = word[0]

        mapping = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5',
            'R': '6',
        }

        for char in word[1:]:
            code = mapping.get(char, '0')
            if code != '0' and code != soundex[-1]:
                soundex += code
            if len(soundex) == 4:
                break

        return soundex.ljust(4, '0')

    def phonetic_similarity(self, word1: str, word2: str) -> float:
        """
        Compute phonetic similarity between two words (0.0 to 1.0).
        Uses Soundex comparison, syllable analysis, and rhyme detection.
        """
        # Guard against empty strings
        if not word1 or not word2:
            return 0.0

        cache_key = (min(word1, word2), max(word1, word2))
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]

        score = 0.0

        # Soundex similarity
        s1 = self.soundex(word1)
        s2 = self.soundex(word2)
        if s1 == s2:
            score += 0.5
        elif s1[0] == s2[0]:
            score += 0.15
            # Count matching digits
            for i in range(1, 4):
                if s1[i] == s2[i]:
                    score += 0.05

        # Common prefix/suffix (rhyme)
        min_len = min(len(word1), len(word2))
        for i in range(2, min(min_len, 5) + 1):
            if word1[-i:] == word2[-i:]:
                score += 0.1 * (i / 5)
                break

        # First letter match
        if word1[0] == word2[0]:
            score += 0.1

        # Same sound-alike group
        for group in self.SOUND_ALIKE_GROUPS:
            if word1 in group and word2 in group:
                score += 0.3
                break

        score = min(score, 1.0)
        self._similarity_cache[cache_key] = score
        return score

    def get_phonetic_candidates(self, word: str, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Get BIP-39 words that sound similar to the given word."""
        # This would normally iterate over the full wordlist
        # For efficiency, we precompute phonetic groups
        candidates = []

        # Check sound-alike groups first
        for group in self.SOUND_ALIKE_GROUPS:
            if word in group:
                for w in group:
                    if w != word:
                        candidates.append((w, 0.8))
                break

        return sorted(candidates, key=lambda x: -x[1])


class VisualMapper:
    """
    Maps visual similarity between BIP-39 words.
    Based on how words look when typed (keyboard proximity)
    and how they appear in print (shape similarity).
    """

    # QWERTY keyboard adjacency map
    KEYBOARD_ADJACENCY = {
        'q': ['w', 'a'], 'w': ['q', 'e', 'a', 's'], 'e': ['w', 'r', 's', 'd'],
        'r': ['e', 't', 'd', 'f'], 't': ['r', 'y', 'f', 'g'], 'y': ['t', 'u', 'g', 'h'],
        'u': ['y', 'i', 'h', 'j'], 'i': ['u', 'o', 'j', 'k'], 'o': ['i', 'p', 'k', 'l'],
        'p': ['o', 'l'], 'a': ['q', 'w', 's', 'z'], 's': ['w', 'e', 'a', 'd', 'z', 'x'],
        'd': ['e', 'r', 's', 'f', 'x', 'c'], 'f': ['r', 't', 'd', 'g', 'c', 'v'],
        'g': ['t', 'y', 'f', 'h', 'v', 'b'], 'h': ['y', 'u', 'g', 'j', 'b', 'n'],
        'j': ['u', 'i', 'h', 'k', 'n', 'm'], 'k': ['i', 'o', 'j', 'l', 'm'],
        'l': ['o', 'p', 'k'], 'z': ['a', 's', 'x'], 'x': ['s', 'd', 'z', 'c'],
        'c': ['d', 'f', 'x', 'v'], 'v': ['f', 'g', 'c', 'b'], 'b': ['g', 'h', 'v', 'n'],
        'n': ['h', 'j', 'b', 'm'], 'm': ['j', 'k', 'n'],
    }

    # Visually similar character pairs (confusable characters)
    VISUAL_CONFUSABLES = {
        'a': ['o', 'e'], 'b': ['d', 'p', 'q'], 'c': ['e', 'o'],
        'd': ['b', 'p', 'q'], 'e': ['c', 'a'], 'f': ['t'],
        'g': ['q', 'y'], 'h': ['n', 'k'], 'i': ['l', 'j', '1'],
        'j': ['i', 'l'], 'k': ['h', 'x'], 'l': ['i', '1', 'j'],
        'm': ['n', 'rn'], 'n': ['h', 'm'], 'o': ['a', 'c', '0'],
        'p': ['b', 'd', 'q'], 'q': ['g', 'b', 'd', 'p'],
        'r': ['v'], 's': ['z', '5'], 't': ['f', '7'],
        'u': ['v', 'w'], 'v': ['u', 'r'], 'w': ['u', 'v'],
        'x': ['k', 'z'], 'y': ['g'], 'z': ['s', 'x'],
    }

    def keyboard_typo_candidates(self, word: str) -> List[str]:
        """Generate possible typos based on keyboard adjacency."""
        candidates = set()
        word = word.lower()

        for i, char in enumerate(word):
            if char in self.KEYBOARD_ADJACENCY:
                for adj_char in self.KEYBOARD_ADJACENCY[char]:
                    # Substitution
                    typo = word[:i] + adj_char + word[i + 1:]
                    candidates.add(typo)

                    # Omission (skip this character)
                    typo = word[:i] + word[i + 1:]
                    candidates.add(typo)

                    # Insertion (add adjacent character)
                    typo = word[:i] + adj_char + word[i:]
                    candidates.add(typo)

                    # Transposition (swap with next)
                    if i + 1 < len(word):
                        typo = word[:i] + word[i + 1] + char + word[i + 2:]
                        candidates.add(typo)

        return list(candidates)

    def visual_similarity(self, word1: str, word2: str) -> float:
        """
        Compute visual similarity between two words (0.0 to 1.0).
        Based on character-level visual confusability and length similarity.
        """
        if not word1 or not word2:
            return 0.0

        word1, word2 = word1.lower(), word2.lower()

        # Length penalty
        len_diff = abs(len(word1) - len(word2))
        max_len = max(len(word1), len(word2))
        len_score = 1.0 - (len_diff / max_len)

        # Character-level similarity
        min_len = min(len(word1), len(word2))
        char_score = 0.0
        for i in range(min_len):
            if word1[i] == word2[i]:
                char_score += 1.0
            elif word2[i] in self.VISUAL_CONFUSABLES.get(word1[i], []):
                char_score += 0.5

        char_score /= max_len

        return 0.4 * len_score + 0.6 * char_score


class CognitiveGraph:
    """
    Cognitive Graph for modeling how humans remember and misremember seedphrases.

    This implements the "Cognitive Graph Traversal" technique:
    - Nodes represent BIP-39 words
    - Edges represent cognitive connections (phonetic, visual, semantic, temporal)
    - Edge weights represent the likelihood of one word being confused for another
    """

    def __init__(self):
        self.phonetic = PhoneticMapper()
        self.visual = VisualMapper()
        self._graph: Dict[str, Dict[str, float]] = defaultdict(dict)

    def get_confusion_probability(self, actual_word: str, remembered_word: str,
                                   days_since_exposure: int = 365) -> float:
        """
        Compute the probability that `actual_word` would be remembered as
        `remembered_word`, given the time since exposure.

        Applies Ebbinghaus forgetting curve: R = e^(-t/S)
        where t = time, S = stability constant (~30 days for unfamiliar material)

        This implements the "Temporal Decay Modeling" technique.
        """
        # Guard against empty strings
        if not actual_word or not remembered_word:
            return 0.0

        # Base confusion scores
        phon_score = self.phonetic.phonetic_similarity(remembered_word, actual_word)
        vis_score = self.visual.visual_similarity(remembered_word, actual_word)

        # Exact match
        if actual_word == remembered_word:
            # Even exact recall decays over time
            stability = 60  # days
            retention = 2.718281828 ** (-days_since_exposure / stability)
            return max(retention, 0.1)  # floor at 10% even for exact matches

        # Semantic/phonetic confusion gets WORSE then BETTERS (misremembering peaks)
        # People initially remember correctly, then confuse, then forget entirely
        confusion_peak = 30  # days - peak confusion period
        if days_since_exposure < confusion_peak:
            confusion_factor = days_since_exposure / confusion_peak
        else:
            confusion_factor = max(0.1, 1.0 - (days_since_exposure - confusion_peak) / 365)

        # Combined score
        first_letter_match = 1.0 if (actual_word and remembered_word and actual_word[0] == remembered_word[0]) else 0.0
        base_score = 0.5 * phon_score + 0.3 * vis_score + 0.2 * first_letter_match

        return base_score * confusion_factor

    def get_likely_actual_words(self, remembered_word: str,
                                 wordlist: List[str],
                                 days_since: int = 365,
                                 top_k: int = 20) -> List[Tuple[str, float]]:
        """
        Given a word the user thinks they remember, return the most likely
        actual BIP-39 words they might have meant, ranked by confusion probability.

        This is a key component of the "Cognitive Graph Traversal" technique.
        """
        scores = []
        for word in wordlist:
            if word == remembered_word:
                prob = self.get_confusion_probability(word, remembered_word, days_since)
                scores.append((word, prob))
            else:
                prob = self.get_confusion_probability(word, remembered_word, days_since)
                if prob > 0.05:  # Filter out very unlikely confusions
                    scores.append((word, prob))

        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]
