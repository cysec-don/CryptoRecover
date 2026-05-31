# Comprehensive AI/LLM Provider Research for Crypto Wallet Recovery

> **Document Version**: 1.0  
> **Date**: 2025-03-04  
> **Purpose**: Reference guide for integrating LLM capabilities into the CryptoRecover application  

---

## Table of Contents

1. [Cloud AI Providers](#1-cloud-ai-providers)
2. [Local AI Providers](#2-local-ai-providers)
3. [LLM-Enhanced Crypto Wallet Recovery](#3-llm-enhanced-crypto-wallet-recovery)
4. [API Compatibility Patterns](#4-api-compatibility-patterns)
5. [Practical Integration Flow](#5-practical-integration-flow)

---

## 1. Cloud AI Providers

### 1.1 OpenAI

| Field | Details |
|-------|---------|
| **API Base URL** | `https://api.openai.com/v1` |
| **Auth** | Bearer token (`Authorization: Bearer sk-...`) |
| **Key Models** | GPT-4o, GPT-4o-mini, GPT-4.1, GPT-4.1-mini, GPT-4.1-nano, GPT-5, GPT-5.4-mini, GPT-5.4-nano, GPT-5.5, o1, o1-mini, o3, o3-mini, o4-mini |
| **Context Windows** | 128K (GPT-4o), 1M (GPT-4.1 family), 200K (o1/o3) |

**Pricing (per 1M tokens):**

| Model | Input | Output | Cached Input |
|-------|-------|--------|-------------|
| GPT-4o | $2.50 | $10.00 | $1.25 |
| GPT-4o-mini | $0.15 | $0.60 | $0.075 |
| GPT-4.1 | $2.00 | $8.00 | $0.50 |
| GPT-4.1-mini | $0.40 | $1.60 | $0.10 |
| GPT-4.1-nano | $0.10 | $0.40 | $0.025 |
| GPT-5 | $1.25 | $10.00 | — |
| o1 | $15.00 | $60.00 | $7.50 |
| o3 | $10.00 | $40.00 | $2.50 |
| o3-mini | $1.10 | $4.40 | $0.55 |
| o4-mini | $1.10 | $4.40 | $0.275 |

**Rate Limits (Tier-based):**
- **Free tier**: 100 RPD, 40K TPM
- **Tier 1** ($5 paid): 500 RPM, 200K TPM for GPT-4o
- **Tier 2** ($50 paid): 5,000 RPM, 2M TPM for GPT-4o
- **Tier 3** ($200 paid): 10,000 RPM, 10M TPM for GPT-4o
- **Tier 4** ($250+ paid): Higher limits, varies by model
- Reasoning models (o1/o3) have lower rate limits per tier

**Relevance for Wallet Recovery:**
- GPT-4o/4.1: Best for semantic analysis of BIP-39 word patterns, password profiling
- o1/o3: Reasoning models for complex deductive logic about seed phrase structure
- GPT-4.1-mini/nano: Fast, cheap candidates for bulk candidate generation

---

### 1.2 Anthropic (Claude)

| Field | Details |
|-------|---------|
| **API Base URL** | `https://api.anthropic.com/v1` |
| **Auth** | `x-api-key` header + `anthropic-version` header |
| **Key Models** | Claude Opus 4, Claude Sonnet 4, Claude Haiku 4.5, Claude 3.5 Sonnet |
| **Context Windows** | 200K tokens (all models) |
| **Max Output** | 32K tokens (Opus 4), 16K (Sonnet 4), 8K (Haiku) |

**Pricing (per 1M tokens):**

| Model | Input | Output | Batch (50% off) |
|-------|-------|--------|----------------|
| Claude Opus 4 | $15.00 | $75.00 | $7.50/$37.50 |
| Claude Sonnet 4 | $3.00 | $15.00 | $1.50/$7.50 |
| Claude Haiku 4.5 | $1.00 | $5.00 | $0.50/$2.50 |
| Claude 3.5 Sonnet | $3.00 | $15.00 | $1.50/$7.50 |

**Rate Limits:**
- **Tier 1**: 1,000 RPD, 40K TPM (per model)
- **Tier 2**: 5,000 RPD, 160K TPM
- **Tier 3**: 15,000 RPD, 800K TPM
- **Tier 4**: Custom/enterprise
- Prompt caching available (90% discount on cached input)

**Relevance for Wallet Recovery:**
- Claude excels at nuanced language tasks, ideal for password profiling from user hints
- Strong at following complex structured output instructions
- Excellent for semantic clustering of BIP-39 words
- Batch API enables cost-effective bulk processing of candidates

---

### 1.3 Google (Gemini)

| Field | Details |
|-------|---------|
| **API Base URL** | `https://generativelanguage.googleapis.com/v1beta` |
| **Auth** | API key (`?key=...`) |
| **Key Models** | Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 2.0 Flash, Gemini 2.0 Flash Lite |
| **Context Windows** | 1M tokens (2.5 Pro), 1M (2.5 Flash), 1M (2.0 Flash) |

**Pricing (per 1M tokens):**

| Model | Input (≤200K) | Input (>200K) | Output (≤200K) | Output (>200K) |
|-------|--------------|--------------|----------------|----------------|
| Gemini 2.5 Pro | $1.25 | $2.50 | $10.00 | $15.00 |
| Gemini 2.5 Flash | $0.30 | — | $2.50 | — |
| Gemini 2.0 Flash | $0.10 | — | $0.40 | — |
| Gemini 2.0 Flash-Lite | $0.025 | — | $0.10 | — |

**Rate Limits (Free Tier):**
- Gemini 2.5 Pro: 50 RPD, 10 RPM
- Gemini 2.5 Flash: 500 RPD, 10 RPM
- Gemini 2.0 Flash: 1,500 RPD, 15 RPM

**Rate Limits (Paid Tier):**
- Gemini 2.5 Pro: 5,000 RPD, 360 RPM (Tier 1)
- Gemini 2.5 Flash: 10,000 RPD, 1,000 RPM (Tier 1)
- Much higher limits at Tier 2/3

**Relevance for Wallet Recovery:**
- Massive context window (1M) allows loading entire BIP-39 wordlist + word embeddings
- Gemini 2.5 Flash offers excellent cost/performance ratio for bulk work
- Free tier sufficient for development and testing
- Competitive pricing for production use

---

### 1.4 Mistral AI

| Field | Details |
|-------|---------|
| **API Base URL** | `https://api.mistral.ai/v1` |
| **Auth** | Bearer token |
| **Key Models** | Mistral Large, Mistral Medium 3, Mistral Small, Mistral Nemo, Codestral |
| **Context Windows** | 128K (Large), 131K (Medium 3), 128K (Small) |

**Pricing (per 1M tokens):**

| Model | Input | Output |
|-------|-------|--------|
| Mistral Large | $2.00 | $6.00 |
| Mistral Medium 3 | $0.40 | $2.00 |
| Mistral Small | $0.20 | $0.60 |
| Mistral Nemo | $0.10 | $0.30 |
| Codestral | $0.30 | $0.90 |

**Rate Limits:**
- Free Tier: 1 RPS per API key (global)
- La Plateforme tiers: 500 RPM (Tier 1), scales with usage
- Dynamic rate limits that scale with usage history

**Relevance for Wallet Recovery:**
- Open-weight models that can be self-hosted for privacy
- Mistral Medium 3 is very cost-effective for candidate generation
- Codestral could help generate recovery scripts
- Mistral Small/Nemo for fast, cheap bulk processing

---

### 1.5 DeepSeek

| Field | Details |
|-------|---------|
| **API Base URL** | `https://api.deepseek.com/v1` |
| **Auth** | Bearer token |
| **Key Models** | DeepSeek-V3 (deepseek-chat), DeepSeek-R1 (deepseek-reasoner) |
| **Context Windows** | 128K (V3), 64K (R1) |

**Pricing (per 1M tokens):**

| Model | Input | Input (Cache Hit) | Output |
|-------|-------|-------------------|--------|
| DeepSeek-V3 | $0.55 | $0.14 | $2.19 |
| DeepSeek-R1 | $4.00 | $0.55 | $16.00 |

**Rate Limits:**
- Concurrency limit: 2,500 for V3, varies for R1
- Very generous compared to competitors
- No fixed RPM/TPM tiers - concurrency-based

**Relevance for Wallet Recovery:**
- **Extremely cost-effective** - cheapest quality LLM API available
- DeepSeek-V3 at $0.55/$2.19 is ~5x cheaper than GPT-4o
- Cache hit pricing ($0.14/1M) is revolutionary for repeated queries
- DeepSeek-R1 is a reasoning model comparable to o1 at lower cost
- Excellent for bulk candidate generation where cost matters

---

### 1.6 Cohere

| Field | Details |
|-------|---------|
| **API Base URL** | `https://api.cohere.ai/v1` |
| **Auth** | Bearer token |
| **Key Models** | Command A, Command R+, Command R, Command, Command Light |
| **Context Windows** | 256K (Command A), 128K (Command R+) |

**Pricing (per 1M tokens):**

| Model | Input | Output |
|-------|-------|--------|
| Command A | $2.50 | $10.00 |
| Command R+ | $2.50 | $10.00 |
| Command R | $0.50 | $1.50 |
| Command | $1.00 | $2.00 |
| Command Light | $0.30 | $0.60 |

**Rate Limits:**
- Trial key: 20 RPM, 100K TPM
- Production key: 1,000 RPM, scales with usage
- Enterprise: Custom limits

**Relevance for Wallet Recovery:**
- Command R+ has excellent RAG capabilities (useful for searching BIP-39 context)
- Command R is cost-effective for bulk work
- Built-in embedding models for semantic similarity of seed words
- Embed endpoint useful for computing word similarity vectors

---

### 1.7 Together AI

| Field | Details |
|-------|---------|
| **API Base URL** | `https://api.together.xyz/v1` |
| **Auth** | Bearer token |
| **Key Models** | 200+ open-source models (Llama 3.1, Qwen 3, DeepSeek, Mixtral, etc.) |
| **API Format** | OpenAI-compatible |

**Pricing (per 1M tokens):**

| Model | Input | Output |
|-------|-------|--------|
| Llama 3.1 405B | $3.50 | $3.50 |
| Llama 3.1 70B | $0.88 | $0.88 |
| Llama 3.1 8B | $0.18 | $0.18 |
| Qwen 3 235B | $2.00 | $2.00 |
| Mixtral 8x7B | $0.60 | $0.60 |
| DeepSeek V3 | $0.98 | $0.98 |

**Rate Limits:**
- Dynamic rate limits that scale with usage
- No fixed RPM/TPM thresholds
- Free credits available for testing ($5 signup bonus)

**Relevance for Wallet Recovery:**
- Access to many open-source models through a single API
- OpenAI-compatible format = drop-in replacement
- Can A/B test different models for recovery effectiveness
- Fine-tuning support for custom BIP-39 prediction models

---

### 1.8 Fireworks AI

| Field | Details |
|-------|---------|
| **API Base URL** | `https://api.fireworks.ai/inference/v1` |
| **Auth** | Bearer token |
| **Key Models** | 40+ models (Llama 3, Mixtral, Qwen, etc.) |
| **API Format** | OpenAI-compatible |

**Pricing (per 1M tokens):**
- Starting from $0.10/1M input tokens
- Varies by model (typically 50-80% cheaper than first-party APIs)
- Example: Llama 3.1 70B at ~$0.20/$0.20 per 1M tokens

**Rate Limits:**
- 6,000 RPM cap (account-wide)
- Adaptive rate limits for serverless
- Enterprise: Custom, no rate limits

**Relevance for Wallet Recovery:**
- Very fast inference (optimized serverless)
- Good for high-throughput candidate generation
- Fine-tuning and custom model deployment support
- OpenAI-compatible API for easy integration

---

### 1.9 OpenRouter (Aggregator)

| Field | Details |
|-------|---------|
| **API Base URL** | `https://openrouter.ai/api/v1` |
| **Auth** | Bearer token + HTTP referrer headers |
| **Key Feature** | Routes to 100+ models from multiple providers |
| **API Format** | OpenAI-compatible |

**Pricing:**
- Pass-through pricing from each provider
- Small 5.5% markup on credit purchases
- Some models available for free (with rate limits)
- Prices vary by model (from $0.01/1M to $30+/1M)

**Rate Limits:**
- Depends on the underlying provider
- Free models: ~20 RPM
- Paid: Provider-specific limits apply

**Relevance for Wallet Recovery:**
- **Single API key for all providers** - huge integration simplification
- Easy model switching for A/B testing recovery strategies
- Fallback routing if one provider is down
- Price comparison across providers built-in
- Best choice for a "multi-provider" integration strategy

---

### 1.10 Groq (Fast Inference)

| Field | Details |
|-------|---------|
| **API Base URL** | `https://api.groq.com/openai/v1` |
| **Auth** | Bearer token |
| **Key Models** | Llama 3.1 8B, Llama 3.1 70B, Mixtral 8x7B, Gemma 2 |
| **API Format** | OpenAI-compatible |
| **Key Feature** | LPU hardware - 300-1,000+ tokens/sec |

**Pricing (per 1M tokens):**

| Model | Input | Output |
|-------|-------|--------|
| Llama 3.1 8B Instant | $0.05 | $0.08 |
| Llama 3.1 70B | $0.59 | $0.79 |
| Mixtral 8x7B | $0.24 | $0.24 |
| Gemma 2 9B | $0.08 | $0.08 |

**Rate Limits:**
- Free tier: 30 RPM, 14,400 RPD, 6K TPM
- Developer tier: 360 RPM, 14,400 RPD, 30K TPM
- Enterprise: Custom

**Relevance for Wallet Recovery:**
- **Fastest inference available** - critical for high-throughput candidate generation
- Llama 3.1 8B at $0.05/1M input is extremely cheap
- Perfect for rapid iteration of candidate generation loops
- Limited model selection (no GPT-4-class models)
- Best used as a "fast and cheap" secondary provider

---

### 1.11 Perplexity API

| Field | Details |
|-------|---------|
| **API Base URL** | `https://api.perplexity.ai` |
| **Auth** | Bearer token |
| **Key Models** | Sonar, Sonar Pro, Sonar Reasoning, Sonar Reasoning Pro |
| **Key Feature** | Web-grounded answers with citations |

**Pricing (per 1M tokens):**

| Model | Input | Output |
|-------|-------|--------|
| Sonar | $0.20 | $0.20 |
| Sonar Pro | $1.00 | $1.00 |
| Sonar Reasoning | $1.00 | $5.00 |
| Sonar Reasoning Pro | $2.00 | $8.00 |

**Rate Limits:**
- Tier-based (0-5), scaling with usage
- Free tier available for testing

**Relevance for Wallet Recovery:**
- **Lower relevance** - primarily search-augmented generation
- Could be useful for researching wallet-specific recovery techniques
- Not ideal for bulk candidate generation
- Good for helping users find documentation about their specific wallet

---

### 1.12 Anyscale

| Field | Details |
|-------|---------|
| **API Base URL** | `https://api.endpoints.anyscale.com/v1` |
| **Auth** | Bearer token |
| **Key Feature** | Ray-based distributed computing platform |
| **API Format** | OpenAI-compatible |

**Pricing:**
- ~$1.00/1M tokens for open-source models
- $100 free credits on signup
- GPU clusters from $1.75/hour
- Fine-tuning available

**Relevance for Wallet Recovery:**
- Good for deploying custom fine-tuned models
- Distributed inference for parallel candidate generation
- Less relevant for simple API-based integration

---

### 1.13 Other Notable Providers

| Provider | Specialty | Pricing Range | Notes |
|----------|-----------|---------------|-------|
| **Cerebras** | Ultra-fast CS-2 wafer inference | ~$0.10/1M | 2,000+ tok/s, limited models |
| **SambaNova** | Custom AI hardware | Competitive | Enterprise focus |
| **Replicate** | Easy model deployment | Pay-per-second | Good for custom models |
| **Hugging Face Inference** | Open-source model hub | Free tier + paid | Huge model selection |
| **Novita AI** | Cost-effective inference | Very low | Growing model catalog |
| **Silicon Flow** | Chinese cloud provider | Very cheap | Good for APAC users |
| **Cerebras** | Fastest inference | Competitive | Llama models |

---

### Cloud Provider Comparison Matrix (for Wallet Recovery)

| Provider | Cost-Effectiveness | Speed | Model Quality | OpenAI-Compatible | Best For |
|----------|-------------------|-------|---------------|-------------------|----------|
| **OpenAI** | Medium | Fast | Best | Native | Complex reasoning, o1/o3 |
| **Anthropic** | Medium | Fast | Excellent | No (own format) | Nuanced language, password profiling |
| **Google Gemini** | Good | Fast | Excellent | Partial | Large context, bulk processing |
| **DeepSeek** | Best | Medium | Good | Yes | Cheapest quality output |
| **Mistral** | Good | Fast | Good | Yes | Balanced cost/quality |
| **Together AI** | Good | Fast | Good | Yes | Model variety, fine-tuning |
| **Fireworks AI** | Very Good | Very Fast | Good | Yes | Fast cheap inference |
| **OpenRouter** | Variable | Variable | Variable | Yes | Multi-provider flexibility |
| **Groq** | Best | Fastest | Moderate | Yes | Ultra-fast cheap generation |
| **Cohere** | Good | Fast | Good | No (own format) | Embeddings, RAG |

---

## 2. Local AI Providers

### 2.1 Ollama

| Field | Details |
|-------|---------|
| **Project URL** | https://ollama.com |
| **API Endpoint** | `http://localhost:11434` |
| **OpenAI-Compatible** | Yes (`http://localhost:11434/v1`) |
| **Install** | `curl -fsSL https://ollama.com/install.sh \| sh` |
| **Model Management** | `ollama pull llama3.1`, `ollama run llama3.1` |

**Key Features:**
- Simplest local LLM setup available
- OpenAI-compatible REST API (`/v1/chat/completions`)
- Supports GGUF model format
- Automatic GPU/CPU detection and optimization
- Model library with one-command installs

**Supported Models (relevant for wallet recovery):**
- `llama3.1:8b` - Good balance of speed/quality
- `llama3.1:70b` - High quality, needs 40GB+ VRAM
- `mistral:7b` - Fast, efficient
- `qwen2.5:7b` - Strong multilingual
- `deepseek-coder-v2:16b` - Code/reasoning
- `gemma2:9b` - Google's open model
- `phi3:mini` - Tiny, fast (3.8B params)

**API Example:**
```bash
# List models
curl http://localhost:11434/api/tags

# Chat completion (native)
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.1",
  "messages": [{"role": "user", "content": "Predict BIP-39 words similar to 'abandon'"}]
}'

# OpenAI-compatible
curl http://localhost:11434/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "llama3.1",
  "messages": [{"role": "user", "content": "Predict BIP-39 words similar to 'abandon'"}]
}'
```

**Relevance: HIGH** - Best local provider for wallet recovery. Easy setup, OpenAI-compatible, privacy-preserving.

---

### 2.2 LM Studio

| Field | Details |
|-------|---------|
| **Project URL** | https://lmstudio.ai |
| **API Endpoint** | `http://localhost:1234/v1` |
| **OpenAI-Compatible** | Yes (full OpenAI API) |
| **Platform** | Desktop app (Windows, Mac, Linux) |

**Key Features:**
- Beautiful GUI for model management
- Built-in model search and download from Hugging Face
- Local inference server with OpenAI-compatible API
- Supports GGUF, GGML, and other formats
- LM Studio 3.0: Chat + API + fine-tuning modes simultaneously
- One-click model discovery and download

**API Example:**
```bash
# Chat completion (OpenAI-compatible on port 1234)
curl http://localhost:1234/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "llama-3.1-8b",
  "messages": [{"role": "user", "content": "Hello"}]
}'

# List models
curl http://localhost:1234/v1/models
```

**Relevance: MEDIUM** - Great for development/testing but desktop-focused. Ollama is better for headless/CLI usage.

---

### 2.3 llama.cpp Server

| Field | Details |
|-------|---------|
| **Project URL** | https://github.com/ggerganov/llama.cpp |
| **API Endpoint** | `http://localhost:8080` |
| **OpenAI-Compatible** | Yes (`/v1/chat/completions`) |
| **Install** | Build from source or pre-built binaries |

**Key Features:**
- The foundation that Ollama/LM Studio/KoboldCpp are built on
- Raw C/C++ implementation for maximum performance
- Minimal overhead, maximum throughput
- GPU support (CUDA, Metal, Vulkan, OpenCL)
- Quantization support (Q2_K through Q8_0)

**API Example:**
```bash
# Start server
./llama-server -m model.gguf --port 8080 -ngl 99

# Chat completion (OpenAI-compatible)
curl http://localhost:8080/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "model",
  "messages": [{"role": "user", "content": "Hello"}]
}'
```

**Relevance: MEDIUM** - Best raw performance, but harder to set up. Ollama wraps this for ease of use.

---

### 2.4 text-generation-webui (oobabooga)

| Field | Details |
|-------|---------|
| **Project URL** | https://github.com/oobabooga/text-generation-webui |
| **API Endpoint** | `http://localhost:5000` |
| **OpenAI-Compatible** | Yes (extension available) |
| **Platform** | Desktop + Web UI |

**Key Features:**
- Full-featured web interface for text generation
- Multiple loader backends (llama.cpp, ExLlama, AutoGPTQ, etc.)
- OpenAI API extension (must be enabled)
- Supports LoRA fine-tuning
- Character/chat mode support

**API Access:**
- Native API at `http://localhost:5000/api/v1/generate`
- OpenAI-compatible extension at `http://localhost:5000/v1/chat/completions` (must enable)
- Streaming support available

**Relevance: LOW** - Primarily a GUI tool. API requires extension setup. Better alternatives for programmatic use.

---

### 2.5 KoboldCpp

| Field | Details |
|-------|---------|
| **Project URL** | https://github.com/LostRuins/koboldcpp |
| **API Endpoint** | `http://localhost:5001` |
| **OpenAI-Compatible** | Partial (KoboldAI API + basic OpenAI) |
| **Install** | Single executable, self-contained |

**Key Features:**
- Single self-contained executable - easiest deployment
- Based on llama.cpp with added features
- Built-in web UI
- Supports GGUF, GGML models
- Custom KoboldAI API + partial OpenAI compatibility
- Low resource usage

**API Example:**
```bash
# Start server
./koboldcpp --model model.gguf --port 5001

# KoboldAI API
curl http://localhost:5001/api/v1/generate -d '{
  "prompt": "Predict words similar to 'abandon' from the BIP-39 list",
  "max_length": 100
}'

# OpenAI-compatible (limited)
curl http://localhost:5001/v1/chat/completions
```

**Relevance: LOW** - Good for quick setup, but API compatibility is limited. Better for interactive use.

---

### 2.6 GPT4All

| Field | Details |
|-------|---------|
| **Project URL** | https://gpt4all.io |
| **API Endpoint** | Varies (desktop app or Python bindings) |
| **OpenAI-Compatible** | Partial (via Python API) |
| **Platform** | Desktop app + Python library |

**Key Features:**
- Runs on CPU (no GPU required)
- Optimized for low-resource machines
- Python bindings: `from gpt4all import GPT4All`
- Supports GGUF models
- Built-in chat UI

**Python API:**
```python
from gpt4all import GPT4All

model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_K_M.gguf")
response = model.generate("Predict BIP-39 words similar to 'abandon'")
```

**Relevance: LOW-MEDIUM** - CPU-only limits performance. Python API useful for direct integration without HTTP.

---

### 2.7 LocalAI

| Field | Details |
|-------|---------|
| **Project URL** | https://github.com/mudler/LocalAI |
| **API Endpoint** | `http://localhost:8080` |
| **OpenAI-Compatible** | Yes (drop-in replacement) |
| **Install** | Docker or binary |

**Key Features:**
- **Most complete OpenAI API compatibility** among local providers
- Drop-in replacement for OpenAI API (including embeddings, audio, images)
- Docker-first deployment
- Supports multiple model formats (GGUF, GGML, SafeTensors)
- GPU acceleration support
- Concurrent model loading

**API Example:**
```bash
# Docker run
docker run -p 8080:8080 -v models:/models localai/localai

# Identical to OpenAI API
curl http://localhost:8080/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "llama-3.1-8b",
  "messages": [{"role": "user", "content": "Hello"}]
}'

# Embeddings (important for BIP-39 word similarity)
curl http://localhost:8080/v1/embeddings -d '{
  "model": "text-embedding-ada-002",
  "input": "abandon"
}'
```

**Relevance: HIGH** - Best OpenAI compatibility, Docker deployment, supports embeddings for word similarity.

---

### Local Provider Comparison Matrix

| Provider | OpenAI Compat | Ease of Setup | Performance | Embeddings | Best For |
|----------|---------------|---------------|-------------|------------|----------|
| **Ollama** | Yes (`/v1`) | Easiest | Good | Limited | Production local inference |
| **LM Studio** | Yes (`/v1`) | Easy (GUI) | Good | No | Development/testing |
| **llama.cpp** | Yes (`/v1`) | Hard (build) | Best | No | Maximum performance |
| **text-gen-webui** | Partial | Medium | Good | No | Interactive exploration |
| **KoboldCpp** | Partial | Easy | Good | No | Quick single-file setup |
| **GPT4All** | Python API | Easy | CPU-only | No | Low-resource machines |
| **LocalAI** | Full | Medium (Docker) | Good | Yes | Complete OpenAI replacement |

---

## 3. LLM-Enhanced Crypto Wallet Recovery

### 3.1 Understanding the BIP-39 Challenge

The BIP-39 standard uses a fixed wordlist of **2,048 words** to generate seed phrases:

- **12-word phrase**: 128 bits of entropy + 4-bit checksum = 132 bits total
- **24-word phrase**: 256 bits of entropy + 8-bit checksum = 264 bits total

**Key Constraints:**
- The last word includes a checksum (makes pure random guessing harder)
- With 1 missing word (position known): 2,048 possibilities (but checksum narrows to ~128 for 12-word or ~256 for 24-word)
- With 2 missing words: ~2,048 × 2,048 = 4,194,304 combinations (pre-checksum)
- With 3 missing words: ~8.6 billion combinations
- With 4+ missing words: Trillions+ (practically impossible without optimization)

**LLM research finding (from Hackread study):**
> AI (LSTM-based) could retrieve 1 missing word in 0.02 seconds, 2 words in 29 seconds, 3 words in 2.28 hours, and 4 words in maximum feasible time.

### 3.2 Smart Candidate Generation for Seed Phrases

#### How LLMs Can Predict Missing BIP-39 Words

**IMPORTANT CAVEAT**: BIP-39 seed phrases are generated from random entropy, NOT from natural language patterns. The words are NOT semantically related. An LLM cannot "predict" a truly random seed phrase from scratch.

**Where LLMs ARE useful:**

1. **Error Correction for Misremembered Words**
   - User thinks the word was "apple" but it's actually "april" or "apart" in BIP-39
   - LLM can identify phonetically or visually similar BIP-39 words
   - "I think it was something like 'quantum'" → suggest "quantity", "qualify" from BIP-39 list

2. **Likely Confusion Pairs**
   - BIP-39 has many confusingly similar words: `abandon`/`abide`, `actor`/`acid`, `age`/`ago`
   - LLM can rank candidates by likelihood of confusion

3. **Context from Partial Memories**
   - "I remember the word was related to nature" → cluster BIP-39 nature words
   - "The word started with 'cr'" → filter + rank BIP-39 words starting with "cr"

#### Prompt Engineering for Seed Phrase Recovery

```python
SEED_WORD_PREDICTION_PROMPT = """
You are a BIP-39 seed phrase recovery assistant. The BIP-39 wordlist contains exactly 2,048 words.

The user has a seed phrase where one or more words are missing or may be incorrect.

Known words: {known_words}
Missing word position(s): {missing_positions}
User hints about missing word: {user_hints}

Based on the user's hints and common mnemonic errors, suggest the 20 most likely 
BIP-39 words for each missing position, ranked by probability.

Consider:
1. Words that sound similar to what the user remembers
2. Words that look similar (visual confusion)
3. Words in the same semantic category as the hint
4. Commonly confused BIP-39 word pairs

Output as JSON: {{"suggestions": [{{"word": "...", "confidence": 0.0-1.0, "reason": "..."}}]}}
"""
```

### 3.3 Password Profiling Based on User Hints/Context

LLMs excel at understanding human psychology and pattern prediction:

#### Password Pattern Analysis

```python
PASSWORD_PROFILING_PROMPT = """
You are a password recovery expert. Based on the user's context, predict likely 
password patterns for their crypto wallet.

User information:
- Name: {name}
- Birth year: {birth_year}  
- Pet names: {pets}
- Favorite teams/hobbies: {interests}
- Likely password length: {length_hint}
- Partial memory: {partial_password}

Generate 50 likely password candidates following these common patterns:
1. Name + numbers (e.g., "John1990", "john123")
2. Pet name + special chars (e.g., "Fluffy!", "rex@2020")
3. Hobby/interest + numbers (e.g., "Lakers23", "bitcoin2021")
4. Common substitutions (e.g., "p@ssw0rd", "cr7pt0")
5. Keyboard patterns with personal touches
6. Reversed words with numbers
7. Capitalization variants

Output as JSON array of password strings.
"""
```

#### Psychological Profiling Categories

| Pattern | Description | LLM Capability |
|---------|-------------|----------------|
| **Personal identifiers** | Names, dates, locations | Excellent - understands context |
| **Substitution patterns** | a→@, e→3, o→0 | Very good - learns common patterns |
| **Keyboard walks** | qwerty, asdfgh | Good - can generate variants |
| **Cultural references** | Movies, songs, teams | Good - broad knowledge |
| **Number sequences** | Years, 123, 000 | Good - pattern completion |
| **Mixed patterns** | Name+year+special | Very good - combines contexts |
| **Passphrase patterns** | Multiple words joined | Excellent - language model strength |

### 3.4 Pattern Recognition for Likely Word Sequences

While BIP-39 words are randomly selected, users may misremember words in systematic ways:

#### Confusion Matrices
- **Phonetic confusion**: "piece" ↔ "peace", "right" ↔ "write"
- **Visual confusion**: "ostrich" ↔ "ocean" (misread handwritten)
- **Semantic confusion**: User remembers concept not exact word → LLM maps concept to BIP-39

#### LLM-Based Word Similarity Scoring

```python
WORD_SIMILARITY_PROMPT = """
Given a BIP-39 word that a user might have misremembered, score each candidate 
replacement by how likely the user would confuse it with the original.

Original (possibly wrong) word: "{word}"
Candidate replacements: {candidates}

Score each 0.0-1.0 based on:
- Phonetic similarity (how it sounds)
- Visual similarity (how it looks written)
- Semantic similarity (related meaning)
- Typographic distance (keyboard proximity)

Output: JSON array of {{"word": "...", "phonetic_score": 0.0, "visual_score": 0.0, 
"semantic_score": 0.0, "typographic_score": 0.0, "combined_score": 0.0}}
"""
```

### 3.5 Error Correction for Misremembered Words

#### Multi-Strategy Error Correction

```python
ERROR_CORRECTION_STRATEGIES = {
    "typo": {
        "description": "Single character typo in word",
        "method": "Levenshtein distance + LLM ranking",
        "max_candidates": 50,
        "example": "abandn → abandon"
    },
    "wrong_word_similar": {
        "description": "Completely different but similar-sounding word",
        "method": "Phonetic matching + LLM semantic analysis",
        "max_candidates": 30,
        "example": "apple → apply (both in BIP-39)"
    },
    "wrong_position": {
        "description": "Correct word but in wrong position",
        "method": "Position permutation + checksum validation",
        "max_candidates": "n! where n = phrase length",
        "example": "Word at position 5 should be at position 8"
    },
    "partial_recall": {
        "description": "User remembers some letters/concept",
        "method": "LLM with partial hints + BIP-39 filtering",
        "max_candidates": 100,
        "example": "'starts with cr, something cold' → crust, crop, crew"
    }
}
```

### 3.6 Search Space Prioritization Using Probability

This is the **most impactful** use of LLMs in wallet recovery:

#### Priority Queue Architecture

```
┌─────────────────────────────────────────────────┐
│            User Input & Hints                    │
│  (partial seed, password fragments, context)     │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│         LLM Priority Scoring Engine              │
│                                                  │
│  1. Generate candidates (all possible words)     │
│  2. Score each candidate 0.0-1.0                │
│  3. Sort by probability                          │
│  4. Group into priority tiers                    │
│                                                  │
│  Tier 1 (90%+ probability): Top 10 candidates   │
│  Tier 2 (70-90%): Next 50 candidates            │
│  Tier 3 (50-70%): Next 200 candidates           │
│  Tier 4 (<50%): All remaining 1,788 candidates  │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│     Checksum-Filtered Brute Force Engine         │
│                                                  │
│  Process Tier 1 first → Tier 2 → Tier 3 → ...   │
│  Check BIP-39 checksum before derivation         │
│  Skip invalid checksums (saves ~93.75% of work)  │
└─────────────────────────────────────────────────┘
```

**Expected speedup**: With good LLM prioritization, the correct word is found in the first 50-100 attempts instead of 2,048, giving **20-40x speedup** for single-word recovery.

### 3.7 Semantic Clustering of BIP-39 Words

LLMs can cluster the 2,048 BIP-39 words into semantic groups:

```python
BIP39_SEMANTIC_CLUSTERS = {
    "nature": ["abandon", "abstract", "academy", "aquarium", "bamboo", "blossom", ...],
    "body": ["ankle", "arm", "blood", "bone", "brain", "cheek", ...],
    "animals": ["buffalo", "butterfly", "camel", "cat", "cobra", "crab", ...],
    "emotions": ["anger", "bliss", "calm", "cheer", "comfort", ...],
    "time": ["annual", "calendar", "century", "clock", "daily", ...],
    "weather": ["breeze", "cloud", "cold", "damp", "dew", "dust", ...],
    "food": ["apple", "bacon", "bread", "butter", "candy", "cereal", ...],
    # ... more clusters
}
```

When a user says "I think the word was related to weather", the LLM can immediately narrow 2,048 → ~50-100 candidates.

### 3.8 Adaptive Learning from Failed Attempts

```python
ADAPTIVE_LEARNING_PROMPT = """
We have been trying to recover a seed phrase. Here are the attempts that FAILED:

Seed phrase: {known_words} + [MISSING at position {pos}]

Failed candidates (already tried): {failed_words}

Based on these failures:
1. What patterns can you identify in the failures?
2. What categories of words have we exhausted?
3. What remaining categories should we try next?
4. Generate 20 NEW candidates that are different from the failed ones.

Consider:
- If many similar-sounding words failed, try different phonetic categories
- If semantic cluster X is exhausted, move to cluster Y
- If partial matches suggest specific letter patterns, focus there
"""
```

### 3.9 Markov Chain-Enhanced Prediction with LLM Refinement

A hybrid approach combining statistical methods with LLM reasoning:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Markov Chain   │     │   LLM Refinement │     │   Checksum +     │
│   First Pass     │────▶│   Second Pass    │────▶│   Address Check  │
│                  │     │                  │     │                  │
│ • Word transition│     │ • Context aware  │     │ • BIP-39 valid   │
│   probabilities  │     │   ranking        │     │ • Derive address │
│ • n-gram models  │     │ • User hint      │     │ • Compare to     │
│ • Bigram freq    │     │   integration    │     │   target address │
│   from seed data │     │ • Semantic       │     │                  │
│                  │     │   clustering     │     │                  │
│ Output: Top 500  │     │ Output: Top 50   │     │ Output: MATCH or │
│ candidates       │     │ ranked candidates│     │ continue search  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

**Markov Chain Component:**
- Build transition probabilities from known seed phrases in the wild
- P(word_i | word_{i-1}) for bigram models
- P(word_i | word_{i-2}, word_{i-1}) for trigram models
- Note: This has LIMITED predictive power for truly random seeds, but helps with user-error patterns

**LLM Refinement Component:**
- Take Markov chain top-500 candidates
- Re-rank based on:
  - User hints ("I think it started with 's'")
  - Semantic coherence with surrounding words
  - Common confusion patterns
  - Failed attempt history

### 3.10 Psychological Profiling for Likely Password Patterns

```python
PSYCHOLOGICAL_PROFILING_PROMPT = """
You are an expert in password psychology and crypto wallet recovery.

User Profile:
- Age: {age}
- Technical skill: {skill_level}
- Occupation: {occupation}
- Nationality: {nationality}
- Year wallet was created: {creation_year}
- Any password hints: {hints}

Based on research in password psychology:
1. Users rarely change their password patterns across services
2. Most users use 1-3 password "formulas" with minor variations
3. Password complexity correlates with technical skill
4. Cultural factors influence password choices
5. Year of creation affects patterns (2021 crypto passwords differ from 2017)

Generate 100 likely password candidates ranked by probability.
Include variations for each base pattern (capitalization, l33t speak, special chars).
"""
```

---

## 4. API Compatibility Patterns

### 4.1 The OpenAI API Standard

Most LLM providers have adopted the OpenAI Chat Completions API as a de facto standard:

#### Chat Completions Endpoint

```
POST {base_url}/v1/chat/completions
```

**Request Body:**
```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "top_p": 1.0,
  "stream": false,
  "stop": ["\n"],
  "response_format": {"type": "json_object"},
  "seed": 42
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4o",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

### 4.2 Provider-Specific Endpoint Mapping

| Provider | Base URL | Auth Method | Notes |
|----------|----------|-------------|-------|
| **OpenAI** | `https://api.openai.com/v1` | `Authorization: Bearer sk-...` | Original standard |
| **Anthropic** | `https://api.anthropic.com/v1` | `x-api-key: sk-...` + `anthropic-version: 2023-06-01` | **NOT OpenAI-compatible** |
| **Google Gemini** | `https://generativelanguage.googleapis.com/v1beta` | `?key=API_KEY` | **NOT OpenAI-compatible** |
| **Mistral** | `https://api.mistral.ai/v1` | `Authorization: Bearer ...` | OpenAI-compatible |
| **DeepSeek** | `https://api.deepseek.com/v1` | `Authorization: Bearer ...` | OpenAI-compatible |
| **Cohere** | `https://api.cohere.ai/v1` | `Authorization: Bearer ...` | **NOT OpenAI-compatible** |
| **Together AI** | `https://api.together.xyz/v1` | `Authorization: Bearer ...` | OpenAI-compatible |
| **Fireworks AI** | `https://api.fireworks.ai/inference/v1` | `Authorization: Bearer ...` | OpenAI-compatible |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `Authorization: Bearer ...` | OpenAI-compatible |
| **Groq** | `https://api.groq.com/openai/v1` | `Authorization: Bearer ...` | OpenAI-compatible |
| **Perplexity** | `https://api.perplexity.ai` | `Authorization: Bearer ...` | Partial compatibility |
| **Ollama** | `http://localhost:11434/v1` | None | OpenAI-compatible |
| **LM Studio** | `http://localhost:1234/v1` | None | OpenAI-compatible |
| **llama.cpp** | `http://localhost:8080/v1` | None | OpenAI-compatible |
| **LocalAI** | `http://localhost:8080/v1` | None | OpenAI-compatible |

### 4.3 Streaming Support

Most OpenAI-compatible providers support SSE streaming:

```python
# Streaming request
import httpx

async def stream_chat(base_url, model, messages):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "stream": True
            },
            headers={"Authorization": f"Bearer {api_key}"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    yield json.loads(data)
```

**Streaming support matrix:**

| Provider | Streaming | Notes |
|----------|-----------|-------|
| OpenAI | Yes | SSE format |
| Anthropic | Yes | SSE format (different event types) |
| Google Gemini | Yes | SSE format |
| Mistral | Yes | SSE format |
| DeepSeek | Yes | SSE format |
| Together AI | Yes | SSE format |
| Fireworks AI | Yes | SSE format |
| OpenRouter | Yes | SSE format |
| Groq | Yes | SSE format |
| Ollama | Yes | SSE + native streaming |
| LM Studio | Yes | SSE format |
| llama.cpp | Yes | SSE format |
| LocalAI | Yes | SSE format |

### 4.4 Model Listing

```bash
# OpenAI-compatible providers
GET {base_url}/v1/models

# Response:
{
  "object": "list",
  "data": [
    {"id": "gpt-4o", "object": "model", "created": ..., "owned_by": "openai"},
    {"id": "gpt-4o-mini", "object": "model", "created": ..., "owned_by": "openai"}
  ]
}
```

### 4.5 Embeddings API (for Word Similarity)

```bash
# OpenAI
POST https://api.openai.com/v1/embeddings
{
  "model": "text-embedding-3-small",
  "input": "abandon"
}

# LocalAI
POST http://localhost:8080/v1/embeddings
{
  "model": "text-embedding-ada-002",
  "input": "abandon"
}

# Ollama
POST http://localhost:11434/api/embeddings
{
  "model": "nomic-embed-text",
  "prompt": "abandon"
}
```

### 4.6 Unified Provider Abstraction

```python
from dataclasses import dataclass
from typing import Optional, List, AsyncIterator

@dataclass
class LLMProvider:
    name: str
    base_url: str
    api_key: Optional[str]
    auth_header: str  # "Authorization" or "x-api-key"
    auth_prefix: str  # "Bearer " or ""
    openai_compatible: bool
    default_model: str
    supports_streaming: bool
    supports_embeddings: bool
    max_context_tokens: int
    price_per_1m_input: float
    price_per_1m_output: float

PROVIDERS = {
    "openai": LLMProvider(
        name="OpenAI", base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY", auth_header="Authorization",
        auth_prefix="Bearer ", openai_compatible=True,
        default_model="gpt-4o-mini", supports_streaming=True,
        supports_embeddings=True, max_context_tokens=128000,
        price_per_1m_input=0.15, price_per_1m_output=0.60
    ),
    "anthropic": LLMProvider(
        name="Anthropic", base_url="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY", auth_header="x-api-key",
        auth_prefix="", openai_compatible=False,
        default_model="claude-sonnet-4-20250514", supports_streaming=True,
        supports_embeddings=False, max_context_tokens=200000,
        price_per_1m_input=3.00, price_per_1m_output=15.00
    ),
    "deepseek": LLMProvider(
        name="DeepSeek", base_url="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY", auth_header="Authorization",
        auth_prefix="Bearer ", openai_compatible=True,
        default_model="deepseek-chat", supports_streaming=True,
        supports_embeddings=False, max_context_tokens=128000,
        price_per_1m_input=0.55, price_per_1m_output=2.19
    ),
    "groq": LLMProvider(
        name="Groq", base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY", auth_header="Authorization",
        auth_prefix="Bearer ", openai_compatible=True,
        default_model="llama-3.1-8b-instant", supports_streaming=True,
        supports_embeddings=False, max_context_tokens=131072,
        price_per_1m_input=0.05, price_per_1m_output=0.08
    ),
    "ollama": LLMProvider(
        name="Ollama", base_url="http://localhost:11434/v1",
        api_key_env=None, auth_header="Authorization",
        auth_prefix="Bearer ", openai_compatible=True,
        default_model="llama3.1", supports_streaming=True,
        supports_embeddings=True, max_context_tokens=131072,
        price_per_1m_input=0.0, price_per_1m_output=0.0  # Free/local
    ),
    # ... more providers
}
```

---

## 5. Practical Integration Flow

### 5.1 Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     CryptoRecover Application                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────┐ │
│  │  User Input  │    │  LLM Engine │    │  Brute Force Engine  │ │
│  │  Module      │    │             │    │                      │ │
│  │              │    │  ┌───────┐  │    │  ┌────────────────┐  │ │
│  │ • Seed frag  │    │  │Cloud  │  │    │  │ Checksum Filter│  │ │
│  │ • Hints      │───▶│  │LLMs   │  │───▶│  │ (BIP-39 valid) │  │ │
│  │ • Context    │    │  └───────┘  │    │  └────────┬───────┘  │ │
│  │ • Password   │    │  ┌───────┐  │    │           │          │ │
│  │   hints      │    │  │Local  │  │    │  ┌────────▼───────┐  │ │
│  │              │    │  │LLMs   │  │    │  │ Address        │  │ │
│  └─────────────┘    │  └───────┘  │    │  │ Derivation     │  │ │
│                      │  ┌───────┐  │    │  └────────┬───────┘  │ │
│                      │  │Embed  │  │    │           │          │ │
│                      │  │Models │  │    │  ┌────────▼───────┐  │ │
│                      │  └───────┘  │    │  │ Address Match  │  │ │
│                      └─────────────┘    │  └────────────────┘  │ │
│                                          └──────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Orchestration Layer                        │ │
│  │  • Priority queue management                                  │ │
│  │  • Parallel LLM + BF execution                                │ │
│  │  • Checkpoint/resume system                                   │ │
│  │  • Adaptive strategy selection                                │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 How to Query the LLM for Candidate Generation

#### Step 1: Context Gathering

```python
@dataclass
class RecoveryContext:
    # Seed phrase info
    known_words: List[Optional[str]]  # None for missing positions
    total_words: int  # 12 or 24
    missing_positions: List[int]
    
    # User hints
    word_hints: Dict[int, str]  # position → hint text
    password_hint: Optional[str] = None
    
    # Wallet info
    target_address: Optional[str] = None
    wallet_type: str = "bitcoin"  # bitcoin, ethereum, etc.
    derivation_path: str = "m/44'/0'/0'/0/0"
    
    # Recovery metadata
    failed_candidates: Dict[int, Set[str]] = field(default_factory=dict)
    attempt_count: int = 0
```

#### Step 2: LLM Query with Validation

```python
import json
import re
from typing import List, Tuple

BIP39_WORDLIST = set()  # Load from config/bip39_english.txt

class LLMCandidateGenerator:
    def __init__(self, provider: LLMProvider, model: str = None):
        self.provider = provider
        self.model = model or provider.default_model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate_seed_candidates(
        self, 
        context: RecoveryContext,
        position: int,
        top_k: int = 50
    ) -> List[Tuple[str, float]]:
        """Generate ranked BIP-39 word candidates for a missing position."""
        
        prompt = self._build_seed_prompt(context, position)
        response = await self._query_llm(prompt)
        candidates = self._parse_and_validate(response, top_k)
        
        return candidates
    
    def _build_seed_prompt(self, context: RecoveryContext, position: int) -> str:
        hint = context.word_hints.get(position, "no specific hint")
        failed = context.failed_candidates.get(position, set())
        
        return f"""You are a BIP-39 seed phrase recovery assistant. The BIP-39 wordlist 
contains exactly 2,048 words. Your task is to suggest likely words for a missing 
position in a seed phrase.

Seed phrase (None = missing):
{context.known_words}

Missing position: {position} (0-indexed)
User hint for this position: "{hint}"

Previously tried and FAILED words: {list(failed)[:100]}

IMPORTANT RULES:
1. ALL suggested words MUST be from the BIP-39 wordlist
2. Rank by likelihood based on the user's hint and common confusion patterns
3. Consider phonetic, visual, and semantic similarity to the hint
4. Do NOT repeat any words from the failed list
5. Return exactly {top_k} candidates

Output format (JSON only, no markdown):
{{"candidates": [{{"word": "example", "confidence": 0.95, "reason": "exact match to hint"}}]}}"""

    def _parse_and_validate(
        self, 
        response: str, 
        top_k: int
    ) -> List[Tuple[str, float]]:
        """Parse LLM response and validate against BIP-39 wordlist."""
        
        # Extract JSON from response (handle markdown wrappers)
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            return []
        
        try:
            data = json.loads(json_match.group())
            candidates = data.get("candidates", [])
        except json.JSONDecodeError:
            return []
        
        validated = []
        for c in candidates[:top_k * 2]:  # Request more, filter down
            word = c.get("word", "").lower().strip()
            confidence = float(c.get("confidence", 0.5))
            
            # CRITICAL: Validate against BIP-39 wordlist
            if word in BIP39_WORDLIST:
                validated.append((word, confidence))
        
        # Sort by confidence, return top_k
        validated.sort(key=lambda x: x[1], reverse=True)
        return validated[:top_k]
```

#### Step 3: Multi-Provider Redundancy

```python
class MultiProviderGenerator:
    """Query multiple LLM providers and merge results."""
    
    def __init__(self, providers: List[LLMProvider]):
        self.generators = {
            p.name: LLMCandidateGenerator(p) for p in providers
        }
    
    async def generate_candidates(
        self,
        context: RecoveryContext,
        position: int,
        top_k: int = 50
    ) -> List[Tuple[str, float]]:
        """Query all providers in parallel, merge and re-rank results."""
        
        tasks = []
        for name, gen in self.generators.items():
            tasks.append(gen.generate_seed_candidates(context, position, top_k))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results using weighted voting
        merged = {}
        weights = {"deepseek": 0.3, "openai": 0.3, "ollama": 0.2, "groq": 0.2}
        
        for (name, result) in zip(self.generators.keys(), results):
            if isinstance(result, Exception):
                continue
            weight = weights.get(name, 0.1)
            for word, confidence in result:
                if word in merged:
                    merged[word] += confidence * weight
                else:
                    merged[word] = confidence * weight
        
        # Sort by merged score
        candidates = sorted(merged.items(), key=lambda x: x[1], reverse=True)
        return candidates[:top_k]
```

### 5.3 How to Rank/Prioritize LLM Suggestions

```python
class CandidateRanker:
    """Multi-signal candidate ranking system."""
    
    def __init__(self):
        self.bip39_embeddings = {}  # Pre-computed word embeddings
    
    def rank_candidates(
        self,
        candidates: List[Tuple[str, float]],
        context: RecoveryContext,
        position: int
    ) -> List[Tuple[str, float]]:
        """Re-rank candidates using multiple signals."""
        
        ranked = []
        for word, llm_score in candidates:
            score = 0.0
            
            # Signal 1: LLM confidence (weight: 0.35)
            score += llm_score * 0.35
            
            # Signal 2: BIP-39 checksum validity (weight: 0.25)
            # A valid checksum means this word produces valid entropy
            is_valid_checksum = self._check_checksum(context, position, word)
            score += (1.0 if is_valid_checksum else 0.0) * 0.25
            
            # Signal 3: Embedding similarity to hint (weight: 0.20)
            hint = context.word_hints.get(position, "")
            if hint and word in self.bip39_embeddings:
                similarity = self._cosine_similarity(hint, word)
                score += similarity * 0.20
            
            # Signal 4: Failed attempt penalty (weight: 0.10)
            if word in context.failed_candidates.get(position, set()):
                score -= 1.0 * 0.10  # Should never happen, but safety check
            
            # Signal 5: Edit distance to hint word (weight: 0.10)
            if hint:
                min_edit_dist = min(
                    self._levenshtein(word, h) for h in hint.split()
                )
                normalized = 1.0 - (min_edit_dist / max(len(word), 1))
                score += normalized * 0.10
            
            ranked.append((word, score))
        
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked
    
    def _check_checksum(
        self, context: RecoveryContext, position: int, word: str
    ) -> bool:
        """Check if substituting this word produces a valid BIP-39 checksum."""
        test_phrase = context.known_words.copy()
        test_phrase[position] = word
        
        # BIP-39 checksum validation
        # Last 4-8 bits (depending on word count) must match SHA256 hash
        try:
            return validate_bip39_checksum(test_phrase)
        except Exception:
            return False
```

### 5.4 How to Handle LLM Hallucinations

LLMs frequently hallucinate - they may suggest words NOT in the BIP-39 list, or claim impossible checksums are valid. Mitigation strategies:

#### Strategy 1: Strict Output Validation

```python
class StrictOutputValidator:
    """Validate and sanitize all LLM outputs."""
    
    BIP39_WORDS: Set[str] = set()  # Loaded from wordlist
    
    def validate_seed_candidates(self, response: dict) -> List[dict]:
        """Strict validation pipeline for seed word candidates."""
        
        valid = []
        for candidate in response.get("candidates", []):
            word = candidate.get("word", "").lower().strip()
            
            # Check 1: Must be in BIP-39 wordlist
            if word not in self.BIP39_WORDS:
                continue  # Hallucinated word - discard silently
            
            # Check 2: Confidence must be numeric and in range
            try:
                conf = float(candidate.get("confidence", 0))
                conf = max(0.0, min(1.0, conf))  # Clamp to [0, 1]
            except (ValueError, TypeError):
                conf = 0.5  # Default for malformed confidence
            
            # Check 3: No duplicate words
            if any(c["word"] == word for c in valid):
                continue
            
            valid.append({"word": word, "confidence": conf})
        
        return valid
    
    def validate_password_candidates(self, response: dict) -> List[str]:
        """Validate password candidates from LLM."""
        
        valid = []
        for pwd in response.get("passwords", []):
            if isinstance(pwd, str):
                # Basic sanity: length, no control chars
                pwd = pwd.strip()
                if 1 <= len(pwd) <= 256 and all(ord(c) >= 32 for c in pwd):
                    valid.append(pwd)
        
        return valid
```

#### Strategy 2: Multi-Model Consensus

```python
class ConsensusValidator:
    """Require multiple LLMs to agree before accepting a candidate."""
    
    def __init__(self, generators: List[LLMCandidateGenerator], threshold: int = 2):
        self.generators = generators
        self.threshold = threshold  # Number of models that must agree
    
    async def get_consensus_candidates(
        self, context: RecoveryContext, position: int
    ) -> List[Tuple[str, float]]:
        """Only return candidates that multiple models agree on."""
        
        all_results = await asyncio.gather(*[
            gen.generate_seed_candidates(context, position, 100)
            for gen in self.generators
        ])
        
        # Count how many models suggest each word
        word_votes = {}
        for results in all_results:
            for word, confidence in results:
                if word not in word_votes:
                    word_votes[word] = {"count": 0, "total_conf": 0.0}
                word_votes[word]["count"] += 1
                word_votes[word]["total_conf"] += confidence
        
        # Filter by consensus threshold
        consensus = []
        for word, data in word_votes.items():
            if data["count"] >= self.threshold:
                avg_conf = data["total_conf"] / data["count"]
                # Boost confidence for multi-model agreement
                boost = 1.0 + (data["count"] - 1) * 0.1
                consensus.append((word, avg_conf * boost))
        
        consensus.sort(key=lambda x: x[1], reverse=True)
        return consensus
```

#### Strategy 3: Structured Output Enforcement

```python
STRUCTURED_OUTPUT_CONFIG = {
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "name": "bip39_candidates",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "candidates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "word": {
                                    "type": "string",
                                    "enum": list(BIP39_WORDS)  # Force valid words only
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 1.0
                                },
                                "reason": {
                                    "type": "string"
                                }
                            },
                            "required": ["word", "confidence", "reason"]
                        }
                    }
                },
                "required": ["candidates"]
            }
        }
    }
}
```

### 5.5 How to Combine LLM Output with Traditional Brute Force

```python
class HybridRecoveryEngine:
    """Combines LLM-guided search with traditional brute force."""
    
    def __init__(
        self,
        llm_generator: MultiProviderGenerator,
        brute_force_engine: BruteForceEngine,
        ranker: CandidateRanker,
    ):
        self.llm = llm_generator
        self.bf = brute_force_engine
        self.ranker = ranker
    
    async def recover_seed_phrase(
        self,
        context: RecoveryContext,
        target_address: str,
    ) -> Optional[List[str]]:
        """Hybrid recovery: LLM-guided priority + exhaustive brute force."""
        
        # Phase 1: LLM-guided search (fast, smart)
        result = await self._llm_guided_search(context, target_address)
        if result:
            return result
        
        # Phase 2: Hybrid - LLM suggestions + systematic brute force
        result = await self._hybrid_search(context, target_address)
        if result:
            return result
        
        # Phase 3: Full brute force (slow, exhaustive)
        result = await self._exhaustive_search(context, target_address)
        return result
    
    async def _llm_guided_search(
        self, context: RecoveryContext, target_address: str
    ) -> Optional[List[str]]:
        """Phase 1: Try LLM suggestions first (top candidates only)."""
        
        for position in context.missing_positions:
            candidates = await self.llm.generate_candidates(
                context, position, top_k=20
            )
            ranked = self.ranker.rank_candidates(candidates, context, position)
            
            for word, score in ranked[:10]:  # Try top 10 only
                test_phrase = context.known_words.copy()
                test_phrase[position] = word
                
                if self._validate_phrase(test_phrase, target_address):
                    return test_phrase
        
        return None
    
    async def _hybrid_search(
        self, context: RecoveryContext, target_address: str
    ) -> Optional[List[str]]:
        """Phase 2: LLM-ranked full wordlist with checksum pre-filter."""
        
        for position in context.missing_positions:
            # Get LLM ranking for ALL 2048 words
            candidates = await self._rank_all_bip39_words(context, position)
            
            # Filter by checksum first (eliminates ~94% of candidates)
            valid_candidates = [
                (word, score) for word, score in candidates
                if self.ranker._check_checksum(context, position, word)
            ]
            
            # Try LLM-ranked + checksum-valid candidates
            for word, score in valid_candidates:
                test_phrase = context.known_words.copy()
                test_phrase[position] = word
                
                if self._validate_phrase(test_phrase, target_address):
                    return test_phrase
        
        return None
    
    async def _rank_all_bip39_words(
        self, context: RecoveryContext, position: int
    ) -> List[Tuple[str, float]]:
        """Use LLM to rank all 2,048 BIP-39 words for a position."""
        
        # Batch processing: ask LLM to categorize all words
        prompt = f"""Categorize all 2,048 BIP-39 words by how likely they would 
appear at position {position} given these hints: {context.word_hints.get(position, 'none')}

Surrounding words: {context.known_words[max(0,position-2):position+3]}

Return categories:
- "highly_likely": Words that strongly match the hints
- "possible": Words that could match
- "unlikely": Words that don't match but can't be ruled out

Output as JSON with these three arrays."""
        
        # Fallback: Use embedding similarity for all words
        # This doesn't require LLM inference for all 2048 words
        return self._embedding_based_ranking(context, position)
```

### 5.6 Parallel LLM + Traditional Recovery

```python
class ParallelRecoveryOrchestrator:
    """Run LLM-guided and brute-force recovery in parallel."""
    
    def __init__(self, config: RecoveryConfig):
        self.llm_generator = LLMCandidateGenerator(config.primary_provider)
        self.bf_engine = BruteForceEngine(config.gpu_config)
        self.found = asyncio.Event()
        self.result = None
    
    async def recover(
        self, context: RecoveryContext, target_address: str
    ) -> Optional[List[str]]:
        """Run LLM and brute-force searches concurrently."""
        
        # Shared priority queue
        priority_queue = asyncio.PriorityQueue()
        tried_words = set()
        
        # Start parallel tasks
        tasks = [
            asyncio.create_task(
                self._llm_producer(context, priority_queue, tried_words)
            ),
            asyncio.create_task(
                self._brute_force_producer(context, priority_queue, tried_words)
            ),
            asyncio.create_task(
                self._consumer(context, target_address, priority_queue)
            ),
        ]
        
        # Wait for first success or all producers done
        await self.found.wait()
        
        # Cancel remaining tasks
        for task in tasks:
            task.cancel()
        
        return self.result
    
    async def _llm_producer(
        self, context: RecoveryContext,
        queue: asyncio.PriorityQueue,
        tried: set
    ):
        """LLM generates high-priority candidates."""
        for position in context.missing_positions:
            candidates = await self.llm_generator.generate_seed_candidates(
                context, position, top_k=100
            )
            for word, confidence in candidates:
                if word not in tried:
                    tried.add(word)
                    # Lower priority number = higher priority
                    priority = int((1.0 - confidence) * 1000)
                    await queue.put((priority, "llm", position, word))
    
    async def _brute_force_producer(
        self, context: RecoveryContext,
        queue: asyncio.PriorityQueue,
        tried: set
    ):
        """Systematic brute force fills in remaining candidates."""
        for word in BIP39_WORDLIST:
            if word not in tried:
                tried.add(word)
                # Brute force candidates get lowest priority (999)
                await queue.put((999, "bf", context.missing_positions[0], word))
    
    async def _consumer(
        self, context: RecoveryContext,
        target_address: str,
        queue: asyncio.PriorityQueue
    ):
        """Consume candidates in priority order and check them."""
        batch = []
        batch_size = 32  # GPU batch size
        
        while not self.found.is_set():
            try:
                priority, source, position, word = await asyncio.wait_for(
                    queue.get(), timeout=1.0
                )
                batch.append((position, word))
                
                if len(batch) >= batch_size:
                    results = await self._batch_check(
                        context, batch, target_address
                    )
                    if results:
                        self.result = results
                        self.found.set()
                    batch = []
            except asyncio.TimeoutError:
                # Process remaining batch
                if batch:
                    results = await self._batch_check(
                        context, batch, target_address
                    )
                    if results:
                        self.result = results
                        self.found.set()
                    batch = []
```

### 5.7 Error Handling and Fallback Strategies

```python
class RecoveryOrchestrator:
    """Main orchestrator with comprehensive error handling."""
    
    # Provider fallback chain (ordered by cost-effectiveness)
    PROVIDER_FALLBACK = [
        "ollama",       # Free, local, fast (if available)
        "deepseek",     # Cheapest cloud, good quality
        "groq",         # Ultra-fast, cheap
        "openai",       # Highest quality, expensive
        "anthropic",    # Fallback for complex reasoning
    ]
    
    async def execute_with_fallback(
        self,
        task: str,
        prompt: str,
        max_retries: int = 3,
    ) -> Optional[dict]:
        """Execute LLM task with provider fallback and retries."""
        
        for provider_name in self.PROVIDER_FALLBACK:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            
            for attempt in range(max_retries):
                try:
                    result = await self._query_provider(
                        provider, prompt, timeout=30 + attempt * 10
                    )
                    
                    # Validate result
                    if self._validate_result(task, result):
                        return result
                    else:
                        # Hallucination detected, retry with different temperature
                        prompt = self._adjust_prompt_for_accuracy(prompt)
                        continue
                        
                except httpx.TimeoutException:
                    self.logger.warning(
                        f"Timeout for {provider_name}, attempt {attempt+1}"
                    )
                    continue
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        # Rate limited - wait and retry
                        wait_time = 2 ** attempt
                        await asyncio.sleep(wait_time)
                        continue
                    elif e.response.status_code >= 500:
                        # Server error - try next provider
                        break
                    elif e.response.status_code == 401:
                        # Auth error - skip this provider
                        self.logger.error(
                            f"Auth failed for {provider_name}, skipping"
                        )
                        break
                        
                except (ConnectionError, httpx.ConnectError):
                    # Provider unreachable - try next
                    self.logger.warning(
                        f"Cannot connect to {provider_name}, trying fallback"
                    )
                    break
                    
                except json.JSONDecodeError:
                    # Malformed response
                    continue
            
        # All providers failed - fall back to non-LLM approach
        self.logger.error("All LLM providers failed, using fallback strategy")
        return await self._non_llm_fallback(task)
    
    async def _non_llm_fallback(self, task: str) -> Optional[dict]:
        """Fallback when no LLM is available."""
        
        if task == "seed_recovery":
            # Use pure brute force with checksum filtering
            return {"mode": "brute_force", "checksum_filter": True}
        
        elif task == "password_recovery":
            # Use common password lists + rule-based generation
            return {"mode": "dictionary_attack", "rules": "standard"}
        
        elif task == "word_similarity":
            # Use pre-computed embedding similarity
            return {"mode": "embedding_similarity", "source": "local_cache"}
        
        return None
```

### 5.8 Complete Integration Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    RECOVERY FLOW (End-to-End)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. USER INPUT                                                    │
│     ├── Partial seed phrase (with gaps)                           │
│     ├── Password hints / context                                  │
│     ├── Target wallet address (optional)                          │
│     └── User memory about missing words                           │
│                                                                   │
│  2. CONTEXT ANALYSIS (LLM-powered)                               │
│     ├── Classify recovery type:                                   │
│     │   ├── Missing seed words (1-4)                              │
│     │   ├── Wrong seed words (typo/confusion)                     │
│     │   ├── Forgotten password                                    │
│     │   └── Wrong word order                                      │
│     ├── Estimate search space size                                │
│     └── Select optimal strategy                                   │
│                                                                   │
│  3. LLM CANDIDATE GENERATION (Phase 1)                           │
│     ├── Generate initial candidate set (50-100 per position)      │
│     ├── Rank by confidence + context matching                     │
│     ├── Validate against BIP-39 wordlist                          │
│     └── Pre-filter by checksum validity                           │
│                                                                   │
│  4. FAST ATTEMPT (Phase 2)                                       │
│     ├── Try top-10 LLM candidates                                 │
│     ├── Batch GPU validation                                      │
│     └── Check address match                                       │
│                                                                   │
│  5. PARALLEL SEARCH (Phase 3)                                    │
│     ├── LLM thread: Generates + ranks expanded candidates        │
│     ├── Brute-force thread: Systematic enumeration               │
│     ├── Consumer thread: Batch validation                         │
│     └── First match wins, cancel all threads                      │
│                                                                   │
│  6. ADAPTIVE LEARNING (Phase 4)                                  │
│     ├── After every N failed attempts:                            │
│     │   ├── Feed failures back to LLM                             │
│     │   ├── Request new candidate generation                      │
│     │   └── Adjust strategy based on failure patterns             │
│     └── Progressive widening of search space                      │
│                                                                   │
│  7. RESULT                                                        │
│     ├── SUCCESS: Return recovered seed/password                   │
│     ├── PARTIAL: Report progress, save checkpoint                 │
│     └── FAILED: Suggest next steps (more info needed, etc.)      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 5.9 Cost Estimation

#### Estimated LLM API Costs for Recovery Scenarios

| Scenario | LLM Calls | Est. Tokens | DeepSeek Cost | OpenAI Cost | Ollama Cost |
|----------|-----------|-------------|---------------|-------------|-------------|
| 1 missing word | 5-10 | 5K-10K | <$0.01 | $0.05-0.10 | Free |
| 2 missing words | 20-50 | 20K-50K | $0.01-0.03 | $0.20-0.50 | Free |
| 3 missing words | 100-500 | 100K-500K | $0.05-0.30 | $1.00-5.00 | Free |
| Password recovery | 10-30 | 10K-30K | $0.01-0.02 | $0.10-0.30 | Free |
| Full phrase (impossible) | N/A | N/A | N/A | N/A | N/A |

**Recommendation**: Use DeepSeek or Ollama as primary provider for cost-effectiveness. Reserve OpenAI/Anthropic for complex reasoning tasks only.

### 5.10 Recommended Provider Strategy

```python
RECOMMENDED_STRATEGY = {
    # Primary: Local LLM (free, private, fast enough)
    "primary": {
        "provider": "ollama",
        "model": "llama3.1:8b",
        "use_case": "All candidate generation, word similarity, clustering",
        "reason": "Free, private, no rate limits, sufficient quality"
    },
    
    # Secondary: Cheap cloud (when local is unavailable or needs more power)
    "secondary": {
        "provider": "deepseek", 
        "model": "deepseek-chat",
        "use_case": "Complex reasoning, password profiling, adaptive learning",
        "reason": "Cheapest quality cloud API, good enough for most tasks"
    },
    
    # Tertiary: Fast inference (for high-throughput batch generation)
    "tertiary": {
        "provider": "groq",
        "model": "llama-3.1-8b-instant",
        "use_case": "Bulk candidate generation, embedding computation",
        "reason": "Fastest inference, cheapest per-token, good for bulk work"
    },
    
    # Premium: Best quality (for difficult cases, user willing to pay)
    "premium": {
        "provider": "openai",
        "model": "gpt-4o",
        "use_case": "Complex password profiling, deep reasoning about user hints",
        "reason": "Best quality output, most nuanced understanding"
    },
    
    # Aggregator: Fallback/routing (simplifies integration)
    "aggregator": {
        "provider": "openrouter",
        "model": "auto",  # Route to best available
        "use_case": "Fallback when primary providers are down",
        "reason": "Single API for 100+ models, automatic failover"
    }
}
```

---

## Appendix A: Quick-Start Provider Setup

### OpenAI
```bash
pip install openai
export OPENAI_API_KEY="sk-..."
```

### Anthropic
```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

### DeepSeek
```bash
pip install openai  # Uses OpenAI-compatible API
export DEEPSEEK_API_KEY="sk-..."
# Change base_url to https://api.deepseek.com/v1
```

### Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1
ollama pull nomic-embed-text  # For embeddings
# API at http://localhost:11434/v1 (no auth needed)
```

### Groq
```bash
pip install openai  # Uses OpenAI-compatible API
export GROQ_API_KEY="gsk_..."
# Change base_url to https://api.groq.com/openai/v1
```

### OpenRouter
```bash
pip install openai  # Uses OpenAI-compatible API
export OPENROUTER_API_KEY="sk-or-..."
# Change base_url to https://openrouter.ai/api/v1
```

---

## Appendix B: BIP-39 Wordlist Considerations

The BIP-39 English wordlist has specific properties important for LLM integration:

1. **2,048 words** - fixed, known set
2. **No duplicates** - first 4 characters are unique (can use first-4 as shorthand)
3. **Sorted alphabetically** - binary search possible
4. **Word lengths**: 3-8 characters
5. **Common confusion pairs**:
   - `abandon`/`ability` (both start with "ab")
   - `apple`/`apply` (one letter difference)
   - `buffalo`/`burden` (both start with "bu")
   - `cradle`/`crane`/`crash`/`crazy`/`cream`/`creek`/`crime` (all "cr___")
6. **Semantic clusters**: Many words fall into natural categories (nature, body, food, etc.)
7. **Checksum**: Last word encodes checksum bits, reducing valid candidates by ~94-97%

---

## Appendix C: Security & Ethical Considerations

1. **Never send complete seed phrases to cloud LLMs** - Always mask known words when querying
2. **Prefer local LLMs for sensitive data** - Ollama/LocalAI keep data on-device
3. **Rate limit your own queries** - Prevent accidental DoS of provider APIs
4. **Log all LLM interactions** - For debugging and audit trails
5. **Implement circuit breakers** - Stop after N failed attempts to prevent abuse
6. **User consent required** - Before sending any wallet data to cloud APIs
7. **No storage of seed phrases** - LLM context only, never persisted

---

*End of Research Document*
