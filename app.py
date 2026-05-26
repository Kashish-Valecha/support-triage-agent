#!/usr/bin/env python3
"""
HackerRank Orchestrate - Gradio Web Interface
Interactive support ticket classification UI for HuggingFace Spaces
"""

import os
import sys
import json
import time
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "code"))

import gradio as gr
from dotenv import load_dotenv
from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load environment variables
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# ============================================================================
# CONFIGURATION
# ============================================================================

MODEL = "google/gemma-2-2b-it"
TOP_K_DOCS = 3
MAX_TOKENS = 500

REPO_ROOT = Path(__file__).parent
DATA_DIR = REPO_ROOT / "data"

# System prompt for classification
SYSTEM_PROMPT = """You are a support triage agent for HackerRank, Claude, and Visa.

Your job is to read a support ticket and decide:
1. Whether to reply with a helpful answer (status: Replied)
2. Or escalate to a human (status: Escalated)

CRITICAL RULES:
- Use ONLY the provided support corpus. Do not use your training knowledge.
- Never hallucinate policies, features, or procedures not in the corpus.
- ALWAYS REPLY when possible. Only escalate for critical security/legal/operational issues.
- ESCALATE IF the issue contains: fraud, hacked, stolen, unauthorized, lawsuit, legal, data breach, site down, or no relevant docs found.
- For billing, features, account questions, general issues — REPLY with helpful guidance from corpus.
- Do NOT escalate just because information isn't explicit in corpus — try to provide helpful guidance anyway.

Respond with a JSON object (NOT an array):
{
  "status": "Replied" or "Escalated",
  "product_area": "short category name (under 20 chars)",
  "response": "user-facing answer or escalation message",
  "justification": "brief explanation of your decision",
  "request_type": "product_issue", "feature_request", "bug", or "invalid"
}

Only output valid JSON."""

# ============================================================================
# GLOBAL STATE (loaded once on startup)
# ============================================================================

class TriageAgent:
    """Singleton triage agent with cached corpus and retriever."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        print("🔄 Initializing support triage agent...")
        
        # Load documents
        print("📚 Loading support corpus...")
        self.documents = self._load_documents()
        print(f"✓ Loaded {len(self.documents)} documents")
        
        # Build TF-IDF retriever
        print("🔧 Building TF-IDF index...")
        self.retriever = self._build_retriever(self.documents)
        print("✓ TF-IDF index built")
        
        self._initialized = True
    
    def _load_documents(self):
        """Load all .md files from data/ directory."""
        documents = {}
        if not DATA_DIR.exists():
            print(f"⚠️ Warning: data/ directory not found at {DATA_DIR}")
            return documents
        
        for md_file in DATA_DIR.rglob("*.md"):
            try:
                with open(md_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    rel_path = md_file.relative_to(REPO_ROOT)
                    documents[str(rel_path)] = content
            except Exception as e:
                print(f"⚠️ Warning: Could not read {md_file}: {e}")
        
        return documents
    
    def _build_retriever(self, documents):
        """Build TF-IDF vectorizer on corpus."""
        doc_ids = list(documents.keys())
        doc_texts = list(documents.values())
        
        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            lowercase=True,
            ngram_range=(1, 2),
        )
        tfidf_matrix = vectorizer.fit_transform(doc_texts)
        
        return {
            "vectorizer": vectorizer,
            "tfidf_matrix": tfidf_matrix,
            "doc_ids": doc_ids,
            "doc_texts": doc_texts,
        }
    
    def retrieve_docs(self, query):
        """Retrieve top-k relevant documents for a query."""
        try:
            query_vec = self.retriever["vectorizer"].transform([query])
            scores = cosine_similarity(query_vec, self.retriever["tfidf_matrix"])[0]
            
            top_indices = np.argsort(scores)[-TOP_K_DOCS:][::-1]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    doc_id = self.retriever["doc_ids"][idx]
                    content = self.retriever["doc_texts"][idx]
                    score = scores[idx]
                    truncated = content[:300] + "..." if len(content) > 300 else content
                    results.append((doc_id, truncated, score))
            
            return results
        except Exception as e:
            print(f"⚠️ Retrieval error: {e}")
            return []
    
    def classify_ticket(self, ticket_text):
        """Classify a single ticket via Groq API."""
        # Retrieve context
        context_docs = self.retrieve_docs(ticket_text)
        
        context_text = "## SUPPORT DOCS\n\n"
        for doc_id, content, score in context_docs:
            context_text += f"### {doc_id} (relevance: {score:.3f})\n{content}\n\n"
        
        if not context_docs:
            context_text += "*No relevant docs found in corpus*\n"
        
        # Build prompt
        prompt = f"{SYSTEM_PROMPT}\n\nTICKET:\n{ticket_text}\n\n{context_text}\n\nRespond with JSON object only."
        
        # Call API using Groq
        try:
            groq_key = os.getenv("GROQ_API_KEY")
            if not groq_key:
                raise ValueError("GROQ_API_KEY not set")
            
            client = Groq(api_key=groq_key)
            
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3,
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON from response
            response_text = response_text.strip()
            
            # Try to extract JSON
            if "{" in response_text:
                json_start = response_text.index("{")
                json_str = response_text[json_start:]
                if "}" in json_str:
                    json_end = json_str.rindex("}") + 1
                    json_str = json_str[:json_end]
                    parsed = json.loads(json_str)
                    
                    # Normalize
                    status = parsed.get("status", "Escalated").lower()
                    if status == "replied":
                        status = "Classified + Answered ✓"
                    elif status != "escalated":
                        status = "Escalated"
                    else:
                        status = "Escalated"
                    
                    return {
                        "status": status,
                        "product_area": parsed.get("product_area", "general")[:20],
                        "response": parsed.get("response", "")[:500],
                        "justification": parsed.get("justification", ""),
                        "request_type": parsed.get("request_type", "product_issue"),
                    }
            
            # JSON parsing failed, fall through to TF-IDF fallback
            pass
        
        except Exception as e:
            # API failed, use TF-IDF fallback
            pass
        
        # ===== FALLBACK: Use TF-IDF results only =====
        if context_docs:
            # Get the product area from top doc's path
            top_doc_id = context_docs[0][0]  # e.g., "data/claude/features-and-capabilities/..."
            path_parts = top_doc_id.split("/")
            
            # Extract domain from path (e.g., "claude", "hackerrank", "visa")
            product_area = "general"
            if len(path_parts) > 1:
                domain = path_parts[1].lower()
                if domain in ["claude", "hackerrank", "visa"]:
                    product_area = domain.capitalize()
            
            return {
                "status": "Classified (fallback)",
                "product_area": product_area,
                "response": f"Ticket classified and routed to {product_area} team for review.",
                "justification": "Classified via TF-IDF corpus matching (LLM API unavailable)",
                "request_type": "support",
            }
        
        # No docs found and API failed
        return {
            "error": "No LLM response and no docs found",
            "status": "Escalated",
            "product_area": "general",
            "response": "Unable to classify ticket. Escalated to human review.",
            "justification": "LLM API failed and insufficient corpus match",
            "request_type": "invalid"
        }


# ============================================================================
# GRADIO INTERFACE
# ============================================================================

def classify_support_ticket(ticket_text, ticket_subject=""):
    """Process a support ticket and return classification."""
    if not ticket_text or not ticket_text.strip():
        return "Please enter a support ticket", "", "", "", ""
    
    # Get agent instance
    agent = TriageAgent()
    
    # Combine subject + text for better retrieval
    query = f"{ticket_subject} {ticket_text}".strip()
    
    # Classify
    result = agent.classify_ticket(query)
    
    # Format output
    status = result.get("status", "Escalated")
    product_area = result.get("product_area", "general")
    response = result.get("response", "")
    justification = result.get("justification", "")
    request_type = result.get("request_type", "product_issue")
    
    return status, product_area, response, justification, request_type


def create_interface():
    """Create Gradio interface."""
    
    demo = gr.Interface(
        fn=classify_support_ticket,
        inputs=[
            gr.Textbox(
                label="Support Ticket",
                placeholder="Describe your issue here...",
                lines=6,
            ),
            gr.Textbox(
                label="Subject (optional)",
                placeholder="Brief subject line",
            ),
        ],
        outputs=[
            gr.Textbox(label="Status", interactive=False),
            gr.Textbox(label="Product Area", interactive=False),
            gr.Textbox(label="Response", interactive=False, lines=6),
            gr.Textbox(label="Justification", interactive=False),
            gr.Textbox(label="Request Type", interactive=False),
        ],
        title="Multi-Domain Support Triage Agent",
        description="Automatically classify and route support tickets for HackerRank, Claude, and Visa.",
        examples=[
            [
                "My payment failed but money was deducted from my account. I tried again and now I see duplicate charges.",
                "Payment Failed - Duplicate Charge",
            ],
            [
                "I cannot login, it says invalid credentials. I tried resetting my password but the reset email never arrived.",
                "Cannot Login - Invalid Credentials",
            ],
            [
                "The mobile app keeps crashing on the checkout screen. Every time I try to complete my purchase, it crashes.",
                "App Crashing - Checkout Screen",
            ],
        ],
    )
    
    return demo


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 HackerRank Orchestrate - Support Triage Agent")
    print("="*60 + "\n")
    
    # Initialize agent
    agent = TriageAgent()
    
    # Create and launch interface
    demo = create_interface()
    print("✅ Agent ready!")
    print("🌐 Launching Gradio interface...\n")
    
    demo.launch(share=True)
