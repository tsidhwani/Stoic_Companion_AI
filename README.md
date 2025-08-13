# AI Stoic Companion (MVP)

Minimal chat-only MVP plus Stoic Reasoning Practice:
- Backend: FastAPI proxy to OpenRouter (default: Qwen Instruct)
- iOS: SwiftUI with two tabs: Chat and Practice (medal scoring)

## Backend

See `backend/README.md` for setup. Quick run:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env # set OPENROUTER_API_KEY
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

## iOS App

- Open Xcode and create a new iOS App project named `AIStoicCompanion`.
- Add the Swift files from `ios/` to the project (`ContentView.swift`, `AIStoicCompanionApp.swift`, `ChatView.swift`, `PracticeView.swift`, `Models/Message.swift`).
- For local HTTP calls to `http://127.0.0.1:8000`, add an ATS exception in your app `Info.plist` for `NSAppTransportSecurity` → `NSAllowsArbitraryLoads` = YES (or add a localhost exception).
- Run on the simulator; the app calls `http://127.0.0.1:8000`.

## Notes

- Default model is `qwen/qwen-2.5-instruct` via OpenRouter. Override by setting `OPENROUTER_MODEL`.
- No auth, analytics, or persistence in MVP. 