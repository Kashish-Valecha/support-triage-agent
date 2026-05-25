#!/usr/bin/env python3
"""
HackerRank Orchestrate - Support Triage Agent
Processes support tickets using TF-IDF retrieval + HuggingFace Inference API
"""

import os
import sys
import csv
import json
import time
import random
import requests
from datetime import datetime
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load environment variables from .env file (if it exists)
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # dotenv not installed, will fall back to environment variables
    pass


# ============================================================================
# CONFIGURATION
# ============================================================================

SEED = 42
MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
HF_API_URL = f"https://api-inference.huggingface.co/models/{MODEL}"
TOP_K_DOCS = 3  # Number of relevant docs to retrieve
MAX_TOKENS = 1000  # Max tokens for response

# Paths
REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
TICKETS_CSV = REPO_ROOT / "support_tickets" / "support_tickets.csv"
OUTPUT_CSV = REPO_ROOT / "support_tickets" / "output.csv"

# Log file location
LOG_DIR = Path.home() / "hackerrank_orchestrate"
LOG_FILE = LOG_DIR / "log.txt"

# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """You are a support triage agent for HackerRank, Claude, and Visa.

Your job is to read support tickets and decide for each:
1. Whether to reply with a helpful answer (status: Replied)
2. Or escalate to a human (status: Escalated)

CRITICAL RULES:
- Use ONLY the provided support corpus. Do not use your training knowledge.
- Never hallucinate policies, features, or procedures that aren't in the corpus.
- ALWAYS REPLY when possible. Only escalate for critical security/legal/operational issues.
- ESCALATE ONLY IF the issue contains keywords like: fraud, hacked, stolen, unauthorized, lawsuit, legal, data breach, site down, or none of the pages.
- For all other issues (billing, features, account questions, general issues) — REPLY with helpful guidance from the corpus.
- Do NOT escalate just because information isn't explicit in corpus — try to provide helpful guidance anyway.

For EACH ticket, respond with a JSON object in an array. Return ONLY a JSON array with one object per ticket (no markdown, no extra text):
[
  {
    "ticket_id": "ticket identifier",
    "status": "Replied" or "Escalated",
    "product_area": "short category name (under 20 chars)",
    "response": "user-facing answer or escalation message",
    "justification": "brief explanation of your decision",
    "request_type": "product_issue", "feature_request", "bug", or "invalid"
  },
  ...
]

Ensure status is capitalized. Ensure product_area is never empty. Only output valid JSON array."""


# ============================================================================
# DOCUMENT LOADING
# ============================================================================

def load_documents() -> dict:
    """Load all .md files from data/ into a dict {path: content}."""
    documents = {}
    for md_file in DATA_DIR.rglob("*.md"):
        try:
            with open(md_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # Store relative path as key for traceability
                rel_path = md_file.relative_to(REPO_ROOT)
                documents[str(rel_path)] = content
        except Exception as e:
            print(f"Warning: Could not read {md_file}: {e}")
    return documents


# ============================================================================
# TF-IDF RETRIEVAL
# ============================================================================

class TFIDFRetriever:
    """TF-IDF based document retriever."""

    def __init__(self, documents: dict):
        """
        Args:
            documents: dict of {doc_id: content}
        """
        self.documents = documents
        self.doc_ids = list(documents.keys())
        self.doc_texts = list(documents.values())

        # Build TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            lowercase=True,
            ngram_range=(1, 2),
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.doc_texts)

    def retrieve(self, query: str, top_k: int = 5) -> list:
        """
        Retrieve top-k most relevant documents for a query.

        Args:
            query: Search query (usually the issue + subject)
            top_k: Number of documents to return

        Returns:
            List of (doc_id, content, score) tuples, sorted by relevance
        """
        try:
            query_vec = self.vectorizer.transform([query])
            scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]

            # Get top-k indices
            top_indices = np.argsort(scores)[-top_k:][::-1]

            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include docs with non-zero similarity
                    results.append(
                        (self.doc_ids[idx], self.doc_texts[idx], scores[idx])
                    )
            return results
        except Exception as e:
            print(f"Warning: Retrieval error: {e}")
            return []


# ============================================================================
# HUGGINGFACE INFERENCE API
# ============================================================================

def call_huggingface_api(
    batch_tickets: list,
    retriever: TFIDFRetriever,
    hf_token: str,
) -> str:
    """
    Call HuggingFace Inference API with a batch of tickets.

    Args:
        batch_tickets: List of up to 10 ticket dicts
        retriever: TFIDFRetriever instance for context retrieval
        hf_token: HuggingFace API token

    Returns:
        API response (should be JSON array)
    """
    # Build ticket descriptions and retrieve context for each
    tickets_text = ""
    all_context_docs = {}
    
    for i, ticket in enumerate(batch_tickets):
        issue = ticket.get("Issue", "").strip()
        subject = ticket.get("Subject", "").strip()
        company = ticket.get("Company", "").strip()
        query = f"{issue} {subject} {company}".strip()
        
        tickets_text += f"\n\nTICKET #{i+1}:\n"
        tickets_text += f"Subject: {subject}\n"
        tickets_text += f"Company: {company}\n"
        tickets_text += f"Issue: {issue}"
        
        # Retrieve context for this ticket
        context_docs = retriever.retrieve(query, top_k=TOP_K_DOCS)
        all_context_docs[i] = context_docs
    
    # Format context (shared corpus)
    context_text = "## SUPPORT CORPUS\n\n"
    seen_docs = set()
    for doc_list in all_context_docs.values():
        for doc_id, content, score in doc_list:
            if doc_id not in seen_docs:
                truncated = content[:500] + "..." if len(content) > 500 else content
                context_text += f"### {doc_id} (relevance: {score:.3f})\n{truncated}\n\n"
                seen_docs.add(doc_id)
    
    full_message = f"{tickets_text}\n\n{context_text}\n\nRespond with a JSON array with one result object per ticket (matching the order above)."
    combined_prompt = f"{SYSTEM_PROMPT}\n\n{full_message}"
    
    # Call HuggingFace API
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "inputs": combined_prompt,
        "parameters": {
            "max_new_tokens": MAX_TOKENS,
            "temperature": 0.3,
            "top_p": 0.95,
        },
    }
    
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # HuggingFace returns list with one element containing generated_text
        if isinstance(result, list) and len(result) > 0:
            response_text = result[0].get("generated_text", "")
        else:
            response_text = result.get("generated_text", "")
        
        return response_text
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: HuggingFace API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"DEBUG: Response: {e.response.text}")
        raise


# ============================================================================
# LOGGING
# ============================================================================

def setup_logging():
    """Create log directory if it doesn't exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_ticket(issue: dict, output: dict):
    """Append ticket processing to log file."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"\n## {timestamp}\n")
            f.write(f"ISSUE: {json.dumps(issue)}\n")
            f.write(f"OUTPUT: {json.dumps(output)}\n")
    except Exception as e:
        print(f"Warning: Could not log: {e}")


# ============================================================================
# MAIN AGENT
# ============================================================================

def main():
    """Main agent loop."""
    # Set seed for reproducibility
    random.seed(SEED)
    np.random.seed(SEED)

    # Setup
    setup_logging()

    # Check for API key
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("ERROR: HF_TOKEN environment variable not set")
        print("Please set your HuggingFace API token:")
        print("  export HF_TOKEN='your_token_here'")
        sys.exit(1)

    # Load documents
    print("Loading support corpus...")
    documents = load_documents()
    print(f"✓ Loaded {len(documents)} documents from data/")

    # Build retriever
    print("Building TF-IDF index...")
    retriever = TFIDFRetriever(documents)
    print("✓ TF-IDF index built\n")

    # Read tickets
    print(f"Reading support tickets from {TICKETS_CSV}...")
    tickets = []
    try:
        with open(TICKETS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            tickets = list(reader)
    except FileNotFoundError:
        print(f"ERROR: {TICKETS_CSV} not found")
        sys.exit(1)

    print(f"✓ Found {len(tickets)} tickets to process\n")

    # Process tickets in batches of 10
    output_rows = []
    batch_size = 10

    for batch_start in range(0, len(tickets), batch_size):
        batch_end = min(batch_start + batch_size, len(tickets))
        batch_tickets = tickets[batch_start:batch_end]
        batch_num = (batch_start // batch_size) + 1
        
        # Progress
        print(f"[Batch {batch_num} ({batch_start+1}-{batch_end}/{len(tickets)})] Processing...", end=" ", flush=True)

        # Call HuggingFace API with batch of tickets (with retry logic)
        response_text = None
        try:
            response_text = call_huggingface_api(batch_tickets, retriever, hf_token)
            # Strip markdown formatting if present
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]  # Get content between markers
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()  # Remove "json" prefix
            response_text = response_text.strip()
            # Parse JSON array response
            outputs = json.loads(response_text)
            if not isinstance(outputs, list):
                outputs = [outputs]  # Handle single object wrapped in list
        except Exception as e:
            # Retry once after 10 seconds (rate limit or transient error)
            print(f"ERROR (retrying in 10s): {e}")
            time.sleep(10)
            try:
                response_text = call_huggingface_api(batch_tickets, retriever, hf_token)
                # Strip markdown formatting if present
                response_text = response_text.strip()
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:].strip()
                response_text = response_text.strip()
                outputs = json.loads(response_text)
                if not isinstance(outputs, list):
                    outputs = [outputs]
            except json.JSONDecodeError as e2:
                print(f"ERROR: Could not parse response as JSON after retry: {e2}")
                # Create error placeholders for each ticket in batch
                outputs = [
                    {
                        "status": "escalated",
                        "product_area": "",
                        "response": "Error processing ticket",
                        "justification": "Failed to parse response after retry",
                        "request_type": "invalid",
                    }
                    for _ in batch_tickets
                ]
            except Exception as e2:
                print(f"ERROR: Retry failed: {e2}")
                outputs = [
                    {
                        "status": "escalated",
                        "product_area": "",
                        "response": "Error processing ticket",
                        "justification": f"API error after retry: {str(e2)}",
                        "request_type": "invalid",
                    }
                    for _ in batch_tickets
                ]

        # Ensure we have the right number of outputs
        while len(outputs) < len(batch_tickets):
            outputs.append({
                "status": "escalated",
                "product_area": "",
                "response": "Error processing ticket",
                "justification": "Missing response from batch",
                "request_type": "invalid",
            })

        # Process each output in batch
        for i, (ticket, output) in enumerate(zip(batch_tickets, outputs[:len(batch_tickets)])):
            issue = ticket.get("Issue", "").strip()
            subject = ticket.get("Subject", "").strip()
            company = ticket.get("Company", "").strip()
            
            # Print routing info for visibility
            print(f"\n  Ticket #{i+1}: {subject[:50] if subject else 'No subject'}")
            print(f"    Company: {company if company else 'Unknown'}")

            # Validate output structure
            if not isinstance(output, dict):
                output = {}
            
            required_fields = {"status", "product_area", "response", "justification", "request_type"}
            if not required_fields.issubset(output.keys()):
                output = {
                    "status": output.get("status", "escalated"),
                    "product_area": output.get("product_area", ""),
                    "response": output.get("response", "Error processing ticket"),
                    "justification": output.get("justification", "Invalid response format"),
                    "request_type": output.get("request_type", "invalid"),
                }

            # Log
            log_entry = {
                "issue": issue[:100],
                "subject": subject[:50],
                "company": company,
            }
            log_ticket(log_entry, output)

            # Normalize output before collecting
            # Capitalize status
            output['status'] = output.get('status', 'Escalated').lower().capitalize()
            if output['status'] not in ['Replied', 'Escalated']:
                output['status'] = 'Escalated'
            
            # Normalize request_type to allowed values
            req_type = output.get('request_type', 'product_issue').lower()
            if req_type == 'security_issue':
                req_type = 'bug'
            if req_type not in ['product_issue', 'feature_request', 'bug', 'invalid']:
                req_type = 'product_issue'
            output['request_type'] = req_type
            
            # Ensure product_area is not empty (fallback to company)
            product_area = output.get('product_area', '').strip()
            if not product_area:
                company_fallback = ticket.get('Company', '').strip()
                product_area = company_fallback if company_fallback else 'general'
            # Truncate to 20 chars if too long
            if len(product_area) > 20:
                product_area = product_area[:17] + '...'
            output['product_area'] = product_area

            # Print classification for visibility
            print(f"    → Classification: {output['status']} | Product: {product_area} | Type: {req_type}")

            # Collect output row
            output_rows.append(output)

        print("Done")
        
        # Rate limiting: sleep 3 seconds between API calls
        time.sleep(3)

    # Write output CSV
    print(f"\nWriting output to {OUTPUT_CSV}...")
    try:
        fieldnames = ["Status", "Product Area", "Response", "Justification", "Request Type"]
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in output_rows:
                # Map lowercase keys to capitalized header names
                normalized_row = {
                    "Status": row.get('status', 'Escalated'),
                    "Product Area": row.get('product_area', ''),
                    "Response": row.get('response', ''),
                    "Justification": row.get('justification', ''),
                    "Request Type": row.get('request_type', 'invalid')
                }
                writer.writerow(normalized_row)
        print(f"✓ Wrote {len(output_rows)} rows to output.csv")
    except Exception as e:
        print(f"ERROR: Could not write output CSV: {e}")
        sys.exit(1)

    print("\n✓ Agent completed successfully")
    print(f"Log: {LOG_FILE}")
    print(f"Output: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
