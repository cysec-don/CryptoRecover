"""
CryptoRecover - Core Package
=============================
Advanced cryptocurrency wallet recovery engine with multiple
invented techniques: CPF, PVP, LWO, HCP, SWP, AWD, CWP, EGS.
"""

# Legacy compatibility - old engine still available
from .recovery_engine import (
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

# New advanced bruteforce engine
from .bruteforce_engine import (
    BruteforceEngine,
    BruteforceConfig,
    BruteforceResult,
    RecoveryMode,
    SearchStrategy,
)

# Address derivation with bloom filter support
from .address_derivation import (
    AddressMatcher,
    AddressType,
    BloomFilter,
    mnemonic_to_seed as mnemonic_to_seed_v2,
    seed_to_master_key,
    generate_address,
    generate_addresses,
    derive_first_address,
    check_seed_against_targets,
    COIN_CONFIG,
    DERIVATION_PATHS,
)

# Checksum pre-filter with LWO and HCP
from .checksum_filter import (
    validate_bip39_checksum as validate_checksum_v2,
    find_valid_last_words,
    HierarchicalChecksumPruner,
    ChecksumBatchValidator,
    IncrementalEntropyBuilder,
)

# Smart candidate generators
from .candidate_generators import (
    SeedPhraseGenerator,
    PassphraseGenerator,
    PassphraseConfig,
    PasswordGenerator,
    PasswordConfig,
    MarkovGenerator,
    ContextualWordPredictor,
)

# Progressive verification pipeline
from .verification_pipeline import (
    ProgressiveVerificationPipeline,
    PipelineStage,
    PipelineStats,
    VerificationResult,
)

# GPU acceleration
from .gpu_accelerator import (
    GPUAccelerator,
    AcceleratorConfig,
    AccelerationBackend,
    detect_gpu_backends,
    get_cpu_info,
)

# Checkpoint system
from .checkpoint import (
    CheckpointManager,
    CheckpointState,
)

__all__ = [
    # Legacy
    "RecoveryEngine",
    "RecoveryConfig",
    "RecoveryResult",
    "RecoveryType",
    "RecoveryStatus",
    "SeedStandard",
    "RecoveryFlowOrchestrator",
    "get_bip39_wordlist",
    "validate_bip39_checksum",
    "mnemonic_to_seed",
    # Advanced Engine
    "BruteforceEngine",
    "BruteforceConfig",
    "BruteforceResult",
    "RecoveryMode",
    "SearchStrategy",
    # Address Derivation
    "AddressMatcher",
    "AddressType",
    "BloomFilter",
    "seed_to_master_key",
    "generate_address",
    "generate_addresses",
    "derive_first_address",
    "check_seed_against_targets",
    "COIN_CONFIG",
    "DERIVATION_PATHS",
    # Checksum
    "find_valid_last_words",
    "HierarchicalChecksumPruner",
    "ChecksumBatchValidator",
    "IncrementalEntropyBuilder",
    # Generators
    "SeedPhraseGenerator",
    "PassphraseGenerator",
    "PassphraseConfig",
    "PasswordGenerator",
    "PasswordConfig",
    "MarkovGenerator",
    "ContextualWordPredictor",
    # Pipeline
    "ProgressiveVerificationPipeline",
    "PipelineStage",
    "PipelineStats",
    "VerificationResult",
    # GPU
    "GPUAccelerator",
    "AcceleratorConfig",
    "AccelerationBackend",
    "detect_gpu_backends",
    "get_cpu_info",
    # Checkpoint
    "CheckpointManager",
    "CheckpointState",
]
