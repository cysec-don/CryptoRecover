"""
Comprehensive Crypto Wallet Database
=====================================
All known wallets, their seed phrase formats, passphrase support,
login technologies, and recovery methods.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict


class SeedType(Enum):
    BIP39 = "BIP39"
    ELECTRUM = "Electrum"
    SLIP39 = "SLIP39"  # Shamir Backup
    MONERO = "Monero"
    CUSTOM = "Custom"


class LoginTech(Enum):
    SEED_PHRASE = "Seed Phrase"
    PASSPHRASE = "Passphrase (BIP39)"
    PASSWORD = "Password"
    PIN = "PIN"
    BIOMETRIC = "Biometric"
    HARDWARE_KEY = "Hardware Key"
    TWO_FA = "2FA (TOTP)"
    MULTI_SIG = "Multi-Sig"
    HMAC = "HMAC"
    SECURE_ELEMENT = "Secure Element"
    SHARED_SECRET = "Shared Secret"
    KYC = "KYC Verification"
    EMAIL_RECOVERY = "Email Recovery"
    SOCIAL_RECOVERY = "Social Recovery"
    MFA = "MFA (Multi-Factor Auth)"
    CLOUD_BACKUP = "Cloud Backup"


class WalletCategory(Enum):
    HARDWARE = "Hardware"
    SOFTWARE_DESKTOP = "Software (Desktop)"
    SOFTWARE_MOBILE = "Software (Mobile)"
    SOFTWARE_WEB = "Software (Web)"
    SOFTWARE_EXTENSION = "Software (Browser Extension)"
    PAPER = "Paper"
    CUSTODIAL = "Custodial"
    NON_CUSTODIAL = "Non-Custodial"
    MULTI_CHAIN = "Multi-Chain"
    SINGLE_CHAIN = "Single-Chain"


@dataclass
class WalletInfo:
    name: str
    category: List[WalletCategory]
    supported_seed_types: List[SeedType]
    seed_lengths: List[int]  # 12, 15, 18, 21, 24 words
    supports_passphrase: bool
    login_technologies: List[LoginTech]
    derivation_paths: List[str]
    supported_coins: List[str]
    recovery_difficulty: str  # Easy, Medium, Hard, Very Hard
    notes: str
    wallet_file_format: Optional[str] = None
    encryption_method: Optional[str] = None
    api_endpoint: Optional[str] = None


# ==============================================================================
# COMPREHENSIVE WALLET DATABASE
# ==============================================================================

WALLETS: Dict[str, WalletInfo] = {
    # ─── HARDWARE WALLETS ──────────────────────────────────────────────────
    "Ledger Nano S": WalletInfo(
        name="Ledger Nano S",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.SECURE_ELEMENT, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/44'/60'/0'"],
        supported_coins=["BTC", "ETH", "LTC", "XRP", "ADA", "DOT", "SOL", "BNB", "MATIC", "1000+"],
        recovery_difficulty="Medium",
        notes="BIP39 seed stored on secure element. PIN protects device access. Passphrase acts as 25th word. Recovery via seed phrase only.",
        wallet_file_format=None,
        encryption_method="Secure Element (ST33)"
    ),
    "Ledger Nano X": WalletInfo(
        name="Ledger Nano X",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.SECURE_ELEMENT, LoginTech.BIOMETRIC, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/44'/60'/0'"],
        supported_coins=["BTC", "ETH", "LTC", "XRP", "ADA", "DOT", "SOL", "BNB", "MATIC", "1000+"],
        recovery_difficulty="Medium",
        notes="Bluetooth enabled. Same recovery as Nano S. Biometric via Ledger Live mobile.",
        wallet_file_format=None,
        encryption_method="Secure Element (ST33) + Bluetooth"
    ),
    "Ledger Nano S Plus": WalletInfo(
        name="Ledger Nano S Plus",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.SECURE_ELEMENT, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/44'/60'/0'"],
        supported_coins=["BTC", "ETH", "LTC", "XRP", "ADA", "DOT", "SOL", "BNB", "MATIC", "1000+"],
        recovery_difficulty="Medium",
        notes="Larger screen than Nano S. Same recovery procedure.",
        wallet_file_format=None,
        encryption_method="Secure Element (ST33)"
    ),
    "Trezor Model One": WalletInfo(
        name="Trezor Model One",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 18, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/44'/60'/0'"],
        supported_coins=["BTC", "ETH", "LTC", "XRP", "ADA", "DOT", "SOL", "BNB", "1000+"],
        recovery_difficulty="Medium",
        notes="No secure element. Seed displayed on host computer during recovery. Passphrase entered on host.",
        wallet_file_format=None,
        encryption_method="PIN + Passphrase"
    ),
    "Trezor Model T": WalletInfo(
        name="Trezor Model T",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39, SeedType.SLIP39],
        seed_lengths=[12, 18, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE, LoginTech.MULTI_SIG],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/44'/60'/0'"],
        supported_coins=["BTC", "ETH", "LTC", "XRP", "ADA", "DOT", "SOL", "BNB", "1000+"],
        recovery_difficulty="Medium",
        notes="Touchscreen. Supports SLIP39 Shamir backup. Passphrase entered on device touchscreen.",
        wallet_file_format=None,
        encryption_method="PIN + Passphrase + SLIP39"
    ),
    "Trezor Safe 3": WalletInfo(
        name="Trezor Safe 3",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39, SeedType.SLIP39],
        seed_lengths=[12, 20, 24, 33],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE, LoginTech.SECURE_ELEMENT, LoginTech.MULTI_SIG],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/44'/60'/0'"],
        supported_coins=["BTC", "ETH", "LTC", "XRP", "ADA", "DOT", "SOL", "BNB", "1000+"],
        recovery_difficulty="Medium",
        notes="Secure element (Optiga). Supports both BIP39 and SLIP39. 20-word and 33-word SLIP39 seeds.",
        wallet_file_format=None,
        encryption_method="Secure Element + PIN + Passphrase"
    ),
    "KeepKey": WalletInfo(
        name="KeepKey",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 18, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/44'/60'/0'"],
        supported_coins=["BTC", "ETH", "LTC", "DOGE", "DASH", "BTC forks"],
        recovery_difficulty="Medium",
        notes="Large display. Acquired by ShapeShift. Standard BIP39 recovery.",
        wallet_file_format=None,
        encryption_method="PIN + Passphrase"
    ),
    "Coldcard Mk4": WalletInfo(
        name="Coldcard Mk4",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE, LoginTech.SECURE_ELEMENT, LoginTech.MULTI_SIG],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/48'/0'/0'/2'"],
        supported_coins=["BTC"],
        recovery_difficulty="Medium",
        notes="Bitcoin-only. Dual secure elements. Air-gapped via SD card. Supports duress PIN and sub-accounts.",
        wallet_file_format=None,
        encryption_method="Dual Secure Element + PIN"
    ),
    "BitBox02": WalletInfo(
        name="BitBox02",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 18, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE, LoginTech.SECURE_ELEMENT, LoginTech.MFA],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/44'/60'/0'"],
        supported_coins=["BTC", "ETH", "LTC", "BNB", "MATIC", "ERC-20 tokens"],
        recovery_difficulty="Medium",
        notes="Swiss-made. Secure chip. Supports both Multi and Bitcoin-only editions.",
        wallet_file_format=None,
        encryption_method="Secure Chip + PIN + Passphrase"
    ),
    "SeedSigner": WalletInfo(
        name="SeedSigner",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSPHRASE, LoginTech.MULTI_SIG],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/48'/0'/0'/2'"],
        supported_coins=["BTC"],
        recovery_difficulty="Easy",
        notes="DIY hardware wallet. Air-gapped. QR code based. No persistent storage of seed. Camera reads seed from QR.",
        wallet_file_format=None,
        encryption_method="None (stateless)"
    ),
    "Jade": WalletInfo(
        name="Blockstream Jade",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/48'/0'/0'/2'"],
        supported_coins=["BTC", "Liquid BTC"],
        recovery_difficulty="Medium",
        notes="Camera for QR air-gapped signing. Supports blind oracle for PIN unlock.",
        wallet_file_format=None,
        encryption_method="PIN + Passphrase + Blind Oracle"
    ),
    "NGRAVE ZERO": WalletInfo(
        name="NGRAVE ZERO",
        category=[WalletCategory.HARDWARE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 15, 18, 21, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE, LoginTech.SECURE_ELEMENT, LoginTech.BIOMETRIC],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/44'/60'/0'"],
        supported_coins=["BTC", "ETH", "1000+"],
        recovery_difficulty="Medium",
        notes="EAL5+ certified secure element. Printer for paper backup. Perfect key generation.",
        wallet_file_format=None,
        encryption_method="EAL5+ Secure Element + PIN"
    ),

    # ─── DESKTOP SOFTWARE WALLETS ──────────────────────────────────────────
    "Electrum": WalletInfo(
        name="Electrum",
        category=[WalletCategory.SOFTWARE_DESKTOP, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39, SeedType.ELECTRUM],
        seed_lengths=[12, 13, 24, 25],  # Electrum seeds are 12 or 13 words; BIP39 12/24
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.PASSPHRASE, LoginTech.MULTI_SIG, LoginTech.TWO_FA],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/48'/0'/0'/2'"],
        supported_coins=["BTC"],
        recovery_difficulty="Easy",
        notes="Electrum uses its own seed format (not BIP39 by default). Supports 2FA with trustedcoin. Wallet file encrypted with password. seedrecover.py can recover Electrum seeds.",
        wallet_file_format=".electrum/wallets/*",
        encryption_method="AES-256-CBC (wallet file) + Password"
    ),
    "Bitcoin Core": WalletInfo(
        name="Bitcoin Core",
        category=[WalletCategory.SOFTWARE_DESKTOP, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.PASSWORD, LoginTech.SEED_PHRASE],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'"],
        supported_coins=["BTC"],
        recovery_difficulty="Hard",
        notes="Full node. wallet.dat file encrypted with password. hd seedphrase since v0.18. btcrecover.py can brute-force wallet.dat passwords. Dump wallet for seed phrase.",
        wallet_file_format="wallet.dat",
        encryption_method="AES-256-CBC (wallet.dat) + Password"
    ),
    "Exodus": WalletInfo(
        name="Exodus",
        category=[WalletCategory.SOFTWARE_DESKTOP, WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.EMAIL_RECOVERY],
        derivation_paths=["m/44'/0'/0'", "m/44'/60'/0'", "m/44'/3'/0'", "m/44'/133'/0'"],
        supported_coins=["BTC", "ETH", "LTC", "SOL", "ADA", "DOT", "BNB", "MATIC", "200+"],
        recovery_difficulty="Easy",
        notes="12-word BIP39 seed. Password-protected wallet file. Email recovery option. No passphrase support.",
        wallet_file_format="exodus.wallet",
        encryption_method="AES-256 + Password"
    ),
    "Wasabi Wallet": WalletInfo(
        name="Wasabi Wallet",
        category=[WalletCategory.SOFTWARE_DESKTOP, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.PASSPHRASE],
        derivation_paths=["m/84'/0'/0'"],
        supported_coins=["BTC"],
        recovery_difficulty="Easy",
        notes="Privacy-focused. CoinJoin. BIP39 12-word seed with optional passphrase. Password for wallet file.",
        wallet_file_format="Main.json",
        encryption_method="AES-256 + Password + BIP39"
    ),
    "Samourai Wallet": WalletInfo(
        name="Samourai Wallet",
        category=[WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE],
        derivation_paths=["m/84'/0'/0'", "m/49'/0'/0'", "m/44'/0'/0'"],
        supported_coins=["BTC"],
        recovery_difficulty="Medium",
        notes="Privacy-focused. BIP39 + passphrase. PIN for app access. Ricochet, Stonewall features. Uses DER format for backup.",
        wallet_file_format="samourai.backup",
        encryption_method="AES-256 + PIN + BIP39 Passphrase"
    ),
    "Sparrow Wallet": WalletInfo(
        name="Sparrow Wallet",
        category=[WalletCategory.SOFTWARE_DESKTOP, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39, SeedType.ELECTRUM, SeedType.SLIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.PASSPHRASE, LoginTech.HARDWARE_KEY, LoginTech.MULTI_SIG],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/48'/0'/0'/2'"],
        supported_coins=["BTC"],
        recovery_difficulty="Easy",
        notes="Modern Bitcoin wallet. Connects to Electrum server or Bitcoin Core. Supports hardware wallet integration. BIP39/SLIP39/Electrum seeds.",
        wallet_file_format=".sparrow/*.wallet",
        encryption_method="AES-256 + Password"
    ),

    # ─── BROWSER EXTENSION WALLETS ─────────────────────────────────────────
    "MetaMask": WalletInfo(
        name="MetaMask",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/60'/0'/0"],
        supported_coins=["ETH", "ERC-20", "BSC", "Polygon", "Arbitrum", "Optimism", "EVM chains"],
        recovery_difficulty="Easy",
        notes="12-word BIP39 seed. Password protects vault (browser extension). Vault data stored in browser localStorage. btcrecover.py can brute-force vault password.",
        wallet_file_format="metamask_vault.json",
        encryption_method="AES-128-CTR + Password-derived Key (PBKDF2)"
    ),
    "Phantom": WalletInfo(
        name="Phantom",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/501'/0'/0'", "m/44'/60'/0'/0"],
        supported_coins=["SOL", "ETH", "MATIC", "SPL tokens"],
        recovery_difficulty="Easy",
        notes="Primary Solana wallet. BIP39 seed. Password for browser extension. Supports passphrase as hidden seed.",
        wallet_file_format="phantom_vault.json",
        encryption_method="AES-256-GCM + Password"
    ),
    "Trust Wallet": WalletInfo(
        name="Trust Wallet",
        category=[WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE, LoginTech.BIOMETRIC],
        derivation_paths=["m/44'/0'/0'", "m/44'/60'/0'", "m/44'/501'/0'", "m/44'/3'/0'"],
        supported_coins=["BTC", "ETH", "BNB", "SOL", "ADA", "DOT", "60+ blockchains"],
        recovery_difficulty="Easy",
        notes="12-word BIP39. PIN/biometric for app access. Passphrase supported. Binance-backed.",
        wallet_file_format="trust_wallet_backup.dat",
        encryption_method="AES-256 + PIN/Password"
    ),
    "Coinbase Wallet": WalletInfo(
        name="Coinbase Wallet",
        category=[WalletCategory.SOFTWARE_MOBILE, WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.BIOMETRIC, LoginTech.CLOUD_BACKUP],
        derivation_paths=["m/44'/60'/0'/0"],
        supported_coins=["ETH", "BTC", "SOL", "ERC-20", "1000+"],
        recovery_difficulty="Easy",
        notes="Separate from Coinbase exchange. 12-word seed. iCloud/Google Drive backup option. Not passphrase-aware.",
        wallet_file_format=None,
        encryption_method="Cloud KMS + Password"
    ),
    "Keplr": WalletInfo(
        name="Keplr",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/118'/0'/0", "m/44'/564'/0'/0"],
        supported_coins=["ATOM", "OSMO", "JUNO", "Cosmos ecosystem"],
        recovery_difficulty="Easy",
        notes="Cosmos ecosystem wallet. BIP39 12/24 words. Password for extension lock.",
        wallet_file_format="keplr_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "XDEFI": WalletInfo(
        name="XDEFI Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/60'/0'/0", "m/44'/501'/0'/0'", "m/44'/118'/0'/0"],
        supported_coins=["BTC", "ETH", "SOL", "ATOM", "THORChain", "Multi-chain"],
        recovery_difficulty="Easy",
        notes="Multi-chain. BIP39 seed. Password for extension. Supports Ledger integration.",
        wallet_file_format="xdefi_vault.json",
        encryption_method="AES-256 + Password"
    ),

    # ─── MOBILE WALLETS ────────────────────────────────────────────────────
    "BlueWallet": WalletInfo(
        name="BlueWallet",
        category=[WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE, LoginTech.BIOMETRIC, LoginTech.MULTI_SIG],
        derivation_paths=["m/44'/0'/0'", "m/84'/0'/0'", "m/49'/0'/0'", "m/48'/0'/0'/2'"],
        supported_coins=["BTC", "Lightning BTC"],
        recovery_difficulty="Easy",
        notes="Bitcoin & Lightning. BIP39 + passphrase. Supports watch-only, vault (multisig). Lightning is custodial via LNDhub.",
        wallet_file_format="bluewallet_backup.json",
        encryption_method="AES-256 + PIN/Password"
    ),
    "Mycelium": WalletInfo(
        name="Mycelium",
        category=[WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/0'/0'", "m/49'/0'/0'"],
        supported_coins=["BTC"],
        recovery_difficulty="Medium",
        notes="One of the oldest Bitcoin mobile wallets. BIP39 + passphrase. Encrypted backup to SD card or cloud.",
        wallet_file_format="mycelium_backup.dat",
        encryption_method="AES-256 + PIN + BIP39"
    ),
    "BRD (Bread)": WalletInfo(
        name="BRD (Bread Wallet)",
        category=[WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN],
        derivation_paths=["m/44'/0'/0'", "m/44'/60'/0'"],
        supported_coins=["BTC", "ETH", "BCH"],
        recovery_difficulty="Easy",
        notes="Simple 12-word BIP39. No passphrase. Acquired by Coinbase.",
        wallet_file_format="bread_backup.dat",
        encryption_method="AES-256 + PIN"
    ),
    "Edge": WalletInfo(
        name="Edge",
        category=[WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.PIN, LoginTech.PASSPHRASE, LoginTech.MFA],
        derivation_paths=["m/44'/0'/0'", "m/44'/60'/0'", "m/44'/3'/0'"],
        supported_coins=["BTC", "ETH", "LTC", "XRP", "BCH", "DASH", "40+"],
        recovery_difficulty="Easy",
        notes="Username/password based login with 2FA. BIP39 seed for recovery. PIN for quick access. Supports passphrase.",
        wallet_file_format="edge_backup.json",
        encryption_method="AES-256 + Password + MFA"
    ),

    # ─── WEB / CUSTODIAL WALLETS ───────────────────────────────────────────
    "Binance": WalletInfo(
        name="Binance Exchange",
        category=[WalletCategory.CUSTODIAL, WalletCategory.SOFTWARE_WEB, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[],
        seed_lengths=[],
        supports_passphrase=False,
        login_technologies=[LoginTech.PASSWORD, LoginTech.TWO_FA, LoginTech.EMAIL_RECOVERY, LoginTech.MFA, LoginTech.BIOMETRIC, LoginTech.HARDWARE_KEY],
        derivation_paths=[],
        supported_coins=["BTC", "ETH", "BNB", "SOL", "500+"],
        recovery_difficulty="Very Hard",
        notes="Custodial exchange. No seed phrase. 2FA (TOTP/SMS), email verification, anti-phishing codes. Account recovery via KYC only.",
        wallet_file_format=None,
        encryption_method="Server-side + MFA"
    ),
    "Coinbase Exchange": WalletInfo(
        name="Coinbase Exchange",
        category=[WalletCategory.CUSTODIAL, WalletCategory.SOFTWARE_WEB, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[],
        seed_lengths=[],
        supports_passphrase=False,
        login_technologies=[LoginTech.PASSWORD, LoginTech.TWO_FA, LoginTech.EMAIL_RECOVERY, LoginTech.MFA, LoginTech.BIOMETRIC, LoginTech.SECURE_ELEMENT],
        derivation_paths=[],
        supported_coins=["BTC", "ETH", "SOL", "200+"],
        recovery_difficulty="Very Hard",
        notes="Custodial. No seed phrase. 2FA (TOTP/SMS), Coinbase Vault for extra security. Recovery via KYC/support.",
        wallet_file_format=None,
        encryption_method="Server-side + MFA + Vault"
    ),
    "Kraken": WalletInfo(
        name="Kraken Exchange",
        category=[WalletCategory.CUSTODIAL, WalletCategory.SOFTWARE_WEB, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[],
        seed_lengths=[],
        supports_passphrase=False,
        login_technologies=[LoginTech.PASSWORD, LoginTech.TWO_FA, LoginTech.EMAIL_RECOVERY, LoginTech.MFA, LoginTech.HARDWARE_KEY],
        derivation_paths=[],
        supported_coins=["BTC", "ETH", "DOT", "200+"],
        recovery_difficulty="Very Hard",
        notes="Custodial. Supports YubiKey hardware 2FA. No seed. Recovery via KYC/support.",
        wallet_file_format=None,
        encryption_method="Server-side + MFA + YubiKey"
    ),

    # ─── MULTI-CHAIN DESKTOP WALLETS ───────────────────────────────────────
    "Atomic Wallet": WalletInfo(
        name="Atomic Wallet",
        category=[WalletCategory.SOFTWARE_DESKTOP, WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/0'/0'", "m/44'/60'/0'", "m/44'/3'/0'", "m/44'/133'/0'"],
        supported_coins=["BTC", "ETH", "LTC", "XRP", "ADA", "300+"],
        recovery_difficulty="Easy",
        notes="12-word BIP39 seed. Password for app. No passphrase. Decentralized order book (Atomic Swaps).",
        wallet_file_format="atomic_wallet.dat",
        encryption_method="AES-256 + Password + BIP39"
    ),
    "Guarda": WalletInfo(
        name="Guarda Wallet",
        category=[WalletCategory.SOFTWARE_DESKTOP, WalletCategory.SOFTWARE_MOBILE, WalletCategory.SOFTWARE_WEB, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.EMAIL_RECOVERY],
        derivation_paths=["m/44'/0'/0'", "m/44'/60'/0'", "m/44'/501'/0'"],
        supported_coins=["BTC", "ETH", "SOL", "50+ blockchains"],
        recovery_difficulty="Easy",
        notes="Multi-platform. BIP39 seed. No passphrase. Encrypted backup via email.",
        wallet_file_format="guarda_backup.dat",
        encryption_method="AES-256 + Password"
    ),

    # ─── SPECIALIZED WALLETS ───────────────────────────────────────────────
    "Monero GUI": WalletInfo(
        name="Monero GUI Wallet",
        category=[WalletCategory.SOFTWARE_DESKTOP, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.MONERO],
        seed_lengths=[25],  # Monero uses 25-word seeds
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["Custom Monero derivation"],
        supported_coins=["XMR"],
        recovery_difficulty="Hard",
        notes="Monero 25-word seed (NOT BIP39). Polyseed (16 words) also supported. Keys file encrypted with password. Unique cryptography.",
        wallet_file_format="monero_wallet.keys",
        encryption_method="Chacha20 + Password"
    ),
    "Cake Wallet": WalletInfo(
        name="Cake Wallet",
        category=[WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.MONERO, SeedType.BIP39],
        seed_lengths=[16, 25],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.PASSWORD],
        derivation_paths=["Custom Monero", "m/44'/60'/0'"],
        supported_coins=["XMR", "BTC", "ETH", "LTC"],
        recovery_difficulty="Medium",
        notes="Monero-focused. Supports Monero 25-word and Polyseed 16-word. Also BIP39 for non-XMR coins. PIN for app.",
        wallet_file_format="cake_wallet_backup.json",
        encryption_method="AES-256 + PIN/Password"
    ),
    "MyMonero": WalletInfo(
        name="MyMonero",
        category=[WalletCategory.SOFTWARE_WEB, WalletCategory.SOFTWARE_DESKTOP, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.MONERO],
        seed_lengths=[25],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["Custom Monero"],
        supported_coins=["XMR"],
        recovery_difficulty="Hard",
        notes="Monero light wallet. 25-word mnemonic. Login keys derived from seed. Web and desktop versions.",
        wallet_file_format=None,
        encryption_method="Server-assisted + Password"
    ),
    "Ronin Wallet": WalletInfo(
        name="Ronin Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/60'/0'/0", "m/44'/1000'/0'/0"],
        supported_coins=["RON", "AXS", "SLP", "ERC-20 on Ronin"],
        recovery_difficulty="Easy",
        notes="Axie Infinity / Sky Mavis wallet. BIP39 12 words. Password for extension. Custom chain derivation.",
        wallet_file_format="ronin_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Kaikas": WalletInfo(
        name="Kaikas",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/8217'/0'/0"],
        supported_coins=["KLAY", "KIP-7", "KIP-17"],
        recovery_difficulty="Easy",
        notes="Klaytn wallet. BIP39 12 words. Password for extension. Klaytn-specific derivation path.",
        wallet_file_format="kaikas_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Martian Wallet": WalletInfo(
        name="Martian Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/637'/0'/0"],
        supported_coins=["APT", "Aptos tokens"],
        recovery_difficulty="Easy",
        notes="Aptos wallet. BIP39 12 words. Password for extension. Aptos-specific derivation.",
        wallet_file_format="martian_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Petra Wallet": WalletInfo(
        name="Petra Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/637'/0'/0"],
        supported_coins=["APT", "Aptos tokens"],
        recovery_difficulty="Easy",
        notes="Aptos wallet by Aptos Labs. BIP39 12 words. Password for extension.",
        wallet_file_format="petra_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Fuel Wallet": WalletInfo(
        name="Fuel Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/60'/0'/0"],
        supported_coins=["ETH on Fuel", "Fuel tokens"],
        recovery_difficulty="Easy",
        notes="Fuel layer 2 wallet. BIP39 seed. EVM-compatible derivation.",
        wallet_file_format="fuel_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Sui Wallet": WalletInfo(
        name="Sui Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/784'/0'/0"],
        supported_coins=["SUI", "Sui tokens"],
        recovery_difficulty="Easy",
        notes="Sui blockchain wallet. BIP39 12 words. Custom derivation path.",
        wallet_file_format="sui_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Solflare": WalletInfo(
        name="Solflare",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/501'/0'/0'", "m/44'/501'/0'/1'"],
        supported_coins=["SOL", "SPL tokens"],
        recovery_difficulty="Easy",
        notes="Solana wallet. BIP39 + passphrase. Password for extension. Supports Ledger.",
        wallet_file_format="solflare_vault.json",
        encryption_method="AES-256 + Password + BIP39"
    ),
    "Stargazer": WalletInfo(
        name="Stargazer Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/1137'/0'/0"],
        supported_coins=["DAG", "Constellation tokens"],
        recovery_difficulty="Easy",
        notes="Constellation Network wallet. BIP39 seed. Custom derivation path.",
        wallet_file_format="stargazer_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Gnosis Safe": WalletInfo(
        name="Gnosis Safe (now Safe)",
        category=[WalletCategory.SOFTWARE_WEB, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.MULTI_SIG, LoginTech.HARDWARE_KEY, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/60'/0'/0"],
        supported_coins=["ETH", "ERC-20", "Multi-chain"],
        recovery_difficulty="Hard",
        notes="Multi-sig smart contract wallet. Recovery via owner keys (M-of-N). Social recovery options. Hardware wallet compatible.",
        wallet_file_format=None,
        encryption_method="Smart Contract + Multi-sig"
    ),
    "Argent": WalletInfo(
        name="Argent",
        category=[WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.SOCIAL_RECOVERY, LoginTech.BIOMETRIC, LoginTech.EMAIL_RECOVERY],
        derivation_paths=["m/44'/60'/0'/0"],
        supported_coins=["ETH", "ERC-20", "StarkNet"],
        recovery_difficulty="Medium",
        notes="Smart contract wallet with social recovery. Guardians can help recover. No seed phrase needed for normal use. zk-rollup focused.",
        wallet_file_format=None,
        encryption_method="Smart Contract + Social Recovery"
    ),
    "Rainbow": WalletInfo(
        name="Rainbow",
        category=[WalletCategory.SOFTWARE_MOBILE, WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.BIOMETRIC],
        derivation_paths=["m/44'/60'/0'/0"],
        supported_coins=["ETH", "ERC-20", "NFTs", "EVM chains"],
        recovery_difficulty="Easy",
        notes="Ethereum-focused. 12-word BIP39. Password/biometric for app access. NFT display. ENS support.",
        wallet_file_format="rainbow_vault.json",
        encryption_method="AES-256 + Password/Biometric"
    ),
    "Unisat": WalletInfo(
        name="UniSat Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/86'/0'/0'", "m/44'/0'/0'"],
        supported_coins=["BTC", "BRC-20", "Ordinals"],
        recovery_difficulty="Easy",
        notes="Bitcoin Ordinals / BRC-20 wallet. BIP39 12 words. Taproot derivation path.",
        wallet_file_format="unisat_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Xverse": WalletInfo(
        name="Xverse",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/86'/0'/0'", "m/84'/0'/0'"],
        supported_coins=["BTC", "Ordinals", "BRC-20", "SIP-10"],
        recovery_difficulty="Easy",
        notes="Bitcoin Web3 wallet. Ordinals and BRC-20 support. BIP39 seed.",
        wallet_file_format="xverse_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Leap Wallet": WalletInfo(
        name="Leap Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/118'/0'/0", "m/44'/60'/0'/0"],
        supported_coins=["ATOM", "OSMO", "INJ", "Cosmos + EVM"],
        recovery_difficulty="Easy",
        notes="Cosmos and EVM wallet. BIP39 seed. Multi-chain support.",
        wallet_file_format="leap_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Rabby": WalletInfo(
        name="Rabby Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.HARDWARE_KEY, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/60'/0'/0"],
        supported_coins=["ETH", "EVM chains", "Multi-chain"],
        recovery_difficulty="Easy",
        notes="By DeBank. Multi-chain EVM. Supports hardware wallets. BIP39 + passphrase. Transaction simulation.",
        wallet_file_format="rabby_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Core Wallet": WalletInfo(
        name="Core Wallet (Avalanche)",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.SOFTWARE_DESKTOP, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.HARDWARE_KEY],
        derivation_paths=["m/44'/60'/0'/0", "m/44'/9000'/0'/0"],
        supported_coins=["AVAX", "C-Chain", "X-Chain", "P-Chain"],
        recovery_difficulty="Easy",
        notes="Avalanche wallet by Ava Labs. BIP39 seed. Hardware wallet support. Non-custodial.",
        wallet_file_format="core_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Yoroi": WalletInfo(
        name="Yoroi Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[15],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/1815'/0'/0"],
        supported_coins=["ADA", "Native tokens"],
        recovery_difficulty="Medium",
        notes="Cardano light wallet by Emurgo. 15-word mnemonic. Password for extension. By Emurgo.",
        wallet_file_format="yoroi_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Eternl": WalletInfo(
        name="Eternl Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[15, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/1815'/0'/0", "m/1852'/1815'/0'"],
        supported_coins=["ADA", "Native tokens", "NFTs"],
        recovery_difficulty="Medium",
        notes="Cardano wallet. 15 or 24 words. Advanced features. Multi-address tracking.",
        wallet_file_format="eternl_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Nami": WalletInfo(
        name="Nami Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[15, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/1815'/0'/0", "m/1852'/1815'/0'"],
        supported_coins=["ADA", "Native tokens", "NFTs"],
        recovery_difficulty="Medium",
        notes="Cardano wallet. Acquired by IOG. 15 or 24 words.",
        wallet_file_format="nami_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "NuFi": WalletInfo(
        name="NuFi Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 15, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/60'/0'/0", "m/44'/1815'/0'/0", "m/44'/501'/0'/0'"],
        supported_coins=["ADA", "ETH", "SOL", "FLOW"],
        recovery_difficulty="Easy",
        notes="Multi-chain extension wallet. Supports Cardano, EVM, Solana, Flow.",
        wallet_file_format="nufi_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "HashPack": WalletInfo(
        name="HashPack Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["Custom Hedera"],
        supported_coins=["HBAR", "HTS tokens"],
        recovery_difficulty="Medium",
        notes="Hedera wallet. 24-word phrase. Password for extension.",
        wallet_file_format="hashpack_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "MyAlgo": WalletInfo(
        name="MyAlgo Wallet",
        category=[WalletCategory.SOFTWARE_WEB, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[25],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/283'/0'/0"],
        supported_coins=["ALGO", "ASA tokens"],
        recovery_difficulty="Medium",
        notes="Algorand wallet. 25-word mnemonic. Note: suffered keylogger attack in 2023.",
        wallet_file_format=None,
        encryption_method="AES-256 + Password"
    ),
    "Pera": WalletInfo(
        name="Pera Wallet",
        category=[WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[25],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PIN, LoginTech.BIOMETRIC],
        derivation_paths=["m/44'/283'/0'/0"],
        supported_coins=["ALGO", "ASA tokens"],
        recovery_difficulty="Easy",
        notes="Algorand mobile wallet. Formerly Algorand Wallet. 25-word mnemonic. PIN/biometric access.",
        wallet_file_format="pera_backup.dat",
        encryption_method="AES-256 + PIN/Biometric"
    ),
    "Temple Wallet": WalletInfo(
        name="Temple Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 15, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/1729'/0'/0'"],
        supported_coins=["XTZ", "FA2 tokens"],
        recovery_difficulty="Easy",
        notes="Tezos wallet. BIP39 seed. Password for extension. Tezos-specific derivation.",
        wallet_file_format="temple_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Polkadot.js": WalletInfo(
        name="Polkadot.js Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/354'/0'/0"],
        supported_coins=["DOT", "KSM", "Substrate chains"],
        recovery_difficulty="Easy",
        notes="Polkadot/Substrate ecosystem. BIP39 seed. sr25519 and ed25519 key types.",
        wallet_file_format="polkadot_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "SubWallet": WalletInfo(
        name="SubWallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/354'/0'/0", "m/44'/60'/0'/0"],
        supported_coins=["DOT", "KSM", "Substrate + EVM chains"],
        recovery_difficulty="Easy",
        notes="Polkadot ecosystem + EVM. BIP39 seed. Multi-chain.",
        wallet_file_format="subwallet_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "MathWallet": WalletInfo(
        name="MathWallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["Chain-specific paths"],
        supported_coins=["BTC", "ETH", "SOL", "DOT", "100+ chains"],
        recovery_difficulty="Easy",
        notes="Multi-chain wallet. BIP39 seed. Supports 100+ blockchains.",
        wallet_file_format="mathwallet_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "TokenPocket": WalletInfo(
        name="TokenPocket",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/60'/0'/0", "m/44'/730'/0'/0"],
        supported_coins=["ETH", "EOS", "TRON", "BSC", "HECO"],
        recovery_difficulty="Easy",
        notes="Multi-chain wallet popular in Asia. BIP39 seed. Supports EOS and TRON.",
        wallet_file_format="tokenpocket_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "TronLink": WalletInfo(
        name="TronLink",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.SOFTWARE_MOBILE, WalletCategory.NON_CUSTODIAL, WalletCategory.SINGLE_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/195'/0'/0"],
        supported_coins=["TRX", "TRC-20", "TRC-721"],
        recovery_difficulty="Easy",
        notes="TRON ecosystem wallet. BIP39 12 words. Password for extension.",
        wallet_file_format="tronlink_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Liquality": WalletInfo(
        name="Liquality Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/60'/0'/0", "m/44'/0'/0'", "m/44'/137'/0'/0"],
        supported_coins=["BTC", "ETH", "RSK", "BNB"],
        recovery_difficulty="Easy",
        notes="Atomic swap wallet. BIP39 seed. Cross-chain swaps.",
        wallet_file_format="liquality_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Enkrypt": WalletInfo(
        name="Enkrypt Wallet",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/60'/0'/0", "m/44'/354'/0'/0", "m/44'/501'/0'/0'"],
        supported_coins=["ETH", "DOT", "SOL", "BTC", "Multi-chain"],
        recovery_difficulty="Easy",
        notes="Multi-chain by MyCrypto. BIP39 seed. EVM + Substrate + Solana.",
        wallet_file_format="enkrypt_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Frame": WalletInfo(
        name="Frame",
        category=[WalletCategory.SOFTWARE_DESKTOP, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=True,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD, LoginTech.PASSPHRASE],
        derivation_paths=["m/44'/60'/0'/0"],
        supported_coins=["ETH", "EVM chains"],
        recovery_difficulty="Easy",
        notes="Desktop wallet for EVM. BIP39 + passphrase. System-level wallet.",
        wallet_file_format="frame_vault.json",
        encryption_method="AES-256 + Password"
    ),
    "Taho (formerly Tally Ho)": WalletInfo(
        name="Taho (Tally Ho)",
        category=[WalletCategory.SOFTWARE_EXTENSION, WalletCategory.NON_CUSTODIAL, WalletCategory.MULTI_CHAIN],
        supported_seed_types=[SeedType.BIP39],
        seed_lengths=[12, 24],
        supports_passphrase=False,
        login_technologies=[LoginTech.SEED_PHRASE, LoginTech.PASSWORD],
        derivation_paths=["m/44'/60'/0'/0"],
        supported_coins=["ETH", "EVM chains"],
        recovery_difficulty="Easy",
        notes="Community-owned wallet fork of MetaMask. BIP39 seed. Open source.",
        wallet_file_format="taho_vault.json",
        encryption_method="AES-256 + Password"
    ),
}


# ==============================================================================
# LOGIN TECHNOLOGY SUMMARY
# ==============================================================================

LOGIN_TECHNOLOGIES = {
    LoginTech.SEED_PHRASE: {
        "name": "Seed Phrase (Mnemonic)",
        "description": "BIP39, Electrum, SLIP39, or Monero mnemonic phrase used to derive wallet keys",
        "word_counts": [12, 15, 16, 18, 20, 21, 24, 25, 33],
        "standards": ["BIP39", "Electrum v1", "Electrum v2", "SLIP39", "Monero/Polyseed"],
        "recovery_tools": ["seedrecover.py", "btcrecover.py", "Ian Coleman's BIP39 Tool"],
        "difficulty": "Varies by missing words"
    },
    LoginTech.PASSPHRASE: {
        "name": "BIP39 Passphrase (25th Word)",
        "description": "Optional passphrase added to BIP39 seed for additional security. Creates entirely different wallets.",
        "word_counts": None,
        "standards": ["BIP39"],
        "recovery_tools": ["seedrecover.py", "btcrecover.py", "Custom brute-force"],
        "difficulty": "Hard - entire search space must be tested"
    },
    LoginTech.PASSWORD: {
        "name": "Wallet Password",
        "description": "Password used to encrypt wallet files (wallet.dat, vault JSON, etc.)",
        "word_counts": None,
        "standards": ["AES-256-CBC", "AES-128-CTR", "AES-256-GCM", "ChaCha20"],
        "recovery_tools": ["btcrecover.py", "hashcat", "john the ripper"],
        "difficulty": "Depends on password complexity"
    },
    LoginTech.PIN: {
        "name": "PIN Code",
        "description": "Short numeric code (4-8 digits) for device or app access",
        "word_counts": None,
        "standards": ["Device-specific"],
        "recovery_tools": ["btcrecover.py (limited)", "Brute-force on extracted hash"],
        "difficulty": "Easy to brute-force if hash extracted"
    },
    LoginTech.BIOMETRIC: {
        "name": "Biometric Authentication",
        "description": "Fingerprint, Face ID, or other biometric verification for wallet access",
        "word_counts": None,
        "standards": ["Touch ID", "Face ID", "Android BiometricPrompt"],
        "recovery_tools": ["Not recoverable - fallback to seed phrase or password"],
        "difficulty": "Not applicable - use fallback auth"
    },
    LoginTech.HARDWARE_KEY: {
        "name": "Hardware Security Key (U2F/FIDO2)",
        "description": "Physical security key (YubiKey, etc.) for 2FA authentication",
        "word_counts": None,
        "standards": ["U2F", "FIDO2", "WebAuthn"],
        "recovery_tools": ["Not recoverable - use backup codes or seed phrase"],
        "difficulty": "Not applicable - use backup method"
    },
    LoginTech.TWO_FA: {
        "name": "Two-Factor Authentication (2FA/TOTP)",
        "description": "Time-based One-Time Password via authenticator app or SMS",
        "word_counts": None,
        "standards": ["TOTP (RFC 6238)", "HOTP (RFC 4226)", "SMS OTP"],
        "recovery_tools": ["Backup codes", "Authenticator export", "Seed phrase bypass"],
        "difficulty": "Medium - need backup codes or authenticator secret"
    },
    LoginTech.MULTI_SIG: {
        "name": "Multi-Signature",
        "description": "M-of-N signature scheme requiring multiple parties to approve transactions",
        "word_counts": None,
        "standards": ["BIP67", "Electrum multisig", "Gnosis Safe"],
        "recovery_tools": ["All required co-signer keys/seeds"],
        "difficulty": "Hard - requires minimum M keys from N signers"
    },
    LoginTech.SECURE_ELEMENT: {
        "name": "Secure Element",
        "description": "Dedicated security chip (ST33, Optiga, EAL5+) that stores private keys",
        "word_counts": None,
        "standards": ["CC EAL5+", "FIPS 140-2"],
        "recovery_tools": ["Not extractable - seed phrase is only backup"],
        "difficulty": "Not applicable - use seed phrase"
    },
    LoginTech.SOCIAL_RECOVERY: {
        "name": "Social Recovery",
        "description": "Designated guardians who can help recover wallet access",
        "word_counts": None,
        "standards": ["Argent Social Recovery", "Gnosis Recovery"],
        "recovery_tools": ["Guardian approval process"],
        "difficulty": "Medium - requires guardian cooperation"
    },
    LoginTech.MFA: {
        "name": "Multi-Factor Authentication",
        "description": "Combination of 2+ authentication factors (password + 2FA + biometric, etc.)",
        "word_counts": None,
        "standards": ["Various combinations"],
        "recovery_tools": ["Account-specific recovery flow"],
        "difficulty": "Very Hard - need to bypass multiple factors"
    },
}


def get_wallet_by_name(name: str) -> Optional[WalletInfo]:
    return WALLETS.get(name)


def get_wallets_by_seed_type(seed_type: SeedType) -> List[WalletInfo]:
    return [w for w in WALLETS.values() if seed_type in w.supported_seed_types]


def get_wallets_by_coin(coin: str) -> List[WalletInfo]:
    coin_upper = coin.upper()
    return [w for w in WALLETS.values() if any(coin_upper in c.upper() for c in w.supported_coins)]


def get_wallets_by_login_tech(tech: LoginTech) -> List[WalletInfo]:
    return [w for w in WALLETS.values() if tech in w.login_technologies]


def list_all_wallets() -> List[str]:
    return list(WALLETS.keys())


def list_all_seed_types() -> List[str]:
    return [s.value for s in SeedType]


def list_all_login_techs() -> List[str]:
    return [t.value for t in LoginTech]
