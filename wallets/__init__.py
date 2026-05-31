"""
CryptoRecover - Wallets Database Package
"""

from .wallet_database import (
    WALLETS,
    WalletInfo,
    SeedType,
    LoginTech,
    WalletCategory,
    list_all_wallets,
    list_all_seed_types,
    list_all_login_techs,
    get_wallet_by_name,
    get_wallets_by_seed_type,
    get_wallets_by_coin,
    get_wallets_by_login_tech,
    LOGIN_TECHNOLOGIES,
)

__all__ = [
    "WALLETS",
    "WalletInfo",
    "SeedType",
    "LoginTech",
    "WalletCategory",
    "list_all_wallets",
    "list_all_seed_types",
    "list_all_login_techs",
    "get_wallet_by_name",
    "get_wallets_by_seed_type",
    "get_wallets_by_coin",
    "get_wallets_by_login_tech",
    "LOGIN_TECHNOLOGIES",
]
