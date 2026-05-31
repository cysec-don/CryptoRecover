"""Tests for Enhanced Bruteforce Engine"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.bip39_engine import BIP39Engine, RecoveryContext
from src.bruteforce.enhanced_engine import (
    EnhancedBruteforceEngine, EntropyFunnel, CognitiveTraversal,
    SemanticResonance, AdversarialCandidateGenerator,
    ProbabilisticCheckpointManager, MultiOracleValidator,
    SearchState, RecoveryPhase, ValidationResult,
)
from src.core.phonetic_visual import CognitiveGraph, PhoneticMapper, VisualMapper


class TestEntropyFunnel:
    """Tests for Entropy Funnel."""

    @pytest.fixture
    def engine(self):
        return BIP39Engine()

    @pytest.fixture
    def cognitive(self):
        return CognitiveGraph()

    @pytest.fixture
    def funnel(self, engine, cognitive):
        return EntropyFunnel(engine, cognitive)

    def test_funnel_basic(self, funnel, engine):
        """Test that the funnel filters and ranks candidates."""
        raw = [("abandon", 0, 0.5), ("notaword", 0, 0.8), ("ability", 0, 0.3)]
        result = funnel.funnel_candidates(raw, RecoveryContext(), max_output=10)
        # "notaword" should be filtered out (not in BIP-39)
        words = [w for w, p, c in result]
        assert "notaword" not in words
        assert "abandon" in words

    def test_funnel_with_approximate_words(self, funnel, engine):
        """Test that approximate words get a confidence boost."""
        context = RecoveryContext(
            approximate_words={0: "abandn"}  # Typo of "abandon"
        )
        raw = [("abandon", 0, 0.5), ("ability", 0, 0.5)]
        result = funnel.funnel_candidates(raw, context, max_output=10)
        # "abandon" should have higher confidence due to similarity
        abandon_score = next(c for w, p, c in result if w == "abandon")
        ability_score = next(c for w, p, c in result if w == "ability")
        assert abandon_score > ability_score


class TestCognitiveTraversal:
    """Tests for Cognitive Graph Traversal."""

    @pytest.fixture
    def engine(self):
        return BIP39Engine()

    @pytest.fixture
    def traversal(self, engine):
        return CognitiveTraversal(engine, CognitiveGraph())

    def test_generate_candidates_with_approximate(self, traversal, engine):
        """Test generating candidates when approximate words are provided."""
        context = RecoveryContext(
            total_words=12,
            missing_positions=[0],
            approximate_words={0: "abandn"},
        )
        candidates = traversal.generate_cognitive_candidates(context, top_k_per_position=10)
        assert 0 in candidates
        # Should suggest "abandon" as a likely correction
        words = [w for w, p in candidates[0]]
        assert "abandon" in words


class TestSemanticResonance:
    """Tests for Semantic Resonance."""

    @pytest.fixture
    def engine(self):
        return BIP39Engine()

    @pytest.fixture
    def resonance(self, engine):
        return SemanticResonance(engine)

    def test_resonance_score(self, resonance):
        """Test that semantic resonance computation works."""
        score = resonance.resonance_score("abandon", "ability")
        assert 0.0 <= score <= 1.0

    def test_self_resonance(self, resonance):
        """Test that a word has maximum resonance with itself."""
        score = resonance.resonance_score("abandon", "abandon")
        assert score > 0.9

    def test_predict_next_words(self, resonance):
        """Test word prediction based on resonance."""
        predictions = resonance.predict_next_words(["abandon", "ability"], top_k=10)
        assert len(predictions) > 0
        assert len(predictions) <= 10
        # All predictions should be BIP-39 words
        for word, score in predictions:
            assert 0.0 <= score <= 1.0


class TestAdversarialGenerator:
    """Tests for Adversarial Candidate Generation."""

    @pytest.fixture
    def engine(self):
        return BIP39Engine()

    @pytest.fixture
    def generator(self, engine):
        return AdversarialCandidateGenerator(engine)

    def test_generate_candidates(self, generator):
        """Test adversarial candidate generation."""
        # All positions except 2 are known
        context = RecoveryContext(
            total_words=12,
            known_words={i: "abandon" for i in range(12) if i != 2},
            missing_positions=[2],
        )
        # But the last word (position 11) needs to produce a valid checksum
        # So we set only 1 missing position
        context.known_words = {
            0: "abandon", 1: "ability", 3: "about", 4: "above",
            5: "absent", 6: "absorb", 7: "abstract", 8: "absurd",
            9: "abuse", 10: "access", 11: "accident"
        }
        context.missing_positions = [2]
        candidates = generator.generate_adversarial_candidates(context, budget=100)
        assert len(candidates) > 0
        assert len(candidates) <= 100


class TestProbabilisticCheckpointManager:
    """Tests for Probabilistic Checkpoint Recovery."""

    def test_add_and_get_state(self):
        """Test adding and retrieving states."""
        mgr = ProbabilisticCheckpointManager()
        state = SearchState(
            phase=RecoveryPhase.LLM_GUIDED,
            position=0,
            word_index=0,
            candidates_remaining=100,
            priority=0.5,
        )
        mgr.add_state(state)
        next_state = mgr.get_next_state()
        assert next_state is not None
        assert next_state.phase == RecoveryPhase.LLM_GUIDED

    def test_ucb1_score(self):
        """Test UCB1 scoring."""
        state = SearchState(
            phase=RecoveryPhase.COGNITIVE,
            position=0,
            word_index=0,
            candidates_tried=0,
            priority=0.5,
        )
        # Untried states should have infinite score
        assert state.ucb1_score(100) == float('inf')

        # Tried states should have finite score
        state.candidates_tried = 10
        score = state.ucb1_score(100)
        assert 0 < score < float('inf')

    def test_save_and_load_checkpoint(self):
        """Test checkpoint save/load."""
        mgr = ProbabilisticCheckpointManager()
        mgr.add_state(SearchState(
            phase=RecoveryPhase.SEMANTIC,
            position=3,
            word_index=500,
            candidates_tried=50,
            candidates_remaining=200,
            priority=0.8,
        ))

        data = mgr.save_checkpoint()
        assert "states" in data
        assert len(data["states"]) == 1

        mgr2 = ProbabilisticCheckpointManager()
        mgr2.load_checkpoint(data)
        state = mgr2.get_next_state()
        assert state is not None


class TestPhoneticMapper:
    """Tests for Phonetic Mapper."""

    def test_soundex(self):
        mapper = PhoneticMapper()
        code = mapper.soundex("abandon")
        assert len(code) == 4
        assert code[0].isalpha()

    def test_phonetic_similarity(self):
        mapper = PhoneticMapper()
        # Same word should have high similarity
        sim = mapper.phonetic_similarity("abandon", "abandon")
        assert sim > 0.5

    def test_different_words(self):
        mapper = PhoneticMapper()
        sim = mapper.phonetic_similarity("abandon", "zoo")
        assert sim < 0.5


class TestVisualMapper:
    """Tests for Visual Mapper."""

    def test_keyboard_typo_candidates(self):
        mapper = VisualMapper()
        typos = mapper.keyboard_typo_candidates("abandon")
        assert len(typos) > 0

    def test_visual_similarity(self):
        mapper = VisualMapper()
        sim = mapper.visual_similarity("abandon", "abandon")
        assert sim > 0.8

        sim2 = mapper.visual_similarity("abc", "xyz")
        assert sim2 < 0.5


class TestCognitiveGraph:
    """Tests for Cognitive Graph."""

    def test_confusion_probability_exact(self):
        graph = CognitiveGraph()
        prob = graph.get_confusion_probability("abandon", "abandon", days_since_exposure=0)
        assert prob > 0.5

    def test_confusion_probability_decay(self):
        graph = CognitiveGraph()
        prob_recent = graph.get_confusion_probability("abandon", "abandon", days_since_exposure=1)
        prob_old = graph.get_confusion_probability("abandon", "abandon", days_since_exposure=1000)
        assert prob_recent > prob_old

    def test_get_likely_actual_words(self):
        graph = CognitiveGraph()
        bip39 = BIP39Engine()
        likely = graph.get_likely_actual_words(
            "abandn", bip39.wordlist, days_since=30, top_k=10
        )
        assert len(likely) > 0
        words = [w for w, p in likely]
        assert "abandon" in words
