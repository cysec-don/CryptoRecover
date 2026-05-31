"""
CryptoRecover - Checkpoint & Resume System
============================================
Save and restore recovery progress for long-running searches.

Features:
- Periodic auto-save of recovery state
- Resume from last checkpoint after interruption
- Compact binary format for efficient storage
- Thread-safe checkpoint writing
- Compression for large checkpoint files
"""

import gzip
import json
import os
import threading
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

CHECKPOINT_VERSION = 2
CHECKPOINT_FILE_EXTENSION = ".ckpt"


@dataclass
class CheckpointState:
    """State snapshot for a recovery operation."""
    version: int = CHECKPOINT_VERSION
    timestamp: float = 0.0
    recovery_type: str = ""  # "seed_phrase", "passphrase", "password"
    total_candidates: int = 0
    candidates_tested: int = 0
    candidates_passed_checksum: int = 0
    candidates_passed_pipeline: int = 0
    time_elapsed: float = 0.0
    rate_per_second: float = 0.0
    # Seed phrase specific
    seed_length: int = 0
    known_words: List[str] = field(default_factory=list)
    missing_positions: List[int] = field(default_factory=list)
    strategy: str = ""
    # Position in candidate generation
    last_candidate_index: int = 0
    # Passphrase specific
    seed_phrase: str = ""
    partial_passphrase: str = ""
    last_passphrase_index: int = 0
    # Password specific
    wallet_file: str = ""
    last_password_index: int = 0
    # Results found so far
    found_results: List[Dict] = field(default_factory=list)
    # Configuration
    config: Dict = field(default_factory=dict)


class CheckpointManager:
    """Manages checkpoint save/restore for recovery operations.

    Supports:
    - Auto-save at configurable intervals
    - Manual save/resume
    - Compression for large checkpoints
    - Atomic writes (no corrupt checkpoints)
    - Cleanup of old checkpoints
    """

    def __init__(
        self,
        checkpoint_dir: str = "",
        auto_save_interval: float = 60.0,  # seconds
        max_checkpoints: int = 5,
        compress: bool = True,
    ):
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoint files (default: temp dir)
            auto_save_interval: Seconds between auto-saves (0 = disabled)
            max_checkpoints: Maximum checkpoint files to keep
            compress: Use gzip compression
        """
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else Path.home() / ".cryptorecover" / "checkpoints"
        self.auto_save_interval = auto_save_interval
        self.max_checkpoints = max_checkpoints
        self.compress = compress
        self._lock = threading.Lock()
        self._last_save_time = 0.0
        self._auto_save_thread: Optional[threading.Thread] = None
        self._running = False
        self._current_state: Optional[CheckpointState] = None

        # Ensure directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: CheckpointState, name: str = "recovery") -> str:
        """Save a checkpoint.

        Args:
            state: Current recovery state
            name: Checkpoint name (used in filename)

        Returns:
            Path to saved checkpoint file
        """
        with self._lock:
            state.timestamp = time.time()

            # Create filename
            timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(state.timestamp))
            filename = f"{name}_{timestamp_str}{CHECKPOINT_FILE_EXTENSION}"
            if self.compress:
                filename += ".gz"
            filepath = self.checkpoint_dir / filename

            # Serialize state
            data = asdict(state)

            # Write atomically (write to temp, then rename)
            temp_path = filepath.with_suffix(filepath.suffix + ".tmp")
            try:
                if self.compress:
                    with gzip.open(temp_path, 'wt', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                else:
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)

                # Atomic rename
                temp_path.rename(filepath)
                logger.info(f"Checkpoint saved: {filepath}")
            except Exception as e:
                logger.error(f"Failed to save checkpoint: {e}")
                if temp_path.exists():
                    temp_path.unlink()
                raise

            # Clean up old checkpoints
            self._cleanup_old_checkpoints(name)

            return str(filepath)

    def load(self, filepath: str) -> CheckpointState:
        """Load a checkpoint from file.

        Args:
            filepath: Path to checkpoint file

        Returns:
            CheckpointState with restored state
        """
        filepath = Path(filepath)

        with self._lock:
            try:
                if filepath.suffix == '.gz' or str(filepath).endswith('.ckpt.gz'):
                    with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load checkpoint: {e}")
                raise

            # Validate version
            if data.get('version', 0) > CHECKPOINT_VERSION:
                logger.warning(f"Checkpoint version {data.get('version')} is newer than supported {CHECKPOINT_VERSION}")

            state = CheckpointState(
                version=data.get('version', CHECKPOINT_VERSION),
                timestamp=data.get('timestamp', 0),
                recovery_type=data.get('recovery_type', ''),
                total_candidates=data.get('total_candidates', 0),
                candidates_tested=data.get('candidates_tested', 0),
                candidates_passed_checksum=data.get('candidates_passed_checksum', 0),
                candidates_passed_pipeline=data.get('candidates_passed_pipeline', 0),
                time_elapsed=data.get('time_elapsed', 0),
                rate_per_second=data.get('rate_per_second', 0),
                seed_length=data.get('seed_length', 0),
                known_words=data.get('known_words', []),
                missing_positions=data.get('missing_positions', []),
                strategy=data.get('strategy', ''),
                last_candidate_index=data.get('last_candidate_index', 0),
                seed_phrase=data.get('seed_phrase', ''),
                partial_passphrase=data.get('partial_passphrase', ''),
                last_passphrase_index=data.get('last_passphrase_index', 0),
                wallet_file=data.get('wallet_file', ''),
                last_password_index=data.get('last_password_index', 0),
                found_results=data.get('found_results', []),
                config=data.get('config', {}),
            )

            logger.info(f"Checkpoint loaded: {filepath} "
                       f"(tested {state.candidates_tested}/{state.total_candidates})")
            return state

    def list_checkpoints(self, name: str = None) -> List[Dict]:
        """List available checkpoints.

        Args:
            name: Filter by checkpoint name prefix

        Returns:
            List of dicts with checkpoint info (name, path, timestamp, size)
        """
        checkpoints = []
        for f in sorted(self.checkpoint_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if CHECKPOINT_FILE_EXTENSION in f.name:
                if name and not f.name.startswith(name):
                    continue
                try:
                    stat = f.stat()
                    checkpoints.append({
                        'name': f.name,
                        'path': str(f),
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                    })
                except OSError:
                    pass
        return checkpoints

    def get_latest_checkpoint(self, name: str = "recovery") -> Optional[str]:
        """Get the path to the latest checkpoint for a given name.

        Returns:
            Path string or None if no checkpoint exists
        """
        checkpoints = self.list_checkpoints(name)
        if checkpoints:
            return checkpoints[0]['path']
        return None

    def delete_checkpoint(self, filepath: str):
        """Delete a checkpoint file."""
        try:
            Path(filepath).unlink()
            logger.info(f"Checkpoint deleted: {filepath}")
        except OSError as e:
            logger.error(f"Failed to delete checkpoint: {e}")

    def _cleanup_old_checkpoints(self, name: str):
        """Remove old checkpoints beyond max_checkpoints."""
        checkpoints = self.list_checkpoints(name)
        while len(checkpoints) > self.max_checkpoints:
            oldest = checkpoints.pop()
            self.delete_checkpoint(oldest['path'])

    def start_auto_save(
        self,
        state_provider: callable,
        name: str = "recovery",
    ):
        """Start automatic checkpoint saving in a background thread.

        Args:
            state_provider: Callable that returns current CheckpointState
            name: Checkpoint name prefix
        """
        if self.auto_save_interval <= 0:
            return

        self._running = True
        self._current_name = name
        self._state_provider = state_provider

        def _auto_save_loop():
            while self._running:
                time.sleep(self.auto_save_interval)
                if not self._running:
                    break
                try:
                    state = self._state_provider()
                    if state:
                        self.save(state, self._current_name)
                except Exception as e:
                    logger.error(f"Auto-save failed: {e}")

        self._auto_save_thread = threading.Thread(target=_auto_save_loop, daemon=True)
        self._auto_save_thread.start()
        logger.info(f"Auto-save started (interval: {self.auto_save_interval}s)")

    def stop_auto_save(self):
        """Stop automatic checkpoint saving."""
        self._running = False
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            self._auto_save_thread.join(timeout=5)
        logger.info("Auto-save stopped")

    def should_auto_save(self) -> bool:
        """Check if enough time has passed since last auto-save."""
        if self.auto_save_interval <= 0:
            return False
        return (time.time() - self._last_save_time) >= self.auto_save_interval
