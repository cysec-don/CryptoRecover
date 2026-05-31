"""
Wallet Registry - Comprehensive list of all crypto wallets and their login technologies.

This module maintains a registry of all known cryptocurrency wallets,
their seedphrase formats, derivation paths, and authentication methods.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class WalletType(Enum):
    SOFTWARE = "software"
    HARDWARE = "hardware"
    EXCHANGE = "exchange"
    PAPER = "paper"
    BRAIN = "brain"
    MULTISIG = "multisig"
    SMART_CONTRACT = "smart_contract"


class SeedFormat(Enum):
    BIP39 = "bip39"
    SLIP39 = "slip39"       # Shamir Secret Sharing (Trezor)
    ELECTRUM = "electrum"   # Electrum seed format
    MONERO = "monero"       # Monero mnemonic
    AVALANCHE = "avalanche" # Avalanche mnemonic
    CUSTOM = "custom"


class AuthMethod(Enum):
    SEEDPHRASE = "seedphrase"
    PASSPHRASE = "passphrase"
    PASSWORD = "password"
    PIN = "pin"
    BIOMETRIC = "biometric"
    HARDWARE_KEY = "hardware_key"
    TOTP = "totp"            # Time-based One-Time Password
    HOTP = "hotp"            # HMAC-based One-Time Password
    SMS = "sms"              # SMS verification
    EMAIL = "email"          # Email verification
    U2F = "u2f"              # Universal 2nd Factor
    WEBAUTHN = "webauthn"    # Web Authentication
    YUBIKEY = "yubikey"      # YubiKey
    GOOGLE_AUTH = "google_auth"  # Google Authenticator
    AUTHY = "authy"          # Authy
    MULTI_SIG = "multi_sig"  # Multi-signature
    SHAMIR = "shamir"        # Shamir Secret Sharing
    SOCIAL_RECOVERY = "social_recovery"  # Social recovery


@dataclass
class WalletInfo:
    """Information about a cryptocurrency wallet."""
    name: str
    wallet_type: WalletType
    supported_coins: List[str]
    seed_format: SeedFormat
    word_counts: List[int]           # Supported word counts (e.g., [12, 24])
    default_derivation: str          # Default BIP-32/44/49/84 derivation path
    supports_passphrase: bool
    auth_methods: List[AuthMethod]
    notes: str = ""
    website: str = ""


# ============================================================
# Complete Wallet Registry
# ============================================================

WALLET_REGISTRY: Dict[str, WalletInfo] = {
    # === Hardware Wallets ===
    "ledger_nano_s": WalletInfo(
        name="Ledger Nano S",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC", "ETH", "LTC", "DOGE", "XRP", "ADA", "SOL", "DOT", "MATIC", "AVAX", "ALGO", "ATOM", "XTZ", "EOS", "NEO", "TRX", "BNB", "USDT"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE],
        website="https://www.ledger.com",
    ),
    "ledger_nano_x": WalletInfo(
        name="Ledger Nano X",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC", "ETH", "LTC", "DOGE", "XRP", "ADA", "SOL", "DOT", "MATIC", "AVAX", "ALGO", "ATOM", "XTZ", "EOS", "NEO", "TRX", "BNB", "USDT"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE, AuthMethod.BIOMETRIC],
        website="https://www.ledger.com",
    ),
    "ledger_nano_s_plus": WalletInfo(
        name="Ledger Nano S Plus",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC", "ETH", "LTC", "DOGE", "XRP", "ADA", "SOL", "DOT", "MATIC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE],
        website="https://www.ledger.com",
    ),
    "ledger_stax": WalletInfo(
        name="Ledger Stax",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC", "ETH", "LTC", "DOGE", "XRP", "ADA", "SOL", "DOT", "MATIC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE, AuthMethod.BIOMETRIC],
        website="https://www.ledger.com",
    ),
    "trezor_one": WalletInfo(
        name="Trezor One",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC", "ETH", "LTC", "DOGE", "XRP", "ADA", "SOL", "DOT"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 18, 24],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE],
        website="https://trezor.io",
    ),
    "trezor_model_t": WalletInfo(
        name="Trezor Model T",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC", "ETH", "LTC", "DOGE", "XRP", "ADA", "SOL", "DOT", "MATIC", "AVAX"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 18, 24],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE, AuthMethod.SHAMIR],
        notes="Also supports SLIP39 Shamir backup",
        website="https://trezor.io",
    ),
    "trezor_safe_3": WalletInfo(
        name="Trezor Safe 3",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC", "ETH", "LTC", "DOGE", "XRP", "ADA", "SOL", "DOT"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 18, 24],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE, AuthMethod.SHAMIR],
        website="https://trezor.io",
    ),
    "trezor_safe_5": WalletInfo(
        name="Trezor Safe 5",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC", "ETH", "LTC", "DOGE", "XRP", "ADA", "SOL", "DOT"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 18, 24],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE, AuthMethod.SHAMIR, AuthMethod.BIOMETRIC],
        website="https://trezor.io",
    ),
    "coldcard_mk4": WalletInfo(
        name="Coldcard Mk4",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE],
        notes="Bitcoin-only, air-gapped, extremely secure",
        website="https://coldcard.com",
    ),
    "coldcard_q1": WalletInfo(
        name="Coldcard Q1",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE],
        notes="Bitcoin-only, QWERTY keyboard, air-gapped",
        website="https://coldcard.com",
    ),
    "bitbox02": WalletInfo(
        name="BitBox02",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC", "ETH", "LTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 18, 24],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE],
        website="https://bitbox.swiss",
    ),
    "keystone_pro_3": WalletInfo(
        name="Keystone Pro 3",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC", "ETH", "SOL", "MATIC", "BNB"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE, AuthMethod.BIOMETRIC],
        website="https://keyst.one",
    ),
    "seedsigner": WalletInfo(
        name="SeedSigner",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSPHRASE],
        notes="DIY air-gapped Bitcoin hardware wallet",
        website="https://seedsigner.com",
    ),
    "jade": WalletInfo(
        name="Blockstream Jade",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC", "LTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE],
        website="https://blockstream.com/jade",
    ),
    "foundation_passport": WalletInfo(
        name="Foundation Passport",
        wallet_type=WalletType.HARDWARE,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE],
        notes="Bitcoin-only, air-gapped",
        website="https://foundationdevices.com",
    ),

    # === Software Wallets ===
    "metamask": WalletInfo(
        name="MetaMask",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["ETH", "MATIC", "BNB", "AVAX", "ARB", "OP", "BASE", "All EVM chains"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12],
        default_derivation="m/44'/60'/0'/0/0",
        supports_passphrase=False,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD],
        notes="Most popular Ethereum wallet. Uses SRP (Secret Recovery Phrase).",
        website="https://metamask.io",
    ),
    "trust_wallet": WalletInfo(
        name="Trust Wallet",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["BTC", "ETH", "BNB", "SOL", "DOT", "ADA", "AVAX", "MATIC", "XRP", "DOGE", "ATOM", "NEAR", "FTM", "One", "ALGO"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12],
        default_derivation="m/44'/60'/0'/0/0",
        supports_passphrase=False,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.BIOMETRIC],
        website="https://trustwallet.com",
    ),
    "exodus": WalletInfo(
        name="Exodus",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["BTC", "ETH", "LTC", "DOGE", "XRP", "ADA", "SOL", "DOT", "MATIC", "AVAX", "ALGO", "ATOM", "XTZ", "EOS", "NEO", "TRX", "BNB", "USDT", "100+ more"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD, AuthMethod.BIOMETRIC],
        website="https://www.exodus.com",
    ),
    "electrum": WalletInfo(
        name="Electrum",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["BTC"],
        seed_format=SeedFormat.ELECTRUM,
        word_counts=[12],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD],
        notes="Uses Electrum seed format (NOT BIP-39). Can convert to BIP-39.",
        website="https://electrum.org",
    ),
    "bluewallet": WalletInfo(
        name="BlueWallet",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["BTC", "LTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.BIOMETRIC],
        website="https://bluewallet.io",
    ),
    "sparrow": WalletInfo(
        name="Sparrow Wallet",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD],
        notes="Advanced Bitcoin wallet with hardware wallet support",
        website="https://sparrowwallet.com",
    ),
    "muun": WalletInfo(
        name="Muun",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=False,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.BIOMETRIC, AuthMethod.EMAIL],
        notes="Emergency recovery uses 2-of-2 multisig with recovery code",
        website="https://muun.com",
    ),
    "wasabi": WalletInfo(
        name="Wasabi Wallet",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD],
        notes="Privacy-focused Bitcoin wallet with CoinJoin",
        website="https://wasabiwallet.io",
    ),
    "samourai": WalletInfo(
        name="Samourai Wallet",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSPHRASE],
        notes="Privacy-focused. Uses BIP-47 payment codes.",
        website="https://samouraiwallet.com",
    ),
    "phantom": WalletInfo(
        name="Phantom",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["SOL", "USDC", "USDT", "All SPL tokens"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/501'/0'/0'",
        supports_passphrase=False,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD, AuthMethod.BIOMETRIC],
        website="https://phantom.app",
    ),
    "solflare": WalletInfo(
        name="Solflare",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["SOL", "All SPL tokens"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/501'/0'/0'",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD, AuthMethod.BIOMETRIC],
        website="https://solflare.com",
    ),
    "myetherwallet": WalletInfo(
        name="MyEtherWallet (MEW)",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["ETH", "All ERC-20 tokens"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/60'/0'/0/0",
        supports_passphrase=False,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD, AuthMethod.HARDWARE_KEY],
        website="https://www.myetherwallet.com",
    ),
    "rainbow": WalletInfo(
        name="Rainbow",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["ETH", "MATIC", "ARB", "OP", "BASE", "All EVM chains"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12],
        default_derivation="m/44'/60'/0'/0/0",
        supports_passphrase=False,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD, AuthMethod.BIOMETRIC],
        website="https://rainbow.me",
    ),
    "coinbase_wallet": WalletInfo(
        name="Coinbase Wallet",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["BTC", "ETH", "SOL", "MATIC", "AVAX", "All EVM chains"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/60'/0'/0/0",
        supports_passphrase=False,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD, AuthMethod.BIOMETRIC, AuthMethod.GOOGLE_AUTH],
        website="https://www.coinbase.com/wallet",
    ),
    "rabby": WalletInfo(
        name="Rabby Wallet",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["ETH", "All EVM chains"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12],
        default_derivation="m/44'/60'/0'/0/0",
        supports_passphrase=False,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD],
        website="https://rabby.io",
    ),
    "keplr": WalletInfo(
        name="Keplr",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["ATOM", "OSMO", "JUNO", "All Cosmos ecosystem"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/118'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD, AuthMethod.BIOMETRIC],
        website="https://www.keplr.app",
    ),
    "yoroi": WalletInfo(
        name="Yoroi",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["ADA", "All Cardano tokens"],
        seed_format=SeedFormat.BIP39,
        word_counts=[15, 24],
        default_derivation="m/1852'/1815'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD],
        website="https://yoroi-wallet.com",
    ),
    "daedalus": WalletInfo(
        name="Daedalus",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["ADA"],
        seed_format=SeedFormat.BIP39,
        word_counts=[15, 24],
        default_derivation="m/1852'/1815'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD],
        website="https://daedaluswallet.io",
    ),
    "monero_gui": WalletInfo(
        name="Monero GUI Wallet",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["XMR"],
        seed_format=SeedFormat.MONERO,
        word_counts=[25],
        default_derivation="",
        supports_passphrase=False,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD],
        notes="25-word Monero mnemonic, NOT BIP-39",
        website="https://www.getmonero.org",
    ),
    "cake_wallet": WalletInfo(
        name="Cake Wallet",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["XMR", "BTC", "ETH", "LTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 16, 24, 25],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PIN, AuthMethod.PASSWORD, AuthMethod.BIOMETRIC],
        notes="Supports Monero 25-word format and BIP-39",
        website="https://cakewallet.com",
    ),
    "ronin_wallet": WalletInfo(
        name="Ronin Wallet",
        wallet_type=WalletType.SOFTWARE,
        supported_coins=["RON", "AXS", "SLP", "All Ronin tokens"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12],
        default_derivation="m/44'/60'/0'/0/0",
        supports_passphrase=False,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSWORD],
        website="https://wallet.roninchain.com",
    ),

    # === Exchange Wallets ===
    "binance": WalletInfo(
        name="Binance",
        wallet_type=WalletType.EXCHANGE,
        supported_coins=["All major cryptocurrencies"],
        seed_format=SeedFormat.CUSTOM,
        word_counts=[],
        default_derivation="",
        supports_passphrase=False,
        auth_methods=[AuthMethod.PASSWORD, AuthMethod.TOTP, AuthMethod.SMS, AuthMethod.EMAIL, AuthMethod.YUBIKEY, AuthMethod.GOOGLE_AUTH],
        notes="Exchange - no seedphrase. Uses 2FA (TOTP/SMS/Email/YubiKey)",
        website="https://www.binance.com",
    ),
    "coinbase_exchange": WalletInfo(
        name="Coinbase Exchange",
        wallet_type=WalletType.EXCHANGE,
        supported_coins=["All major cryptocurrencies"],
        seed_format=SeedFormat.CUSTOM,
        word_counts=[],
        default_derivation="",
        supports_passphrase=False,
        auth_methods=[AuthMethod.PASSWORD, AuthMethod.TOTP, AuthMethod.SMS, AuthMethod.EMAIL, AuthMethod.WEBAUTHN, AuthMethod.GOOGLE_AUTH],
        notes="Exchange - no seedphrase. Uses 2FA",
        website="https://www.coinbase.com",
    ),
    "kraken": WalletInfo(
        name="Kraken",
        wallet_type=WalletType.EXCHANGE,
        supported_coins=["All major cryptocurrencies"],
        seed_format=SeedFormat.CUSTOM,
        word_counts=[],
        default_derivation="",
        supports_passphrase=False,
        auth_methods=[AuthMethod.PASSWORD, AuthMethod.TOTP, AuthMethod.SMS, AuthMethod.EMAIL, AuthMethod.YUBIKEY, AuthMethod.WEBAUTHN, AuthMethod.GOOGLE_AUTH],
        notes="Exchange - no seedphrase. Uses 2FA",
        website="https://www.kraken.com",
    ),
    "kucoin": WalletInfo(
        name="KuCoin",
        wallet_type=WalletType.EXCHANGE,
        supported_coins=["All major cryptocurrencies"],
        seed_format=SeedFormat.CUSTOM,
        word_counts=[],
        default_derivation="",
        supports_passphrase=False,
        auth_methods=[AuthMethod.PASSWORD, AuthMethod.TOTP, AuthMethod.SMS, AuthMethod.EMAIL, AuthMethod.GOOGLE_AUTH],
        notes="Exchange - no seedphrase. Uses 2FA",
        website="https://www.kucoin.com",
    ),
    "bybit": WalletInfo(
        name="Bybit",
        wallet_type=WalletType.EXCHANGE,
        supported_coins=["All major cryptocurrencies"],
        seed_format=SeedFormat.CUSTOM,
        word_counts=[],
        default_derivation="",
        supports_passphrase=False,
        auth_methods=[AuthMethod.PASSWORD, AuthMethod.TOTP, AuthMethod.SMS, AuthMethod.EMAIL, AuthMethod.GOOGLE_AUTH],
        notes="Exchange - no seedphrase. Uses 2FA",
        website="https://www.bybit.com",
    ),
    "okx": WalletInfo(
        name="OKX",
        wallet_type=WalletType.EXCHANGE,
        supported_coins=["All major cryptocurrencies"],
        seed_format=SeedFormat.CUSTOM,
        word_counts=[],
        default_derivation="",
        supports_passphrase=False,
        auth_methods=[AuthMethod.PASSWORD, AuthMethod.TOTP, AuthMethod.SMS, AuthMethod.EMAIL, AuthMethod.GOOGLE_AUTH],
        website="https://www.okx.com",
    ),
    "gemini": WalletInfo(
        name="Gemini",
        wallet_type=WalletType.EXCHANGE,
        supported_coins=["BTC", "ETH", "All major cryptocurrencies"],
        seed_format=SeedFormat.CUSTOM,
        word_counts=[],
        default_derivation="",
        supports_passphrase=False,
        auth_methods=[AuthMethod.PASSWORD, AuthMethod.TOTP, AuthMethod.SMS, AuthMethod.EMAIL, AuthMethod.WEBAUTHN, AuthMethod.GOOGLE_AUTH],
        website="https://www.gemini.com",
    ),
    "bitget": WalletInfo(
        name="Bitget",
        wallet_type=WalletType.EXCHANGE,
        supported_coins=["All major cryptocurrencies"],
        seed_format=SeedFormat.CUSTOM,
        word_counts=[],
        default_derivation="",
        supports_passphrase=False,
        auth_methods=[AuthMethod.PASSWORD, AuthMethod.TOTP, AuthMethod.SMS, AuthMethod.EMAIL, AuthMethod.GOOGLE_AUTH],
        website="https://www.bitget.com",
    ),
    "gate_io": WalletInfo(
        name="Gate.io",
        wallet_type=WalletType.EXCHANGE,
        supported_coins=["All major cryptocurrencies"],
        seed_format=SeedFormat.CUSTOM,
        word_counts=[],
        default_derivation="",
        supports_passphrase=False,
        auth_methods=[AuthMethod.PASSWORD, AuthMethod.TOTP, AuthMethod.SMS, AuthMethod.EMAIL, AuthMethod.GOOGLE_AUTH],
        website="https://www.gate.io",
    ),
    "huobi": WalletInfo(
        name="HTX (Huobi)",
        wallet_type=WalletType.EXCHANGE,
        supported_coins=["All major cryptocurrencies"],
        seed_format=SeedFormat.CUSTOM,
        word_counts=[],
        default_derivation="",
        supports_passphrase=False,
        auth_methods=[AuthMethod.PASSWORD, AuthMethod.TOTP, AuthMethod.SMS, AuthMethod.EMAIL, AuthMethod.GOOGLE_AUTH],
        website="https://www.htx.com",
    ),

    # === Multisig Wallets ===
    "caravan": WalletInfo(
        name="Caravan",
        wallet_type=WalletType.MULTISIG,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/48'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.MULTI_SIG],
        notes="Multisig Bitcoin wallet",
    ),
    "specter": WalletInfo(
        name="Specter Desktop",
        wallet_type=WalletType.MULTISIG,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.MULTI_SIG, AuthMethod.HARDWARE_KEY],
        notes="Supports multisig with hardware wallets",
        website="https://specter.solutions",
    ),
    "nunchuk": WalletInfo(
        name="Nunchuk",
        wallet_type=WalletType.MULTISIG,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/84'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.MULTI_SIG, AuthMethod.SOCIAL_RECOVERY],
        notes="Quorum-based multisig with social recovery",
        website="https://nunchuk.io",
    ),

    # === Smart Contract Wallets ===
    "safe": WalletInfo(
        name="Safe (Gnosis Safe)",
        wallet_type=WalletType.SMART_CONTRACT,
        supported_coins=["ETH", "All EVM chains"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/60'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.MULTI_SIG, AuthMethod.WEBAUTHN, AuthMethod.SOCIAL_RECOVERY],
        notes="Smart contract multisig wallet",
        website="https://safe.global",
    ),
    "argent": WalletInfo(
        name="Argent",
        wallet_type=WalletType.SMART_CONTRACT,
        supported_coins=["ETH", "All EVM chains"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12],
        default_derivation="m/44'/60'/0'/0/0",
        supports_passphrase=False,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.SOCIAL_RECOVERY, AuthMethod.BIOMETRIC],
        notes="Account abstraction with social recovery",
        website="https://www.argent.xyz",
    ),

    # === Brain Wallets ===
    "brainwallet": WalletInfo(
        name="Brain Wallet",
        wallet_type=WalletType.BRAIN,
        supported_coins=["BTC"],
        seed_format=SeedFormat.BIP39,
        word_counts=[12, 24],
        default_derivation="m/44'/0'/0'/0/0",
        supports_passphrase=True,
        auth_methods=[AuthMethod.SEEDPHRASE, AuthMethod.PASSPHRASE],
        notes="Seedphrase derived from a memorized passphrase. Highly vulnerable to bruteforce.",
    ),
}


def get_all_wallets() -> Dict[str, WalletInfo]:
    """Get the complete wallet registry."""
    return WALLET_REGISTRY


def get_wallets_by_type(wallet_type: WalletType) -> Dict[str, WalletInfo]:
    """Filter wallets by type."""
    return {
        k: v for k, v in WALLET_REGISTRY.items()
        if v.wallet_type == wallet_type
    }


def get_wallets_supporting_coin(coin: str) -> Dict[str, WalletInfo]:
    """Find wallets that support a specific coin."""
    coin = coin.upper()
    return {
        k: v for k, v in WALLET_REGISTRY.items()
        if v.supported_coins and (
            coin in [c.upper() for c in v.supported_coins] or
            any("ALL" in c.upper() for c in v.supported_coins)
        )
    }


def get_wallets_with_auth_method(method: AuthMethod) -> Dict[str, WalletInfo]:
    """Find wallets that use a specific authentication method."""
    return {
        k: v for k, v in WALLET_REGISTRY.items()
        if method in v.auth_methods
    }


def get_all_auth_methods() -> List[Dict[str, str]]:
    """List all authentication methods with descriptions."""
    return [
        {"id": "seedphrase", "name": "Seedphrase/Mnemonic", "description": "BIP-39 or other mnemonic phrase"},
        {"id": "passphrase", "name": "Passphrase/BIP-39 Password", "description": "Additional word/phrase used with seedphrase"},
        {"id": "password", "name": "Password", "description": "Account or wallet password"},
        {"id": "pin", "name": "PIN Code", "description": "Numeric PIN for device access"},
        {"id": "biometric", "name": "Biometric", "description": "Fingerprint, Face ID, or other biometric"},
        {"id": "hardware_key", "name": "Hardware Key", "description": "Physical security key (YubiKey, etc.)"},
        {"id": "totp", "name": "TOTP", "description": "Time-based One-Time Password (Google Auth, Authy)"},
        {"id": "hotp", "name": "HOTP", "description": "HMAC-based One-Time Password"},
        {"id": "sms", "name": "SMS Verification", "description": "SMS-based 2FA code"},
        {"id": "email", "name": "Email Verification", "description": "Email-based 2FA code"},
        {"id": "u2f", "name": "U2F", "description": "Universal 2nd Factor security key"},
        {"id": "webauthn", "name": "WebAuthn", "description": "Web Authentication standard"},
        {"id": "yubikey", "name": "YubiKey", "description": "YubiKey hardware authenticator"},
        {"id": "google_auth", "name": "Google Authenticator", "description": "Google Authenticator TOTP app"},
        {"id": "authy", "name": "Authy", "description": "Authy TOTP app with cloud backup"},
        {"id": "multi_sig", "name": "Multi-Signature", "description": "Multiple signers required for transactions"},
        {"id": "shamir", "name": "Shamir Secret Sharing", "description": "SLIP-39 split seed phrase (Trezor)"},
        {"id": "social_recovery", "name": "Social Recovery", "description": "Trusted contacts can recover access"},
    ]
