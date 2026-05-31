"""
LLM-Enhanced Candidate Generator for CryptoRecover.

This module implements the AI-powered recovery strategies:
1. LLM-Guided Seedphrase Prediction - Use LLMs to predict likely BIP-39 words
2. Password Profiling - Generate likely passwords based on user context
3. Semantic Clustering - Group BIP-39 words by meaning for targeted search
4. Adaptive Learning - Learn from failed attempts to refine guesses
5. Consensus Validation - Multiple LLMs agree on candidates
6. Hybrid Recovery - Combine LLM + traditional bruteforce
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
import json
import asyncio
import hashlib
import time

from .llm_providers import (
    BaseLLMProvider, LLMProviderFactory, LLMMessage, LLMResponse,
    ProviderConfig, ProviderType
)
from ..core.bip39_engine import BIP39Engine, MnemonicCandidate, RecoveryContext


# ============================================================
# Semantic Clusters for BIP-39 Words
# ============================================================

BIP39_SEMANTIC_CLUSTERS = {
    "nature": [
        "abandon", "ability", "absent", "absorb", "abstract", "absurd", "abuse",
        "accident", "acquire", "animal", "annual", "apple", "arctic", "autumn",
        "bamboo", "bark", "beach", "bean", "bear", "berry", "blossom", "blue",
        "border", "breeze", "bridge", "brush", "bubble", "bunny", "cabin",
        "cactus", "camp", "canal", "canvas", "canyon", "castle", "cave",
        "cedar", "channel", "cherry", "climate", "coast", "coral", "cotton",
        "creek", "cricket", "crop", "crystal", "dawn", "desert", "dew",
        "dinosaur", "drift", "dune", "dust", "eagle", "earth", "elephant",
        "ember", "exotic", "falcon", "farm", "fern", "field", "flame", "flock",
        "flood", "flora", "forest", "fossil", "frost", "garden", "glacier",
        "gorilla", "grain", "grass", "grove", "harbor", "harvest", "hawk",
        "herb", "hive", "horizon", "hunter", "ice", "island", "jungle",
        "kangaroo", "lake", "lava", "leaf", "lion", "lotus", "maple", "marsh",
        "meadow", "mimosa", "moon", "morning", "mountain", "mushroom", "nest",
        "night", "oak", "oasis", "ocean", "orchard", "owl", "palm", "panda",
        "peanut", "petal", "pine", "planet", "plunge", "pond", "prairie",
        "rain", "reef", "ridge", "river", "rose", "safari", "season", "seed",
        "shadow", "shark", "shell", "shore", "sky", "slab", "snow", "soil",
        "solar", "spray", "spring", "sprout", "squirrel", "star", "stone",
        "storm", "stream", "sun", "swamp", "thunder", "tiger", "timber",
        "trail", "tree", "tropics", "tundra", "valley", "violin", "volcano",
        "wave", "whale", "wheat", "wild", "wind", "wolf", "zebra",
    ],
    "human_body": [
        "arm", "back", "brain", "cheek", "chest", "chin", "eye", "face",
        "finger", "flesh", "foot", "hair", "hand", "head", "heart", "heel",
        "hip", "jaw", "knee", "leg", "lip", "lung", "muscle", "nail", "neck",
        "nerve", "nose", "palm", "pulse", "rib", "shoulder", "skin", "skull",
        "spine", "stomach", "throat", "thumb", "tongue", "tooth", "vein",
        "wrist",
    ],
    "emotions": [
        "anger", "anxiety", "bliss", "calm", "comfort", "courage", "despair",
        "doubt", "dread", "eager", "envy", "fear", "glad", "gloom", "grace",
        "grief", "guilt", "happy", "hate", "hope", "horror", "humor", "joy",
        "love", "mercy", "mourn", "panic", "passion", "peace", "pride",
        "rage", "regret", "relief", "remorse", "shame", "shock", "sorrow",
        "surprise", "terror", "thrill", "trust", "worry",
    ],
    "technology": [
        "algorithm", "binary", "byte", "cache", "chip", "circuit", "clock",
        "code", "compute", "data", "digital", "engine", "filter", "firmware",
        "format", "frequency", "graph", "hardware", "index", "input", "kernel",
        "link", "logic", "matrix", "memory", "module", "monitor", "network",
        "node", "output", "pixel", "port", "program", "protocol", "query",
        "render", "scan", "signal", "software", "source", "switch", "syntax",
        "system", "terminal", "token", "vector", "virtual",
    ],
    "household": [
        "blanket", "broom", "bucket", "cabinet", "candle", "carpet", "ceiling",
        "chair", "chimney", "clock", "couch", "curtain", "desk", "door",
        "faucet", "fence", "floor", "frame", "furniture", "garage", "gate",
        "glass", "gutter", "hall", "hallway", "heater", "hinge", "kitchen",
        "lamp", "laundry", "lock", "mattress", "mirror", "oven", "pillow",
        "pipe", "plate", "plug", "pot", "refrigerator", "roof", "room",
        "shelf", "shower", "sink", "sofa", "stair", "stove", "table", "tap",
        "towel", "vase", "wall", "wardrobe", "window",
    ],
    "food": [
        "apple", "apricot", "avocado", "bacon", "banana", "bean", "beef",
        "berry", "biscuit", "bread", "butter", "cabbage", "cake", "candy",
        "carrot", "cereal", "cheese", "cherry", "chocolate", "citrus",
        "coconut", "coffee", "cookie", "cream", "date", "dough", "fig",
        "flour", "ginger", "grain", "grape", "honey", "jam", "juice",
        "kiwi", "lemon", "mango", "maple", "melon", "milk", "muffin",
        "mushroom", "noodle", "nut", "olive", "onion", "orange", "pancake",
        "peach", "peanut", "pepper", "pie", "pizza", "plum", "potato",
        "pudding", "pumpkin", "rice", "salad", "salt", "sandwich", "sauce",
        "smoothie", "soup", "spice", "steak", "strawberry", "sugar", "syrup",
        "tea", "toast", "tomato", "vanilla", "waffle", "walnut", "wheat",
        "yogurt",
    ],
    "travel": [
        "airport", "anchor", "arrival", "baggage", "barge", "bicycle",
        "border", "bridge", "bus", "cab", "canal", "caravan", "cargo",
        "carrier", "charter", "cruise", "departure", "destination", "dock",
        "embark", "ferry", "flight", "freeway", "galley", "gate", "glider",
        "harbor", "highway", "hotel", "journey", "kayak", "landing", "luggage",
        "map", "moor", "motel", "navigation", "ocean", "odometer", "passport",
        "pier", "pilot", "platform", "port", "raft", "railway", "route",
        "sail", "ship", "shuttle", "subway", "taxi", "terminal", "ticket",
        "tour", "track", "traffic", "trail", "train", "transit", "transport",
        "trolley", "van", "vehicle", "voyage", "wagon", "yacht",
    ],
    "finance": [
        "account", "asset", "balance", "bank", "bond", "budget", "capital",
        "cash", "coin", "commodity", "credit", "currency", "debt", "deficit",
        "deposit", "dividend", "equity", "exchange", "fee", "fund", "gold",
        "growth", "hedge", "income", "index", "inflation", "interest",
        "investment", "ledger", "leverage", "loan", "margin", "market",
        "mortgage", "payment", "portfolio", "premium", "profit", "rate",
        "reserve", "return", "risk", "savings", "share", "stock", "swap",
        "tariff", "tax", "trade", "treasury", "trust", "vault", "wealth",
        "yield",
    ],
}


@dataclass
class LLMSuggestion:
    """A suggestion from an LLM with metadata."""
    word: str
    position: int
    confidence: float
    reasoning: str = ""
    provider: str = ""


@dataclass
class RecoveryAttempt:
    """Track a recovery attempt for adaptive learning."""
    candidate: MnemonicCandidate
    result: str  # "success", "invalid_checksum", "wrong_address", "error"
    timestamp: float = 0.0
    llm_suggested: bool = False


class LLMCandidateGenerator:
    """
    Uses LLMs to generate likely seedphrase candidates.

    This is the core AI integration that dramatically improves recovery
    by using language models to predict likely BIP-39 word sequences,
    correct misremembered words, and prioritize search space.
    """

    def __init__(self, provider: BaseLLMProvider, bip39: BIP39Engine):
        self.provider = provider
        self.bip39 = bip39
        self._attempt_history: List[RecoveryAttempt] = []

    async def suggest_missing_words(
        self,
        context: RecoveryContext,
        position: int,
        top_k: int = 20
    ) -> List[LLMSuggestion]:
        """
        Ask the LLM to suggest likely words for a specific missing position.

        The LLM is given the known words and context to make intelligent
        predictions based on human psychology and common patterns.
        """
        # Build the partial mnemonic with [MISSING] markers
        partial = []
        for i in range(context.total_words):
            if i in context.known_words:
                partial.append(context.known_words[i])
            elif i in context.approximate_words:
                partial.append(f"[~{context.approximate_words[i]}~]")
            else:
                partial.append("[MISSING]")

        partial_str = " ".join(partial)

        # Build the prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_word_suggestion_prompt(
            partial_str, position, context, top_k
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await self.provider.chat(messages, temperature=0.3)

        if not response.success:
            return []

        return self._parse_word_suggestions(response.content, position, top_k)

    async def suggest_seedphrase_corrections(
        self,
        words: List[str],
        context: RecoveryContext,
        top_k: int = 10
    ) -> List[MnemonicCandidate]:
        """
        Given a possibly-incorrect seedphrase, ask the LLM to suggest
        corrections. This is useful when the user has a seedphrase that
        doesn't validate (wrong checksum) - likely due to a few word errors.
        """
        system_prompt = self._build_system_prompt()
        user_prompt = (
            f"A user has a seedphrase that doesn't validate. "
            f"Here are the words they wrote down:\n\n"
            f"{' '.join(words)}\n\n"
            f"Some of these words might be wrong. The user may have:\n"
            f"- Written a similar-sounding word instead of the correct BIP-39 word\n"
            f"- Made a spelling error\n"
            f"- Confused two words that look or sound similar\n\n"
        )

        if context.approximate_words:
            user_prompt += (
                f"The user says these words might not be exact: "
                f"{context.approximate_words}\n\n"
            )

        if context.time_since_exposure:
            user_prompt += (
                f"The user last saw this seedphrase {context.time_since_exposure} days ago. "
                f"Memory decay may have introduced errors.\n\n"
            )

        if context.user_notes:
            user_prompt += f"User notes: {context.user_notes}\n\n"

        user_prompt += (
            f"Please suggest the top {top_k} most likely corrected seedphrases. "
            f"Output ONLY valid JSON array of objects with keys: "
            f'"words" (array of 12 strings), "confidence" (0-1), "reasoning" (string).\n'
            f'Every word MUST be from the BIP-39 English wordlist.'
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await self.provider.chat(messages, temperature=0.4, max_tokens=4096)

        if not response.success:
            return []

        return self._parse_candidate_suggestions(response.content, top_k)

    async def generate_password_candidates(
        self,
        user_hints: Dict[str, str],
        top_k: int = 50
    ) -> List[Tuple[str, float]]:
        """
        Generate likely password/passphrase candidates based on user hints.

        Uses the LLM's understanding of human password psychology to
        generate candidates that a traditional dictionary attack would miss.
        """
        system_prompt = (
            "You are a password recovery expert. You understand human psychology "
            "and how people create passwords. Given context about a user, generate "
            "likely password candidates. Consider common patterns:\n"
            "- Name + number (e.g., 'John123')\n"
            "- Pet name + special chars (e.g., 'Fluffy!')\n"
            "- Birthday formats (e.g., '011590', 'Jan1590')\n"
            "- Favorite things + year (e.g., 'Bitcoin2019')\n"
            "- Keyboard patterns (e.g., 'qwerty', 'asdf')\n"
            "- Leet speak (e.g., 'p4ssw0rd')\n"
            "- Cultural references (e.g., 'Hogwarts1')\n\n"
            "Output ONLY a JSON array of objects with keys: "
            '"password" (string), "confidence" (0-1), "reasoning" (string).'
        )

        hints_str = "\n".join(f"- {k}: {v}" for k, v in user_hints.items())
        user_prompt = (
            f"Generate the top {top_k} most likely password candidates for a crypto wallet passphrase "
            f"based on these hints about the user:\n\n{hints_str}\n\n"
            f"Be creative and consider all psychological patterns. "
            f"The passphrase could be simple or complex."
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await self.provider.chat(messages, temperature=0.7, max_tokens=4096)

        if not response.success:
            return []

        return self._parse_password_suggestions(response.content, top_k)

    async def semantic_cluster_search(
        self,
        theme_hint: str,
        top_k: int = 50
    ) -> List[str]:
        """
        Given a theme hint (e.g., "nature", "the user loves the ocean"),
        return BIP-39 words semantically related to that theme.

        Combines pre-built semantic clusters with LLM reasoning.
        """
        # First, check pre-built clusters
        prebuilt = set()
        theme_lower = theme_hint.lower()
        for cluster_name, words in BIP39_SEMANTIC_CLUSTERS.items():
            if cluster_name in theme_lower or theme_lower in cluster_name:
                for w in words:
                    if self.bip39.is_valid_word(w):
                        prebuilt.add(w)

        # Then, ask LLM for additional suggestions
        system_prompt = (
            "You are a BIP-39 seedphrase expert. Given a theme or description, "
            "suggest BIP-39 English words that are semantically related. "
            "Only suggest words that are in the official BIP-39 English wordlist. "
            "Output ONLY a JSON array of word strings."
        )

        user_prompt = (
            f"Given the theme/description: '{theme_hint}'\n\n"
            f"Suggest up to {top_k} BIP-39 English words that are semantically "
            f"related to this theme. Only include words from the official BIP-39 wordlist."
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await self.provider.chat(messages, temperature=0.5)

        llm_words = set()
        if response.success:
            try:
                words = json.loads(response.content)
                if isinstance(words, list):
                    for w in words:
                        w = str(w).strip().lower()
                        if self.bip39.is_valid_word(w):
                            llm_words.add(w)
            except json.JSONDecodeError:
                pass

        # Combine and deduplicate
        all_words = list(prebuilt | llm_words)
        all_words = [w for w in all_words if self.bip39.is_valid_word(w)]

        return all_words[:top_k]

    def record_attempt(self, candidate: MnemonicCandidate, result: str):
        """Record a recovery attempt for adaptive learning."""
        self._attempt_history.append(RecoveryAttempt(
            candidate=candidate,
            result=result,
            timestamp=time.time(),
            llm_suggested=candidate.source in ("llm", "semantic", "cognitive"),
        ))

    async def adaptive_refine(self, context: RecoveryContext) -> List[LLMSuggestion]:
        """
        Use failed attempt history to refine future suggestions.

        This implements the "Adaptive Learning" technique: learn from failures
        to avoid repeating similar patterns and focus on more promising areas.
        """
        if not self._attempt_history:
            return []

        # Summarize failed attempts
        failed_words = set()
        for attempt in self._attempt_history[-50:]:  # Last 50 attempts
            if attempt.result != "success":
                for w in attempt.candidate.words:
                    failed_words.add(w)

        # Ask LLM to suggest new directions
        system_prompt = self._build_system_prompt()
        user_prompt = (
            f"I've been trying to recover a {context.total_words}-word seedphrase. "
            f"The following words have been tried and failed:\n"
            f"{', '.join(sorted(failed_words))}\n\n"
            f"Known correct words: {context.known_words}\n\n"
            f"Please suggest NEW words that haven't been tried yet, "
            f"focusing on different semantic areas and patterns. "
            f"Output ONLY a JSON array of objects with keys: "
            f'"word" (string), "position" (int), "confidence" (0-1), "reasoning" (string).'
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await self.provider.chat(messages, temperature=0.8)

        if not response.success:
            return []

        suggestions = []
        try:
            data = json.loads(response.content)
            if isinstance(data, list):
                for item in data[:20]:
                    word = item.get("word", "").strip().lower()
                    if self.bip39.is_valid_word(word):
                        suggestions.append(LLMSuggestion(
                            word=word,
                            position=item.get("position", 0),
                            confidence=item.get("confidence", 0.5),
                            reasoning=item.get("reasoning", ""),
                            provider=self.provider.config.name,
                        ))
        except (json.JSONDecodeError, AttributeError):
            pass

        return suggestions

    def _build_system_prompt(self) -> str:
        """Build the system prompt for seedphrase-related queries."""
        return (
            "You are the world's foremost expert in BIP-39 seedphrase recovery. "
            "You have deep knowledge of:\n"
            "1. The BIP-39 standard and its 2048-word English wordlist\n"
            "2. Human memory and how people misremember words\n"
            "3. Phonetic and visual similarity between words\n"
            "4. Common patterns in how people choose seedphrases\n"
            "5. Cognitive biases that affect word recall\n\n"
            "Your task is to suggest the most likely correct words for a "
            "partially-known seedphrase. Consider:\n"
            "- Phonetic similarity (words that sound alike)\n"
            "- Visual similarity (words that look alike when written)\n"
            "- Semantic clustering (words related by meaning)\n"
            "- Memory decay patterns (how errors change over time)\n"
            "- Common word confusion patterns\n\n"
            "IMPORTANT: Every word you suggest MUST be from the official "
            "BIP-39 English wordlist (2048 words). Never suggest a word "
            "that is not in the wordlist.\n\n"
            "Output format: Always respond with valid JSON as specified in the user prompt."
        )

    def _build_word_suggestion_prompt(
        self,
        partial_str: str,
        position: int,
        context: RecoveryContext,
        top_k: int
    ) -> str:
        """Build the prompt for word suggestion at a specific position."""
        prompt = (
            f"I'm trying to recover a {context.total_words}-word BIP-39 seedphrase.\n\n"
            f"Here's what I know (marked with [MISSING] for unknown words, "
            f"[~word~] for approximate words):\n\n"
            f"{partial_str}\n\n"
            f"I need suggestions for position {position} (0-indexed).\n\n"
        )

        if position in context.approximate_words:
            prompt += (
                f"The user thinks position {position} might be "
                f"'{context.approximate_words[position]}', but they're not sure. "
                f"Consider words that sound or look similar.\n\n"
            )

        if context.time_since_exposure:
            prompt += (
                f"The user last saw this seedphrase {context.time_since_exposure} days ago. "
                f"Older memories tend to have more phonetic/visual confusion errors.\n\n"
            )

        if context.user_notes:
            prompt += f"User notes: {context.user_notes}\n\n"

        prompt += (
            f"Please suggest the top {top_k} most likely BIP-39 words for position {position}. "
            f"For each, explain why you think it's likely.\n\n"
            f"Output ONLY a JSON array of objects with keys: "
            f'"word" (string, must be in BIP-39 wordlist), '
            f'"confidence" (float 0-1), '
            f'"reasoning" (string).'
        )

        return prompt

    def _parse_word_suggestions(
        self, response_text: str, position: int, top_k: int
    ) -> List[LLMSuggestion]:
        """Parse LLM response into structured word suggestions."""
        suggestions = []

        # Try to extract JSON from response
        try:
            # Find JSON array in response
            text = response_text.strip()
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                if isinstance(data, list):
                    for item in data[:top_k]:
                        word = str(item.get("word", "")).strip().lower()
                        if self.bip39.is_valid_word(word):
                            suggestions.append(LLMSuggestion(
                                word=word,
                                position=position,
                                confidence=float(item.get("confidence", 0.5)),
                                reasoning=str(item.get("reasoning", "")),
                                provider=self.provider.config.name,
                            ))
        except (json.JSONDecodeError, ValueError, TypeError):
            # Fallback: try to extract individual words
            for line in response_text.split('\n'):
                line = line.strip().strip('-').strip('*').strip()
                word = line.split()[0].lower() if line else ""
                if self.bip39.is_valid_word(word):
                    suggestions.append(LLMSuggestion(
                        word=word,
                        position=position,
                        confidence=0.3,
                        provider=self.provider.config.name,
                    ))

        return suggestions[:top_k]

    def _parse_candidate_suggestions(
        self, response_text: str, top_k: int
    ) -> List[MnemonicCandidate]:
        """Parse LLM response into full mnemonic candidates."""
        candidates = []

        try:
            text = response_text.strip()
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                if isinstance(data, list):
                    for item in data[:top_k]:
                        words = item.get("words", [])
                        if isinstance(words, list) and len(words) in (12, 15, 18, 21, 24):
                            # Validate all words are BIP-39
                            valid = all(self.bip39.is_valid_word(w) for w in words)
                            if valid:
                                candidates.append(MnemonicCandidate(
                                    words=[w.lower() for w in words],
                                    confidence=float(item.get("confidence", 0.5)),
                                    source="llm",
                                ))
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

        return candidates

    def _parse_password_suggestions(
        self, response_text: str, top_k: int
    ) -> List[Tuple[str, float]]:
        """Parse LLM response into password candidates."""
        candidates = []

        try:
            text = response_text.strip()
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                if isinstance(data, list):
                    for item in data[:top_k]:
                        pw = str(item.get("password", ""))
                        conf = float(item.get("confidence", 0.5))
                        if pw:
                            candidates.append((pw, conf))
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

        return candidates


class MultiProviderConsensus:
    """
    Query multiple LLMs in parallel and use consensus voting
    to improve suggestion quality.

    This implements the "Consensus Validation" technique:
    - Query N different LLMs for the same position
    - Weight their suggestions by provider reliability and agreement
    - Return only high-consensus suggestions
    """

    def __init__(self, providers: List[BaseLLMProvider], bip39: BIP39Engine):
        self.providers = providers
        self.bip39 = bip39
        self._generators = [
            LLMCandidateGenerator(p, bip39) for p in providers
        ]

    async def suggest_with_consensus(
        self,
        context: RecoveryContext,
        position: int,
        top_k: int = 20,
        min_consensus: int = 2
    ) -> List[LLMSuggestion]:
        """
        Get suggestions from multiple providers and return only those
        that have consensus (appear in multiple providers' results).
        """
        # Query all providers in parallel
        tasks = [
            gen.suggest_missing_words(context, position, top_k * 2)
            for gen in self._generators
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate suggestions
        word_scores: Dict[str, List[Tuple[float, str, str]]] = {}
        for result in results:
            if isinstance(result, Exception):
                continue
            for suggestion in result:
                if suggestion.word not in word_scores:
                    word_scores[suggestion.word] = []
                word_scores[suggestion.word].append(
                    (suggestion.confidence, suggestion.reasoning, suggestion.provider)
                )

        # Build consensus suggestions
        consensus_suggestions = []
        for word, scores in word_scores.items():
            provider_count = len(scores)
            if provider_count >= min_consensus:
                avg_confidence = sum(s[0] for s in scores) / len(scores)
                # Boost confidence for multi-provider consensus
                consensus_boost = 1.0 + (0.1 * (provider_count - 1))
                final_confidence = min(avg_confidence * consensus_boost, 1.0)

                all_reasoning = "; ".join(
                    f"[{s[2]}] {s[1]}" for s in scores
                )

                consensus_suggestions.append(LLMSuggestion(
                    word=word,
                    position=position,
                    confidence=final_confidence,
                    reasoning=f"Consensus from {provider_count} providers: {all_reasoning}",
                    provider=",".join(s[2] for s in scores),
                ))

        # Sort by confidence
        consensus_suggestions.sort(key=lambda x: -x.confidence)
        return consensus_suggestions[:top_k]
