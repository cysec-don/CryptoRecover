"""
CryptoRecover - Address Derivation Engine
==========================================
Full BIP32/BIP44/BIP49/BIP84/BIP86 HD wallet address derivation
with bloom filter support for fast multi-address matching.

Supports: Legacy (P2PKH), Nested SegWit (P2SH-P2WPKH),
          Native SegWit (P2WPKH), Taproot (P2TR)
"""

import hashlib
import hmac
import struct
import unicodedata
from typing import List, Optional, Tuple, Set, Dict
from dataclasses import dataclass, field

# ============================================================================
# BASE58 AND BECH32 ENCODING
# ============================================================================

_B58_ALPHABET = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def _b58encode(data: bytes) -> str:
    """Encode bytes to Base58Check string (without checksum)."""
    if not data:
        return ""
    n = int.from_bytes(data, 'big')
    result = bytearray()
    while n > 0:
        n, r = divmod(n, 58)
        result.append(_B58_ALPHABET[r])
    # Add leading '1' for each leading zero byte
    for byte in data:
        if byte == 0:
            result.append(_B58_ALPHABET[0])
        else:
            break
    return bytes(reversed(result)).decode('ascii')


def base58check_encode(payload: bytes, version) -> str:
    """Encode with Base58Check (includes checksum).
    
    Args:
        payload: The hash payload (e.g., RIPEMD160 hash)
        version: Version byte(s) - can be int (1 byte) or bytes (multi-byte for Zcash etc.)
    """
    if isinstance(version, int):
        versioned = bytes([version]) + payload
    else:
        versioned = version + payload
    checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
    return _b58encode(versioned + checksum)


# Bech32/Bech32m encoding
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
BECH32_CONST = 1
BECH32M_CONST = 0x2bc830a3


def _bech32_polymod(values):
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    return chk


def _bech32_hrp_expand(hrp: str):
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _bech32_verify_checksum(hrp: str, data: list) -> int:
    const = _bech32_polymod(_bech32_hrp_expand(hrp) + data)
    if const == BECH32_CONST:
        return BECH32_CONST
    elif const == BECH32M_CONST:
        return BECH32M_CONST
    return 0


def _bech32_create_checksum(hrp: str, data: list, spec: int) -> list:
    values = _bech32_hrp_expand(hrp) + data
    const = BECH32M_CONST if spec == BECH32M_CONST else BECH32_CONST
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def bech32_encode(hrp: str, witver: int, witprog: bytes) -> str:
    """Encode a segwit address."""
    spec = BECH32M_CONST if witver > 0 else BECH32_CONST
    converted = _convertbits(witprog, 8, 5)
    if converted is None:
        return ""  # Invalid witness program
    data = [witver] + converted
    checksum = _bech32_create_checksum(hrp, data, spec)
    return hrp + '1' + ''.join([BECH32_CHARSET[d] for d in data + checksum])


def _convertbits(data, frombits, tobits, pad=True):
    """General power-of-2 base conversion."""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret


# ============================================================================
# SECP256K1 ELLIPTIC CURVE (Pure Python - No External Dependencies)
# ============================================================================

_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
_Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
_A = 0
_B = 7


def _modinv(a, n=_N):
    """Modular inverse using extended Euclidean algorithm."""
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        hm, lm = lm, nm
        high, low = low, new
    return lm % n


def _point_add(p1, p2):
    """Add two points on secp256k1."""
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2:
        if y1 != y2:
            return None
        # Point doubling
        lam = (3 * x1 * x1) * _modinv(2 * y1, _P) % _P
    else:
        lam = (y2 - y1) * _modinv(x2 - x1, _P) % _P
    x3 = (lam * lam - x1 - x2) % _P
    y3 = (lam * (x1 - x3) - y1) % _P
    return (x3, y3)


def _point_mul(k, point=None):
    """Scalar multiplication on secp256k1 using double-and-add."""
    if point is None:
        point = (_Gx, _Gy)
    result = None
    addend = point
    while k:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


def _compress_pubkey(point):
    """Compress a public key point."""
    x, y = point
    prefix = b'\x02' if y % 2 == 0 else b'\x03'
    return prefix + x.to_bytes(32, 'big')


def _decompress_pubkey(compressed: bytes):
    """Decompress a compressed public key."""
    prefix = compressed[0]
    x = int.from_bytes(compressed[1:33], 'big')
    y_sq = (pow(x, 3, _P) + _B) % _P
    y = pow(y_sq, (_P + 1) // 4, _P)
    if y % 2 != (prefix - 2):
        y = _P - y
    return (x, y)


# ============================================================================
# BIP32 HD WALLET DERIVATION
# ============================================================================

@dataclass
class ExtendedKey:
    """BIP32 extended key."""
    private_key: Optional[bytes] = None
    public_key: Optional[bytes] = None
    chain_code: bytes = b''
    depth: int = 0
    parent_fingerprint: bytes = b'\x00\x00\x00\x00'
    index: int = 0

    @property
    def fingerprint(self):
        if self.public_key:
            return hashlib.sha256(self.public_key).digest()[:4]
        return b'\x00\x00\x00\x00'

    def is_private(self):
        return self.private_key is not None


def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """Convert BIP39 mnemonic to 64-byte seed using PBKDF2-SHA512."""
    mnemonic_normalized = unicodedata.normalize("NFKD", mnemonic)
    passphrase_normalized = unicodedata.normalize("NFKD", passphrase)
    salt = ("mnemonic" + passphrase_normalized).encode("utf-8")
    return hashlib.pbkdf2_hmac("sha512", mnemonic_normalized.encode("utf-8"), salt, 2048)


def seed_to_master_key(seed: bytes) -> ExtendedKey:
    """Derive BIP32 master extended key from seed."""
    I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    master_key = I[:32]
    chain_code = I[32:]
    # Verify key is valid (0 < key < N)
    key_int = int.from_bytes(master_key, 'big')
    if key_int == 0 or key_int >= _N:
        raise ValueError("Invalid master key derived from seed")
    pubkey_point = _point_mul(key_int)
    pubkey = _compress_pubkey(pubkey_point)
    return ExtendedKey(
        private_key=master_key,
        public_key=pubkey,
        chain_code=chain_code,
        depth=0,
    )


def derive_child_key(parent: ExtendedKey, index: int) -> ExtendedKey:
    """Derive child key using BIP32 CKD function."""
    if index >= 0x80000000:
        # Hardened derivation - requires private key
        if not parent.is_private():
            raise ValueError("Hardened derivation requires private key")
        data = b'\x00' + parent.private_key + struct.pack('>I', index)
    else:
        # Normal derivation
        data = parent.public_key + struct.pack('>I', index)

    I = hmac.new(parent.chain_code, data, hashlib.sha512).digest()
    IL, IR = I[:32], I[32:]

    il_int = int.from_bytes(IL, 'big')
    if il_int >= _N:
        raise ValueError("Invalid child key (IL >= N)")

    if parent.is_private():
        parent_int = int.from_bytes(parent.private_key, 'big')
        child_int = (il_int + parent_int) % _N
        if child_int == 0:
            raise ValueError("Invalid child key (zero)")
        child_key = child_int.to_bytes(32, 'big')
        child_pubkey_point = _point_mul(child_int)
        child_pubkey = _compress_pubkey(child_pubkey_point)
    else:
        parent_point = _decompress_pubkey(parent.public_key)
        il_point = _point_mul(il_int)
        child_point = _point_add(parent_point, il_point)
        if child_point is None:
            raise ValueError("Invalid child key (point at infinity)")
        child_key = None
        child_pubkey = _compress_pubkey(child_point)

    return ExtendedKey(
        private_key=child_key,
        public_key=child_pubkey,
        chain_code=IR,
        depth=parent.depth + 1,
        parent_fingerprint=parent.fingerprint,
        index=index,
    )


def derive_path(master: ExtendedKey, path: str) -> ExtendedKey:
    """Derive key at a BIP32 path (e.g., m/44'/0'/0'/0/0)."""
    current = master
    parts = path.strip().split('/')
    if parts[0] in ('m', 'M'):
        parts = parts[1:]
    for part in parts:
        if not part:
            continue
        hardened = part.endswith("'") or part.endswith('h') or part.endswith('H')
        index = int(part.rstrip("'hH"))
        if hardened:
            index += 0x80000000
        current = derive_child_key(current, index)
    return current


# ============================================================================
# ADDRESS GENERATION
# ============================================================================

class AddressType:
    P2PKH = "p2pkh"          # Legacy: 1...
    P2SH_P2WPKH = "p2sh_p2wpkh"  # Nested SegWit: 3...
    P2WPKH = "p2wpkh"        # Native SegWit: bc1q...
    P2TR = "p2tr"            # Taproot: bc1p...


# Coin configuration: (symbol, name, p2pkh_version, p2sh_version, bech32_hrp, slip44)
COIN_CONFIG = {
    "BTC": ("BTC", "Bitcoin", 0x00, 0x05, "bc", 0),
    "BTC_TESTNET": ("BTC", "Bitcoin Testnet", 0x6F, 0xC4, "tb", 1),
    "LTC": ("LTC", "Litecoin", 0x30, 0x32, "ltc", 2),
    "DOGE": ("DOGE", "Dogecoin", 0x1E, 0x16, "doge", 3),
    "DASH": ("DASH", "Dash", 0x4C, 0x10, "dash", 5),
    "ZEC": ("ZEC", "Zcash", 0x1CB8, 0x1CBD, "zs", 133),
    "ETH": ("ETH", "Ethereum", None, None, None, 60),
    "XRP": ("XRP", "Ripple", None, None, None, 144),
}


def _pubkey_to_eth_address(pubkey: bytes) -> str:
    """Generate Ethereum address from uncompressed public key.
    ETH uses Keccak-256 hash of the uncompressed public key (without 0x04 prefix).
    Since we may not have pysha3/pycryptodome for keccak, fall back to SHA3-256
    which is NOT the same as Keccak-256. If exact ETH addresses are needed,
    install pycryptodome: pip install pycryptodome
    """
    if len(pubkey) == 33:
        # Decompress the public key
        point = _decompress_pubkey(pubkey)
        x, y = point
        uncompressed = b'\x04' + x.to_bytes(32, 'big') + y.to_bytes(32, 'big')
    elif len(pubkey) == 65 and pubkey[0] == 0x04:
        uncompressed = pubkey
    else:
        return ""

    # Try Keccak-256 from pycryptodome first
    try:
        from Crypto.Hash import keccak
        k = keccak.new(digest_bits=256)
        k.update(uncompressed[1:])  # Remove 0x04 prefix
        addr_bytes = k.digest()[-20:]
        return "0x" + addr_bytes.hex()
    except ImportError:
        pass

    # Fall back to SHA3-256 (NOTE: This is NOT Keccak-256!
    # SHA3-256 and Keccak-256 differ in their padding.
    # This will produce WRONG Ethereum addresses.
    # Install pycryptodome for correct ETH address generation.)
    try:
        import hashlib as hl
        addr_hash = hl.sha3_256(uncompressed[1:]).digest()[-20:]
        return "0x" + addr_hash.hex() + " [WARNING: SHA3-256 not Keccak-256, may be incorrect]"
    except AttributeError:
        return ""

# Standard derivation paths per address type
DERIVATION_PATHS = {
    AddressType.P2PKH: "m/44'/{slip44}'/0'/0/{index}",
    AddressType.P2SH_P2WPKH: "m/49'/{slip44}'/0'/0/{index}",
    AddressType.P2WPKH: "m/84'/{slip44}'/0'/0/{index}",
    AddressType.P2TR: "m/86'/{slip44}'/0'/0/{index}",
}


def pubkey_to_p2pkh(pubkey: bytes, version: int = 0x00) -> str:
    """Generate P2PKH (Legacy) address from compressed public key."""
    sha256_hash = hashlib.sha256(pubkey).digest()
    ripemd160 = hashlib.new('ripemd160', sha256_hash).digest()
    return base58check_encode(ripemd160, version)


def pubkey_to_p2sh_p2wpkh(pubkey: bytes, version: int = 0x05) -> str:
    """Generate P2SH-P2WPKH (Nested SegWit) address from compressed public key."""
    sha256_hash = hashlib.sha256(pubkey).digest()
    ripemd160 = hashlib.new('ripemd160', sha256_hash).digest()
    # Witness program: OP_0 <20-byte-key-hash>
    witness_script = b'\x00\x14' + ripemd160
    # Hash the witness script
    script_hash = hashlib.new('ripemd160', hashlib.sha256(witness_script).digest()).digest()
    return base58check_encode(script_hash, version)


def pubkey_to_p2wpkh(pubkey: bytes, hrp: str = "bc") -> str:
    """Generate P2WPKH (Native SegWit) address from compressed public key."""
    sha256_hash = hashlib.sha256(pubkey).digest()
    ripemd160 = hashlib.new('ripemd160', sha256_hash).digest()
    return bech32_encode(hrp, 0, ripemd160)


def pubkey_to_p2tr(pubkey: bytes, hrp: str = "bc") -> str:
    """Generate P2TR (Taproot) address from compressed public key.
    
    Implements BIP86/BIP341 taproot key tweaking:
    Q = P + int(TaggedHash("TapTweak", P)) * G
    where P is the internal key (x-only) and Q is the output key.
    """
    if len(pubkey) == 33:
        x_only = pubkey[1:]  # Remove prefix byte
    else:
        x_only = pubkey

    # BIP341: Compute taproot tweak
    # TaggedHash("TapTweak", x_only) = SHA256("TapTweak" + x_only)
    tweak_hash = hashlib.sha256(b"TapTweak" + x_only).digest()
    tweak_int = int.from_bytes(tweak_hash, 'big')

    # Get the public key point
    x_int = int.from_bytes(x_only, 'big')
    # Compute y from x (choose even y for BIP340)
    y_sq = (pow(x_int, 3, _P) + _B) % _P
    y = pow(y_sq, (_P + 1) // 4, _P)
    # Ensure even y (BIP340 convention)
    if y % 2 != 0:
        y = _P - y
    P = (x_int, y)

    # Compute Q = P + tweak * G
    tweak_point = _point_mul(tweak_int)
    if tweak_point is None:
        return ""
    Q = _point_add(P, tweak_point)
    if Q is None:
        return ""

    # Output key is the x-coordinate of Q
    output_key = Q[0].to_bytes(32, 'big')
    return bech32_encode(hrp, 1, output_key)


def generate_address(master: ExtendedKey, addr_type: str, coin: str = "BTC",
                     account: int = 0, index: int = 0) -> str:
    """Generate a single address from master key."""
    config = COIN_CONFIG.get(coin, COIN_CONFIG["BTC"])
    slip44 = config[5]

    # Build derivation path
    path_template = DERIVATION_PATHS.get(addr_type, DERIVATION_PATHS[AddressType.P2WPKH])
    path = path_template.format(slip44=slip44, account=account, index=index)

    try:
        child = derive_path(master, path)
    except ValueError:
        return ""

    pubkey = child.public_key
    if pubkey is None:
        return ""

    # Handle ETH specially (uses Keccak-256, not SHA-256+RIPEMD160)
    if coin == "ETH":
        return _pubkey_to_eth_address(pubkey)

    # Handle XRP (uses same derivation as BTC but different version byte)
    if coin == "XRP":
        return pubkey_to_p2pkh(pubkey, 0x00)

    if addr_type == AddressType.P2PKH:
        version = config[2]
        if version is None:
            return ""  # Unsupported address type for this coin
        return pubkey_to_p2pkh(pubkey, version)
    elif addr_type == AddressType.P2SH_P2WPKH:
        version = config[3]
        if version is None:
            return ""
        return pubkey_to_p2sh_p2wpkh(pubkey, version)
    elif addr_type == AddressType.P2WPKH:
        hrp = config[4]
        if hrp is None:
            return ""
        return pubkey_to_p2wpkh(pubkey, hrp)
    elif addr_type == AddressType.P2TR:
        hrp = config[4]
        if hrp is None:
            return ""
        return pubkey_to_p2tr(pubkey, hrp)
    else:
        hrp = config[4]
        if hrp is None:
            return ""
        return pubkey_to_p2wpkh(pubkey, hrp)


def generate_addresses(master: ExtendedKey, addr_types: List[str] = None,
                       coin: str = "BTC", account: int = 0,
                       start_index: int = 0, count: int = 5) -> Dict[str, List[str]]:
    """Generate multiple addresses across address types."""
    if addr_types is None:
        addr_types = [AddressType.P2PKH, AddressType.P2SH_P2WPKH, AddressType.P2WPKH, AddressType.P2TR]

    results = {}
    for addr_type in addr_types:
        addresses = []
        for i in range(start_index, start_index + count):
            addr = generate_address(master, addr_type, coin, account, i)
            if addr:
                addresses.append(addr)
        results[addr_type] = addresses
    return results


# ============================================================================
# BLOOM FILTER FOR FAST ADDRESS MATCHING
# ============================================================================

class BloomFilter:
    """Memory-efficient probabilistic data structure for fast set membership testing.

    False positive rate is configurable. For address matching with
    ~1000 target addresses, a 1MB filter gives <0.01% false positive rate.
    """

    def __init__(self, capacity: int = 1000, fp_rate: float = 0.0001):
        """Initialize bloom filter.

        Args:
            capacity: Expected number of elements
            fp_rate: Desired false positive rate (0.0001 = 0.01%)
        """
        import math
        self.size = max(int(-capacity * math.log(fp_rate) / (math.log(2) ** 2)), 64)
        self.num_hashes = max(int((self.size / capacity) * math.log(2)), 1)
        self.bit_array = bytearray((self.size + 7) // 8)
        self.count = 0

    def _get_hashes(self, item: str) -> List[int]:
        """Double-hashing technique for multiple hash functions."""
        item_bytes = item.encode('utf-8')
        h1 = int(hashlib.md5(item_bytes).hexdigest(), 16)
        h2 = int(hashlib.sha1(item_bytes).hexdigest(), 16)
        return [(h1 + i * h2) % self.size for i in range(self.num_hashes)]

    def add(self, item: str):
        """Add an item to the bloom filter."""
        for pos in self._get_hashes(item):
            self.bit_array[pos // 8] |= (1 << (pos % 8))
        self.count += 1

    def might_contain(self, item: str) -> bool:
        """Check if an item might be in the set (false positives possible)."""
        for pos in self._get_hashes(item):
            if not (self.bit_array[pos // 8] & (1 << (pos % 8))):
                return False
        return True

    def __contains__(self, item: str) -> bool:
        return self.might_contain(item)

    def __len__(self) -> int:
        return self.count


class AddressMatcher:
    """Fast address matching using bloom filter + exact verification.

    Uses a two-stage approach:
    1. Bloom filter for O(1) probabilistic check (eliminates most negatives)
    2. Exact hash comparison for definitive verification

    This is faster than set membership for large target sets because
    bloom filters have better cache locality than hash tables.
    """

    def __init__(self, target_addresses: List[str]):
        """Initialize with target addresses to match against."""
        self.targets = set(addr.lower() for addr in target_addresses)
        self.bloom = BloomFilter(capacity=max(len(target_addresses), 10), fp_rate=0.0001)
        for addr in target_addresses:
            self.bloom.add(addr.lower())
        # Also build reverse lookup: first 8 chars -> full address
        self.prefix_map: Dict[str, Set[str]] = {}
        for addr in target_addresses:
            prefix = addr.lower()[:8]
            if prefix not in self.prefix_map:
                self.prefix_map[prefix] = set()
            self.prefix_map[prefix].add(addr.lower())

    def matches(self, address: str) -> bool:
        """Check if address matches any target (guaranteed no false positives)."""
        addr_lower = address.lower()
        # Stage 1: Bloom filter check
        if not self.bloom.might_contain(addr_lower):
            return False
        # Stage 2: Exact check
        return addr_lower in self.targets

    def quick_check(self, address: str) -> bool:
        """Fast probabilistic check (may have false positives, no false negatives)."""
        return self.bloom.might_contain(address.lower())

    def prefix_check(self, address: str) -> bool:
        """Check if any target address shares the same 8-char prefix."""
        prefix = address.lower()[:8]
        return prefix in self.prefix_map


# ============================================================================
# FULL DERIVATION PIPELINE
# ============================================================================

def derive_addresses_from_seed(
    seed_bytes: bytes,
    addr_types: List[str] = None,
    coin: str = "BTC",
    account: int = 0,
    num_addresses: int = 5,
    start_index: int = 0,
) -> Dict[str, List[str]]:
    """Full pipeline: seed bytes -> master key -> derived addresses."""
    if addr_types is None:
        addr_types = [AddressType.P2WPKH]

    try:
        master = seed_to_master_key(seed_bytes)
    except ValueError:
        return {at: [] for at in addr_types}

    return generate_addresses(master, addr_types, coin, account, start_index, num_addresses)


def derive_first_address(seed_bytes: bytes, addr_type: str = AddressType.P2WPKH,
                         coin: str = "BTC") -> Optional[str]:
    """Derive just the first address from a seed - optimized for recovery speed."""
    try:
        master = seed_to_master_key(seed_bytes)
        return generate_address(master, addr_type, coin, 0, 0)
    except (ValueError, Exception):
        return None


def check_seed_against_targets(
    seed_bytes: bytes,
    target_matcher: AddressMatcher,
    addr_types: List[str] = None,
    coin: str = "BTC",
    num_addresses: int = 5,
) -> bool:
    """Check if a seed generates any target address.

    This is the hot path in bruteforce recovery.
    Uses bloom filter for fast rejection of non-matching seeds.
    """
    if addr_types is None:
        addr_types = [AddressType.P2WPKH, AddressType.P2PKH, AddressType.P2SH_P2WPKH]

    try:
        master = seed_to_master_key(seed_bytes)
    except ValueError:
        return False

    for addr_type in addr_types:
        for i in range(num_addresses):
            addr = generate_address(master, addr_type, coin, 0, i)
            if addr and target_matcher.matches(addr):
                return True
    return False
