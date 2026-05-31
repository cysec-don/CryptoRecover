"""
CryptoRecover - Core Recovery Engine
=====================================
Unified engine for seed phrase, passphrase, and password recovery.
Integrates with btcrecover.py, seedrecover.py, and bitcoin-core.
"""

import hashlib
import itertools
import json
import logging
import os
import subprocess
import sys
import time
import unicodedata
import multiprocessing
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Callable, Tuple, Any

logger = logging.getLogger(__name__)


# ==============================================================================
# BIP39 WORDLIST
# ==============================================================================

BIP39_WORDLIST_PATH = Path(__file__).parent.parent / "config" / "bip39_english.txt"

_bip39_wordlist: Optional[List[str]] = None


def get_bip39_wordlist() -> List[str]:
    global _bip39_wordlist
    if _bip39_wordlist is None:
        try:
            with open(BIP39_WORDLIST_PATH, "r", encoding="utf-8") as f:
                _bip39_wordlist = [w.strip() for w in f.readlines() if w.strip()]
        except FileNotFoundError:
            logger.warning("BIP39 wordlist not found, using embedded fallback")
            _bip39_wordlist = _get_embedded_wordlist()
    return _bip39_wordlist


def _get_embedded_wordlist() -> List[str]:
    """Minimal fallback wordlist for testing - full list should be in config/"""
    return [
        "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
        "absurd", "abuse", "access", "accident", "account", "accuse", "achieve", "acid",
        "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual",
    ]


# ==============================================================================
# RECOVERY TYPES AND DATA CLASSES
# ==============================================================================

class RecoveryType(Enum):
    SEED_PHRASE = "seed_phrase"
    PASSPHRASE = "passphrase"
    PASSWORD = "password"
    PIN = "pin"


class RecoveryStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"
    CANCELLED = "cancelled"


class SeedStandard(Enum):
    BIP39 = "BIP39"
    ELECTRUM = "Electrum"
    SLIP39 = "SLIP39"
    MONERO = "Monero"


@dataclass
class RecoveryConfig:
    recovery_type: RecoveryType
    seed_standard: SeedStandard = SeedStandard.BIP39
    seed_length: int = 12  # number of words
    known_words: List[str] = field(default_factory=list)
    missing_word_positions: List[int] = field(default_factory=list)
    partial_passphrase: str = ""
    passphrase_candidates: List[str] = field(default_factory=list)
    password_candidates: List[str] = field(default_factory=list)
    password_dict_file: Optional[str] = None
    wallet_file: Optional[str] = None
    target_address: Optional[str] = None
    derivation_path: Optional[str] = None
    coin: str = "BTC"
    max_attempts: int = 0  # 0 = unlimited
    num_threads: int = 0  # 0 = auto (CPU count)
    use_gpu: bool = False
    btcrecover_path: Optional[str] = None
    seedrecover_path: Optional[str] = None
    bitcoin_core_path: Optional[str] = None
    callback: Optional[Callable] = None  # Progress callback


@dataclass
class RecoveryResult:
    success: bool
    recovery_type: RecoveryType
    found_value: Optional[str] = None
    attempts: int = 0
    time_elapsed: float = 0.0
    attempts_per_second: float = 0.0
    status: RecoveryStatus = RecoveryStatus.IDLE
    error_message: Optional[str] = None
    details: Dict = field(default_factory=dict)


# ==============================================================================
# BIP39 CHECKSUM VALIDATION
# ==============================================================================

def validate_bip39_checksum(words: List[str]) -> bool:
    """Validate BIP39 mnemonic checksum"""
    if not words:
        return False

    wordlist = get_bip39_wordlist()
    if len(wordlist) < 2048:
        logger.warning("Incomplete BIP39 wordlist - cannot validate checksum, rejecting")
        return False  # Cannot validate without full wordlist - safer to reject

    try:
        indices = [wordlist.index(w) for w in words]
    except ValueError:
        return False

    bits = ""
    for idx in indices:
        bits += format(idx, '011b')

    num_words = len(words)
    total_bits = num_words * 11
    checksum_bits = total_bits // 33
    entropy_bits = total_bits - checksum_bits

    entropy_binary = bits[:entropy_bits]
    checksum_binary = bits[entropy_bits:]

    entropy_bytes = int(entropy_binary, 2).to_bytes((entropy_bits + 7) // 8, 'big')
    expected_checksum = hashlib.sha256(entropy_bytes).digest()
    expected_bits = format(expected_checksum[0], '08b') + format(expected_checksum[1], '08b')
    expected_checksum_binary = expected_bits[:checksum_bits]

    return checksum_binary == expected_checksum_binary


def validate_electrum_seed(words: List[str]) -> bool:
    """Basic Electrum seed validation (simplified)"""
    # Electrum v2 uses HMAC-SHA512 based checksum
    # Full validation requires the full Electrum library
    return len(words) in [12, 13, 24, 25]


# ==============================================================================
# ADDRESS DERIVATION HELPERS
# ==============================================================================

def seed_to_master_key(seed_hex: str) -> Tuple[str, str]:
    """Derive master private key and chain code from seed using BIP32"""
    import hmac
    seed_bytes = bytes.fromhex(seed_hex)
    I = hmac.new(b"Bitcoin seed", seed_bytes, hashlib.sha512).digest()
    master_key = I[:32]
    chain_code = I[32:]
    return master_key.hex(), chain_code.hex()


def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """Convert BIP39 mnemonic to seed using PBKDF2"""
    mnemonic_normalized = unicodedata.normalize("NFKD", mnemonic)
    passphrase_normalized = unicodedata.normalize("NFKD", passphrase)
    salt = ("mnemonic" + passphrase_normalized).encode("utf-8")
    return hashlib.pbkdf2_hmac(
        "sha512",
        mnemonic_normalized.encode("utf-8"),
        salt,
        2048
    )


# ==============================================================================
# CORE RECOVERY ENGINE
# ==============================================================================

class RecoveryEngine:
    """Main recovery engine that coordinates all recovery operations"""

    def __init__(self, config: RecoveryConfig):
        self.config = config
        self.status = RecoveryStatus.IDLE
        self._cancel_flag = False
        self._start_time = 0.0
        self._attempts = 0
        self._result: Optional[RecoveryResult] = None

        if config.num_threads <= 0:
            config.num_threads = multiprocessing.cpu_count() or 1

    def cancel(self):
        """Cancel the running recovery operation"""
        self._cancel_flag = True
        self.status = RecoveryStatus.CANCELLED

    def get_progress(self) -> Dict:
        """Get current progress information"""
        elapsed = time.time() - self._start_time if self._start_time else 0
        return {
            "status": self.status.value,
            "attempts": self._attempts,
            "time_elapsed": elapsed,
            "attempts_per_second": self._attempts / elapsed if elapsed > 0 else 0,
        }

    # ─── SEED PHRASE RECOVERY ──────────────────────────────────────────

    def recover_seed_phrase(self) -> RecoveryResult:
        """Recover missing words from a seed phrase"""
        self.status = RecoveryStatus.RUNNING
        self._start_time = time.time()
        self._cancel_flag = False
        self._attempts = 0

        config = self.config
        wordlist = get_bip39_wordlist()

        if not config.missing_word_positions:
            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.SEED_PHRASE,
                status=RecoveryStatus.ERROR,
                error_message="No missing word positions specified"
            )

        if len(config.known_words) + len(config.missing_word_positions) != config.seed_length:
            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.SEED_PHRASE,
                status=RecoveryStatus.ERROR,
                error_message=f"Word count mismatch: {len(config.known_words)} known + "
                             f"{len(config.missing_word_positions)} missing != {config.seed_length} expected"
            )

        # Build the seed template
        seed_template = [None] * config.seed_length
        known_idx = 0
        missing_positions = sorted(config.missing_word_positions)

        for i in range(config.seed_length):
            if i in missing_positions:
                seed_template[i] = None
            else:
                if known_idx < len(config.known_words):
                    seed_template[i] = config.known_words[known_idx]
                    known_idx += 1

        # Try seedrecover.py first if available
        if config.seedrecover_path and os.path.isfile(config.seedrecover_path):
            result = self._recover_with_seedrecover(seed_template, missing_positions)
            if result and result.success:
                return result

        # Fallback to built-in brute force
        num_missing = len(missing_positions)
        total_combinations = len(wordlist) ** num_missing
        logger.info(f"Starting seed phrase recovery: {num_missing} missing words, "
                    f"{total_combinations} total combinations")

        try:
            if num_missing == 1:
                result = self._brute_force_single_word(
                    seed_template, missing_positions[0], wordlist
                )
            elif num_missing <= 4:
                result = self._brute_force_multi_word(
                    seed_template, missing_positions, wordlist
                )
            else:
                result = RecoveryResult(
                    success=False,
                    recovery_type=RecoveryType.SEED_PHRASE,
                    status=RecoveryStatus.ERROR,
                    error_message=f"Too many missing words ({num_missing}). "
                                 f"Maximum supported: 4 with built-in engine. "
                                 f"Use seedrecover.py for more."
                )
        except Exception as e:
            logger.error(f"Seed phrase recovery error: {e}")
            result = RecoveryResult(
                success=False,
                recovery_type=RecoveryType.SEED_PHRASE,
                status=RecoveryStatus.ERROR,
                error_message=str(e)
            )

        result.time_elapsed = time.time() - self._start_time
        result.attempts = self._attempts
        if result.attempts_per_second == 0 and result.time_elapsed > 0:
            result.attempts_per_second = result.attempts / result.time_elapsed

        self.status = result.status
        self._result = result
        return result

    def _brute_force_single_word(
        self, template: List[Optional[str]], position: int, wordlist: List[str]
    ) -> RecoveryResult:
        """Brute force a single missing word in a seed phrase"""
        for word in wordlist:
            if self._cancel_flag:
                return RecoveryResult(
                    success=False,
                    recovery_type=RecoveryType.SEED_PHRASE,
                    status=RecoveryStatus.CANCELLED
                )

            self._attempts += 1
            template[position] = word

            # Validate checksum
            if validate_bip39_checksum(template):
                seed_phrase = " ".join(template)

                # If target address specified, verify derivation
                if self.config.target_address:
                    if self._verify_address(seed_phrase):
                        return RecoveryResult(
                            success=True,
                            recovery_type=RecoveryType.SEED_PHRASE,
                            found_value=seed_phrase,
                            attempts=self._attempts,
                            status=RecoveryStatus.FOUND,
                            details={"found_word": word, "position": position}
                        )
                else:
                    # Valid checksum without target = potential match
                    return RecoveryResult(
                        success=True,
                        recovery_type=RecoveryType.SEED_PHRASE,
                        found_value=seed_phrase,
                        attempts=self._attempts,
                        status=RecoveryStatus.FOUND,
                        details={"found_word": word, "position": position}
                    )

            if self.config.callback and self._attempts % 100 == 0:
                self.config.callback(self.get_progress())

        return RecoveryResult(
            success=False,
            recovery_type=RecoveryType.SEED_PHRASE,
            attempts=self._attempts,
            status=RecoveryStatus.NOT_FOUND,
            error_message="No valid seed phrase found for the given constraints"
        )

    def _brute_force_multi_word(
        self, template: List[Optional[str]], positions: List[int], wordlist: List[str]
    ) -> RecoveryResult:
        """Brute force multiple missing words (up to 4)"""
        num_missing = len(positions)

        # For efficiency, iterate over word combinations
        # Only check full checksum on the last word of each combination
        word_ranges = [wordlist] * num_missing

        for combo in itertools.product(*word_ranges):
            if self._cancel_flag:
                return RecoveryResult(
                    success=False,
                    recovery_type=RecoveryType.SEED_PHRASE,
                    status=RecoveryStatus.CANCELLED
                )

            self._attempts += 1

            for i, pos in enumerate(positions):
                template[pos] = combo[i]

            if validate_bip39_checksum(template):
                seed_phrase = " ".join(template)

                if self.config.target_address:
                    if self._verify_address(seed_phrase):
                        return RecoveryResult(
                            success=True,
                            recovery_type=RecoveryType.SEED_PHRASE,
                            found_value=seed_phrase,
                            attempts=self._attempts,
                            status=RecoveryStatus.FOUND,
                            details={"found_words": list(combo), "positions": positions}
                        )
                else:
                    return RecoveryResult(
                        success=True,
                        recovery_type=RecoveryType.SEED_PHRASE,
                        found_value=seed_phrase,
                        attempts=self._attempts,
                        status=RecoveryStatus.FOUND,
                        details={"found_words": list(combo), "positions": positions}
                    )

            if self.config.callback and self._attempts % 1000 == 0:
                self.config.callback(self.get_progress())

            if self.config.max_attempts > 0 and self._attempts >= self.config.max_attempts:
                return RecoveryResult(
                    success=False,
                    recovery_type=RecoveryType.SEED_PHRASE,
                    attempts=self._attempts,
                    status=RecoveryStatus.NOT_FOUND,
                    error_message=f"Max attempts ({self.config.max_attempts}) reached"
                )

        return RecoveryResult(
            success=False,
            recovery_type=RecoveryType.SEED_PHRASE,
            attempts=self._attempts,
            status=RecoveryStatus.NOT_FOUND,
            error_message="No valid seed phrase found"
        )

    # ─── PASSPHRASE RECOVERY ────────────────────────────────────────────

    def recover_passphrase(self) -> RecoveryResult:
        """Recover BIP39 passphrase (25th word)"""
        self.status = RecoveryStatus.RUNNING
        self._start_time = time.time()
        self._cancel_flag = False
        self._attempts = 0

        config = self.config

        if not config.known_words:
            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.PASSPHRASE,
                status=RecoveryStatus.ERROR,
                error_message="Known seed phrase words required for passphrase recovery"
            )

        if not config.target_address and not config.wallet_file:
            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.PASSPHRASE,
                status=RecoveryStatus.ERROR,
                error_message="Target address or wallet file required for passphrase recovery"
            )

        seed_phrase = " ".join(config.known_words)

        # Try seedrecover.py first
        if config.seedrecover_path and os.path.isfile(config.seedrecover_path):
            result = self._recover_passphrase_with_seedrecover(seed_phrase)
            if result and result.success:
                return result

        # Built-in passphrase brute force
        candidates = self._generate_passphrase_candidates()

        logger.info(f"Starting passphrase recovery: {len(candidates)} candidates")

        try:
            for candidate in candidates:
                if self._cancel_flag:
                    return RecoveryResult(
                        success=False,
                        recovery_type=RecoveryType.PASSPHRASE,
                        status=RecoveryStatus.CANCELLED
                    )

                self._attempts += 1

                # Derive seed with this passphrase
                try:
                    seed_bytes = mnemonic_to_seed(seed_phrase, candidate)
                    seed_hex = seed_bytes.hex()

                    if config.target_address and self._verify_seed_address(seed_hex):
                        return RecoveryResult(
                            success=True,
                            recovery_type=RecoveryType.PASSPHRASE,
                            found_value=candidate,
                            attempts=self._attempts,
                            status=RecoveryStatus.FOUND,
                            details={"passphrase": candidate}
                        )
                except Exception:
                    continue

                if config.callback and self._attempts % 50 == 0:
                    self.config.callback(self.get_progress())

        except Exception as e:
            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.PASSPHRASE,
                status=RecoveryStatus.ERROR,
                error_message=str(e),
                attempts=self._attempts
            )

        elapsed = time.time() - self._start_time
        return RecoveryResult(
            success=False,
            recovery_type=RecoveryType.PASSPHRASE,
            attempts=self._attempts,
            time_elapsed=elapsed,
            status=RecoveryStatus.NOT_FOUND,
            error_message="Passphrase not found in candidate list"
        )

    def _generate_passphrase_candidates(self) -> List[str]:
        """Generate passphrase candidates from config"""
        candidates = []

        if self.config.passphrase_candidates:
            candidates.extend(self.config.passphrase_candidates)

        if self.config.partial_passphrase:
            # Generate variations of the partial passphrase
            partial = self.config.partial_passphrase
            candidates.append(partial)
            candidates.append(partial.lower())
            candidates.append(partial.upper())
            candidates.append(partial.capitalize())
            candidates.append(partial + "1")
            candidates.append(partial + "123")
            candidates.append(partial + "!")
            candidates.append(partial + "@")
            for i in range(100):
                candidates.append(partial + str(i))
            # Common suffixes
            for suffix in ["!", "@", "#", "$", "1", "123", "1234", "2024", "2025", "2026"]:
                candidates.append(partial + suffix)
            # Common prefixes
            for prefix in ["the", "my", "The", "My", "THE", "MY"]:
                candidates.append(prefix + partial)

        # If no candidates at all, offer common passphrase patterns
        if not candidates:
            common = [
                "", "password", "Password", "12345678", "bitcoin", "Bitcoin",
                "BTC", "crypto", "Crypto", "satoshi", "Satoshi", "nakamoto",
                "Nakamoto", "hodl", "HODL", "moon", "Moon", "wallet",
                "Wallet", "secret", "Secret", "hidden", "Hidden",
            ]
            candidates.extend(common)

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        return unique

    # ─── PASSWORD RECOVERY ──────────────────────────────────────────────

    def recover_password(self) -> RecoveryResult:
        """Recover wallet file password using btcrecover or built-in methods"""
        self.status = RecoveryStatus.RUNNING
        self._start_time = time.time()
        self._cancel_flag = False
        self._attempts = 0

        config = self.config

        if not config.wallet_file and not config.password_candidates and not config.password_dict_file:
            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.PASSWORD,
                status=RecoveryStatus.ERROR,
                error_message="Wallet file and/or password candidates required"
            )

        # Try btcrecover.py first
        if config.btcrecover_path and os.path.isfile(config.btcrecover_path):
            result = self._recover_with_btcrecover()
            if result and result.success:
                return result

        # Built-in password recovery (for supported formats)
        if config.wallet_file:
            result = self._builtin_password_recovery()
        else:
            # Just try candidates against no specific file (validation only)
            result = RecoveryResult(
                success=False,
                recovery_type=RecoveryType.PASSWORD,
                status=RecoveryStatus.ERROR,
                error_message="No wallet file specified for built-in password recovery. "
                             "Install btcrecover.py for advanced recovery."
            )

        result.time_elapsed = time.time() - self._start_time
        result.attempts = self._attempts
        self.status = result.status
        self._result = result
        return result

    def _builtin_password_recovery(self) -> RecoveryResult:
        """Built-in password recovery for known wallet formats"""
        wallet_path = Path(self.config.wallet_file)
        if not wallet_path.exists():
            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.PASSWORD,
                status=RecoveryStatus.ERROR,
                error_message=f"Wallet file not found: {wallet_path}"
            )

        candidates = self._load_password_candidates()
        if not candidates:
            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.PASSWORD,
                status=RecoveryStatus.ERROR,
                error_message="No password candidates available"
            )

        wallet_data = wallet_path.read_bytes()
        wallet_type = self._detect_wallet_type(wallet_data, wallet_path.suffix)

        for candidate in candidates:
            if self._cancel_flag:
                return RecoveryResult(
                    success=False,
                    recovery_type=RecoveryType.PASSWORD,
                    status=RecoveryStatus.CANCELLED
                )

            self._attempts += 1

            if self._try_wallet_password(wallet_data, candidate, wallet_type):
                return RecoveryResult(
                    success=True,
                    recovery_type=RecoveryType.PASSWORD,
                    found_value=candidate,
                    attempts=self._attempts,
                    status=RecoveryStatus.FOUND,
                    details={"wallet_type": wallet_type}
                )

            if self.config.callback and self._attempts % 10 == 0:
                self.config.callback(self.get_progress())

        return RecoveryResult(
            success=False,
            recovery_type=RecoveryType.PASSWORD,
            attempts=self._attempts,
            status=RecoveryStatus.NOT_FOUND,
            error_message="Password not found in candidates"
        )

    def _load_password_candidates(self) -> List[str]:
        """Load password candidates from config and/or dictionary file"""
        candidates = list(self.config.password_candidates) if self.config.password_candidates else []

        if self.config.password_dict_file:
            try:
                with open(self.config.password_dict_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and line not in candidates:
                            candidates.append(line)
            except FileNotFoundError:
                logger.error(f"Password dictionary not found: {self.config.password_dict_file}")

        return candidates

    def _detect_wallet_type(self, data: bytes, extension: str) -> str:
        """Detect wallet type from file data and extension"""
        # Bitcoin Core wallet.dat
        if extension == ".dat" or b"\x0b\x0f\x06\x00\x00\x00" in data[:20]:
            return "bitcoin_core"

        # Electrum wallet
        try:
            text = data.decode("utf-8", errors="ignore")
            if '"seed_version"' in text or '"keystore"' in text:
                return "electrum"
        except Exception:
            pass

        # MetaMask / browser extension vault
        try:
            text = data.decode("utf-8", errors="ignore")
            if '"data"' in text and '"iv"' in text and '"salt"' in text:
                return "metamask_vault"
        except Exception:
            pass

        # Generic JSON wallet
        try:
            text = data.decode("utf-8", errors="ignore")
            json.loads(text)
            return "json_wallet"
        except Exception:
            pass

        return "unknown"

    def _try_wallet_password(self, data: bytes, password: str, wallet_type: str) -> bool:
        """Try a password against a wallet file"""
        if wallet_type == "bitcoin_core":
            return self._try_bitcoin_core_password(data, password)
        elif wallet_type == "electrum":
            return self._try_electrum_password(data, password)
        elif wallet_type == "metamask_vault":
            return self._try_metamask_password(data, password)
        else:
            return False

    def _try_bitcoin_core_password(self, data: bytes, password: str) -> bool:
        """Try password against Bitcoin Core wallet.dat"""
        try:
            import hashlib
            # Bitcoin Core uses SHA-512 for key derivation (since v22+)
            # and AES-256-CBC for encryption
            # This is a simplified check - full implementation needs
            # bitcoin-core RPC or berkeleydb parsing
            key = hashlib.sha512(password.encode("utf-8")).digest()
            # Try AES decryption with derived key
            # Full implementation would parse wallet.dat BDB format
            return False  # Requires bitcoin-core integration
        except Exception:
            return False

    def _try_electrum_password(self, data: bytes, password: str) -> bool:
        """Try password against Electrum wallet file"""
        try:
            wallet_json = json.loads(data.decode("utf-8"))
            # Electrum uses AES-256-CBC with key derived from password
            if "use_encryption" in wallet_json and not wallet_json["use_encryption"]:
                return True  # Not encrypted
            if "seed" not in wallet_json and "keystore" not in wallet_json:
                return False
            # Full decryption requires pbkdf2 + AES-256-CBC
            return False  # Simplified - needs full implementation
        except Exception:
            return False

    def _try_metamask_password(self, data: bytes, password: str) -> bool:
        """Try password against MetaMask vault data"""
        try:
            vault = json.loads(data.decode("utf-8"))
            if isinstance(vault, dict) and "data" in vault:
                vault_data = vault
            elif isinstance(vault, list) and len(vault) > 0:
                vault_data = vault[0] if isinstance(vault[0], dict) else vault
            else:
                return False

            # MetaMask uses PBKDF2 + AES-128-CTR
            salt = bytes.fromhex(vault_data.get("salt", ""))
            iv = bytes.fromhex(vault_data.get("iv", ""))
            encrypted_data = bytes.fromhex(vault_data.get("data", ""))

            if not salt or not iv or not encrypted_data:
                return False

            # Derive key from password
            derived_key = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                10000,  # MetaMask iterations
                dklen=32
            )

            # AES-128-CTR decryption
            try:
                from Crypto.Cipher import AES
                cipher = AES.new(derived_key[:16], AES.MODE_CTR, nonce=b"", initial_value=iv)
                decrypted = cipher.decrypt(encrypted_data)
                # Check if decryption produced valid data
                try:
                    result = json.loads(decrypted.decode("utf-8"))
                    return True
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return False
            except ImportError:
                # Try with cryptography library
                try:
                    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                    cipher = Cipher(algorithms.AES(derived_key[:16]), modes.CTR(iv))
                    decryptor = cipher.decryptor()
                    decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
                    try:
                        result = json.loads(decrypted.decode("utf-8"))
                        return True
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        return False
                except ImportError:
                    logger.warning("No AES library available for MetaMask vault decryption")
                    return False
        except Exception:
            return False

    # ─── EXTERNAL TOOL INTEGRATION ──────────────────────────────────────

    def _recover_with_seedrecover(
        self, template: List[Optional[str]], positions: List[int]
    ) -> Optional[RecoveryResult]:
        """Use seedrecover.py for seed phrase recovery"""
        config = self.config
        if not config.seedrecover_path:
            return None

        try:
            cmd = [
                sys.executable, config.seedrecover_path,
                "--mnemonic", " ".join(str(w) if w else "?" for w in template),
                "--wallet-type", "bitcoin",
                "--addr-limit", "3",
                "--num-threads", str(config.num_threads),
            ]

            if config.target_address:
                cmd.extend(["--addr-search", config.target_address])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3600
            )

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "SEED FOUND" in line or "found" in line.lower():
                        # Parse the found seed
                        found_seed = line.split(":")[-1].strip() if ":" in line else ""
                        return RecoveryResult(
                            success=True,
                            recovery_type=RecoveryType.SEED_PHRASE,
                            found_value=found_seed,
                            status=RecoveryStatus.FOUND,
                            details={"method": "seedrecover.py"}
                        )

            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.SEED_PHRASE,
                status=RecoveryStatus.NOT_FOUND,
                details={"method": "seedrecover.py", "stderr": result.stderr[:500]}
            )

        except subprocess.TimeoutExpired:
            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.SEED_PHRASE,
                status=RecoveryStatus.ERROR,
                error_message="seedrecover.py timed out"
            )
        except Exception as e:
            logger.error(f"seedrecover.py error: {e}")
            return None

    def _recover_passphrase_with_seedrecover(self, seed_phrase: str) -> Optional[RecoveryResult]:
        """Use seedrecover.py for passphrase recovery"""
        config = self.config
        if not config.seedrecover_path:
            return None

        try:
            cmd = [
                sys.executable, config.seedrecover_path,
                "--mnemonic", seed_phrase,
                "--passphrase-phrase",
                "--wallet-type", "bitcoin",
                "--num-threads", str(config.num_threads),
            ]

            if config.target_address:
                cmd.extend(["--addr-search", config.target_address])

            if config.passphrase_candidates:
                cmd.extend(["--passphrase-list", ",".join(config.passphrase_candidates)])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3600
            )

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "PASSPHRASE FOUND" in line or "found" in line.lower():
                        found = line.split(":")[-1].strip() if ":" in line else ""
                        return RecoveryResult(
                            success=True,
                            recovery_type=RecoveryType.PASSPHRASE,
                            found_value=found,
                            status=RecoveryStatus.FOUND,
                            details={"method": "seedrecover.py"}
                        )

            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.PASSPHRASE,
                status=RecoveryStatus.NOT_FOUND,
                details={"method": "seedrecover.py"}
            )

        except Exception as e:
            logger.error(f"seedrecover.py passphrase error: {e}")
            return None

    def _recover_with_btcrecover(self) -> Optional[RecoveryResult]:
        """Use btcrecover.py for password recovery"""
        config = self.config
        if not config.btcrecover_path:
            return None

        try:
            cmd = [
                sys.executable, config.btcrecover_path,
                "--wallet", config.wallet_file,
                "--threads", str(config.num_threads),
            ]

            temp_path = None
            if config.password_dict_file:
                cmd.extend(["--passwordlist", config.password_dict_file])
            elif config.password_candidates:
                # Write candidates to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False,
                                                  encoding="utf-8") as f:
                    for pw in config.password_candidates:
                        f.write(pw + "\n")
                    temp_path = f.name
                cmd.extend(["--passwordlist", temp_path])

            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=3600
                )

                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split("\n")
                    for line in lines:
                        if "PASSWORD FOUND" in line or "found" in line.lower():
                            found = line.split(":")[-1].strip() if ":" in line else ""
                            return RecoveryResult(
                                success=True,
                                recovery_type=RecoveryType.PASSWORD,
                                found_value=found,
                                status=RecoveryStatus.FOUND,
                                details={"method": "btcrecover.py"}
                            )

                return RecoveryResult(
                    success=False,
                    recovery_type=RecoveryType.PASSWORD,
                    status=RecoveryStatus.NOT_FOUND,
                    details={"method": "btcrecover.py", "stderr": result.stderr[:500] if result.stderr else ""}
                )
            finally:
                # Clean up temp file containing sensitive password candidates
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except OSError:
                        pass

        except subprocess.TimeoutExpired:
            return RecoveryResult(
                success=False,
                recovery_type=RecoveryType.PASSWORD,
                status=RecoveryStatus.ERROR,
                error_message="btcrecover.py timed out"
            )
        except Exception as e:
            logger.error(f"btcrecover.py error: {e}")
            return None

    # ─── ADDRESS VERIFICATION ───────────────────────────────────────────

    def _verify_address(self, seed_phrase: str) -> bool:
        """Verify that a seed phrase generates the target address"""
        if not self.config.target_address:
            return True

        try:
            seed_bytes = mnemonic_to_seed(seed_phrase, self.config.partial_passphrase)
            seed_hex = seed_bytes.hex()
            return self._verify_seed_address(seed_hex)
        except Exception:
            return False

    def _verify_seed_address(self, seed_hex: str) -> bool:
        """Verify that a seed hex generates the target address"""
        if not self.config.target_address:
            return True

        # This requires full HD wallet derivation
        # For a complete implementation, we need:
        # - BIP32 derivation
        # - BIP44 path support
        # - Address encoding (Base58Check for legacy, Bech32 for segwit)

        # Try using bitcoin-core if available
        if self.config.bitcoin_core_path:
            return self._verify_with_bitcoin_core(seed_hex)

        # Try using hashlib-based derivation (simplified - BTC only)
        try:
            return self._verify_with_builtin_derivation(seed_hex)
        except Exception:
            logger.warning("Cannot verify address without bitcoin-core or derivation libraries")
            return False

    def _verify_with_bitcoin_core(self, seed_hex: str) -> bool:
        """Use bitcoin-core for address verification"""
        try:
            cmd = [
                self.config.bitcoin_core_path,
                "-regtest",
                "-named",
                "deriveaddresses",
                f"descriptor=pk({seed_hex})"
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                addresses = json.loads(result.stdout)
                return self.config.target_address in addresses
        except Exception as e:
            logger.error(f"bitcoin-core verification error: {e}")
        return False

    def _verify_with_builtin_derivation(self, seed_hex: str) -> bool:
        """Built-in address derivation and verification"""
        try:
            # Try using bip32utils if available
            import bip32utils
            from bip32utils import BIP32Key

            key = BIP32Key.fromExtendedKey(seed_hex)
            derivation = self.config.derivation_path or "m/44'/0'/0'/0/0"

            # Parse derivation path
            path_parts = derivation.replace("m/", "").split("/")
            current_key = key
            for part in path_parts:
                if part.endswith("'"):
                    index = int(part[:-1]) + 0x80000000
                else:
                    index = int(part)
                current_key = current_key.ChildKey(index)

            address = current_key.Address()
            return address == self.config.target_address

        except ImportError:
            # Try using hdwallet library
            try:
                from hdwallet import BIP44HDWallet
                from hdwallet.cryptocurrencies import BitcoinMainnet

                hdwallet = BIP44HDWallet(cryptocurrency=BitcoinMainnet)
                hdwallet.from_seed(seed_hex)

                path = self.config.derivation_path or "m/44'/0'/0'/0/0"
                hdwallet.from_path(path)

                address = hdwallet.address()
                return address == self.config.target_address

            except ImportError:
                logger.warning("No BIP32 derivation library available. "
                             "Install bip32utils or hdwallet for address verification.")
                return False
        except Exception as e:
            logger.error(f"Address verification error: {e}")
            return False


# ==============================================================================
# RECOVERY FLOW ORCHESTRATOR
# ==============================================================================

class RecoveryFlowOrchestrator:
    """Orchestrates the complete recovery workflow based on user scenario"""

    @staticmethod
    def determine_recovery_scenario(
        has_seed: bool = False,
        has_partial_seed: bool = False,
        has_passphrase: bool = False,
        has_wallet_file: bool = False,
        has_target_address: bool = False,
        missing_seed_words: int = 0,
        forgot_passphrase: bool = False,
        forgot_password: bool = False,
    ) -> List[RecoveryType]:
        """Determine the recovery scenario and return ordered recovery steps"""
        steps = []

        if has_partial_seed and missing_seed_words > 0:
            steps.append(RecoveryType.SEED_PHRASE)

        if has_seed and forgot_passphrase:
            steps.append(RecoveryType.PASSPHRASE)

        if has_wallet_file and forgot_password:
            steps.append(RecoveryType.PASSWORD)

        return steps

    @staticmethod
    def create_recovery_config(
        recovery_type: RecoveryType,
        **kwargs
    ) -> RecoveryConfig:
        """Create a recovery config with sensible defaults"""
        config = RecoveryConfig(
            recovery_type=recovery_type,
            **kwargs
        )

        # Auto-detect external tools
        if not config.btcrecover_path:
            config.btcrecover_path = RecoveryFlowOrchestrator._find_tool("btcrecover.py")
        if not config.seedrecover_path:
            config.seedrecover_path = RecoveryFlowOrchestrator._find_tool("seedrecover.py")
        if not config.bitcoin_core_path:
            config.bitcoin_core_path = RecoveryFlowOrchestrator._find_tool("bitcoin-cli")

        return config

    @staticmethod
    def _find_tool(name: str) -> Optional[str]:
        """Find an external tool in PATH or common locations"""
        # Check PATH
        import shutil
        found = shutil.which(name)
        if found:
            return found

        # Check common locations
        common_paths = [
            Path.home() / "tools" / name,
            Path("/usr/local/bin") / name,
            Path("/usr/bin") / name,
            Path.home() / ".local" / "bin" / name,
            Path.cwd() / name,
            Path.cwd() / "tools" / name,
        ]

        # Windows paths
        if sys.platform == "win32":
            common_paths.extend([
                Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / name,
                Path(os.environ.get("USERPROFILE", "")) / "tools" / name,
            ])

        for p in common_paths:
            if p.exists():
                return str(p)

        return None

    @staticmethod
    def run_recovery_flow(config: RecoveryConfig) -> RecoveryResult:
        """Execute the complete recovery flow"""
        engine = RecoveryEngine(config)

        if config.recovery_type == RecoveryType.SEED_PHRASE:
            return engine.recover_seed_phrase()
        elif config.recovery_type == RecoveryType.PASSPHRASE:
            return engine.recover_passphrase()
        elif config.recovery_type == RecoveryType.PASSWORD:
            return engine.recover_password()
        elif config.recovery_type == RecoveryType.PIN:
            # PIN is a subset of password recovery
            return engine.recover_password()
        else:
            return RecoveryResult(
                success=False,
                recovery_type=config.recovery_type,
                status=RecoveryStatus.ERROR,
                error_message=f"Unsupported recovery type: {config.recovery_type}"
            )
