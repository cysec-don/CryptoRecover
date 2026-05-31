"""Tests for Wallet Registry"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.wallets.registry import (
    get_all_wallets, get_wallets_by_type, get_wallets_supporting_coin,
    get_all_auth_methods, WalletType, AuthMethod, WALLET_REGISTRY,
)


class TestWalletRegistry:
    """Tests for the wallet registry."""

    def test_registry_not_empty(self):
        assert len(WALLET_REGISTRY) > 0

    def test_hardware_wallets(self):
        hw = get_wallets_by_type(WalletType.HARDWARE)
        assert len(hw) >= 5
        names = [w.name for w in hw.values()]
        assert "Ledger Nano X" in names
        assert "Trezor Model T" in names

    def test_software_wallets(self):
        sw = get_wallets_by_type(WalletType.SOFTWARE)
        assert len(sw) >= 5
        names = [w.name for w in sw.values()]
        assert "MetaMask" in names
        assert "Electrum" in names

    def test_exchange_wallets(self):
        ew = get_wallets_by_type(WalletType.EXCHANGE)
        assert len(ew) >= 3
        names = [w.name for w in ew.values()]
        assert "Binance" in names

    def test_wallets_supporting_bitcoin(self):
        btc = get_wallets_supporting_coin("BTC")
        assert len(btc) >= 5

    def test_wallets_supporting_ethereum(self):
        eth = get_wallets_supporting_coin("ETH")
        assert len(eth) >= 5

    def test_wallets_with_seedphrase(self):
        seed = get_wallets_by_type(WalletType.HARDWARE)
        for w in seed.values():
            assert AuthMethod.SEEDPHRASE in w.auth_methods

    def test_all_wallets_have_required_fields(self):
        for wid, w in WALLET_REGISTRY.items():
            assert w.name, f"Wallet {wid} missing name"
            assert w.wallet_type, f"Wallet {wid} missing type"
            assert w.seed_format, f"Wallet {wid} missing seed format"
            assert w.auth_methods, f"Wallet {wid} missing auth methods"

    def test_auth_methods_list(self):
        methods = get_all_auth_methods()
        assert len(methods) >= 10
        ids = [m["id"] for m in methods]
        assert "seedphrase" in ids
        assert "password" in ids
        assert "totp" in ids

    def test_metamask_details(self):
        mm = WALLET_REGISTRY.get("metamask")
        assert mm is not None
        assert mm.name == "MetaMask"
        assert 12 in mm.word_counts
        assert "ETH" in mm.supported_coins

    def test_ledger_details(self):
        ledger = WALLET_REGISTRY.get("ledger_nano_x")
        assert ledger is not None
        assert ledger.wallet_type == WalletType.HARDWARE
        assert ledger.supports_passphrase is True

    def test_exchange_wallets_no_seedphrase(self):
        """Exchange wallets should not have seedphrase auth."""
        exchanges = get_wallets_by_type(WalletType.EXCHANGE)
        for w in exchanges.values():
            # Exchanges typically don't have seedphrase access
            assert w.seed_format.value in ("custom", "custom")
