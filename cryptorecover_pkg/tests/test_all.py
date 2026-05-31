"""
CryptoRecover - Test Suite
"""

import unittest
import sys
from pathlib import Path

# Add parent to path
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
    SeedType,
    LoginTech,
    list_all_wallets,
)
from utils.helpers import (
    calculate_seed_combinations,
    format_time,
    format_number,
    generate_password_mutations,
    validate_seed_phrase_format,
)


class TestBIP39Wordlist(unittest.TestCase):
    """Test BIP39 wordlist loading"""

    def test_wordlist_loads(self):
        wordlist = get_bip39_wordlist()
        self.assertGreater(len(wordlist), 0)

    def test_wordlist_has_2048_words(self):
        wordlist = get_bip39_wordlist()
        self.assertEqual(len(wordlist), 2048, "BIP39 wordlist should have exactly 2048 words")

    def test_wordlist_contains_common_words(self):
        wordlist = get_bip39_wordlist()
        self.assertIn("abandon", wordlist)
        self.assertIn("zoo", wordlist)
        self.assertIn("art", wordlist)

    def test_wordlist_no_empty_entries(self):
        wordlist = get_bip39_wordlist()
        for word in wordlist:
            self.assertTrue(len(word) > 0, "Wordlist should not contain empty entries")


class TestBIP39Checksum(unittest.TestCase):
    """Test BIP39 checksum validation"""

    def test_valid_12_word_seed(self):
        # Known valid BIP39 seed
        words = ["abandon", "abandon", "abandon", "abandon", "abandon", "abandon",
                 "abandon", "abandon", "abandon", "abandon", "abandon", "about"]
        result = validate_bip39_checksum(words)
        self.assertTrue(result, "Known valid 12-word seed should pass checksum")

    def test_invalid_seed(self):
        words = ["abandon", "abandon", "abandon", "abandon", "abandon", "abandon",
                 "abandon", "abandon", "abandon", "abandon", "abandon", "abandon"]
        result = validate_bip39_checksum(words)
        self.assertFalse(result, "Modified seed should fail checksum")

    def test_invalid_word_in_seed(self):
        words = ["abandon", "abandon", "abandon", "abandon", "abandon", "abandon",
                 "abandon", "abandon", "abandon", "abandon", "abandon", "zzzzz"]
        result = validate_bip39_checksum(words)
        self.assertFalse(result, "Seed with invalid word should fail")


class TestMnemonicToSeed(unittest.TestCase):
    """Test mnemonic to seed conversion"""

    def test_basic_conversion(self):
        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        seed = mnemonic_to_seed(mnemonic, "")
        self.assertEqual(len(seed), 64, "Seed should be 64 bytes (512 bits)")

    def test_with_passphrase(self):
        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        seed_no_pass = mnemonic_to_seed(mnemonic, "")
        seed_with_pass = mnemonic_to_seed(mnemonic, "mypassword")
        self.assertNotEqual(seed_no_pass, seed_with_pass,
                           "Different passphrases should produce different seeds")


class TestWalletDatabase(unittest.TestCase):
    """Test wallet database"""

    def test_wallets_loaded(self):
        self.assertGreater(len(WALLETS), 40, "Should have 40+ wallets in database")

    def test_list_all_wallets(self):
        names = list_all_wallets()
        self.assertIsInstance(names, list)
        self.assertIn("MetaMask", names)
        self.assertIn("Electrum", names)
        self.assertIn("Ledger Nano S", names)

    def test_wallet_info_complete(self):
        for name, wallet in WALLETS.items():
            self.assertIsInstance(wallet.name, str)
            self.assertTrue(len(wallet.name) > 0)
            self.assertIsInstance(wallet.category, list)
            self.assertTrue(len(wallet.category) > 0)
            self.assertIsInstance(wallet.login_technologies, list)
            self.assertTrue(len(wallet.login_technologies) > 0)
            self.assertIsInstance(wallet.supported_coins, list)
            self.assertTrue(len(wallet.supported_coins) > 0)

    def test_wallets_by_seed_type(self):
        from wallets.wallet_database import get_wallets_by_seed_type
        bip39_wallets = get_wallets_by_seed_type(SeedType.BIP39)
        self.assertGreater(len(bip39_wallets), 10, "Many wallets should support BIP39")

    def test_wallets_by_coin(self):
        from wallets.wallet_database import get_wallets_by_coin
        btc_wallets = get_wallets_by_coin("BTC")
        self.assertGreater(len(btc_wallets), 5, "Many wallets should support BTC")


class TestRecoveryEngine(unittest.TestCase):
    """Test recovery engine"""

    def test_config_creation(self):
        config = RecoveryConfig(
            recovery_type=RecoveryType.SEED_PHRASE,
            seed_length=12,
            known_words=["abandon", "abandon", "abandon", "abandon", "abandon", "abandon",
                         "abandon", "abandon", "abandon", "abandon", "abandon"],
            missing_word_positions=[11],
        )
        self.assertEqual(config.recovery_type, RecoveryType.SEED_PHRASE)
        self.assertEqual(config.seed_length, 12)

    def test_engine_creation(self):
        config = RecoveryConfig(recovery_type=RecoveryType.SEED_PHRASE)
        engine = RecoveryEngine(config)
        self.assertEqual(engine.status, RecoveryStatus.IDLE)

    def test_cancel_recovery(self):
        config = RecoveryConfig(recovery_type=RecoveryType.SEED_PHRASE)
        engine = RecoveryEngine(config)
        engine.cancel()
        self.assertEqual(engine.status, RecoveryStatus.CANCELLED)

    def test_single_word_recovery(self):
        """Test recovering a single missing word"""
        # Known valid seed with one word missing
        config = RecoveryConfig(
            recovery_type=RecoveryType.SEED_PHRASE,
            seed_length=12,
            known_words=["abandon", "abandon", "abandon", "abandon", "abandon", "abandon",
                         "abandon", "abandon", "abandon", "abandon", "abandon"],
            missing_word_positions=[11],
        )
        engine = RecoveryEngine(config)
        result = engine.recover_seed_phrase()
        self.assertTrue(result.success, "Should find the missing word 'about'")
        self.assertIn("about", result.found_value)

    def test_recovery_no_missing_positions(self):
        """Test recovery with no missing positions"""
        config = RecoveryConfig(
            recovery_type=RecoveryType.SEED_PHRASE,
            seed_length=12,
            known_words=["abandon"] * 12,
            missing_word_positions=[],
        )
        engine = RecoveryEngine(config)
        result = engine.recover_seed_phrase()
        self.assertFalse(result.success)
        self.assertEqual(result.status, RecoveryStatus.ERROR)

    def test_recovery_word_count_mismatch(self):
        """Test recovery with mismatched word count"""
        config = RecoveryConfig(
            recovery_type=RecoveryType.SEED_PHRASE,
            seed_length=12,
            known_words=["abandon"] * 15,
            missing_word_positions=[0],
        )
        engine = RecoveryEngine(config)
        result = engine.recover_seed_phrase()
        self.assertFalse(result.success)


class TestRecoveryFlowOrchestrator(unittest.TestCase):
    """Test recovery flow orchestrator"""

    def test_determine_seed_recovery(self):
        steps = RecoveryFlowOrchestrator.determine_recovery_scenario(
            has_partial_seed=True, missing_seed_words=2
        )
        self.assertIn(RecoveryType.SEED_PHRASE, steps)

    def test_determine_passphrase_recovery(self):
        steps = RecoveryFlowOrchestrator.determine_recovery_scenario(
            has_seed=True, forgot_passphrase=True
        )
        self.assertIn(RecoveryType.PASSPHRASE, steps)

    def test_determine_password_recovery(self):
        steps = RecoveryFlowOrchestrator.determine_recovery_scenario(
            has_wallet_file=True, forgot_password=True
        )
        self.assertIn(RecoveryType.PASSWORD, steps)


class TestUtilities(unittest.TestCase):
    """Test utility functions"""

    def test_calculate_seed_combinations(self):
        # 1 missing word from 2048 wordlist
        self.assertEqual(calculate_seed_combinations(1), 2048)
        # 2 missing words
        self.assertEqual(calculate_seed_combinations(2), 2048 * 2048)

    def test_format_time(self):
        self.assertEqual(format_time(30), "30.0s")
        self.assertEqual(format_time(120), "2.0m")
        self.assertEqual(format_time(7200), "2.0h")

    def test_format_number(self):
        self.assertEqual(format_number(1000), "1,000")
        self.assertEqual(format_number(1000000), "1,000,000")

    def test_generate_password_mutations(self):
        base = ["password"]
        mutations = generate_password_mutations(base)
        self.assertIn("password", mutations)
        self.assertIn("Password", mutations)
        self.assertIn("PASSWORD", mutations)
        self.assertIn("password1", mutations)
        self.assertGreater(len(mutations), len(base))

    def test_validate_seed_phrase_format(self):
        result = validate_seed_phrase_format(
            ["abandon"] * 12, expected_length=12
        )
        self.assertEqual(result["word_count"], 12)

    def test_validate_seed_phrase_wrong_length(self):
        result = validate_seed_phrase_format(
            ["abandon"] * 11, expected_length=12
        )
        self.assertFalse(result["valid"])


class TestIntegrations(unittest.TestCase):
    """Test integration layer"""

    def test_bitcoin_core_not_available(self):
        from integrations.external_tools import BitcoinCoreIntegration
        btc = BitcoinCoreIntegration(bitcoin_cli_path="/nonexistent/bitcoin-cli")
        self.assertFalse(btc.is_available())

    def test_btcrecover_not_available(self):
        from integrations.external_tools import BTCRecoverIntegration
        btr = BTCRecoverIntegration(btcrecover_path="/nonexistent/btcrecover.py")
        self.assertFalse(btr.is_available())

    def test_seedrecover_not_available(self):
        from integrations.external_tools import SeedRecoverIntegration
        sr = SeedRecoverIntegration(seedrecover_path="/nonexistent/seedrecover.py")
        self.assertFalse(sr.is_available())

    def test_integration_factory(self):
        from integrations.external_tools import IntegrationFactory
        checks = IntegrationFactory.check_all_integrations()
        self.assertIsInstance(checks, dict)
        self.assertIn("bitcoin_core", checks)
        self.assertIn("btcrecover", checks)
        self.assertIn("seedrecover", checks)


if __name__ == "__main__":
    unittest.main()
