from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.common.fuseki import FusekiUnavailable
from src.viewer.workflow import ViewerWorkflow


class QuestionRequest(BaseModel):
    question: str
    session_id: str


class QuestionResponse(BaseModel):
    session_id: str
    answer: str
    facts: list[dict[str, str]]


def create_app(workflow: ViewerWorkflow | None = None) -> FastAPI:
    viewer = workflow or ViewerWorkflow()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        start_method = getattr(viewer, "start_fuseki_if_needed", None)
        if callable(start_method):
            start_method()
        try:
            yield
        finally:
            stop_method = getattr(viewer, "stop_fuseki_if_started", None)
            if callable(stop_method):
                stop_method()

    app = FastAPI(title="Vibe Semanting Viewer", lifespan=lifespan)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return HTML_PAGE

    @app.get("/api/status")
    def status() -> dict[str, object]:
        return viewer.graph_status()

    @app.post("/api/chat/session")
    def create_chat_session() -> dict[str, object]:
        return viewer.create_chat_session()

    @app.get("/api/chat/{session_id}")
    def chat_history(session_id: str) -> dict[str, object]:
        try:
            return viewer.chat_history(session_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/question", response_model=QuestionResponse)
    def ask(request: QuestionRequest) -> QuestionResponse:
        try:
            result = viewer.answer_question(request.question, session_id=request.session_id)
        except (FusekiUnavailable, RuntimeError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return QuestionResponse(
            session_id=request.session_id,
            answer=result.answer,
            facts=result.facts,
        )

    @app.get("/api/export.ttl")
    def export_turtle() -> Response:
        try:
            turtle = viewer.export_turtle()
        except FusekiUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return Response(
            content=turtle,
            media_type="text/turtle",
            headers={"Content-Disposition": 'attachment; filename="semantic_web.ttl"'},
        )

    @app.get("/api/plot.html", response_class=HTMLResponse)
    def plot_html() -> str:
        try:
            return viewer.plot_html()
        except (FusekiUnavailable, RuntimeError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return app


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Vibe Semanting Viewer</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --line: #d8dde4;
      --text: #1e252d;
      --muted: #5f6b7a;
      --accent: #0f766e;
      --accent-dark: #115e59;
      --danger: #b42318;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .shell {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr auto;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 20px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1 {
      margin: 0;
      font-size: 18px;
      font-weight: 700;
      letter-spacing: 0;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .status {
      min-height: 32px;
      padding: 7px 10px;
      border: 1px solid var(--line);
      background: #f9fafb;
      color: var(--muted);
      font-size: 13px;
    }
    button {
      min-height: 34px;
      border: 1px solid var(--accent);
      background: var(--accent);
      color: #fff;
      padding: 0 12px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      border-radius: 4px;
    }
    button.secondary {
      background: #fff;
      color: var(--accent-dark);
    }
    button:disabled {
      opacity: 0.55;
      cursor: not-allowed;
    }
    main {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      gap: 0;
      min-height: 0;
    }
    .conversation {
      min-height: 0;
      overflow: auto;
      padding: 18px 20px;
    }
    .message {
      max-width: 920px;
      margin: 0 0 12px;
      padding: 12px 14px;
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 6px;
      white-space: pre-wrap;
      line-height: 1.45;
    }
    .message.user {
      border-left: 4px solid var(--accent);
    }
    .message.error {
      border-left: 4px solid var(--danger);
      color: var(--danger);
    }
    aside {
      border-left: 1px solid var(--line);
      background: var(--panel);
      min-height: 0;
      overflow: auto;
      padding: 16px;
    }
    aside h2 {
      margin: 0 0 10px;
      font-size: 15px;
      letter-spacing: 0;
    }
    .fact {
      border-top: 1px solid var(--line);
      padding: 10px 0;
      font-size: 12px;
      color: var(--muted);
      overflow-wrap: anywhere;
    }
    form {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      padding: 14px 20px;
      border-top: 1px solid var(--line);
      background: var(--panel);
    }
    textarea {
      width: 100%;
      min-height: 44px;
      max-height: 140px;
      resize: vertical;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 4px;
      font: inherit;
      line-height: 1.35;
    }
    @media (max-width: 820px) {
      main { grid-template-columns: 1fr; }
      aside { display: none; }
      header { align-items: flex-start; flex-direction: column; }
      .toolbar { justify-content: flex-start; }
      form { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <h1>Vibe Semanting Viewer</h1>
      <div class="toolbar">
        <div class="status" id="status">Checking Fuseki</div>
        <button class="secondary" id="exportBtn" type="button">Export Turtle</button>
        <button class="secondary" id="plotBtn" type="button">Graph</button>
      </div>
    </header>
    <main>
      <section class="conversation" id="conversation"></section>
      <aside>
        <h2>Queried Facts</h2>
        <div id="facts"></div>
      </aside>
    </main>
    <form id="questionForm">
      <textarea id="question" name="question" placeholder="Ask a question about the semantic web"></textarea>
      <button id="askBtn" type="submit">Ask</button>
    </form>
  </div>
  <script>
    const statusEl = document.getElementById("status");
    const conversationEl = document.getElementById("conversation");
    const factsEl = document.getElementById("facts");
    const formEl = document.getElementById("questionForm");
    const questionEl = document.getElementById("question");
    const askBtn = document.getElementById("askBtn");
    const exportBtn = document.getElementById("exportBtn");
    let sessionId = null;

    function addMessage(text, kind) {
      const node = document.createElement("div");
      node.className = `message ${kind || ""}`;
      node.textContent = text;
      conversationEl.appendChild(node);
      conversationEl.scrollTop = conversationEl.scrollHeight;
    }

    function renderFacts(facts) {
      factsEl.textContent = "";
      for (const fact of facts.slice(0, 20)) {
        const node = document.createElement("div");
        node.className = "fact";
        node.textContent = Object.entries(fact).map(([key, value]) => `${key}: ${value}`).join("\\n");
        factsEl.appendChild(node);
      }
    }

    async function refreshStatus() {
      const response = await fetch("/api/status");
      const status = await response.json();
      statusEl.textContent = status.available
        ? `Fuseki ready: ${status.triple_count} triples`
        : status.message;
    }

    async function startChatSession() {
      const response = await fetch("/api/chat/session", {method: "POST"});
      const session = await response.json();
      if (!response.ok) throw new Error(session.detail || "Could not create chat session");
      sessionId = session.session_id;
      statusEl.title = session.path || "";
    }

    formEl.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = questionEl.value.trim();
      if (!question) return;
      if (!sessionId) {
        addMessage("Chat session is not ready yet.", "error");
        return;
      }
      addMessage(question, "user");
      questionEl.value = "";
      askBtn.disabled = true;
      try {
        const response = await fetch("/api/question", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({question, session_id: sessionId})
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || "Question failed");
        addMessage(payload.answer, "assistant");
        renderFacts(payload.facts || []);
      } catch (error) {
        addMessage(error.message, "error");
      } finally {
        askBtn.disabled = false;
      }
    });

    exportBtn.addEventListener("click", () => {
      window.location.href = "/api/export.ttl";
    });

    plotBtn.addEventListener("click", () => {
      window.open("/api/plot.html", "_blank", "noopener,noreferrer");
    });

    Promise.all([startChatSession(), refreshStatus()]).catch((error) => {
      statusEl.textContent = error.message;
    });
  </script>
</body>
</html>
"""
