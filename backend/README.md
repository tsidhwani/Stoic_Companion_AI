# AI Stoic Companion Backend (MVP)

FastAPI service exposing a simple `/chat` endpoint that forwards messages to OpenRouter (default: Qwen Instruct).

Also provides `/score` to evaluate a user's proposed response to a problem and return a medal (none/bronze/silver/gold) with a brief explanation.

## Setup

1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

3. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set OPENROUTER_API_KEY
```

4. Run the API

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. Test: Chat

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"I missed my flight. Help me apply Stoicism."}'
```

6. Test: Scoring

```bash
curl -X POST http://127.0.0.1:8000/score \
  -H 'Content-Type: application/json' \
  -d '{"problem":"My flight is delayed","proposed_response":"It is outside my control, I will stay calm and focus on what I can do next."}'
``` 