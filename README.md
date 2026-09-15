# Interactive Compiler Pipeline Visualizer

Full-stack visualizer for a small C-like compiler pipeline. The backend compiles source code through lexer, parser, semantic analysis, three-address code generation, and optimization. The frontend displays the pipeline with Monaco Editor, React Flow, playback controls, token chips, AST graphs, symbol tables, TAC, basic blocks, DAG nodes, and peephole changes.

## Stack

- Backend: Python, FastAPI, Pydantic v2, pytest
- Frontend: Next.js 14, TypeScript, Tailwind CSS, Monaco Editor, React Flow, Framer Motion, Zustand
- Storage: none; compilation is stateless request/response

## Project Structure

```text
backend/
  app/
    engine/        compiler phases
    routers/       FastAPI routes
    main.py        FastAPI app
    pipeline.py    full pipeline orchestration
  tests/           backend pytest suite
  requirements.txt
frontend/
  app/             Next.js App Router pages/styles
  components/      visualizer panels and controls
  lib/             API client, shared types, graph layout helpers
  store/           Zustand pipeline state
README.md
```

## Requirements

- Python 3.10+ works in this implementation; Python 3.11+ is recommended by the original plan
- Node.js 18+ recommended for Next.js 14
- npm

## Install

Backend:

```powershell
cd backend
pip install -r requirements.txt
```

Frontend:

```powershell
cd frontend
npm install
```

## Run

Start the backend API:

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

Start the frontend in another terminal:

```powershell
cd frontend
npm run dev
```

Open:

```text
http://localhost:3000
```

The frontend expects the backend at `http://localhost:8000`. To use a different API URL:

```powershell
cd frontend
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
```

## Test And Verify

Run backend tests:

```powershell
cd backend
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest -q
```

Build the frontend:

```powershell
cd frontend
npm run build
```

Quick API check:

```powershell
cd backend
python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); r=c.post('/api/compile/full', json={'source':'void main() { int x = 2 + 3; }'}); print(r.status_code, r.json()['optimize']['success'])"
```

## API Endpoints

All endpoints accept:

```json
{ "source": "void main() { int x = 2 + 3; }" }
```

Endpoints:

- `POST /api/compile/lex`
- `POST /api/compile/parse`
- `POST /api/compile/semantic`
- `POST /api/compile/tac`
- `POST /api/compile/optimize`
- `POST /api/compile/full`

The frontend uses `/api/compile/full`.

## Supported Source Language

The compiler supports a small C-like subset:

- Types: `int`, `float`, `bool`, `void`
- Variables and function declarations
- Blocks, expression statements, `if/else`, `while`, `return`
- Assignments, arithmetic, comparisons, equality, boolean operators
- Function calls

Non-goals include arrays, pointers, structs, real machine code, persistence, auth, and full C compatibility.

## Notes From Local Verification

- Frontend production build passed with `npm run build`.
- FastAPI full pipeline endpoint returned `200 True` in a direct `TestClient` check.
- Backend pytest printed all 23 tests passing at `100%`, but the local Windows runner process did not exit before the shell timeout even with plugin autoload disabled.
