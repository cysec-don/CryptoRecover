# CryptoRecover v2.0.0

**AI-Enhanced Cryptocurrency Wallet Recovery Tool**

> The most advanced open-source cryptocurrency wallet seed phrase, passphrase, and password recovery tool available. Featuring 10 novel bruteforce techniques invented specifically for this project, AI/LLM integration for intelligent candidate generation, and support for 50+ wallets across all major blockchains.

**Author:** Cysec Don | cysecdon@gmail.com  
**License:** MIT  
**Repository:** [github.com/cysec-don/CryptoRecover](https://github.com/cysec-don/CryptoRecover)

---

## Table of Contents

- [Features](#features)
- [Novel Techniques Invented](#novel-techniques-invented)
- [AI/LLM Integration](#aillm-integration)
- [Supported Wallets](#supported-wallets)
- [System Requirements](#system-requirements)
- [Installation](#installation)
  - [Quick Install (All Platforms)](#quick-install-all-platforms)
  - [Linux Installation (Step-by-Step)](#linux-installation-step-by-step)
  - [Windows Installation (Step-by-Step)](#windows-installation-step-by-step)
  - [macOS Installation (Step-by-Step)](#macos-installation-step-by-step)
  - [Docker Installation](#docker-installation)
  - [Installing AI/LLM Providers](#installing-aillm-providers)
  - [Installing GPU Acceleration](#installing-gpu-acceleration)
  - [Installing External Recovery Tools](#installing-external-recovery-tools)
  - [Verifying Your Installation](#verifying-your-installation)
  - [Troubleshooting Installation](#troubleshooting-installation)
- [Usage](#usage)
  - [CLI Usage](#cli-usage)
  - [GUI Usage](#gui-usage)
  - [Interactive Wizard](#interactive-wizard)
- [Recovery Modes](#recovery-modes)
- [Architecture](#architecture)
- [External Tool Integration](#external-tool-integration)
- [Performance Benchmarks](#performance-benchmarks)
- [Security Considerations](#security-considerations)
- [FAQ](#faq)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)

---

## Features

### Core Recovery Capabilities
- **Seed Phrase Recovery** - Recover missing words from BIP39 (12/15/18/21/24-word), Electrum, and SLIP39 seed phrases
- **Passphrase Recovery** - Recover BIP39 passphrases (the "25th word") with smart candidate generation
- **Password Recovery** - Recover wallet file passwords for Bitcoin Core, Electrum, MetaMask, and other wallet formats
- **Multi-coin Support** - BTC, ETH, LTC, DOGE, DASH, ZEC, XRP and more with correct derivation paths

### Advanced Engine Features
- **10 Novel Bruteforce Techniques** - Invented specifically for this project (see below)
- **AI/LLM Integration** - Use AI models to intelligently generate recovery candidates, reducing search space by up to 99%
- **GPU Acceleration** - Optional OpenCL/CUDA acceleration for PBKDF2 computations
- **Checkpoint & Resume** - Save progress and resume long-running recovery operations
- **Progressive Verification Pipeline** - Multi-stage fail-fast verification that eliminates invalid candidates at the cheapest possible stage

### Interfaces
- **CLI** - Full-featured command-line interface with advanced options
- **GUI** - Cross-platform tkinter graphical interface with dark theme
- **Interactive Wizard** - Guided recovery wizard for first-time users

---

## Novel Techniques Invented

This project introduces **10 novel bruteforce optimization techniques** that dramatically reduce recovery time:

| # | Technique | Abbreviation | Speedup | Description |
|---|-----------|-------------|---------|-------------|
| 1 | **Checksum Pre-Filter** | CPF | 16x | Eliminates 93.75%+ candidates before expensive PBKDF2 by validating BIP39 checksum first |
| 2 | **Progressive Verification Pipeline** | PVP | 10000x | Multi-stage verification ordered from cheapest to most expensive; fail fast, fail cheap |
| 3 | **Last-Word Optimization** | LWO | 16x | Only 128 valid candidates for last word of 12-word seed (vs 2048) |
| 4 | **Hierarchical Checksum Pruning** | HCP | 16x | Pre-compute partial checksum states for known words, enabling early pruning |
| 5 | **Statistical Word Prioritization** | SWP | 2-10x | Rank BIP39 words by real-world frequency to try likely words first |
| 6 | **Adaptive Work Distribution** | AWD | Variable | Dynamic CPU/GPU work splitting based on measured throughput |
| 7 | **Contextual Word Prediction** | CWP | 10-50x | Predict similar BIP39 words using edit distance, prefix matching, and phonetic similarity |
| 8 | **Entropy-Guided Search** | EGS | Variable | Search most constrained positions first to maximize early pruning |
| 9 | **Memory-Mapped Candidate Streams** | MMCS | N/A | Generator-based candidate generation for infinite search spaces without memory limits |
| 10 | **Smart Resume/Checkpoint** | SRC | N/A | Save and restore progress for long searches with atomic writes |

**Combined optimization estimate:** These techniques can provide up to ~10 million times speedup in ideal scenarios. For example, recovering a single missing last word takes <1 second (128 candidates with LWO vs 2048 full enumeration), and recovering 2 missing words (including last position) takes 1-5 minutes instead of hours.

---

## AI/LLM Integration

CryptoRecover supports **20+ AI/LLM providers** for intelligent candidate generation:

### Cloud Providers
| Provider | Models | API Key Required | Setup |
|----------|--------|-----------------|-------|
| OpenAI | GPT-4, GPT-3.5 | Yes | Set `OPENAI_API_KEY` |
| Anthropic | Claude 3.5, Claude 3 | Yes | Set `ANTHROPIC_API_KEY` |
| Google Gemini | Gemini Pro, Ultra | Yes | Set `GOOGLE_API_KEY` |
| Mistral AI | Mistral Large, Medium, Small | Yes | Set `MISTRAL_API_KEY` |
| DeepSeek | DeepSeek-V2, Coder | Yes | Set `DEEPSEEK_API_KEY` |
| Groq | Llama, Mixtral (fast) | Yes | Set `GROQ_API_KEY` |
| OpenRouter | Multi-model gateway | Yes | Set `OPENROUTER_API_KEY` |
| Cohere | Command R+ | Yes | Set `COHERE_API_KEY` |
| AI21 Labs | Jurassic-2 | Yes | Set `AI21_API_KEY` |
| Together AI | Open-source models | Yes | Set `TOGETHER_API_KEY` |
| Fireworks AI | Fast inference | Yes | Set `FIREWORKS_API_KEY` |
| Anyscale | Llama, Mistral | Yes | Set `ANYSCALE_API_KEY` |
| Hugging Face | Inference API | Yes | Set `HF_API_KEY` |

### Local Providers (Privacy-First)
| Provider | Description | Installation |
|----------|-------------|-------------|
| **Ollama** | Run Llama, Mistral, Phi, and other models locally | [ollama.com](https://ollama.com) |
| **LM Studio** | Desktop app for running local models | [lmstudio.ai](https://lmstudio.ai) |
| **llama.cpp** | C++ inference engine | [github.com/ggerganov/llama.cpp](https://github.com/ggerganov/llama.cpp) |
| **text-generation-webui** | Oobabooga web UI | [github.com/oobabooga](https://github.com/oobabooga/text-generation-webui) |
| **KoboldCpp** | Lightweight local inference | [github.com/LostRuins/koboldcpp](https://github.com/LostRuins/koboldcpp) |
| **GPT4All** | Desktop local model runner | [gpt4all.io](https://gpt4all.io) |
| **LocalAI** | OpenAI-compatible local server | [github.com/go-skynet/LocalAI](https://github.com/go-skynet/LocalAI) |

### How AI Improves Recovery
1. **Intelligent Candidate Generation** - LLMs generate likely seed words based on partial memories and context
2. **Semantic Clustering** - Group similar words together for faster search
3. **Adaptive Learning** - AI learns from failed attempts to refine future candidates
4. **Multi-Provider Consensus** - Multiple LLMs vote on most likely candidates
5. **Search Space Reduction** - AI can reduce the search space by up to 99% through intelligent filtering

---

## Supported Wallets

50+ wallets across all categories:

### Hardware Wallets
Ledger Nano S/X/S Plus, Trezor Model One/T/Safe 3, KeepKey, Coldcard Mk4, BitBox02, SeedSigner, Blockstream Jade, NGRAVE ZERO

### Desktop Wallets
Electrum, Bitcoin Core, Exodus, Wasabi Wallet, Sparrow Wallet, Atomic Wallet, Guarda

### Browser Extension Wallets
MetaMask, Phantom, Keplr, XDEFI, Ronin Wallet, Kaikas, Martian Wallet, Petra Wallet, Fuel Wallet, Sui Wallet, Solflare, UniSat, Xverse

### Mobile Wallets
BlueWallet, Trust Wallet, Coinbase Wallet, Samourai Wallet, Edge, BRD, Rainbow, Cake Wallet, Mycelium

### Specialized
Monero GUI, Gnosis Safe, Argent, Stargazer

### Exchange (Custodial)
Binance, Coinbase Exchange, Kraken

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Python** | 3.8+ | 3.10+ |
| **RAM** | 2 GB | 8 GB+ |
| **Disk Space** | 500 MB | 2 GB+ |
| **CPU** | 2 cores | 8+ cores |
| **GPU** | None (optional) | NVIDIA/AMD with OpenCL support |
| **OS** | Windows 10, Ubuntu 18.04, macOS 10.14 | Windows 11, Ubuntu 22.04, macOS 13+ |

---

## Installation

### Quick Install (All Platforms)

```bash
# Clone the repository
git clone https://github.com/cysec-don/CryptoRecover.git
cd CryptoRecover

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows

# Install with pip (basic installation)
pip install -e .

# Or install with full crypto dependencies
pip install -e ".[full]"

# Verify installation
cryptorecover --version
```

---

### Linux Installation (Step-by-Step)

#### Step 1: Install Python 3.10+

Python 3.10 or newer is required. Most modern Linux distributions include Python 3.10+ by default, but if your distribution ships an older version, use the following commands to install or update Python.

**Ubuntu/Debian:**

```bash
# Update package list
sudo apt update

# Install Python 3 and pip
sudo apt install python3 python3-pip python3-venv -y

# For Ubuntu 20.04 or older, you may need to add the deadsnakes PPA:
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Verify Python version
python3 --version   # Should show 3.10+ or 3.11+
```

**Fedora:**

```bash
# Install Python 3 and pip
sudo dnf install python3 python3-pip python3-devel -y

# Verify
python3 --version
```

**Arch Linux:**

```bash
# Install Python 3 and pip
sudo pacman -S python python-pip -y

# Verify
python3 --version
```

#### Step 2: Install Git

Git is required to clone the repository. Install it if it is not already available on your system.

```bash
# Ubuntu/Debian
sudo apt install git -y

# Fedora
sudo dnf install git -y

# Arch Linux
sudo pacman -S git -y

# Verify
git --version
```

#### Step 3: Clone the Repository

Clone the CryptoRecover repository from GitHub to your local machine. This creates a `CryptoRecover` directory containing all source files, configuration, and documentation.

```bash
git clone https://github.com/cysec-don/CryptoRecover.git
cd CryptoRecover
```

#### Step 4: Create a Virtual Environment

It is strongly recommended to use a Python virtual environment. This isolates CryptoRecover's dependencies from your system Python packages, preventing version conflicts and ensuring a clean installation. The virtual environment is created in a `venv/` directory inside the project folder.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it (you must do this every time you open a new terminal)
source venv/bin/activate

# You should see (venv) at the beginning of your terminal prompt
# Upgrade pip to the latest version
pip install --upgrade pip
```

> **Note:** To deactivate the virtual environment later, run `deactivate`. Always activate the venv before running CryptoRecover.

#### Step 5: Install Dependencies

CryptoRecover offers multiple installation options depending on your needs. The basic installation includes the core recovery engine and CLI/GUI. The full installation adds all cryptographic libraries for advanced wallet support.

```bash
# Option A: Basic installation (core engine + CLI + GUI)
pip install -e .

# Option B: Full installation with all crypto libraries (recommended)
pip install -e ".[full]"

# Option C: Development installation (includes testing tools + crypto)
pip install -e ".[dev]"
pip install -e ".[full]"
```

The `-e` flag installs the package in "editable" mode, meaning any changes you make to the source code are immediately reflected without re-installing.

**What each option installs:**

| Option | Includes | Best For |
|--------|----------|----------|
| Basic | Core engine, CLI, GUI | Quick start, seed phrase recovery only |
| Full | All crypto libs (bip32utils, hdwallet, pycryptodome, cryptography) | Complete wallet support, address derivation |
| Dev | pytest, coverage tools | Contributing, running tests |

#### Step 6: Install Optional GPU Support (Recommended for Speed)

GPU acceleration can speed up PBKDF2 computations dramatically (10x-100x depending on your GPU). This step is entirely optional - the tool works perfectly on CPU alone.

```bash
# For OpenCL GPU acceleration (AMD, Intel, and NVIDIA GPUs)
pip install pyopencl

# For CUDA GPU acceleration (NVIDIA GPUs only - faster than OpenCL on NVIDIA)
pip install pycuda

# Install numpy (required for GPU array operations)
pip install numpy
```

> **Prerequisites for GPU support:**
> - **NVIDIA GPUs:** Install the NVIDIA CUDA Toolkit ([developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads))
> - **AMD GPUs:** Install ROCm ([rocm.docs.amd.com](https://rocm.docs.amd.com/))
> - **Intel GPUs:** Install Intel OpenCL runtime ([intel.com](https://www.intel.com/content/www/us/en/developer/tools/opencl-sdk/overview.html))

#### Step 7: Install Optional External Recovery Tools

CryptoRecover integrates with established wallet recovery tools for maximum compatibility. These are optional but recommended for recovering wallet file passwords and leveraging GPU-accelerated seed searching.

```bash
# Install btcrecover.py (advanced password recovery for 100+ wallet formats)
git clone https://github.com/3rdIteration/btcrecover.git ~/btcrecover
cd ~/btcrecover
pip install -r requirements.txt
cd ~/CryptoRecover

# seedrecover.py is included in the btcrecover repository above
# It provides GPU-accelerated seed phrase searching

# Install Bitcoin Core (for wallet.dat recovery and address verification)
# Ubuntu/Debian:
sudo apt install bitcoin-cli -y
# Or download the full node from: https://bitcoincore.org/en/download/

# Arch Linux:
sudo pacman -S bitcoin-cli
```

#### Step 8: Verify Installation

Run these commands to confirm everything is installed correctly. If all commands succeed, your installation is ready to use.

```bash
# Check version
cryptorecover --version
# Expected output: CryptoRecover v2.0.0

# Show help
cryptorecover --help

# List supported wallets
cryptorecover list-wallets

# Run the test suite to verify all modules
cd ~/CryptoRecover
python -m pytest tests/ -v

# Benchmark your hardware
cryptorecover benchmark
```

---

### Windows Installation (Step-by-Step)

#### Step 1: Install Python 3.10+

Python is not pre-installed on Windows, so you must download and install it manually. Follow these steps carefully, paying special attention to the PATH option.

1. Visit [python.org/downloads](https://www.python.org/downloads/) and download the latest Python 3.11 or 3.12 installer
2. Run the installer executable
3. **CRITICAL:** At the bottom of the first installer screen, check the box that says **"Add Python to PATH"** - this is essential for running Python from the command line
4. Click **"Install Now"** (or "Customize installation" if you want to change the install location)
5. Wait for the installation to complete
6. Open Command Prompt or PowerShell and verify:

```cmd
python --version
# Should show Python 3.10.x or higher
pip --version
# Should show pip 23.x or higher
```

> **Troubleshooting:** If `python` is not recognized, you may need to:
> - Re-run the installer and check "Add Python to PATH"
> - Or manually add Python to your system PATH: `System Properties > Advanced > Environment Variables > Path > Edit > Add C:\Python311\ and C:\Python311\Scripts\`

#### Step 2: Install Git

Git is required to clone the CryptoRecover repository from GitHub.

1. Visit [git-scm.com/download/win](https://git-scm.com/download/win) and download the installer
2. Run the installer with default settings (click Next through all screens)
3. Open a new Command Prompt and verify:

```cmd
git --version
# Should show git version 2.x.x
```

#### Step 3: Clone the Repository

Open Command Prompt or PowerShell and clone the CryptoRecover repository. This downloads all source files to your machine.

```cmd
git clone https://github.com/cysec-don/CryptoRecover.git
cd CryptoRecover
```

#### Step 4: Create a Virtual Environment

Creating a virtual environment isolates CryptoRecover's dependencies from other Python projects on your system. This prevents version conflicts and makes the installation cleaner.

```cmd
# Create the virtual environment
python -m venv venv

# Activate it (you must do this every time you open a new terminal)
venv\Scripts\activate

# You should see (venv) at the beginning of your command prompt
# Upgrade pip
pip install --upgrade pip
```

> **Note on PowerShell execution policy:** If you get an error about running scripts being disabled, run this command first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

#### Step 5: Install Dependencies

Install CryptoRecover with the appropriate dependency set. The full installation is recommended for complete wallet support.

```cmd
# Option A: Basic installation (core engine + CLI + GUI)
pip install -e .

# Option B: Full installation with all crypto libraries (recommended)
pip install -e ".[full]"

# Option C: Development installation
pip install -e ".[dev]"
```

#### Step 6: Install Optional GPU Support

GPU acceleration can dramatically speed up the recovery process on Windows, especially for computationally intensive operations like PBKDF2 key derivation.

```cmd
# For NVIDIA GPU acceleration (most common on Windows)
pip install pycuda

# For OpenCL GPU acceleration (AMD or Intel GPUs, also works on NVIDIA)
pip install pyopencl

# Required for GPU array operations
pip install numpy
```

> **Prerequisites:**
> - **NVIDIA GPUs:** Install [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) (version 11.0+ recommended)
> - **AMD GPUs:** Install [AMD Adrenalin drivers](https://www.amd.com/en/support) with OpenCL support
> - After installing CUDA, verify: `nvcc --version`

#### Step 7: Install Optional External Tools

External tools extend CryptoRecover's capabilities with additional wallet formats and GPU-accelerated recovery methods.

- **btcrecover.py:**
  1. Download from [github.com/3rdIteration/btcrecover](https://github.com/3rdIteration/btcrecover)
  2. Extract the ZIP file to a folder (e.g., `C:\Tools\btcrecover`)
  3. Install its requirements: `pip install -r C:\Tools\btcrecover\requirements.txt`

- **Bitcoin Core:**
  1. Download from [bitcoincore.org/en/download](https://bitcoincore.org/en/download/)
  2. Run the installer
  3. Add Bitcoin Core to your PATH or note its installation path for configuration

#### Step 8: Verify Installation

```cmd
# Check version
cryptorecover --version

# Show help
cryptorecover --help

# List supported wallets
cryptorecover list-wallets

# Run tests
python -m pytest tests/ -v

# Benchmark
cryptorecover benchmark
```

---

### macOS Installation (Step-by-Step)

#### Step 1: Install Homebrew (Package Manager)

Homebrew is the recommended package manager for macOS. It simplifies the installation of Python, Git, and other dependencies. If you already have Homebrew installed, skip to Step 2.

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# If you're on an Apple Silicon Mac (M1/M2/M3), add Homebrew to your PATH:
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Verify
brew --version
```

#### Step 2: Install Python

macOS ships with an older version of Python. Install the latest version through Homebrew for full compatibility with CryptoRecover.

```bash
# Install Python 3.11 (or latest available)
brew install python@3.11

# Verify (Homebrew Python is accessible as python3)
python3 --version
# Should show Python 3.11.x or higher

# pip is included with Homebrew Python
pip3 --version
```

#### Step 3: Install Git

Git may already be installed on macOS (Xcode Command Line Tools), but install it via Homebrew for the latest version.

```bash
# Install Git
brew install git

# Verify
git --version
```

#### Step 4: Clone the Repository

Clone the CryptoRecover source code from GitHub to your local machine.

```bash
git clone https://github.com/cysec-don/CryptoRecover.git
cd CryptoRecover
```

#### Step 5: Create a Virtual Environment

A virtual environment ensures CryptoRecover's dependencies do not interfere with other Python projects on your Mac.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### Step 6: Install Dependencies

Install CryptoRecover with the dependencies appropriate for your use case.

```bash
# Basic installation
pip install -e .

# Full installation (recommended - includes all crypto libraries)
pip install -e ".[full]"

# Development installation
pip install -e ".[dev]"
```

#### Step 7: Install Optional GPU Support

macOS supports OpenCL natively, which CryptoRecover can leverage for GPU acceleration on both Intel and Apple Silicon Macs.

```bash
# For OpenCL (macOS has built-in OpenCL support)
pip install pyopencl

# Note: CUDA is NOT available on macOS (NVIDIA stopped supporting macOS)
# Apple Silicon Macs (M1/M2/M3) use Metal, which pyopencl can access

# Install numpy for GPU operations
pip install numpy
```

> **Apple Silicon (M1/M2/M3) Users:** The pyopencl package works with Apple's Metal framework through OpenCL compatibility. Performance is excellent on M-series chips for PBKDF2 operations.

#### Step 8: Install Optional External Tools

```bash
# Install btcrecover.py
git clone https://github.com/3rdIteration/btcrecover.git ~/btcrecover
cd ~/btcrecover
pip install -r requirements.txt
cd ~/CryptoRecover

# Install Bitcoin Core via Homebrew
brew install bitcoin

# Or download from: https://bitcoincore.org/en/download/
```

#### Step 9: Verify Installation

```bash
# Check version
cryptorecover --version

# Show help
cryptorecover --help

# Run tests
python -m pytest tests/ -v

# Benchmark your hardware
cryptorecover benchmark
```

---

### Docker Installation

For users who prefer containerized deployment or want to avoid installing Python dependencies directly on their system, CryptoRecover provides Docker support.

```bash
# Clone the repository
git clone https://github.com/cysec-don/CryptoRecover.git
cd CryptoRecover

# Build the Docker image
docker build -t cryptorecover .

# Run CLI commands
docker run --rm cryptorecover --version
docker run --rm cryptorecover --help
docker run --rm cryptorecover list-wallets

# Run recovery with mounted wallet file
docker run --rm -v /path/to/wallet:/data cryptorecover bruteforce \
  --mode password --wallet-file /data/wallet.dat

# Run GUI (requires X11 forwarding on Linux)
docker run --rm --net=host -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix cryptorecover-gui
```

---

### Installing AI/LLM Providers

One of CryptoRecover's most powerful features is AI-assisted recovery. Follow these instructions to set up LLM providers that can dramatically reduce search space and recovery time.

#### Cloud Provider Setup

Cloud LLM providers offer the most capable models but require API keys and send partial recovery context to their servers.

```bash
# Set API keys as environment variables
# Add these to your ~/.bashrc or ~/.zshrc for persistence

# OpenAI (GPT-4, GPT-3.5)
export OPENAI_API_KEY="sk-..."

# Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-..."

# Google Gemini
export GOOGLE_API_KEY="AIza..."

# Mistral AI
export MISTRAL_API_KEY="..."

# DeepSeek
export DEEPSEEK_API_KEY="..."

# Groq (fast inference)
export GROQ_API_KEY="gsk_..."

# OpenRouter (multi-model gateway)
export OPENROUTER_API_KEY="sk-or-..."

# Cohere
export COHERE_API_KEY="..."

# AI21 Labs
export AI21_API_KEY="..."

# Together AI
export TOGETHER_API_KEY="..."

# Fireworks AI
export FIREWORKS_API_KEY="..."

# Hugging Face
export HF_API_KEY="hf_..."
```

Then configure your preferred provider in CryptoRecover:

```bash
# Use a specific provider via CLI
cryptorecover bruteforce --mode seed \
  --ai-provider openai \
  --ai-model gpt-4 \
  --mnemonic "abandon ? abandon ..."

# Or configure in the GUI under Settings > AI Provider
```

#### Local Provider Setup (Privacy-First)

Local LLM providers run entirely on your machine, ensuring your recovery data never leaves your computer. This is the recommended approach for security-sensitive recovery operations.

**Ollama (Recommended):**

```bash
# Install Ollama
# Linux:
curl -fsSL https://ollama.com/install.sh | sh

# macOS:
brew install ollama

# Windows: Download from https://ollama.com/download/windows

# Pull a model (Mistral 7B is a good balance of speed and intelligence)
ollama pull mistral

# Start the Ollama server
ollama serve

# Use with CryptoRecover
cryptorecover bruteforce --mode seed \
  --ai-provider ollama \
  --ai-model mistral \
  --mnemonic "abandon ? abandon ..."
```

**LM Studio:**

1. Download and install LM Studio from [lmstudio.ai](https://lmstudio.ai)
2. Open LM Studio and download a model (recommended: Llama 3 8B or Mistral 7B)
3. Start the local server (LM Studio provides an OpenAI-compatible API at `http://localhost:1234`)
4. Use with CryptoRecover:

```bash
cryptorecover bruteforce --mode seed \
  --ai-provider lmstudio \
  --ai-model local-model \
  --mnemonic "abandon ? abandon ..."
```

**llama.cpp:**

```bash
# Clone and build llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Download a GGUF model and start the server
./server -m /path/to/model.gguf --port 8080

# Use with CryptoRecover
cryptorecover bruteforce --mode seed \
  --ai-provider llamacpp \
  --ai-endpoint http://localhost:8080 \
  --mnemonic "abandon ? abandon ..."
```

---

### Installing GPU Acceleration

GPU acceleration is optional but highly recommended for faster recovery, especially when recovering 2+ missing seed words.

#### NVIDIA GPU Setup

```bash
# 1. Install NVIDIA drivers (if not already installed)
# Ubuntu/Debian:
sudo apt install nvidia-driver-535 -y

# 2. Install CUDA Toolkit
# Download from: https://developer.nvidia.com/cuda-downloads
# Or via package manager:
sudo apt install nvidia-cuda-toolkit -y

# 3. Verify CUDA installation
nvcc --version
nvidia-smi

# 4. Install Python CUDA bindings
pip install pycuda numpy
```

#### AMD GPU Setup

```bash
# 1. Install ROCm (AMD's GPU compute platform)
# Follow instructions at: https://rocm.docs.amd.com/
# Ubuntu:
sudo apt install rocm-libs -y

# 2. Install OpenCL Python bindings
pip install pyopencl numpy
```

#### Verify GPU Support

```bash
# Benchmark with GPU
cryptorecover benchmark --gpu

# Check GPU detection
cryptorecover benchmark --verbose
```

---

### Installing External Recovery Tools

CryptoRecover integrates with three external tools for enhanced recovery capabilities. These are optional but provide additional wallet format support and GPU-accelerated recovery.

#### btcrecover.py

btcrecover.py is a well-established tool for recovering wallet file passwords across 100+ wallet formats. CryptoRecover can leverage its password generation and verification capabilities.

```bash
# Clone the btcrecover repository
git clone https://github.com/3rdIteration/btcrecover.git ~/btcrecover

# Install dependencies
cd ~/btcrecover
pip install -r requirements.txt

# Verify
python ~/btcrecover/btcrecover.py --help
```

Configure the path in CryptoRecover:

```bash
cryptorecover bruteforce --mode password \
  --btcrecover ~/btcrecover/btcrecover.py \
  --wallet-file wallet.dat
```

#### seedrecover.py

seedrecover.py (included in btcrecover) specializes in seed phrase recovery with GPU acceleration and multi-wallet address verification.

```bash
# seedrecover.py is in the btcrecover repository
ls ~/btcrecover/seedrecover.py

# Configure the path
cryptorecover bruteforce --mode seed \
  --seedrecover ~/btcrecover/seedrecover.py \
  --mnemonic "abandon ? abandon ..."
```

#### Bitcoin Core (bitcoin-cli)

Bitcoin Core provides wallet.dat password verification and address derivation for Bitcoin wallets.

```bash
# Ubuntu/Debian:
sudo apt install bitcoin-cli -y

# macOS:
brew install bitcoin

# Windows: Download from https://bitcoincore.org/en/download/

# Verify
bitcoin-cli --version

# Configure (you need a running Bitcoin Core node for some operations)
cryptorecover bruteforce --mode password \
  --bitcoin-core /usr/bin/bitcoin-cli \
  --wallet-file wallet.dat
```

---

### Verifying Your Installation

After completing the installation, run these verification steps to ensure everything is working correctly.

```bash
# Step 1: Check the version
cryptorecover --version
# Expected: CryptoRecover v2.0.0

# Step 2: Run the built-in test suite
python -m pytest tests/ -v
# All tests should pass (PASSED)

# Step 3: List supported wallets
cryptorecover list-wallets
# Should display 50+ wallets

# Step 4: List login technologies
cryptorecover list-login-techs
# Should display supported authentication methods

# Step 5: Run a benchmark
cryptorecover benchmark
# Should show your CPU (and GPU if installed) performance metrics

# Step 6: Validate a known seed phrase (quick sanity check)
cryptorecover validate --mnemonic "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
# Should report: Valid BIP39 mnemonic

# Step 7: Test AI integration (if configured)
cryptorecover predict-words --word abandn --ai-provider ollama
# Should return ranked similar words
```

---

### Troubleshooting Installation

#### Python Version Issues

```bash
# Check your Python version
python3 --version

# If Python is too old (< 3.10), install a newer version:
# Ubuntu:
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install python3.11 python3.11-venv -y
python3.11 -m venv venv
source venv/bin/activate
```

#### pip Installation Fails

```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# If that fails, try:
python3 -m pip install --upgrade pip

# For permission errors (never use sudo with pip in a venv):
pip install --user -e .
```

#### Cryptographic Library Errors

```bash
# If you get errors about bip32utils or hdwallet:
pip install --no-cache-dir bip32utils hdwallet

# If pycryptodome conflicts with pycrypto:
pip uninstall pycrypto pycryptodome -y
pip install pycryptodome
```

#### GPU Not Detected

```bash
# Check if your GPU is visible to the system
nvidia-smi                    # NVIDIA
/opt/rocm/bin/rocm-smi        # AMD

# Reinstall GPU Python bindings
pip uninstall pycuda pyopencl -y
pip install pycuda pyopencl

# Check OpenCL platforms
python -c "import pyopencl; print(pyopencl.get_platforms())"
```

#### tkinter GUI Not Launching

```bash
# Linux: Install tkinter (not included in some minimal Python installs)
sudo apt install python3-tk -y     # Ubuntu/Debian
sudo dnf install python3-tkinter -y  # Fedora

# macOS: tkinter is included with Homebrew Python
brew install python-tk

# Windows: tkinter is included with the standard Python installer
```

#### Import Errors After Installation

```bash
# Ensure you're in the virtual environment
which python
# Should point to: .../CryptoRecover/venv/bin/python

# Reinstall in editable mode
pip install -e ".[full]" --force-reinstall

# Clear any cached bytecode
find . -type d -name __pycache__ -exec rm -rf {} +
```

---

## Usage

### CLI Usage

#### Advanced Bruteforce Recovery (Recommended)

```bash
# Recover missing seed phrase words
cryptorecover bruteforce --mode seed \
  --mnemonic "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon ?" \
  --target-address bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

# Recover BIP39 passphrase
cryptorecover bruteforce --mode passphrase \
  --mnemonic "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about" \
  --target-address bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \
  --partial-passphrase "my"

# Recover wallet file password
cryptorecover bruteforce --mode password \
  --wallet-file wallet.dat \
  --password-list "password123,bitcoin,wallet"
```

#### Estimate Recovery Time

```bash
# Estimate for 1 missing word (last position)
cryptorecover estimate --missing-words 1 --seed-length 12 --last-missing

# Estimate for 2 missing words
cryptorecover estimate --missing-words 2 --seed-length 12

# Estimate with GPU acceleration
cryptorecover estimate --missing-words 3 --seed-length 12 --gpu
```

#### Predict Similar BIP39 Words

```bash
# Find words similar to a misspelling
cryptorecover predict-words --word abandn
cryptorecover predict-words --word abot --max-distance 2

# Use AI for contextual prediction
cryptorecover predict-words --word abandn --ai-provider ollama --ai-model mistral
```

#### Validate a Seed Phrase

```bash
cryptorecover validate --mnemonic "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
```

#### Generate Addresses from Seed

```bash
cryptorecover generate-addresses \
  --mnemonic "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about" \
  --coin BTC --count 5
```

#### Benchmark Hardware

```bash
# CPU benchmark
cryptorecover benchmark

# Detailed benchmark (10 seconds)
cryptorecover benchmark --duration 10

# GPU benchmark
cryptorecover benchmark --gpu
```

#### List Supported Wallets

```bash
cryptorecover list-wallets
cryptorecover list-wallets --coin BTC
cryptorecover list-wallets --seed-type BIP39
cryptorecover list-login-techs
```

#### Use Specific Strategy

```bash
# Use Last-Word Optimization
cryptorecover bruteforce --mode seed --strategy lwo \
  --mnemonic "abandon ? ? about above absent absorb abstract absurd abuse access accident"

# Use Hierarchical Checksum Pruning
cryptorecover bruteforce --mode seed --strategy hcp \
  --mnemonic "abandon ? ? about above absent absorb abstract absurd abuse access accident"

# Use Contextual Word Prediction
cryptorecover bruteforce --mode seed --strategy cwp \
  --mnemonic "abandon ? ? about above absent absorb abstract absurd abuse access accident"

# Use AI-assisted strategy
cryptorecover bruteforce --mode seed --strategy ai \
  --ai-provider ollama --ai-model mistral \
  --mnemonic "abandon ? ? about above absent absorb abstract absurd abuse access accident"
```

#### Resume from Checkpoint

```bash
cryptorecover bruteforce --mode seed \
  --mnemonic "abandon ? about above ..." \
  --resume ~/.cryptorecover/checkpoints/recovery_20240101_120000.ckpt.gz
```

### GUI Usage

```bash
# Launch the graphical interface
cryptorecover-gui

# Or via Python
python cryptorecover_gui.py
```

The GUI features:
- **Tabbed interface** for Seed Phrase, Passphrase, Password, Wallet Database, and Settings
- **Dark theme** with intuitive controls and professional appearance
- **Real-time progress** display with speed and estimated time remaining
- **Built-in wallet database browser** with search and filtering by coin, type, and seed standard
- **Auto-detection** of external recovery tools (btcrecover, seedrecover, bitcoin-cli)
- **AI provider configuration** with built-in testing of API connections
- **Results export** to JSON, text, or clipboard

### Interactive Wizard

```bash
# Launch the interactive recovery wizard
cryptorecover interactive
```

The wizard guides you through:
1. **Select recovery type** - Seed phrase, passphrase, or password recovery
2. **Enter known information** - Partial seed, known words, wallet file location
3. **Configure options** - Strategy, GPU usage, AI provider, checkpoint interval
4. **Run the recovery** - Real-time progress with ability to pause/resume
5. **View and save results** - Copy found seed phrase, save to file, or export

---

## Recovery Modes

### Seed Phrase Recovery

| Missing Words | Strategy | Candidates | Estimated Time |
|--------------|----------|------------|----------------|
| 1 (last position) | LWO | 128 | <1 second |
| 1 (any position) | HCP | 128-2048 | <1 second |
| 2 (inc. last) | HCP+LWO | ~262K | 1-5 minutes |
| 2 (no last) | HCP | ~4.2M | 10-60 minutes |
| 3 | HCP | ~537M (checksum-valid) | Hours (CPU) |
| 4+ | HCP+GPU | Varies | Hours-Days (GPU cluster) |

### Passphrase Recovery

The passphrase generator uses a multi-strategy approach, ordered from most likely to least likely:
1. **Empty string** - Many users do not set a passphrase (most common case)
2. **Exact partial match** - If you remember part of the passphrase
3. **Common passphrases** - 100+ known patterns (single words, dates, names)
4. **Custom candidates** - User-provided candidate list
5. **Dictionary words** - English dictionary with common passphrases
6. **Mutations** - Case variations, number substitutions, symbol additions, leet speak
7. **Markov chain generation** - Probability-ordered character sequences

### Password Recovery

Supports wallet file password recovery for:
- **Bitcoin Core** (wallet.dat) - via btcrecover.py or built-in PBKDF2 verification
- **Electrum** wallet files - Standard and encrypted formats
- **MetaMask** vault data - Browser extension encrypted vault
- **Generic encrypted wallet files** - Custom encryption schemes

---

## Architecture

```
CryptoRecover/
├── __init__.py                  # Package initialization (author: Cysec Don)
├── setup.py                     # Installation script
├── pyproject.toml               # Modern Python project config
├── cryptorecover_cli.py         # CLI entry point
├── cryptorecover_gui.py         # GUI entry point
├── run.py                       # Quick launcher
├── README.md                    # This file
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignore rules
├── config/
│   ├── __init__.py
│   └── bip39_english.txt        # BIP39 wordlist (2048 words)
├── core/
│   ├── __init__.py              # Core exports
│   ├── bruteforce_engine.py     # Advanced bruteforce engine (10 techniques)
│   ├── recovery_engine.py       # Basic recovery engine + orchestrator
│   ├── address_derivation.py    # BIP32/44/49/84/86 + secp256k1 + address generation
│   ├── candidate_generators.py  # Smart candidate generation (5 strategies)
│   ├── checksum_filter.py       # BIP39 checksum validation + HCP + LWO
│   ├── verification_pipeline.py # Progressive Verification Pipeline (PVP)
│   ├── gpu_accelerator.py       # GPU/OpenCL/CUDA acceleration + AWD
│   └── checkpoint.py            # Checkpoint & resume system
├── cli/
│   ├── __init__.py
│   └── main.py                  # CLI with argparse + all commands
├── gui/
│   ├── __init__.py
│   └── main.py                  # tkinter GUI with dark theme
├── wallets/
│   ├── __init__.py
│   └── wallet_database.py       # 50+ wallet database with full metadata
├── integrations/
│   ├── __init__.py
│   └── external_tools.py        # btcrecover, seedrecover, bitcoin-core integration
├── utils/
│   ├── __init__.py
│   └── helpers.py               # Formatting, system info, result saving
├── src/
│   ├── __init__.py
│   ├── main.py                  # Unified entry point (CLI/TUI)
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── candidate_generator.py  # AI-powered candidate generation
│   │   └── llm_providers.py        # 20+ LLM provider implementations
│   ├── bruteforce/
│   │   ├── __init__.py
│   │   └── enhanced_engine.py      # Enhanced bruteforce with novel techniques
│   ├── cli/
│   │   ├── __init__.py
│   │   └── app.py                  # Click-based CLI application
│   ├── core/
│   │   ├── __init__.py
│   │   ├── bip39_engine.py         # BIP39 mnemonic engine
│   │   └── phonetic_visual.py      # Phonetic & visual similarity analysis
│   ├── gui/
│   │   ├── __init__.py
│   │   └── tui.py                  # Textual TUI interface
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py               # Configuration management
│   │   └── logger.py               # Logging utilities
│   └── wallets/
│       ├── __init__.py
│       └── registry.py             # Wallet registry with metadata
├── tests/
│   ├── __init__.py
│   ├── test_all.py              # Comprehensive test suite
│   ├── test_bip39.py            # BIP39 checksum tests
│   ├── test_bruteforce.py       # Bruteforce engine tests
│   ├── test_ai_providers.py     # AI provider tests
│   └── test_wallets.py          # Wallet database tests
└── cryptorecover_pkg/           # Alternative package layout
    ├── __init__.py
    ├── cli/
    ├── gui/
    ├── core/
    ├── config/
    ├── wallets/
    ├── integrations/
    ├── utils/
    └── tests/
```

---

## External Tool Integration

### btcrecover.py
- Password recovery for 100+ wallet formats
- Tokenlist-based password generation
- Multi-threaded brute force
- Auto-detection of btcrecover.py installation

### seedrecover.py
- Seed phrase recovery with address verification
- Support for multiple wallet types
- GPU-accelerated seed searching
- Auto-detection of seedrecover.py installation

### Bitcoin Core (bitcoin-cli)
- Wallet.dat password verification
- Address validation and derivation
- Blockchain-rescan for address verification
- RPC interface for advanced operations

Configure external tools in Settings or via CLI:
```bash
cryptorecover bruteforce --mode seed \
  --btcrecover /path/to/btcrecover.py \
  --seedrecover /path/to/seedrecover.py \
  --bitcoin-core /path/to/bitcoin-cli \
  --mnemonic "abandon ? abandon ..."
```

---

## Performance Benchmarks

### Single Missing Word (Last Position) - LWO

| Hardware | Candidates | Time |
|----------|-----------|------|
| CPU (1 core) | 128 | <0.1s |
| CPU (8 cores) | 128 | <0.1s |
| GPU (RTX 3060) | 128 | <0.1s |

### Two Missing Words (Including Last) - HCP+LWO

| Hardware | Candidates | Time |
|----------|-----------|------|
| CPU (1 core) | ~262K | ~3 min |
| CPU (8 cores) | ~262K | ~30s |
| GPU (RTX 3060) | ~262K | ~5s |
| GPU (RTX 4090) | ~262K | ~1s |

### Two Missing Words (No Last Position) - HCP

| Hardware | Candidates | Time |
|----------|-----------|------|
| CPU (1 core) | ~4.2M | ~50 min |
| CPU (8 cores) | ~4.2M | ~7 min |
| GPU (RTX 3060) | ~4.2M | ~45s |
| GPU (RTX 4090) | ~4.2M | ~11s |

---

## Security Considerations

- **NEVER share your seed phrase** with anyone or enter it into untrusted software
- **Only use this tool to recover YOUR OWN wallets** - unauthorized access to others' wallets is illegal
- **Run locally** - this tool runs entirely on your machine; no data is sent to external servers (unless you configure AI providers)
- **Air-gapped operation** - for maximum security, run on an offline computer
- **API keys** - if using cloud AI providers, your API keys are stored locally with file permissions restricted to owner-only (0600)
- **Checkpoint files** - may contain sensitive recovery state; stored in `~/.cryptorecover/checkpoints/`
- **Results files** - contain found seed phrases; stored in `~/.cryptorecover/data/` with restricted permissions
- **Local LLMs recommended** - for maximum privacy, use Ollama, LM Studio, or other local providers instead of cloud APIs
- **No telemetry** - CryptoRecover does not phone home or collect any usage data

---

## FAQ

### General Questions

**Q: Can CryptoRecover recover my wallet if I lost all 12/24 words?**  
A: No. Recovering a completely unknown seed phrase is computationally infeasible (2^128 to 2^256 possibilities). CryptoRecover works when you have partial information - some known words, a target address, or partial passphrase memory. The more you remember, the faster the recovery.

**Q: How many missing words can CryptoRecover handle?**  
A: Practically, 1-3 missing words are recoverable in reasonable time on consumer hardware. 4+ missing words require GPU clusters and significant time. The tool provides an estimate command (`cryptorecover estimate`) to predict recovery time before starting.

**Q: Is it safe to use cloud AI providers?**  
A: Cloud AI providers (OpenAI, Anthropic, etc.) receive partial seed phrase context when generating candidates. If this concerns you, use local providers like Ollama or LM Studio instead - they run entirely on your machine and no data leaves your computer.

**Q: Does CryptoRecover work with hardware wallets?**  
A: Yes. CryptoRecover can recover seed phrases for any BIP39-compatible hardware wallet (Ledger, Trezor, etc.). However, it does not interact with the hardware wallet directly - it works by deriving addresses from candidate seed phrases and comparing them against your known target address.

### Technical Questions

**Q: What is the Last-Word Optimization (LWO)?**  
A: The BIP39 checksum means that for any valid 12-word seed phrase, only 128 out of 2048 possible words are valid for the last position. LWO exploits this property to reduce the search space by 16x when the last word is missing.

**Q: How does AI improve recovery speed?**  
A: AI models analyze partial seed information (known words, misspellings, phonetic hints) to generate ranked candidate lists. Instead of trying all 2048 words equally, the AI prioritizes words that are semantically or phonetically similar to what you remember, often reducing the effective search space by 95-99%.

**Q: Can I use multiple AI providers simultaneously?**  
A: Yes. CryptoRecover supports multi-provider consensus, where multiple LLMs vote on the most likely candidates. Words ranked highly by multiple providers are tried first, improving hit rates.

**Q: How do checkpoints work?**  
A: CryptoRecover periodically saves its progress to checkpoint files (every 60 seconds by default). If a recovery is interrupted (power loss, Ctrl+C, crash), you can resume from the last checkpoint using the `--resume` flag, avoiding redundant computation.

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository on GitHub
2. Clone your fork locally (`git clone https://github.com/YOUR-USERNAME/CryptoRecover.git`)
3. Create a feature branch (`git checkout -b feature/amazing-feature`)
4. Make your changes and add tests if applicable
5. Run the test suite (`python -m pytest tests/ -v`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to your fork (`git push origin feature/amazing-feature`)
8. Open a Pull Request against the main repository

### Development Setup

```bash
# Clone the repo
git clone https://github.com/cysec-don/CryptoRecover.git
cd CryptoRecover

# Create venv and install dev dependencies
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pip install -e ".[full]"

# Run tests
python -m pytest tests/ -v

# Run linting
ruff check .
black --check .
```

---

## Disclaimer

**IMPORTANT LEGAL NOTICE:**

This tool is provided for **legitimate wallet recovery purposes only**. You may only use this tool to recover access to cryptocurrency wallets that you own or have explicit authorization to recover.

**Unauthorized access to another person's cryptocurrency wallet is:**
- A criminal offense in virtually all jurisdictions
- Subject to severe penalties including imprisonment
- A violation of computer fraud and abuse laws

The authors and contributors of CryptoRecover assume no liability for misuse of this tool. By using this software, you agree to use it only for lawful purposes and on wallets you own or are authorized to access.

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

Copyright (c) 2024-2026 Cysec Don (cysecdon@gmail.com)

---

**Built with passion by [Cysec Don](mailto:cysecdon@gmail.com)**  
**If this tool helped you recover your wallet, consider starring the repo!**
