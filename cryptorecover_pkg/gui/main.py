"""
CryptoRecover - Graphical User Interface
==========================================
Cross-platform GUI built with tkinter for crypto wallet recovery.
Works on Windows, Linux, and macOS.
"""

import logging
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
from typing import Optional, Dict, Callable

# Add parent to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.recovery_engine import (
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
from wallets.wallet_database import (
    WALLETS,
    SeedType,
    LoginTech,
    list_all_wallets,
)
from utils.helpers import (
    format_time,
    format_number,
    calculate_seed_combinations,
    estimate_recovery_time,
    save_recovery_result,
    ensure_dirs,
    get_data_dir,
    get_platform,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# COLOR SCHEME
# ==============================================================================

COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_medium": "#16213e",
    "bg_light": "#0f3460",
    "accent": "#e94560",
    "accent_hover": "#ff6b6b",
    "success": "#00d084",
    "warning": "#ffb700",
    "error": "#ff3860",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0c0",
    "text_muted": "#606080",
    "input_bg": "#2a2a4a",
    "input_border": "#3a3a5a",
    "button_primary": "#e94560",
    "button_success": "#00d084",
    "button_warning": "#ffb700",
}


# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

class CryptoRecoverApp:
    """Main GUI Application"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CryptoRecover - Wallet Recovery Tool")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        # Apply dark theme
        self._setup_styles()

        # State
        self._recovery_engine: Optional[RecoveryEngine] = None
        self._recovery_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._progress_updater: Optional[str] = None

        # Build UI
        self._build_ui()

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1100 // 2)
        y = (self.root.winfo_screenheight() // 2) - (750 // 2)
        self.root.geometry(f"+{x}+{y}")

    def _setup_styles(self):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()
        style.theme_use("clam")

        # General styles
        style.configure("TFrame", background=COLORS["bg_dark"])
        style.configure("TLabel", background=COLORS["bg_dark"], foreground=COLORS["text_primary"],
                        font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"),
                        foreground=COLORS["accent"])
        style.configure("Subtitle.TLabel", font=("Segoe UI", 12),
                        foreground=COLORS["text_secondary"])
        style.configure("Success.TLabel", foreground=COLORS["success"])
        style.configure("Error.TLabel", foreground=COLORS["error"])
        style.configure("Warning.TLabel", foreground=COLORS["warning"])

        style.configure("TNotebook", background=COLORS["bg_dark"])
        style.configure("TNotebook.Tab", background=COLORS["bg_medium"],
                        foreground=COLORS["text_primary"],
                        padding=[15, 8],
                        font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                   background=[("selected", COLORS["bg_light"])],
                   foreground=[("selected", COLORS["accent"])])

        style.configure("TButton", background=COLORS["button_primary"],
                        foreground=COLORS["text_primary"],
                        font=("Segoe UI", 10, "bold"),
                        padding=[12, 6])
        style.map("TButton",
                   background=[("active", COLORS["accent_hover"])])

        style.configure("Success.TButton", background=COLORS["success"])
        style.configure("TEntry", fieldbackground=COLORS["input_bg"],
                        foreground=COLORS["text_primary"])

        style.configure("TCombobox", fieldbackground=COLORS["input_bg"],
                        foreground=COLORS["text_primary"])

        style.configure("Horizontal.TProgressbar",
                        troughcolor=COLORS["input_bg"],
                        background=COLORS["accent"])

    def _build_ui(self):
        """Build the main UI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="🔐 CryptoRecover",
                  style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="Wallet Recovery Tool v1.0",
                  style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(15, 0))

        # Notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self._build_seed_tab()
        self._build_passphrase_tab()
        self._build_password_tab()
        self._build_wallets_tab()
        self._build_settings_tab()

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var,
                  style="Subtitle.TLabel").pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(status_frame, mode="determinate", length=300)
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))

        self.attempts_var = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.attempts_var,
                  style="Subtitle.TLabel").pack(side=tk.RIGHT, padx=(10, 0))

    # ─── SEED PHRASE TAB ────────────────────────────────────────────────

    def _build_seed_tab(self):
        """Build seed phrase recovery tab"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="  Seed Phrase  ")

        # Input section
        input_frame = ttk.LabelFrame(tab, text="Seed Phrase Input", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="Enter seed phrase (use ? for unknown words):").pack(anchor=tk.W)
        self.seed_input = tk.Text(input_frame, height=3, width=80,
                                   bg=COLORS["input_bg"], fg=COLORS["text_primary"],
                                   insertbackground=COLORS["text_primary"],
                                   font=("Consolas", 11), wrap=tk.WORD)
        self.seed_input.pack(fill=tk.X, pady=5)
        self.seed_input.insert("1.0", "abandon ? ? about above absent absorb abstract absurd abuse access accident")

        # Options row
        opts_frame = ttk.Frame(input_frame)
        opts_frame.pack(fill=tk.X, pady=5)

        ttk.Label(opts_frame, text="Seed Standard:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.seed_standard_var = tk.StringVar(value="BIP39")
        seed_standard_combo = ttk.Combobox(opts_frame, textvariable=self.seed_standard_var,
                                            values=["BIP39", "Electrum", "SLIP39", "Monero"],
                                            width=12, state="readonly")
        seed_standard_combo.grid(row=0, column=1, padx=5)

        ttk.Label(opts_frame, text="Seed Length:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.seed_length_var = tk.StringVar(value="12")
        ttk.Combobox(opts_frame, textvariable=self.seed_length_var,
                      values=["12", "15", "18", "21", "24", "25"],
                      width=6, state="readonly").grid(row=0, column=3, padx=5)

        ttk.Label(opts_frame, text="Coin:").grid(row=0, column=4, sticky=tk.W, padx=5)
        self.seed_coin_var = tk.StringVar(value="BTC")
        ttk.Combobox(opts_frame, textvariable=self.seed_coin_var,
                      values=["BTC", "ETH", "LTC", "SOL", "BNB", "MATIC", "DOT", "ADA"],
                      width=6, state="readonly").grid(row=0, column=5, padx=5)

        # Target address
        addr_frame = ttk.Frame(input_frame)
        addr_frame.pack(fill=tk.X, pady=5)

        ttk.Label(addr_frame, text="Target Address (optional):").pack(side=tk.LEFT)
        self.seed_target_var = tk.StringVar()
        ttk.Entry(addr_frame, textvariable=self.seed_target_var, width=50,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Derivation path
        dpath_frame = ttk.Frame(input_frame)
        dpath_frame.pack(fill=tk.X, pady=2)

        ttk.Label(dpath_frame, text="Derivation Path (optional):").pack(side=tk.LEFT)
        self.seed_dpath_var = tk.StringVar()
        ttk.Entry(dpath_frame, textvariable=self.seed_dpath_var, width=50,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Estimate section
        est_frame = ttk.LabelFrame(tab, text="Recovery Estimate", padding=10)
        est_frame.pack(fill=tk.X, pady=(0, 10))

        self.seed_estimate_var = tk.StringVar(value="Enter a seed phrase with ? for unknown words to see estimate")
        ttk.Label(est_frame, textvariable=self.seed_estimate_var,
                  style="Subtitle.TLabel", wraplength=900).pack(fill=tk.X)

        ttk.Button(est_frame, text="Calculate Estimate",
                   command=self._calc_seed_estimate).pack(pady=5)

        # Action buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.seed_start_btn = ttk.Button(btn_frame, text="▶ Start Recovery",
                                          command=self._start_seed_recovery)
        self.seed_start_btn.pack(side=tk.LEFT, padx=5)

        self.seed_cancel_btn = ttk.Button(btn_frame, text="⏹ Cancel",
                                           command=self._cancel_recovery, state=tk.DISABLED)
        self.seed_cancel_btn.pack(side=tk.LEFT, padx=5)

        self.seed_validate_btn = ttk.Button(btn_frame, text="✓ Validate Seed",
                                             command=self._validate_seed)
        self.seed_validate_btn.pack(side=tk.LEFT, padx=5)

        # Result section
        result_frame = ttk.LabelFrame(tab, text="Result", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.seed_result_text = scrolledtext.ScrolledText(
            result_frame, height=8, bg=COLORS["input_bg"],
            fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"],
            font=("Consolas", 10), wrap=tk.WORD, state=tk.DISABLED
        )
        self.seed_result_text.pack(fill=tk.BOTH, expand=True)

    # ─── PASSPHRASE TAB ────────────────────────────────────────────────

    def _build_passphrase_tab(self):
        """Build passphrase recovery tab"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="  Passphrase  ")

        # Input section
        input_frame = ttk.LabelFrame(tab, text="Passphrase Recovery (BIP39 25th Word)", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="Complete Seed Phrase:").pack(anchor=tk.W)
        self.pass_mnemonic_input = tk.Text(input_frame, height=2, width=80,
                                            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
                                            insertbackground=COLORS["text_primary"],
                                            font=("Consolas", 11), wrap=tk.WORD)
        self.pass_mnemonic_input.pack(fill=tk.X, pady=5)

        # Target address
        ttk.Label(input_frame, text="Target Address (required for verification):").pack(anchor=tk.W)
        self.pass_target_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.pass_target_var, width=80,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).pack(fill=tk.X, pady=5)

        # Passphrase hints
        hints_frame = ttk.Frame(input_frame)
        hints_frame.pack(fill=tk.X, pady=5)

        ttk.Label(hints_frame, text="Partial Passphrase Hint:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.pass_partial_var = tk.StringVar()
        ttk.Entry(hints_frame, textvariable=self.pass_partial_var, width=30,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).grid(row=0, column=1, padx=5)

        ttk.Label(hints_frame, text="Candidates (comma-separated):").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.pass_candidates_var = tk.StringVar()
        ttk.Entry(hints_frame, textvariable=self.pass_candidates_var, width=40,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).grid(row=0, column=3, padx=5)

        # Candidates file
        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill=tk.X, pady=5)

        self.pass_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.pass_file_var, width=50,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Browse Candidates File",
                   command=lambda: self._browse_file(self.pass_file_var, [("Text files", "*.txt")])).pack(side=tk.LEFT)

        # Action buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.pass_start_btn = ttk.Button(btn_frame, text="▶ Start Passphrase Recovery",
                                          command=self._start_passphrase_recovery)
        self.pass_start_btn.pack(side=tk.LEFT, padx=5)

        self.pass_cancel_btn = ttk.Button(btn_frame, text="⏹ Cancel",
                                           command=self._cancel_recovery, state=tk.DISABLED)
        self.pass_cancel_btn.pack(side=tk.LEFT, padx=5)

        # Result section
        result_frame = ttk.LabelFrame(tab, text="Result", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.pass_result_text = scrolledtext.ScrolledText(
            result_frame, height=10, bg=COLORS["input_bg"],
            fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"],
            font=("Consolas", 10), wrap=tk.WORD, state=tk.DISABLED
        )
        self.pass_result_text.pack(fill=tk.BOTH, expand=True)

    # ─── PASSWORD TAB ───────────────────────────────────────────────────

    def _build_password_tab(self):
        """Build password recovery tab"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="  Password  ")

        # Input section
        input_frame = ttk.LabelFrame(tab, text="Password Recovery", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        # Wallet file
        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill=tk.X, pady=5)

        ttk.Label(file_frame, text="Wallet File:").pack(side=tk.LEFT)
        self.pwd_wallet_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.pwd_wallet_var, width=50,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse",
                   command=lambda: self._browse_file(self.pwd_wallet_var, [
                       ("Wallet files", "*.dat *.json *.wallet *.keys"),
                       ("All files", "*.*")
                   ])).pack(side=tk.LEFT)

        # Password candidates
        ttk.Label(input_frame, text="Password Candidates (comma-separated):").pack(anchor=tk.W, pady=(10, 0))
        self.pwd_candidates_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.pwd_candidates_var, width=80,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).pack(fill=tk.X, pady=5)

        # Dictionary file
        dict_frame = ttk.Frame(input_frame)
        dict_frame.pack(fill=tk.X, pady=5)

        ttk.Label(dict_frame, text="Password Dictionary:").pack(side=tk.LEFT)
        self.pwd_dict_var = tk.StringVar()
        ttk.Entry(dict_frame, textvariable=self.pwd_dict_var, width=50,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).pack(side=tk.LEFT, padx=5)
        ttk.Button(dict_frame, text="Browse",
                   command=lambda: self._browse_file(self.pwd_dict_var, [
                       ("Text files", "*.txt"), ("Dictionary files", "*.dict"), ("All files", "*.*")
                   ])).pack(side=tk.LEFT)

        # Action buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.pwd_start_btn = ttk.Button(btn_frame, text="▶ Start Password Recovery",
                                         command=self._start_password_recovery)
        self.pwd_start_btn.pack(side=tk.LEFT, padx=5)

        self.pwd_cancel_btn = ttk.Button(btn_frame, text="⏹ Cancel",
                                          command=self._cancel_recovery, state=tk.DISABLED)
        self.pwd_cancel_btn.pack(side=tk.LEFT, padx=5)

        # Result section
        result_frame = ttk.LabelFrame(tab, text="Result", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.pwd_result_text = scrolledtext.ScrolledText(
            result_frame, height=10, bg=COLORS["input_bg"],
            fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"],
            font=("Consolas", 10), wrap=tk.WORD, state=tk.DISABLED
        )
        self.pwd_result_text.pack(fill=tk.BOTH, expand=True)

    # ─── WALLETS DATABASE TAB ───────────────────────────────────────────

    def _build_wallets_tab(self):
        """Build wallets database browser tab"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="  Wallets DB  ")

        # Search bar
        search_frame = ttk.Frame(tab)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.wallet_search_var = tk.StringVar()
        self.wallet_search_var.trace_add("write", lambda *args: self._filter_wallets())
        ttk.Entry(search_frame, textvariable=self.wallet_search_var, width=40,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).pack(side=tk.LEFT, padx=5)

        # Coin filter
        ttk.Label(search_frame, text="Coin:").pack(side=tk.LEFT, padx=(10, 0))
        self.wallet_coin_var = tk.StringVar(value="All")
        ttk.Combobox(search_frame, textvariable=self.wallet_coin_var,
                      values=["All", "BTC", "ETH", "SOL", "ADA", "DOT", "BNB", "XMR", "LTC"],
                      width=8, state="readonly").pack(side=tk.LEFT, padx=5)

        # Treeview for wallets
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "category", "seed_type", "seed_length", "passphrase", "login_techs", "difficulty")
        self.wallet_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)

        self.wallet_tree.heading("name", text="Wallet Name")
        self.wallet_tree.heading("category", text="Category")
        self.wallet_tree.heading("seed_type", text="Seed Type")
        self.wallet_tree.heading("seed_length", text="Seed Length")
        self.wallet_tree.heading("passphrase", text="Passphrase")
        self.wallet_tree.heading("login_techs", text="Login Technologies")
        self.wallet_tree.heading("difficulty", text="Recovery Difficulty")

        self.wallet_tree.column("name", width=180)
        self.wallet_tree.column("category", width=140)
        self.wallet_tree.column("seed_type", width=80)
        self.wallet_tree.column("seed_length", width=80)
        self.wallet_tree.column("passphrase", width=80)
        self.wallet_tree.column("login_techs", width=250)
        self.wallet_tree.column("difficulty", width=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.wallet_tree.yview)
        self.wallet_tree.configure(yscrollcommand=scrollbar.set)

        self.wallet_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.wallet_tree.bind("<<TreeviewSelect>>", self._on_wallet_select)

        # Details panel
        detail_frame = ttk.LabelFrame(tab, text="Wallet Details", padding=10)
        detail_frame.pack(fill=tk.X, pady=(10, 0))

        self.wallet_detail_var = tk.StringVar(value="Select a wallet to view details")
        ttk.Label(detail_frame, textvariable=self.wallet_detail_var,
                  style="Subtitle.TLabel", wraplength=1000, justify=tk.LEFT).pack(fill=tk.X)

        # Populate treeview
        self._populate_wallet_tree()

    # ─── SETTINGS TAB ───────────────────────────────────────────────────

    def _build_settings_tab(self):
        """Build settings tab"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="  Settings  ")

        # External tools
        tools_frame = ttk.LabelFrame(tab, text="External Recovery Tools", padding=10)
        tools_frame.pack(fill=tk.X, pady=(0, 10))

        # btcrecover.py
        ttk.Label(tools_frame, text="btcrecover.py path:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.btcrecover_var = tk.StringVar()
        ttk.Entry(tools_frame, textvariable=self.btcrecover_var, width=50,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).grid(row=0, column=1, padx=5)
        ttk.Button(tools_frame, text="Browse",
                   command=lambda: self._browse_file(self.btcrecover_var, [("Python files", "*.py")])).grid(row=0, column=2)

        # seedrecover.py
        ttk.Label(tools_frame, text="seedrecover.py path:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.seedrecover_var = tk.StringVar()
        ttk.Entry(tools_frame, textvariable=self.seedrecover_var, width=50,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).grid(row=1, column=1, padx=5)
        ttk.Button(tools_frame, text="Browse",
                   command=lambda: self._browse_file(self.seedrecover_var, [("Python files", "*.py")])).grid(row=1, column=2)

        # bitcoin-cli
        ttk.Label(tools_frame, text="bitcoin-cli path:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.bitcoin_core_var = tk.StringVar()
        ttk.Entry(tools_frame, textvariable=self.bitcoin_core_var, width=50,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).grid(row=2, column=1, padx=5)
        ttk.Button(tools_frame, text="Browse",
                   command=lambda: self._browse_file(self.bitcoin_core_var, [("All files", "*.*")])).grid(row=2, column=2)

        # Auto-detect button
        ttk.Button(tools_frame, text="Auto-Detect Tools",
                   command=self._auto_detect_tools).grid(row=3, column=0, columnspan=3, pady=10)

        # Performance settings
        perf_frame = ttk.LabelFrame(tab, text="Performance", padding=10)
        perf_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(perf_frame, text="Number of Threads (0 = auto):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.threads_var = tk.StringVar(value="0")
        ttk.Entry(perf_frame, textvariable=self.threads_var, width=10,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).grid(row=0, column=1, padx=5)

        # Save results
        save_frame = ttk.LabelFrame(tab, text="Output", padding=10)
        save_frame.pack(fill=tk.X, pady=(0, 10))

        self.save_results_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(save_frame, text="Save recovery results automatically",
                        variable=self.save_results_var).pack(anchor=tk.W)

        ttk.Label(save_frame, text="Output Directory:").pack(anchor=tk.W, pady=(10, 0))
        self.output_dir_var = tk.StringVar(value=str(get_data_dir()))
        ttk.Entry(save_frame, textvariable=self.output_dir_var, width=50,
                  bg=COLORS["input_bg"], fg=COLORS["text_primary"]).pack(fill=tk.X, pady=5)

        # About
        about_frame = ttk.LabelFrame(tab, text="About", padding=10)
        about_frame.pack(fill=tk.X, pady=(0, 10))

        about_text = (
            "CryptoRecover v1.0.0\n\n"
            "A comprehensive cryptocurrency wallet recovery tool.\n"
            "Supports seed phrase, passphrase, and password recovery\n"
            "for 50+ wallets across all major blockchains.\n\n"
            "Integrates with btcrecover.py, seedrecover.py, and bitcoin-core\n"
            "for advanced recovery capabilities.\n\n"
            "⚠ WARNING: Only use this tool to recover YOUR OWN wallets.\n"
            "Unauthorized access to others' wallets is illegal."
        )
        ttk.Label(about_frame, text=about_text, justify=tk.LEFT,
                  wraplength=800).pack(fill=tk.X)

    # ─── HELPER METHODS ─────────────────────────────────────────────────

    def _browse_file(self, var: tk.StringVar, filetypes=None):
        """Open file browser dialog"""
        path = filedialog.askopenfilename(filetypes=filetypes or [("All files", "*.*")])
        if path:
            var.set(path)

    def _populate_wallet_tree(self):
        """Populate the wallet treeview"""
        for item in self.wallet_tree.get_children():
            self.wallet_tree.delete(item)

        # Store all items for filtering
        self._all_wallet_items = []

        for name, wallet in WALLETS.items():
            seed_types = ", ".join(s.value for s in wallet.supported_seed_types) or "N/A"
            seed_lengths = ", ".join(str(l) for l in wallet.seed_lengths) or "N/A"
            login_techs = ", ".join(t.value for t in wallet.login_technologies[:3])
            if len(wallet.login_technologies) > 3:
                login_techs += f" +{len(wallet.login_technologies) - 3}"

            item_id = self.wallet_tree.insert("", tk.END, values=(
                wallet.name,
                ", ".join(c.value for c in wallet.category[:2]),
                seed_types,
                seed_lengths,
                "Yes" if wallet.supports_passphrase else "No",
                login_techs,
                wallet.recovery_difficulty,
            ))
            self._all_wallet_items.append(item_id)

    def _filter_wallets(self):
        """Filter wallet treeview based on search"""
        search = self.wallet_search_var.get().lower()
        coin_filter = self.wallet_coin_var.get()

        # Iterate over all stored items (including detached ones)
        for item in self._all_wallet_items:
            try:
                values = self.wallet_tree.item(item, "values")
            except tk.TclError:
                continue  # Item may have been deleted
            name = str(values[0]).lower()
            match_search = search in name or not search
            match_coin = coin_filter == "All" or coin_filter in str(values)

            if match_search and match_coin:
                try:
                    self.wallet_tree.move(item, "", tk.END)
                except tk.TclError:
                    pass
            else:
                try:
                    self.wallet_tree.detach(item)
                except tk.TclError:
                    pass

    def _on_wallet_select(self, event):
        """Handle wallet selection in treeview"""
        selection = self.wallet_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.wallet_tree.item(item, "values")
        wallet_name = str(values[0])
        # Search by name - try direct lookup first, then fuzzy match
        wallet = WALLETS.get(wallet_name)
        if not wallet:
            for key, w in WALLETS.items():
                if w.name == wallet_name or key == wallet_name:
                    wallet = w
                    break

        if wallet:
            detail = (
                f"Name: {wallet.name}\n"
                f"Category: {', '.join(c.value for c in wallet.category)}\n"
                f"Seed Types: {', '.join(s.value for s in wallet.supported_seed_types) or 'None (custodial)'}\n"
                f"Seed Lengths: {', '.join(str(l) for l in wallet.seed_lengths) or 'N/A'}\n"
                f"Passphrase: {'Yes' if wallet.supports_passphrase else 'No'}\n"
                f"Login Technologies: {', '.join(t.value for t in wallet.login_technologies)}\n"
                f"Derivation Paths: {', '.join(wallet.derivation_paths[:5])}\n"
                f"Coins: {', '.join(wallet.supported_coins[:8])}\n"
                f"Difficulty: {wallet.recovery_difficulty}\n"
                f"Wallet File: {wallet.wallet_file_format or 'N/A'}\n"
                f"Notes: {wallet.notes}"
            )
            self.wallet_detail_var.set(detail)

    def _auto_detect_tools(self):
        """Auto-detect external recovery tools"""
        from core.recovery_engine import RecoveryFlowOrchestrator
        btcrecover = RecoveryFlowOrchestrator._find_tool("btcrecover.py")
        seedrecover = RecoveryFlowOrchestrator._find_tool("seedrecover.py")
        bitcoin_cli = RecoveryFlowOrchestrator._find_tool("bitcoin-cli")

        if btcrecover:
            self.btcrecover_var.set(btcrecover)
        if seedrecover:
            self.seedrecover_var.set(seedrecover)
        if bitcoin_cli:
            self.bitcoin_core_var.set(bitcoin_cli)

        found = sum(1 for x in [btcrecover, seedrecover, bitcoin_cli] if x)
        messagebox.showinfo("Auto-Detect", f"Found {found}/3 external tools")

    def _update_result_text(self, text_widget: scrolledtext.ScrolledText, message: str):
        """Update result text widget"""
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, message)
        text_widget.configure(state=tk.DISABLED)

    # ─── RECOVERY OPERATIONS ────────────────────────────────────────────

    def _calc_seed_estimate(self):
        """Calculate and display seed recovery estimate"""
        mnemonic = self.seed_input.get("1.0", tk.END).strip()
        parts = mnemonic.split()
        missing = sum(1 for p in parts if p in ["?", "???", "*"])
        wordlist = get_bip39_wordlist()

        if missing == 0:
            self.seed_estimate_var.set("No missing words found. Use ? for unknown words.")
            return

        total = calculate_seed_combinations(missing, len(wordlist))
        self.seed_estimate_var.set(
            f"Missing words: {missing} | Total combinations: {format_number(total)} | "
            f"Estimated time: {estimate_recovery_time(total)}"
        )

    def _validate_seed(self):
        """Validate the entered seed phrase"""
        mnemonic = self.seed_input.get("1.0", tk.END).strip()
        words = mnemonic.split()

        # Replace ? with empty for validation
        clean_words = [w for w in words if w not in ["?", "???", "*"]]

        if "?" in mnemonic:
            self._update_result_text(self.seed_result_text,
                                     "Cannot validate - seed contains unknown words (?).\n"
                                     "Fill in all words first, or use recovery to find missing words.")
            return

        wordlist = get_bip39_wordlist()
        invalid = [w for w in words if w not in wordlist]

        result_text = f"Seed Phrase: {len(words)} words\n\n"

        if invalid:
            result_text += f"❌ Invalid BIP39 words found: {invalid}\n"
            result_text += "Check spelling of these words.\n"
        else:
            result_text += "✓ All words are valid BIP39 words.\n"

        if len(words) in [12, 15, 18, 21, 24]:
            is_valid = validate_bip39_checksum(words)
            result_text += f"\nBIP39 Checksum: {'✓ VALID' if is_valid else '❌ INVALID'}\n"
            if not is_valid:
                result_text += "One or more words may be incorrect or out of order.\n"
        else:
            result_text += f"\n⚠ Non-standard word count ({len(words)}).\n"
            result_text += "BIP39 standard uses 12, 15, 18, 21, or 24 words.\n"

        self._update_result_text(self.seed_result_text, result_text)

    def _start_seed_recovery(self):
        """Start seed phrase recovery in a background thread"""
        mnemonic = self.seed_input.get("1.0", tk.END).strip()
        if not mnemonic:
            messagebox.showwarning("Warning", "Please enter a seed phrase")
            return

        parts = mnemonic.split()
        known_words = []
        missing_positions = []

        for i, part in enumerate(parts):
            if part in ["?", "???", "*"]:
                missing_positions.append(i)
            else:
                known_words.append(part)

        if not missing_positions:
            messagebox.showwarning("Warning", "No missing words found. Use ? for unknown words.")
            return

        config = RecoveryConfig(
            recovery_type=RecoveryType.SEED_PHRASE,
            seed_standard=SeedStandard(self.seed_standard_var.get()),
            seed_length=int(self.seed_length_var.get()),
            known_words=known_words,
            missing_word_positions=missing_positions,
            target_address=self.seed_target_var.get() or None,
            derivation_path=self.seed_dpath_var.get() or None,
            coin=self.seed_coin_var.get(),
            num_threads=int(self.threads_var.get()) if self.threads_var.get().isdigit() else 0,
            btcrecover_path=self.btcrecover_var.get() or None,
            seedrecover_path=self.seedrecover_var.get() or None,
            bitcoin_core_path=self.bitcoin_core_var.get() or None,
            callback=self._gui_progress_callback,
        )

        self._run_recovery(config, self.seed_result_text,
                           self.seed_start_btn, self.seed_cancel_btn)

    def _start_passphrase_recovery(self):
        """Start passphrase recovery in a background thread"""
        mnemonic = self.pass_mnemonic_input.get("1.0", tk.END).strip()
        if not mnemonic:
            messagebox.showwarning("Warning", "Please enter a seed phrase")
            return

        target = self.pass_target_var.get()
        if not target:
            messagebox.showwarning("Warning", "Target address is required for passphrase recovery")
            return

        candidates = []
        if self.pass_candidates_var.get():
            candidates = [c.strip() for c in self.pass_candidates_var.get().split(",")]

        config = RecoveryConfig(
            recovery_type=RecoveryType.PASSPHRASE,
            known_words=mnemonic.split(),
            passphrase_candidates=candidates,
            partial_passphrase=self.pass_partial_var.get() or "",
            target_address=target,
            seedrecover_path=self.seedrecover_var.get() or None,
            bitcoin_core_path=self.bitcoin_core_var.get() or None,
            num_threads=int(self.threads_var.get()) if self.threads_var.get().isdigit() else 0,
            callback=self._gui_progress_callback,
        )

        self._run_recovery(config, self.pass_result_text,
                           self.pass_start_btn, self.pass_cancel_btn)

    def _start_password_recovery(self):
        """Start password recovery in a background thread"""
        wallet_file = self.pwd_wallet_var.get()
        if not wallet_file:
            messagebox.showwarning("Warning", "Please select a wallet file")
            return

        if not os.path.isfile(wallet_file):
            messagebox.showerror("Error", f"Wallet file not found: {wallet_file}")
            return

        candidates = []
        if self.pwd_candidates_var.get():
            candidates = [c.strip() for c in self.pwd_candidates_var.get().split(",")]

        config = RecoveryConfig(
            recovery_type=RecoveryType.PASSWORD,
            wallet_file=wallet_file,
            password_candidates=candidates,
            password_dict_file=self.pwd_dict_var.get() or None,
            btcrecover_path=self.btcrecover_var.get() or None,
            num_threads=int(self.threads_var.get()) if self.threads_var.get().isdigit() else 0,
            callback=self._gui_progress_callback,
        )

        self._run_recovery(config, self.pwd_result_text,
                           self.pwd_start_btn, self.pwd_cancel_btn)

    def _run_recovery(self, config: RecoveryConfig, result_widget, start_btn, cancel_btn):
        """Run recovery in a background thread"""
        self._is_running = True
        start_btn.configure(state=tk.DISABLED)
        cancel_btn.configure(state=tk.NORMAL)
        self.status_var.set("Recovery in progress...")
        self.progress_bar["value"] = 0

        def recovery_thread():
            engine = RecoveryEngine(config)
            self._recovery_engine = engine

            # Use the engine directly instead of creating a new one via Orchestrator
            if config.recovery_type == RecoveryType.SEED_PHRASE:
                result = engine.recover_seed_phrase()
            elif config.recovery_type == RecoveryType.PASSPHRASE:
                result = engine.recover_passphrase()
            elif config.recovery_type == RecoveryType.PASSWORD:
                result = engine.recover_password()
            else:
                result = RecoveryResult(
                    success=False,
                    recovery_type=config.recovery_type,
                    status=RecoveryStatus.ERROR,
                    error_message=f"Unsupported recovery type: {config.recovery_type}"
                )

            # Update GUI from main thread
            self.root.after(0, lambda: self._on_recovery_complete(result, result_widget, start_btn, cancel_btn))

        self._recovery_thread = threading.Thread(target=recovery_thread, daemon=True)
        self._recovery_thread.start()

        # Start progress update loop
        self._update_progress()

    def _cancel_recovery(self):
        """Cancel the running recovery"""
        if self._recovery_engine:
            self._recovery_engine.cancel()
        self._is_running = False
        self.status_var.set("Recovery cancelled")

    def _gui_progress_callback(self, progress: dict):
        """Progress callback that stores data for GUI update"""
        self._progress_updater = progress

    def _update_progress(self):
        """Periodic GUI progress update"""
        if not self._is_running:
            return

        if self._recovery_engine:
            progress = self._recovery_engine.get_progress()
            self.attempts_var.set(
                f"Attempts: {format_number(progress['attempts'])} | "
                f"Speed: {progress['attempts_per_second']:.0f}/s"
            )
            self.status_var.set(f"Running - {format_time(progress['time_elapsed'])} elapsed")

        self.root.after(500, self._update_progress)

    def _on_recovery_complete(self, result: RecoveryResult, result_widget, start_btn, cancel_btn):
        """Handle recovery completion"""
        self._is_running = False
        start_btn.configure(state=tk.NORMAL)
        cancel_btn.configure(state=tk.DISABLED)

        if result.success:
            self.status_var.set("✓ Recovery Successful!")
            self.progress_bar["value"] = 100

            output = (
                "═══════════════════════════════════════════════\n"
                "           RECOVERY SUCCESSFUL!\n"
                "═══════════════════════════════════════════════\n\n"
                f"  Found: {result.found_value}\n\n"
                f"  Type: {result.recovery_type.value}\n"
                f"  Attempts: {format_number(result.attempts)}\n"
                f"  Time: {format_time(result.time_elapsed)}\n"
                f"  Speed: {result.attempts_per_second:.1f} attempts/sec\n"
            )

            if result.details:
                output += "\n  Details:\n"
                for k, v in result.details.items():
                    output += f"    {k}: {v}\n"

            output += "\n  ⚠ IMPORTANT: Save this information securely!\n"

        else:
            self.status_var.set("✗ Recovery Failed")
            self.progress_bar["value"] = 0

            output = (
                "═══════════════════════════════════════════════\n"
                "           RECOVERY FAILED\n"
                "═══════════════════════════════════════════════\n\n"
                f"  Status: {result.status.value}\n"
                f"  Error: {result.error_message or 'Unknown'}\n"
                f"  Attempts: {format_number(result.attempts)}\n"
                f"  Time: {format_time(result.time_elapsed)}\n\n"
                "  Suggestions:\n"
                "  - Try different candidates or constraints\n"
                "  - Install btcrecover.py for advanced recovery\n"
                "  - Install seedrecover.py for seed phrase recovery\n"
                "  - Check if you have the correct wallet type\n"
            )

        self._update_result_text(result_widget, output)

        if self.save_results_var.get():
            path = save_recovery_result(result)
            self.status_var.set(f"Result saved to: {path}")

    # ─── RUN ────────────────────────────────────────────────────────────

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main():
    """GUI entry point"""
    ensure_dirs()
    app = CryptoRecoverApp()
    app.run()


if __name__ == "__main__":
    main()
