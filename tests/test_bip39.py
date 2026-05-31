"""Tests for BIP-39 Engine"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.bip39_engine import BIP39Engine, RecoveryContext, MnemonicCandidate


class TestBIP39Engine:
    """Tests for BIP39Engine."""

    @pytest.fixture
    def engine(self):
        return BIP39Engine()

    def test_wordlist_loaded(self, engine):
        """Test that the BIP-39 wordlist loads correctly."""
        assert len(engine.wordlist) == 2048

    def test_get_word(self, engine):
        """Test word lookup by index."""
        word = engine.get_word(0)
        assert word == "abandon"
        word = engine.get_word(2047)
        assert word == "zoo"

    def test_get_index(self, engine):
        """Test index lookup by word."""
        assert engine.get_index("abandon") == 0
        assert engine.get_index("zoo") == 2047
        assert engine.get_index("notaword") == -1

    def test_is_valid_word(self, engine):
        """Test word validation."""
        assert engine.is_valid_word("abandon") is True
        assert engine.is_valid_word("zoo") is True
        assert engine.is_valid_word("notaword") is False
        assert engine.is_valid_word("ABANDON") is True  # .lower() is applied internally
        assert engine.is_valid_word(" abandon ") is True  # Strips whitespace

    def test_find_similar_words(self, engine):
        """Test phonetic/visual similarity search."""
        similar = engine.find_similar_words("abandn", max_distance=2)
        words = [w for w, d in similar]
        assert "abandon" in words

    def test_find_prefix_matches(self, engine):
        """Test prefix-based word search."""
        matches = engine.find_prefix_matches("aba")
        assert "abandon" in matches
        assert "abandon" in matches
        assert all(w.startswith("aba") for w in matches)

    def test_validate_mnemonic_valid(self, engine):
        """Test validation of a known valid mnemonic."""
        # This is a well-known test vector
        words = [
            "abandon", "abandon", "abandon", "abandon",
            "abandon", "abandon", "abandon", "abandon",
            "abandon", "abandon", "abandon", "about"
        ]
        assert engine.validate_mnemonic(words) is True

    def test_validate_mnemonic_invalid(self, engine):
        """Test validation of an invalid mnemonic."""
        words = [
            "abandon", "abandon", "abandon", "abandon",
            "abandon", "abandon", "abandon", "abandon",
            "abandon", "abandon", "abandon", "abandon"
        ]
        assert engine.validate_mnemonic(words) is False

    def test_validate_mnemonic_invalid_word(self, engine):
        """Test that mnemonics with invalid words fail."""
        words = [
            "notaword", "abandon", "abandon", "abandon",
            "abandon", "abandon", "abandon", "abandon",
            "abandon", "abandon", "abandon", "about"
        ]
        assert engine.validate_mnemonic(words) is False

    def test_validate_mnemonic_wrong_length(self, engine):
        """Test that wrong-length mnemonics fail."""
        assert engine.validate_mnemonic(["abandon"] * 11) is False
        assert engine.validate_mnemonic(["abandon"] * 13) is False

    def test_derive_seed(self, engine):
        """Test seed derivation."""
        words = [
            "abandon", "abandon", "abandon", "abandon",
            "abandon", "abandon", "abandon", "abandon",
            "abandon", "abandon", "abandon", "about"
        ]
        seed = engine.derive_seed(words)
        assert isinstance(seed, bytes)
        assert len(seed) == 64  # SHA-512 produces 64 bytes

    def test_derive_seed_with_passphrase(self, engine):
        """Test seed derivation with passphrase."""
        words = [
            "abandon", "abandon", "abandon", "abandon",
            "abandon", "abandon", "abandon", "abandon",
            "abandon", "abandon", "abandon", "about"
        ]
        seed1 = engine.derive_seed(words, "")
        seed2 = engine.derive_seed(words, "mypassword")
        assert seed1 != seed2  # Different passphrases produce different seeds

    def test_search_space_size(self, engine):
        """Test search space calculation."""
        # 1 missing word
        assert engine.get_search_space_size(1) == 2048

        # 1 missing word at last position (checksum constrained)
        assert engine.get_search_space_size(1, last_word_missing=True) == 128

        # 2 missing words
        assert engine.get_search_space_size(2) == 2048 * 2048

        # 0 missing words
        assert engine.get_search_space_size(0) == 1


class TestRecoveryContext:
    """Tests for RecoveryContext."""

    def test_default_context(self):
        ctx = RecoveryContext()
        assert ctx.total_words == 12
        assert ctx.known_words == {}
        assert ctx.missing_positions == []
        assert ctx.wallet_type == "bitcoin"

    def test_custom_context(self):
        ctx = RecoveryContext(
            total_words=24,
            known_words={0: "abandon", 1: "ability"},
            missing_positions=[2, 3, 4],
            approximate_words={5: "ocean"},
            target_addresses=["bc1qexample"],
            time_since_exposure=180,
        )
        assert ctx.total_words == 24
        assert len(ctx.known_words) == 2
        assert len(ctx.missing_positions) == 3


class TestMnemonicCandidate:
    """Tests for MnemonicCandidate."""

    def test_to_string(self):
        candidate = MnemonicCandidate(
            words=["abandon", "ability", "about"],
            confidence=0.8,
            source="llm",
        )
        assert candidate.to_string() == "abandon ability about"

    def test_hash(self):
        c1 = MnemonicCandidate(words=["abandon", "ability"], confidence=0.5)
        c2 = MnemonicCandidate(words=["abandon", "ability"], confidence=0.9)
        assert hash(c1) == hash(c2)  # Same words = same hash
