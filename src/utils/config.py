"""
Configuration management for CryptoRecover.
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class AIConfig:
    """AI provider configuration."""
    default_provider: str = "ollama"
    api_keys: Dict[str, str] = field(default_factory=dict)
    default_model: Dict[str, str] = field(default_factory=dict)
    temperature: float = 0.7
    max_tokens: int = 4096
    consensus_min_providers: int = 2


@dataclass
class RecoveryConfig:
    """Recovery engine configuration."""
    max_attempts: int = 10_000_000
    checkpoint_interval: int = 10_000
    batch_size: int = 100
    parallel_workers: int = 4
    phases_enabled: Dict[str, bool] = field(default_factory=lambda: {
        "llm_guided": True,
        "cognitive": True,
        "semantic": True,
        "probabilistic": True,
        "exhaustive": True,
    })


@dataclass
class AppConfig:
    """Application configuration."""
    ai: AIConfig = field(default_factory=AIConfig)
    recovery: RecoveryConfig = field(default_factory=RecoveryConfig)
    log_level: str = "INFO"
    data_dir: str = ""

    def __post_init__(self):
        if not self.data_dir:
            self.data_dir = os.path.expanduser("~/.cryptorecover")


CONFIG_DIR = os.path.expanduser("~/.cryptorecover")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def load_config() -> AppConfig:
    """Load configuration from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
            return AppConfig(
                ai=AIConfig(**data.get("ai", {})),
                recovery=RecoveryConfig(**data.get("recovery", {})),
                log_level=data.get("log_level", "INFO"),
                data_dir=data.get("data_dir", ""),
            )
        except (json.JSONDecodeError, TypeError):
            return AppConfig()
    return AppConfig()


def save_config(config: AppConfig) -> None:
    """Save configuration to file with restricted permissions."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    # Set directory permissions to owner-only
    os.chmod(CONFIG_DIR, 0o700)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(asdict(config), f, indent=2)
    # Set file permissions to owner-only (contains API keys)
    os.chmod(CONFIG_FILE, 0o600)


def get_api_key(provider_id: str) -> Optional[str]:
    """Get API key for a provider from config."""
    config = load_config()
    return config.ai.api_keys.get(provider_id)


def set_api_key(provider_id: str, key: str) -> None:
    """Set API key for a provider in config."""
    config = load_config()
    config.ai.api_keys[provider_id] = key
    save_config(config)
