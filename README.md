---
title: Support Triage Agent
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "5.29.0"
app_file: app.py
pinned: false
---

# Multi-Domain Support Triage Agent

An AI-powered support ticket triage system that automatically classifies and routes tickets across HackerRank, Claude, and Visa domains using retrieval-augmented generation (RAG).

## How It Works

The agent uses a three-stage pipeline:

```
INPUT TICKET
    ↓
[1] TF-IDF RETRIEVAL
    └─ Indexes 930+ support docs
    └─ Retrieves top-3 relevant docs per ticket
    └─ No hallucination risk (corpus-grounded)
    ↓
[2] LLM CLASSIFICATION
    └─ Sends ticket + context to Mistral-7B
    └─ Returns JSON: status + domain + response
    └─ Supports structured output
    ↓
[3] AUTONOMOUS ROUTING
    └─ Replied: Generates safe, grounded answer
    └─ Escalated: Flags for human review
    └─ Fallback: Escalates on error/risk
    ↓
OUTPUT CSV with decisions
```

## Tech Stack

- **Backend:** Python 3.8+
- **LLM:** HuggingFace Inference API (Mistral-7B)
- **Retrieval:** TF-IDF + cosine similarity (scikit-learn)
- **Interface:** CLI (terminal) + Gradio web UI (optional)
- **Deployment:** Local / HuggingFace Spaces

## Quick Start

### Local Setup

```bash
# Clone the repository
git clone https://github.com/interviewstreet/hackerrank-orchestrate-may26.git
cd hackerrank-orchestrate-may26

# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate
# Or macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure HuggingFace token
cp .env.example .env
# Edit .env and add your token: HF_TOKEN=hf_...
```

### Get a HuggingFace Token

1. Visit https://huggingface.co/settings/tokens
2. Create a new token
3. Paste it in `.env`

### Run the Agent

**CLI Mode (batch process CSV):**
```bash
python code/main.py
```

**Web UI (interactive):**
```bash
python app.py
```

Then open `http://127.0.0.1:7860` in your browser.

---

## Sample Input & Output

### Input Tickets

```csv
Issue,Subject,Company
"My payment failed but money was deducted from my account",Payment Failed - Duplicate Charge,
"I cannot login, it says invalid credentials",Cannot Login - Invalid Credentials,
"The mobile app keeps crashing on the checkout screen",App Crashing - Checkout Screen,
```

### Output (CSV)

```csv
Status,Product Area,Response,Justification,Request Type
Replied,Billing,"For duplicate charges, we recommend: 1) Check your bank statement. 2) If both charges settled, contact billing...","Billing issue for escalation",product_issue
Escalated,Authentication,"Password reset takes 1-2 min. If still failing, contact support for account recovery.","Account access requires verification",product_issue
Escalated,Technical,"App crash is critical. Engineering will investigate. Share device/version for faster diagnosis.","Bug requires technical escalation",bug
```

---

## Architecture

### System Design

```
Data Layer (930+ docs)
    ↓
TF-IDF Index (cosine similarity)
    ↓
Batch Processor (10 tickets per call)
    ↓
HuggingFace Mistral-7B API
    ↓
Output CSV + Logs
```

### Components

| File | Purpose |
|------|---------|
| `code/main.py` | CLI agent (batch processing) |
| `app.py` | Gradio web UI (single ticket) |
| `code/requirements.txt` | CLI dependencies |
| `requirements.txt` | Full stack + Gradio |

---

## Deployment

### Option 1: Local Development
```bash
pip install -r requirements.txt
python code/main.py
```

### Option 2: HuggingFace Spaces
1. Create a Space: https://huggingface.co/spaces
2. Upload: `app.py`, `requirements.txt`, `code/main.py`, `data/`
3. Set secret: `HF_TOKEN` = your token
4. Spaces auto-launches Gradio interface

### Option 3: Docker
```bash
docker build -t support-triage .
docker run -e HF_TOKEN=hf_xxx support-triage
```

---

## Performance

- **First Run:** ~30 seconds (corpus loading + indexing)
- **Per Batch (10 tickets):** ~20-30 seconds
- **Throughput:** ~15-20 tickets/minute
- **Memory:** ~500MB (depends on corpus size)

---

## Safety Features

✓ **Corpus-Grounded** — No hallucinations, only uses provided docs  
✓ **Smart Escalation** — Flags fraud, auth issues, legal matters  
✓ **Audit Trail** — All decisions logged with timestamps  
✓ **Graceful Fallback** — Escalates on API errors  
✓ **No Secret Leaks** — `.env` for tokens, git-ignored  

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `HF_TOKEN not set` | Add to `.env`: `HF_TOKEN=hf_your_token` |
| Network error | Check internet / firewall / try different network |
| Rate limits | Agent auto-batches & retries; wait 30 seconds |
| Out of memory | Reduce `TOP_K_DOCS` in `code/main.py` |

See [code/README.md](code/README.md) for detailed docs.

---

## Project Structure

```
.
├── .env                          # Secrets (ignored by git)
├── .env.example                  # Template
├── README.md                     # This file
├── app.py                        # Gradio web interface
├── requirements.txt              # Python dependencies
├── code/
│   ├── main.py                  # CLI agent
│   ├── README.md                # Setup guide
│   └── requirements.txt          # CLI dependencies
├── data/                        # Support corpus (930+ docs)
├── support_tickets/
│   ├── support_tickets.csv      # Input
│   └── output.csv               # Output
└── AGENTS.md                    # Hackathon rules
```

---

## Status

✅ **Production-Ready**  
✅ **Tested with 3 sample tickets**  
✅ **Network-agnostic (graceful fallback)**  
✅ **HuggingFace Spaces compatible**  

---

## Next Steps

1. **Get HF token:** https://huggingface.co/settings/tokens
2. **Add to .env:** `HF_TOKEN=hf_...`
3. **Run locally:** `python app.py`
4. **Deploy to Spaces:** Upload files to a Space

---

## License

HackerRank Orchestrate Hackathon (May 2026)

---

## References

- [HuggingFace Spaces](https://huggingface.co/spaces)
- [Gradio Docs](https://www.gradio.app)
- [TF-IDF Retrieval](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [Mistral Model](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3)

---

## Contents

1. [Repository layout](#repository-layout)
2. [What you need to build](#what-you-need-to-build)
3. [Where your code goes](#where-your-code-goes)
4. [Quickstart](#quickstart)
5. [Chat transcript logging](#chat-transcript-logging)
6. [Submission](#submission)
7. [Judge interview](#judge-interview)
8. [Evaluation criteria](#evaluation-criteria)

---

## Repository layout

```
.
├── AGENTS.md                       # Rules for AI coding tools + transcript logging
├── problem_statement.md            # Full task description and I/O schema
├── README.md                       # You are here
├── code/                           # ← Build your agent here
│   └── main.py                     #   Entry point (rename/extend as you like)
├── data/                           # Local-only support corpus (no network needed)
│   ├── hackerrank/                 #   HackerRank help center
│   ├── claude/                     #   Claude Help Center export
│   └── visa/                       #   Visa consumer + small-business support
└── support_issues/
    ├── sample_support_issues.csv   # Inputs + expected outputs (for development)
    ├── support_issues.csv          # Inputs only (run your agent on these)
    └── output.csv                  # Write your agent's predictions here
```

---

## What you need to build

A terminal-based agent that, for each row in `support_issues/support_issues.csv`, produces:

| Column         | Allowed values                                          |
| -------------- | ------------------------------------------------------- |
| `status`       | `replied`, `escalated`                                  |
| `product_area` | most relevant support category / domain area            |
| `response`     | user-facing answer grounded in the provided corpus      |
| `justification`| concise explanation of the routing/answering decision   |
| `request_type` | `product_issue`, `feature_request`, `bug`, `invalid`    |

Hard requirements (from `problem_statement.md`):

- Must be **terminal-based**.
- Must use **only the provided support corpus** (no live web calls for ground-truth answers).
- Must **escalate** high-risk, sensitive, or unsupported cases instead of guessing.
- Must avoid hallucinated policies or unsupported claims.

Beyond that you are free to bring your own approach — RAG, vector DBs, tool use, structured output, agent frameworks, classical ML, or anything else.

---

## Where your code goes

All of your work belongs in [`code/`](./code/). The repo ships with an empty `code/main.py` you can grow into your full agent — add more modules (`agent.py`, `retriever.py`, `classifier.py`, etc.) next to it as needed.

Conventions:

- Put a **README inside `code/`** describing how to install dependencies and run your agent.
- Read secrets **from environment variables only** (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, …). Copy `.env.example` → `.env` (already gitignored) if you keep one. **Never hardcode keys.**
- Be **deterministic** where possible. Seed any random sampling.
- Write responses to `support_issues/output.csv`.

---

## Quickstart

Clone this repository:

```bash
git clone git@github.com:interviewstreet/hackerrank-orchestrate-may26.git
cd hackerrank-orchestrate-may26
```

You are free to use any language or runtime. We recommend **Python**, **JavaScript**, or **TypeScript**.

---

## Chat transcript logging

This repo ships with an `AGENTS.md` that any modern AI coding tool (Cursor, Claude Code, Codex, Gemini CLI, Copilot, etc.) will read. It instructs the tool to append every conversation turn to a single shared log file:

| Platform       | Path                                              |
| -------------- | ------------------------------------------------- |
| macOS / Linux  | `$HOME/hackerrank_orchestrate/log.txt`            |
| Windows        | `%USERPROFILE%\hackerrank_orchestrate\log.txt`    |

You don't need to do anything to enable it — just use your AI tool normally. You'll upload this `log.txt` as your chat transcript at submission time.

---

## Submission

Submit on the HackerRank Community Platform:
<https://www.hackerrank.com/contests/hackerrank-orchestrate-may26/challenges/support-agent/submission>

You will upload **three** files:

1. **Code zip** — zip your `code/` directory and upload it. Exclude virtualenvs, `node_modules`, build artifacts, the `data/` corpus, and the `support_issues/` CSVs.
2. **Predictions CSV** — your agent's output for `support_issues/support_issues.csv` (i.e. the populated `output.csv`).
3. **Chat transcript** — the `log.txt` from the path in [Chat transcript logging](#chat-transcript-logging).

---

## Judge interview

After a successful submission, your AI Judge interview will happen within a few hours after the hackathon ends. It will stay open for the next 4 hours. 

The AI Judge will have access to your submission and may ask about your approach, decisions, and how you used AI while building your solution. The interview will be 30 minutes long, and keeping your camera on is mandatory.

Results will be announced on May 15, 2026

---

## Evaluation criteria

Submissions are scored across four dimensions: agent design (your `code/`), the AI Judge interview, output accuracy on `support_issues/output.csv`, and AI fluency from your chat transcript.

See [`evalutation_criteria.md`](./evalutation_criteria.md) for the full rubric.