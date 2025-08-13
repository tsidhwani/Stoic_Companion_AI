from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-instruct")

app = FastAPI(title="AI Stoic Companion Backend", version="0.1.0")

# Allow local dev clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost", "http://127.0.0.1", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    system_persona: str | None = None
    model: str | None = None


class ChatResponse(BaseModel):
    reply: str
    model: str


class ScoreRequest(BaseModel):
    problem: str
    proposed_response: str
    model: str | None = None


class ScoreResponse(BaseModel):
    medal: str  # none | bronze | silver | gold
    score: int  # 0..3
    explanation: str
    principles: list[str] | None = None
    model: str


def build_system_prompt(custom_persona: str | None) -> str:
    if custom_persona:
        return custom_persona
    return (
        "You are a calm, concise Stoic mentor in the style of Marcus Aurelius. "
        "Apply Stoic principles to modern situations. Prefer brevity and clarity. "
        "When helpful, reference key Stoic ideas like the dichotomy of control, virtue, and acceptance of fate. "
        "Avoid medical, legal, or financial advice."
    )


def build_scoring_prompt(problem: str | None, proposed_response: str | None) -> str:
    return (
        "You are a Stoic evaluator. Classify how Stoic a user's proposed response is to their problem.\n"
        "Rules:\n"
        "- Gold (3): Clearly applies the dichotomy of control, focuses on internal response, accepts externals, ties to a Stoic principle (e.g., virtue, control, fate), and suggests constructive action within control.\n"
        "- Silver (2): Mostly Stoic: shows restraint, acceptance, or control focus; may not name principles explicitly.\n"
        "- Bronze (1): Partially Stoic: gestures at calm or patience but lacks reasoning or control focus.\n"
        "- None (0): Non-Stoic: blame, entitlement, venting, fixation on externals, or retaliation.\n\n"
        "Output STRICTLY in compact JSON with keys: medal(one of none|bronze|silver|gold), score(0..3), explanation(short), principles(array of short tags). No extra text.\n\n"
        f"Problem: {problem}\n"
        f"ProposedResponse: {proposed_response}\n"
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    model = req.model or DEFAULT_MODEL
    system_prompt = build_system_prompt(req.system_persona)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message},
        ],
        "temperature": 0.7,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optional but recommended by OpenRouter
        "HTTP-Referer": os.getenv("OPENROUTER_APP_URL", "http://localhost"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME", "AI Stoic Companion"),
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")

    try:
        reply_text = data["choices"][0]["message"]["content"].strip()
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected response schema from OpenRouter")

    return ChatResponse(reply=reply_text, model=model)


@app.post("/score", response_model=ScoreResponse)
async def score(req: ScoreRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    model = req.model or DEFAULT_MODEL

    system_prompt = (
        "You are an impartial Stoic evaluator. Be strict but fair."
    )
    user_prompt = build_scoring_prompt(req.problem, req.proposed_response)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_APP_URL", "http://localhost"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME", "AI Stoic Companion"),
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")

    try:
        content = data["choices"][0]["message"]["content"].strip()
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected response schema from OpenRouter")

    # Best-effort JSON parsing with fallbacks
    import json
    medal = "none"
    score_val = 0
    explanation = ""
    principles = []
    try:
        parsed = json.loads(content)
        medal = str(parsed.get("medal", medal)).lower()
        score_val = int(parsed.get("score", score_val))
        explanation = str(parsed.get("explanation", "")).strip()
        principles = parsed.get("principles", []) or []
        if medal not in {"none", "bronze", "silver", "gold"}:
            medal = "none"
        if score_val < 0 or score_val > 3:
            score_val = {"none": 0, "bronze": 1, "silver": 2, "gold": 3}.get(medal, 0)
    except Exception:
        # Fallback heuristic if model didn't return JSON
        text = content.lower()
        if "dichotomy of control" in text or "within my control" in text or "not in my control" in text:
            medal, score_val = "gold", 3
        elif "stay calm" in text or "accept" in text or "focus on what i can do" in text:
            medal, score_val = "silver", 2
        elif "shouldn't get mad" in text or "try to be patient" in text:
            medal, score_val = "bronze", 1
        else:
            medal, score_val = "none", 0
        explanation = content[:200]
        principles = []

    return ScoreResponse(
        medal=medal,
        score=score_val,
        explanation=explanation,
        principles=principles,
        model=model,
    ) 