# Vaani AI
> Autonomous social media AI agent invoked via mentions, powered exclusively by Hugging Face.

Vaani AI is an autonomous AI agent designed for social media platforms such as Twitter/X. Users mention `@vaaniai` in a post or reply with their query. Vaani AI ingests the mention, generates a solution using Hugging Face models (via local transformers pipeline or Inference API), formats the response within character constraints and thread structures, and replies directly.

The system includes a fine-tuning data collector that records interactions in Alpaca/ShareGPT JSONL format for continuous fine-tuning with LoRA / PEFT.

---

## Key Features

- **Mention-Based Invocation**: Detects tag mentions, strips handle tags, and isolates user intent.
- **Hugging Face Architecture**:
  - **Local Transformers Pipeline**: Runs open models (such as `Qwen/Qwen2.5-0.5B-Instruct`) locally on CPU or GPU.
  - **LoRA Adapter Support**: Loads fine-tuned LoRA weights dynamically via `peft`.
  - **Hugging Face Inference API**: Connects to serverless HF endpoints for remote inference.
  - **Mock Engine**: Provides an offline provider for rapid local testing.
- **Continuous Fine-Tuning**:
  - Records solved interactions to `data/dataset.jsonl` in instruction-tuning format.
  - Includes automated fine-tuning pipelines using `trl.SFTTrainer` and `peft.LoraConfig`.
- **Deduplication & State Management**:
  - SQLite database (`data/vaani.db`) tracks processed tweet IDs and cursor pagination to prevent duplicate responses.
- **Formatting & Threading**:
  - Sanitizes markdown formatting unsupported by Twitter.
  - Enforces the 280-character limit and segments longer answers into numbered thread replies.
- **Interactive Simulator**:
  - Terminal-based CLI simulator for testing mention processing without requiring active Twitter API credentials.

---

## Project Structure

```
vaani-AI/
├── pyproject.toml              # Project dependencies and packaging
├── .env.example                # Configuration template
├── .env                        # Local environment variables
├── README.md                   # Project documentation
├── main.py                     # CLI entry point
├── data/
│   ├── vaani.db                # SQLite state and mention deduplication database
│   └── dataset.jsonl           # Interaction instruction dataset
├── vaani/
│   ├── __init__.py
│   ├── config.py               # Settings management
│   ├── storage.py              # SQLite storage layer
│   ├── dataset_collector.py    # Interaction dataset logger
│   ├── agent.py                # Core orchestrator
│   ├── simulator.py            # CLI mention simulator
│   ├── llm/
│   │   ├── __init__.py         # LLM provider factory
│   │   ├── base.py             # LLM interface
│   │   ├── prompt.py           # Persona and system prompts
│   │   ├── mock.py             # Offline provider
│   │   ├── hf_local.py         # Local Transformers + PEFT LoRA
│   │   └── hf_inference.py     # HF InferenceClient provider
│   ├── twitter/
│   │   ├── __init__.py
│   │   ├── formatter.py        # Query cleaner and thread chunker
│   │   ├── client.py           # Twitter API v2 client
│   │   └── poller.py           # Mentions polling service
│   └── fine_tune/
│       ├── __init__.py
│       ├── dataset_loader.py   # Dataset ingestion for Dolly 15k and Alpaca
│       ├── train.py            # LoRA fine-tuning engine
│       ├── train_stub.py       # Fine-tuning script
│       └── colab_finetune.ipynb # Google Colab notebook for GPU training
└── tests/
    ├── test_storage.py
    ├── test_formatter.py
    ├── test_dataset_collector.py
    └── test_agent.py
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+
- `uv` or `pip`

### 2. Installation
```bash
uv venv
.venv\Scripts\activate
uv pip install -e ".[dev]"
```

Alternatively, using standard pip:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Configuration
Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```

Configuration parameters in `.env`:
```ini
BOT_HANDLE=vaaniai

HF_MODE=local
HF_MODEL_ID=Qwen/Qwen2.5-0.5B-Instruct
HF_DEVICE=cpu
HF_LORA_PATH=

TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
TWITTER_BEARER_TOKEN=
```

---

## Usage Modes

### Mode 1: Interactive CLI Simulator
Test mention handling locally in your terminal:
```bash
python main.py --mode simulate
```

### Mode 2: Test Hugging Face Model
Verify inference through the configured Hugging Face model and LoRA adapter:
```bash
python main.py --mode test-hf
```

### Mode 3: View Dataset & Storage Statistics
Check the count of collected training samples and processed mentions:
```bash
python main.py --mode stats
```

### Mode 4: Live Twitter Bot
Start polling Twitter for mentions:
```bash
python main.py --mode live
```

---

## Fine-Tuning Guide (LoRA / PEFT)

Vaani AI logs interactions in instruction-tuning format:

```json
{
  "instruction": "You are Vaani AI (@vaaniai), an intelligent, concise, and polite social media assistant. Solve the user's question clearly and accurately within tweet limits.",
  "input": "explain what is an API in simple terms",
  "output": "An API (Application Programming Interface) is like a restaurant menu...",
  "author": "simulator_user",
  "source": "cli_simulator",
  "timestamp": "2026-09-22T09:12:44.090482+00:00"
}
```

### 1. Download Open Datasets
Download and preprocess open instruction datasets (such as Databricks Dolly 15k):
```bash
python main.py --mode download-data
```

### 2. Run LoRA Fine-Tuning Locally
```bash
python main.py --mode train
```

Custom training parameters can also be passed directly:
```bash
python -m vaani.fine_tune.train \
    --model_id Qwen/Qwen2.5-0.5B-Instruct \
    --dataset_path data/train_large.jsonl \
    --output_dir checkpoints/vaani-lora \
    --epochs 3
```

### 3. Google Colab GPU Training
For GPU acceleration, run `vaani/fine_tune/colab_finetune.ipynb` in Google Colab.

### 4. Activating Fine-Tuned Weights
Set the adapter path in `.env`:
```ini
HF_MODE=local
HF_MODEL_ID=Qwen/Qwen2.5-0.5B-Instruct
HF_LORA_PATH=checkpoints/vaani-lora
```

---

## Running Automated Tests

Run the test suite:
```bash
pytest -v
```

---

## License
This project is licensed under the MIT License - see the LICENSE file for details.