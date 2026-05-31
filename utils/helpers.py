"""
CryptoRecover - Utility Functions
"""

import hashlib
import json
import os
import platform
import sys
import unicodedata
from pathlib import Path
from typing import Optional, Dict, List


def get_platform() -> str:
    """Get normalized platform name"""
    system = platform.system().lower()
    if system == "darwin":
        return "mac"
    elif system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    return system


def get_config_dir() -> Path:
    """Get platform-specific config directory"""
    plat = get_platform()
    if plat == "windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif plat == "mac":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "cryptorecover"


def get_data_dir() -> Path:
    """Get platform-specific data directory"""
    config_dir = get_config_dir()
    data_dir = config_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def ensure_dirs():
    """Ensure all required directories exist"""
    config_dir = get_config_dir()
    (config_dir / "data").mkdir(parents=True, exist_ok=True)
    (config_dir / "logs").mkdir(parents=True, exist_ok=True)
    (config_dir / "temp").mkdir(parents=True, exist_ok=True)


def format_time(seconds: float) -> str:
    """Format seconds into human-readable time"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_number(n: int) -> str:
    """Format large numbers with commas"""
    return f"{n:,}"


def estimate_recovery_time(
    total_combinations: int,
    speed: float = 1000.0  # attempts per second
) -> str:
    """Estimate recovery time based on combinations and speed"""
    if speed <= 0:
        return "Unknown"
    seconds = total_combinations / speed
    return format_time(seconds)


def calculate_seed_combinations(
    missing_words: int,
    wordlist_size: int = 2048
) -> int:
    """Calculate total combinations for missing seed words"""
    return wordlist_size ** missing_words


def calculate_passphrase_combinations(
    charset_size: int,
    length: int
) -> int:
    """Calculate total passphrase combinations"""
    return charset_size ** length


def validate_seed_phrase_format(words: List[str], expected_length: int = 12) -> Dict:
    """Validate seed phrase format and return issues"""
    issues = []
    wordlist = None
    try:
        from ..core.recovery_engine import get_bip39_wordlist
        wordlist = get_bip39_wordlist()
    except Exception:
        pass

    if len(words) != expected_length:
        issues.append(f"Expected {expected_length} words, got {len(words)}")

    if wordlist:
        invalid_words = [w for w in words if w not in wordlist]
        if invalid_words:
            issues.append(f"Invalid BIP39 words: {invalid_words}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "word_count": len(words),
        "expected_count": expected_length
    }


def sanitize_passphrase(passphrase: str) -> str:
    """Normalize passphrase according to BIP39 spec"""
    return unicodedata.normalize("NFKD", passphrase)


def get_system_info() -> Dict:
    """Get system information for debugging"""
    return {
        "platform": platform.platform(),
        "python_version": sys.version,
        "cpu_count": os.cpu_count(),
        "architecture": platform.architecture(),
        "machine": platform.machine(),
    }


def save_recovery_result(result, output_path: Optional[str] = None) -> str:
    """Save recovery result to file"""
    if output_path is None:
        output_path = str(get_data_dir() / "last_result.json")

    data = {
        "success": result.success,
        "recovery_type": result.recovery_type.value if hasattr(result.recovery_type, 'value') else str(result.recovery_type),
        "found_value": result.found_value,
        "attempts": result.attempts,
        "time_elapsed": result.time_elapsed,
        "attempts_per_second": result.attempts_per_second,
        "status": result.status.value if hasattr(result.status, 'value') else str(result.status),
        "error_message": result.error_message,
        "details": result.details,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return output_path


def load_password_dictionary(path: str) -> List[str]:
    """Load a password dictionary file"""
    passwords = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                passwords.append(line)
    return passwords


def generate_password_mutations(base_passwords: List[str]) -> List[str]:
    """Generate common password mutations"""
    mutations = []
    for pw in base_passwords:
        mutations.extend([
            pw,
            pw.lower(),
            pw.upper(),
            pw.capitalize(),
            pw + "1",
            pw + "123",
            pw + "!",
            pw + "@",
            pw + "#",
            pw + "$",
            pw + "2024",
            pw + "2025",
            pw + "2026",
            "!" + pw,
            "@" + pw,
            "#" + pw,
            pw[::-1],  # reversed
        ])
    # Remove duplicates
    return list(dict.fromkeys(mutations))
