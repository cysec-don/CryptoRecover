"""
CryptoRecover - Integrations
================================
Integration layer for external tools: bitcoin-core, btcrecover, seedrecover
"""

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


# ==============================================================================
# BITCOIN CORE INTEGRATION
# ==============================================================================

class BitcoinCoreIntegration:
    """Integration with Bitcoin Core (bitcoin-cli / bitcoind)"""

    def __init__(self, bitcoin_cli_path: Optional[str] = None, rpc_user: Optional[str] = None,
                 rpc_password: Optional[str] = None, rpc_host: str = "127.0.0.1",
                 rpc_port: int = 8332, testnet: bool = False):
        self.bitcoin_cli_path = bitcoin_cli_path or shutil.which("bitcoin-cli")
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.rpc_host = rpc_host
        self.rpc_port = rpc_port
        self.testnet = testnet

    def is_available(self) -> bool:
        """Check if bitcoin-cli is available"""
        return self.bitcoin_cli_path is not None and os.path.isfile(self.bitcoin_cli_path)

    def _run_command(self, *args, timeout: int = 30) -> Tuple[bool, str]:
        """Run a bitcoin-cli command"""
        if not self.is_available():
            return False, "bitcoin-cli not available"

        cmd = [self.bitcoin_cli_path]
        if self.testnet:
            cmd.append("-testnet")
        if self.rpc_user:
            cmd.extend([f"-rpcuser={self.rpc_user}"])
        if self.rpc_password:
            cmd.extend([f"-rpcpassword={self.rpc_password}"])
        cmd.extend([f"-rpcconnect={self.rpc_host}"])
        cmd.extend([f"-rpcport={str(self.rpc_port)}"])
        cmd.extend(args)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def get_blockchain_info(self) -> Dict:
        """Get blockchain information"""
        success, output = self._run_command("getblockchaininfo")
        if success:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                pass
        return {"error": "Could not get blockchain info"}

    def get_wallet_info(self) -> Dict:
        """Get wallet information"""
        success, output = self._run_command("getwalletinfo")
        if success:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                pass
        return {"error": "Could not get wallet info"}

    def dump_wallet(self, output_path: str) -> bool:
        """Dump wallet to file (requires running bitcoind)"""
        success, output = self._run_command("dumpwallet", output_path, timeout=60)
        return success

    def import_seed(self, seed_hex: str, label: str = "cryptorecover") -> bool:
        """Import a seed into Bitcoin Core"""
        # Create descriptor from seed
        success, output = self._run_command(
            "importmulti",
            json.dumps([{
                "desc": f"wpkh({seed_hex})",
                "label": label,
                "timestamp": "now",
                "watchonly": True
            }]),
            json.dumps({"rescan": False}),
            timeout=60
        )
        return success

    def verify_address(self, address: str) -> bool:
        """Verify if an address is valid"""
        success, output = self._run_command("validateaddress", address)
        if success:
            try:
                info = json.loads(output)
                return info.get("isvalid", False)
            except json.JSONDecodeError:
                pass
        return False

    def get_addresses_from_seed(self, seed_hex: str, count: int = 5) -> List[str]:
        """Derive addresses from a seed hex"""
        addresses = []
        # This requires descriptor-based derivation
        for i in range(count):
            success, output = self._run_command(
                "deriveaddresses",
                f"wpkh({seed_hex}/84'/0'/0'/0/{i})",
                timeout=10
            )
            if success:
                try:
                    result = json.loads(output)
                    if isinstance(result, list):
                        addresses.extend(result)
                    elif isinstance(result, str):
                        addresses.append(result)
                except json.JSONDecodeError:
                    pass
        return addresses

    def unlock_wallet(self, passphrase: str, timeout: int = 60) -> bool:
        """Unlock the wallet with passphrase"""
        success, _ = self._run_command("walletpassphrase", passphrase, str(timeout))
        return success


# ==============================================================================
# BTCRECOVER INTEGRATION
# ==============================================================================

class BTCRecoverIntegration:
    """Integration with btcrecover.py"""

    def __init__(self, btcrecover_path: Optional[str] = None):
        self.btcrecover_path = btcrecover_path
        if not self.btcrecover_path:
            self.btcrecover_path = self._find_btcrecover()

    def is_available(self) -> bool:
        """Check if btcrecover is available"""
        return self.btcrecover_path is not None and os.path.isfile(self.btcrecover_path)

    def _find_btcrecover(self) -> Optional[str]:
        """Find btcrecover.py"""
        # Check common locations
        candidates = [
            shutil.which("btcrecover.py"),
            shutil.which("btcrecover"),
            str(Path.home() / "btcrecover" / "btcrecover.py"),
            str(Path.home() / "tools" / "btcrecover.py"),
            str(Path.cwd() / "btcrecover.py"),
        ]
        for path in candidates:
            if path and os.path.isfile(path):
                return path
        return None

    def recover_wallet_password(
        self,
        wallet_file: str,
        password_list: Optional[List[str]] = None,
        password_file: Optional[str] = None,
        token_list: Optional[str] = None,
        threads: int = 0,
        extra_args: Optional[List[str]] = None,
    ) -> Dict:
        """Recover wallet password using btcrecover"""
        if not self.is_available():
            return {"success": False, "error": "btcrecover not available"}

        cmd = [sys.executable, self.btcrecover_path, "--wallet", wallet_file]

        if threads > 0:
            cmd.extend(["--threads", str(threads)])

        temp_file = None
        if password_file:
            cmd.extend(["--passwordlist", password_file])
        elif password_list:
            # Write passwords to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False,
                                              encoding="utf-8") as f:
                for pw in password_list:
                    f.write(pw + "\n")
                temp_file = f.name
            cmd.extend(["--passwordlist", temp_file])

        if token_list:
            cmd.extend(["--tokenlist", token_list])

        if extra_args:
            cmd.extend(extra_args)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            output = result.stdout + result.stderr

            if "Password found" in output or "PASSWORD FOUND" in output:
                # Extract the found password
                found_password = self._extract_found_password(output)
                return {
                    "success": True,
                    "password": found_password,
                    "output": output[:2000]
                }

            return {
                "success": False,
                "error": "Password not found",
                "output": output[:2000]
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "btcrecover timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            # Clean up temp file containing sensitive password candidates
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass

    def recover_seed_phrase(
        self,
        mnemonic: str,
        missing_words: int,
        wallet_type: str = "bitcoin",
        address: Optional[str] = None,
        threads: int = 0,
        extra_args: Optional[List[str]] = None,
    ) -> Dict:
        """Recover seed phrase using btcrecover's seed phrase feature"""
        if not self.is_available():
            return {"success": False, "error": "btcrecover not available"}

        cmd = [sys.executable, self.btcrecover_path, "--big-seed",
               "--mnemonic", mnemonic,
               f"--missing-seed-words={missing_words}",
               f"--wallet-type={wallet_type}"]

        if address:
            cmd.extend(["--address", address])

        if threads > 0:
            cmd.extend(["--threads", str(threads)])

        if extra_args:
            cmd.extend(extra_args)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            output = result.stdout + result.stderr

            if "Seed found" in output or "SEED FOUND" in output:
                found_seed = self._extract_found_seed(output)
                return {
                    "success": True,
                    "seed": found_seed,
                    "output": output[:2000]
                }

            return {
                "success": False,
                "error": "Seed not found",
                "output": output[:2000]
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "btcrecover timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _extract_found_password(self, output: str) -> Optional[str]:
        """Extract found password from btcrecover output"""
        for line in output.split("\n"):
            if "Password found" in line or "PASSWORD FOUND" in line:
                # Try various output formats
                if ":" in line:
                    return line.split(":")[-1].strip().strip("'\"")
        return None

    def _extract_found_seed(self, output: str) -> Optional[str]:
        """Extract found seed from btcrecover output"""
        for line in output.split("\n"):
            if "Seed found" in line or "SEED FOUND" in line:
                if ":" in line:
                    return line.split(":")[-1].strip().strip("'\"")
        return None


# ==============================================================================
# SEEDRECOVER INTEGRATION
# ==============================================================================

class SeedRecoverIntegration:
    """Integration with seedrecover.py (from btcrecover)"""

    def __init__(self, seedrecover_path: Optional[str] = None):
        self.seedrecover_path = seedrecover_path
        if not self.seedrecover_path:
            self.seedrecover_path = self._find_seedrecover()

    def is_available(self) -> bool:
        """Check if seedrecover is available"""
        return self.seedrecover_path is not None and os.path.isfile(self.seedrecover_path)

    def _find_seedrecover(self) -> Optional[str]:
        """Find seedrecover.py"""
        candidates = [
            shutil.which("seedrecover.py"),
            shutil.which("seedrecover"),
            str(Path.home() / "btcrecover" / "seedrecover.py"),
            str(Path.home() / "tools" / "seedrecover.py"),
            str(Path.cwd() / "seedrecover.py"),
        ]
        for path in candidates:
            if path and os.path.isfile(path):
                return path
        return None

    def recover_seed(
        self,
        mnemonic: str,
        wallet_type: str = "bitcoin",
        address: Optional[str] = None,
        derivation_path: Optional[str] = None,
        threads: int = 0,
        extra_args: Optional[List[str]] = None,
    ) -> Dict:
        """Recover missing seed phrase words using seedrecover"""
        if not self.is_available():
            return {"success": False, "error": "seedrecover not available"}

        cmd = [sys.executable, self.seedrecover_path,
               "--mnemonic", mnemonic,
               f"--wallet-type={wallet_type}"]

        if address:
            cmd.extend(["--addr-search", address])
            cmd.extend(["--addr-limit", "5"])

        if derivation_path:
            cmd.extend(["--bip32-path", derivation_path])

        if threads > 0:
            cmd.extend(["--num-threads", str(threads)])

        if extra_args:
            cmd.extend(extra_args)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            output = result.stdout + result.stderr

            if "Seed found" in output or "SEED FOUND" in output or "found" in output.lower():
                found_seed = self._extract_result(output)
                return {
                    "success": True,
                    "seed": found_seed,
                    "output": output[:2000]
                }

            return {
                "success": False,
                "error": "Seed not found",
                "output": output[:2000]
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "seedrecover timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def recover_passphrase(
        self,
        mnemonic: str,
        passphrase_candidates: Optional[List[str]] = None,
        wallet_type: str = "bitcoin",
        address: Optional[str] = None,
        threads: int = 0,
        extra_args: Optional[List[str]] = None,
    ) -> Dict:
        """Recover BIP39 passphrase using seedrecover"""
        if not self.is_available():
            return {"success": False, "error": "seedrecover not available"}

        cmd = [sys.executable, self.seedrecover_path,
               "--mnemonic", mnemonic,
               "--passphrase-phrase",
               f"--wallet-type={wallet_type}"]

        if address:
            cmd.extend(["--addr-search", address])

        if passphrase_candidates:
            cmd.extend(["--passphrase-list", ",".join(passphrase_candidates)])

        if threads > 0:
            cmd.extend(["--num-threads", str(threads)])

        if extra_args:
            cmd.extend(extra_args)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            output = result.stdout + result.stderr

            if "Passphrase found" in output or "PASSPHRASE FOUND" in output:
                found = self._extract_result(output, "passphrase")
                return {
                    "success": True,
                    "passphrase": found,
                    "output": output[:2000]
                }

            return {
                "success": False,
                "error": "Passphrase not found",
                "output": output[:2000]
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "seedrecover timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _extract_result(self, output: str, result_type: str = "seed") -> Optional[str]:
        """Extract found result from seedrecover output"""
        for line in output.split("\n"):
            if "found" in line.lower() and ":" in line:
                return line.split(":")[-1].strip().strip("'\"")
        return None


# ==============================================================================
# INTEGRATION FACTORY
# ==============================================================================

class IntegrationFactory:
    """Factory for creating integration instances"""

    @staticmethod
    def create_bitcoin_core(**kwargs) -> BitcoinCoreIntegration:
        return BitcoinCoreIntegration(**kwargs)

    @staticmethod
    def create_btcrecover(path: Optional[str] = None) -> BTCRecoverIntegration:
        return BTCRecoverIntegration(path)

    @staticmethod
    def create_seedrecover(path: Optional[str] = None) -> SeedRecoverIntegration:
        return SeedRecoverIntegration(path)

    @staticmethod
    def check_all_integrations() -> Dict[str, bool]:
        """Check availability of all integrations"""
        return {
            "bitcoin_core": BitcoinCoreIntegration().is_available(),
            "btcrecover": BTCRecoverIntegration().is_available(),
            "seedrecover": SeedRecoverIntegration().is_available(),
        }
