# Support Triage Agent

A terminal-based support ticket triage agent that uses TF-IDF retrieval and HuggingFace Inference API to classify and route support tickets from HackerRank, Claude, and Visa ecosystems.

## Quick Start

### 1. Get a HuggingFace API Token

1. Go to [huggingface.co](https://huggingface.co)
2. Sign up or log in
3. Navigate to [Settings → API Tokens](https://huggingface.co/settings/tokens)
4. Create a new token (name it something like "hackerrank-orchestrate")
5. Copy the token

### 2. Set Up Environment

```bash
# Navigate to the project root (not the code/ directory)
cd hackerrank-orchestrate-may26

# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r code/requirements.txt

# Create .env file and add your token
# Edit the .env file and replace the placeholder with your actual token
```

### 3. Run the Agent

```bash
python code/main.py
```

---

## What It Does

The agent processes each support ticket in `support_tickets/support_tickets.csv` by:

1. **Loading the corpus** — reads 931 support documentation files from `data/`
2. **Building TF-IDF index** — creates a semantic index for fast retrieval
3. **Processing tickets** — for each ticket:
   - Retrieves the 3 most relevant support docs (TF-IDF + cosine similarity)
   - Sends the ticket + retrieved context to HuggingFace's Mistral-7B model
   - Gets back a JSON response with:
     - `status`: "Replied" or "Escalated"
     - `product_area`: short category (< 20 chars)
     - `response`: user-facing answer grounded in the corpus
     - `justification`: why this routing decision
     - `request_type`: "product_issue", "feature_request", "bug", or "invalid"
4. **Writing output** — saves predictions to `support_tickets/output.csv`

---

## Architecture

```
main.py
├── load_documents()              # Load all .md files from data/
├── TFIDFRetriever                # Build TF-IDF index + retrieve top-k docs
├── call_huggingface_api()        # Call HF Inference API with batch
├── setup_logging()               # Create log directory
└── main()                        # Orchestrate the flow
```

### Key Components

| Component | Purpose |
|-----------|---------|
| **TFIDFRetriever** | Builds a TF-IDF vectorizer on the corpus and retrieves the most relevant documents for each ticket query |
| **call_huggingface_api()** | Calls HF Inference API with a batch of tickets (up to 10) and retrieved context |
| **System Prompt** | Instructs the LLM to classify tickets, decide on status, and escalate high-risk cases |
| **Batch Processing** | Processes up to 10 tickets per API call (more efficient than 1-by-1) |

---

## Configuration

Edit these in `code/main.py`:

```python
MODEL = "mistralai/Mistral-7B-Instruct-v0.3"  # HF model ID
TOP_K_DOCS = 3                                  # Docs to retrieve per ticket
MAX_TOKENS = 1000                               # Max output tokens
```

---

## Troubleshooting

### "HF_TOKEN environment variable not set"

**Solution:** Add your token to the `.env` file:

```bash
# In .env at project root:
HF_TOKEN=hf_your_actual_token_here
```

Then re-run:

```bash
python code/main.py
```

### API Rate Limits

The agent includes:
- Automatic retry logic (waits 10 seconds before retry)
- 3-second delay between batches
- Batch size of 10 tickets (more efficient than single calls)

### Empty or Invalid Responses

If the API returns malformed JSON:
1. The agent will try once more after 10 seconds
2. If it still fails, it logs an error and escalates that ticket
3. Check the log file: `~/hackerrank_orchestrate/log.txt` (macOS/Linux) or `%USERPROFILE%\hackerrank_orchestrate\log.txt` (Windows)

---

## Output

The agent writes to `support_tickets/output.csv` with columns:

| Column | Example |
|--------|---------|
| Status | `Replied` |
| Product Area | `Claude Workspace` |
| Response | `To restore your access, please contact your workspace admin...` |
| Justification | `User is not owner/admin; escalation required` |
| Request Type | `product_issue` |

---

## Example Run

```
Loading support corpus...
✓ Loaded 931 documents from data/
Building TF-IDF index...
✓ TF-IDF index built

Reading support tickets from ../support_tickets/support_tickets.csv...
✓ Found 3 tickets to process

[Batch 1 (1-3/3)] Processing...
  Ticket #1: I lost access to my Claude team workspace
    Company: Claude
    → Classification: Escalated | Product: Claude | Type: product_issue
  Ticket #2: I completed a HackerRank test...
    Company: HackerRank
    → Classification: Escalated | Product: HackerRank | Type: product_issue
  Ticket #3: I used my Visa card...
    Company: Visa
    → Classification: Escalated | Product: Visa | Type: invalid
Done

Writing output to ../support_tickets/output.csv...
✓ Wrote 3 rows to output.csv

✓ Agent completed successfully
Log: /home/user/hackerrank_orchestrate/log.txt
Output: ../support_tickets/output.csv
```

---

## Logging

Every ticket processing is logged to:
- **macOS/Linux:** `~/.hackerrank_orchestrate/log.txt`
- **Windows:** `%USERPROFILE%\hackerrank_orchestrate\log.txt`

Logs include:
- Timestamp
- Ticket details (issue, subject, company)
- Agent's classification output (status, product_area, response, etc.)

---

## Model Info

**Mistral 7B Instruct v0.3**
- Fast, lightweight (~7B parameters)
- Free tier available on HuggingFace
- Supports instruction-following with structured output (JSON)
- Good for classification and routing tasks

---

## Development & Testing

To test locally before running on full dataset:

```bash
# Use sample_support_tickets.csv (if available)
# Edit TICKETS_CSV in main.py:
TICKETS_CSV = REPO_ROOT / "support_tickets" / "sample_support_tickets.csv"

# Then run:
python code/main.py
```

---

## Performance Notes

- **First run:** ~30 seconds (building TF-IDF index)
- **Per batch of 10 tickets:** ~20-30 seconds (API call + wait time)
- **Total for 3 tickets:** ~1 minute (including index build)

---

## Support

For issues:
1. Check the log file (see Logging section above)
2. Ensure your HF_TOKEN is valid and has API access
3. Verify network connectivity to `api-inference.huggingface.co`
4. Check system time (API may reject old timestamps)

```bash
python code/main.py
```

Expected output:
```
Loading support corpus...
Loaded 931 documents from data/
Building TF-IDF index...
Found 56 tickets to process

[1/56] Processing... Done
[2/56] Processing... Done
...
[56/56] Processing... Done

Writing output to support_tickets/output.csv...
Wrote 56 rows to output.csv

✓ Agent completed successfully
Log: C:\Users\YourUser\hackerrank_orchestrate\log.txt
Output: support_tickets/output.csv
```

## Output

### `support_tickets/output.csv`

CSV file with one row per ticket:

| Column | Values | Meaning |
|--------|--------|---------|
| `status` | `replied`, `escalated` | Whether agent answered or escalated |
| `product_area` | string | Most relevant support category |
| `response` | string | User-facing answer |
| `justification` | string | Concise explanation of decision |
| `request_type` | `product_issue`, `feature_request`, `bug`, `invalid` | Request classification |

### `log.txt`

Append-only log file at `~/.hackerrank_orchestrate/log.txt` containing:
- Timestamp
- Input issue (Issue, Subject, Company)
- Output (status, product_area, response, justification, request_type)

## Implementation Details

### TF-IDF Retrieval

- Uses sklearn's `TfidfVectorizer` with 1-2 gram tokens
- Retrieves top-5 documents with highest cosine similarity
- Falls back to escalation if no relevant docs found (score < threshold)

### Claude System Prompt

The agent is instructed to:
- Use ONLY the provided corpus
- Never hallucinate policies or procedures
- Escalate for: fraud, account compromise, billing disputes, legal threats, bugs like "site down"
- Output only valid JSON with required fields

### Determinism

- Fixed random seed (42) for reproducibility
- Seeded NumPy for any randomness in TF-IDF
- No stochastic sampling in retrieval

## Troubleshooting

### "ANTHROPIC_API_KEY environment variable not set"
Set your API key before running. See Installation step 3.

### "support_tickets.csv not found"
Ensure you're running from the repository root: `python code/main.py`

### API rate limits
If you hit rate limits, the agent will error out. Wait and retry.

### Missing documents
If documents fail to load (e.g., filename too long on Windows), they're skipped with a warning. The agent continues with available docs.

## Performance

- **Load time**: ~2 seconds (load 931 docs + build TF-IDF index)
- **Processing time**: ~30-60 seconds for 56 tickets (~1 sec per ticket, including API latency)
- **Total runtime**: ~1 minute

## Dependencies

See `requirements.txt`:
- `anthropic>=0.28.0` — Anthropic Claude API
- `scikit-learn>=1.3.0` — TF-IDF vectorizer
- `numpy>=1.24.0` — Matrix operations

## Notes

- The agent prioritizes **safety** over coverage: when in doubt, it escalates.
- Retrieved documents are shown in the Claude prompt with relevance scores.
- The system prompt is strict: it will not hallucinate features or procedures.
