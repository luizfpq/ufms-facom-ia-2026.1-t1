"""v2 — Buscador de Referências com LLM (FastAPI + Ollama + BM25/KNN/RRF)."""
import json, math, os, re, secrets, tempfile
from pathlib import Path
from typing import Optional

import httpx
import fitz  # pymupdf
from docx import Document as DocxDocument
import trafilatura
from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from search import search_corpus, search_legislation_all


def sanitize(obj):
    """Replace NaN/Inf floats with 0 recursively for JSON safety."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return 0
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
CORPUS_PATH = os.getenv("CORPUS_PATH", "/app/data/corpus.jsonl")
AUTH_USER = os.getenv("AUTH_USER", "prof")
AUTH_PASS = os.getenv("AUTH_PASS", "61PeN9Q2j-r4oDz2ctKGug")

app = FastAPI(title="Buscador de Referências v2")
security = HTTPBasic()


def verify(credentials: HTTPBasicCredentials = Depends(security)):
    if not (secrets.compare_digest(credentials.username, AUTH_USER) and
            secrets.compare_digest(credentials.password, AUTH_PASS)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            headers={"WWW-Authenticate": "Basic"})
    return credentials.username


# --- Text extraction ---

def extract_pdf(data: bytes) -> str:
    doc = fitz.open(stream=data, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def extract_docx(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        f.write(data)
        f.flush()
        doc = DocxDocument(f.name)
    os.unlink(f.name)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_url(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return ""
    return trafilatura.extract(downloaded) or ""


def extract_text(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_pdf(data)
    elif ext in (".docx", ".doc"):
        return extract_docx(data)
    else:
        return data.decode("utf-8", errors="ignore")


# --- LLM interaction ---

async def llm_generate(prompt: str, system: str = "", max_tokens: int = 1024) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.3},
    }
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        r.raise_for_status()
        return r.json()["response"]


SYSTEM_EXTRACT = """You are a research assistant. Given an academic text, extract the main concepts and generate search queries.
Reply ONLY with a JSON object: {"keyphrases": ["...", ...], "queries": ["...", ...]}
- keyphrases: 5-10 key concepts from the text (in the text's language)
- queries: 5-8 search queries to find related academic papers (mix of English and Portuguese)
No explanation, no markdown, just the JSON."""

SYSTEM_JUSTIFY = """You are a research assistant. Given a list of papers found for a research text, write a brief justification (1-2 sentences) for each paper explaining WHY it is relevant.
Reply ONLY with a JSON array of objects: [{"id": 0, "justification": "..."}, ...]
Be concise. Write in Portuguese."""


async def extract_queries_llm(text: str) -> dict:
    truncated = text[:4000]
    raw = await llm_generate(truncated, system=SYSTEM_EXTRACT)
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, TypeError):
        pass
    return {"keyphrases": [], "queries": []}


async def justify_results_llm(text_snippet: str, results: list[dict]) -> list[str]:
    papers_desc = "\n".join(
        f"[{i}] {r.get('title','')} ({r.get('year','')}) — {r.get('abstract','')[:150]}"
        for i, r in enumerate(results[:10])
    )
    prompt = f"Research text (excerpt):\n{text_snippet[:1500]}\n\nPapers found:\n{papers_desc}"
    raw = await llm_generate(prompt, system=SYSTEM_JUSTIFY)
    try:
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if not match:
            match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            justifications = json.loads(match.group())
            out = [""] * len(results)
            for j in justifications:
                idx = j.get("id", -1)
                if 0 <= idx < len(out):
                    out[idx] = j.get("justification", "")
            return out
    except (json.JSONDecodeError, TypeError):
        pass
    return [""] * len(results)


# --- API endpoints ---

@app.post("/api/analyze")
async def analyze(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    user: str = Depends(verify),
):
    # 1. Extract text
    if file:
        data = await file.read()
        content = extract_text(file.filename, data)
        source_name = file.filename
    elif url:
        content = extract_url(url)
        source_name = url
    elif text:
        content = text
        source_name = "texto direto"
    else:
        return JSONResponse({"error": "Envie um arquivo, URL ou texto."}, status_code=400)

    if not content or len(content.strip()) < 50:
        return JSONResponse({"error": "Não foi possível extrair texto suficiente."}, status_code=400)

    # 2. LLM extracts keyphrases + queries
    extracted = await extract_queries_llm(content)
    keyphrases = extracted.get("keyphrases", [])
    queries = extracted.get("queries", [])
    if not queries:
        queries = keyphrases[:5]

    # 3. Search corpus + legislation
    academic = search_corpus(queries, corpus_path=CORPUS_PATH, top_k=15)
    legislation = search_legislation_all(queries, top_n=8)

    # 4. LLM justifies top results
    justifications = await justify_results_llm(content, academic)

    # 5. Format response
    results = []
    for i, doc in enumerate(academic):
        results.append({
            "type": "academic",
            "title": doc.get("title", ""),
            "authors": doc.get("authors", ""),
            "year": doc.get("year", doc.get("publication_year", "")),
            "doi": doc.get("doi", ""),
            "abstract": doc.get("abstract", "")[:300],
            "score": round(doc.get("_score", 0), 4) if doc.get("_score", 0) == doc.get("_score", 0) else 0,
            "justification": justifications[i] if i < len(justifications) else "",
        })
    for r in legislation:
        results.append({
            "type": "legislation",
            "title": f"{r['tipo']} {r['numero']}/{r['ano']}",
            "ementa": r["ementa"],
            "url": r["url"],
            "score": r["relevance_score"],
        })

    return sanitize({
        "source": source_name,
        "text_length": len(content),
        "keyphrases": keyphrases,
        "queries": queries,
        "results": results,
    })


@app.get("/", response_class=HTMLResponse)
async def index(user: str = Depends(verify)):
    return Path("/app/static/index.html").read_text(encoding="utf-8")
