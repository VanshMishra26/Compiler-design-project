# Interactive Compiler Pipeline Visualizer

Full-stack visualizer for a C-like compiler pipeline. The backend compiles source code through lexing, parsing, semantic analysis, three-address code generation, basic-block/CFG construction, DAG generation, and optimization. The frontend displays the pipeline with Monaco Editor, React Flow, playback controls, token chips, AST graphs, symbol tables, TAC, basic blocks, DAG nodes, diagnostics, sample programs, and `.c`/`.h` file upload.

The frontend now follows the VoiceBox design spec: a high-contrast editorial interface with black-and-white surfaces, sharp square borders, uppercase UI labels, a restrained red accent, flat panels, and custom styling for Monaco and React Flow.

This project is a teaching and visualization compiler. It accepts and visualizes a broader practical C surface than the original version, but it does not execute uploaded programs and is not a complete ISO C compiler.

## Stack

- Backend: Python, FastAPI, Pydantic v2, pytest
- Frontend: Next.js 14, TypeScript, Tailwind CSS, Monaco Editor, React Flow, Framer Motion, Zustand
- Storage: none; compilation is stateless request/response

## Recent Changes

- Expanded lexer support for more C keywords, numeric formats, string and character literals, comments, operators, punctuators, and preprocessor line capture.
- Added richer token metadata including source spans, offsets, `lexeme`, and skipped-token markers for comments/preprocessor lines.
- Extended parser tolerance for more C-like declarations, pointer-looking types, struct/union/enum declarations, loops, switch, labels/goto, indexing, member access, postfix operators, and initializer lists.
- Added builtin semantic symbols for common C library functions and types such as `printf`, `malloc`, `free`, `strlen`, `size_t`, `FILE`, and `NULL`.
- Added top-level full-pipeline response fields for diagnostics, comments, preprocessor data, grouped function output, CFG data, AST stats, and type-layout placeholders.
- Added `POST /api/compile/upload` for in-memory `.c`/`.h` uploads with extension, size, encoding, empty-file, BOM, and newline handling.
- Added frontend upload controls, editor drag-and-drop, uploaded-file chip, diagnostics strip, expanded C sample picker, and synced TypeScript response types.
- Updated optimizer output with CFG and ordered optimization-step metadata while keeping the existing phase response shape.
- Restyled the frontend to match `voicebox-DESIGN.md`: centralized design tokens, VoiceBox CSS variables, square-edged controls, heavy borders, editorial typography stacks, custom Monaco theme, and React Flow node/control styling.

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

- Python 3.10+ works in this implementation; Python 3.11+ is recommended
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

Quick upload check:

```powershell
cd backend
python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); r=c.post('/api/compile/upload', files={'file':('sample.c', b'int main(){ return 0; }', 'text/x-c')}); print(r.status_code, r.json()['filename'], r.json()['parse']['success'])"
```

## API Endpoints

These endpoints accept JSON:

```json
{ "source": "void main() { int x = 2 + 3; }" }
```

- `POST /api/compile/lex`
- `POST /api/compile/parse`
- `POST /api/compile/semantic`
- `POST /api/compile/tac`
- `POST /api/compile/optimize`
- `POST /api/compile/full`

The upload endpoint accepts multipart form data:

- `POST /api/compile/upload`

The frontend uses `/api/compile/full` for editor source and `/api/compile/upload` for uploaded files.

`/api/compile/upload` expects a `file` field. Files must use a `.c` or `.h` extension, be non-empty, and be no larger than 256 KB. The backend decodes UTF-8, falls back to latin-1 with an info diagnostic, strips a UTF-8 BOM, normalizes newlines, and processes the source entirely in memory.

`/api/compile/full` keeps the original phase objects and also returns richer top-level fields for large-program visualizations:

- `tokens`, `comments`, `preprocessor`, `lex_errors`
- `ast`, `parse_errors`, `ast_stats`
- `symbol_tables`, `types`, `diagnostics`
- `functions[]` with `tac`, `basic_blocks`, `cfg`, `dag`, `optimization_steps`, and `optimized_tac`
- `data_section`

Upload responses include the same pipeline data plus `filename`, `size_bytes`, `line_count`, and normalized `source`.

## Supported Source Language

The compiler supports the original small C-like subset and now tokenizes/parses a broader practical C surface:

- Types: `char`, `short`, `int`, `long`, `float`, `double`, `bool`, `void`, plus basic `struct`/`union`/`enum` declarations
- Global and local variables, function declarations, and simple prototypes
- Blocks, expression statements, `if/else`, `while`, `for`, `do/while`, `switch`, `break`, `continue`, `goto`, labels, and `return`
- Assignments, arithmetic, comparisons, equality, boolean, bitwise, shift, unary, call, index, member, and postfix expressions
- Function calls, builtin declarations for common C library functions, pointer-looking declarations, array-looking declarations, string and character literals, comments, and preprocessor line capture

## Upload UX

The frontend header includes an upload button for `.c` and `.h` files, and the editor accepts drag-and-drop. Successful uploads load the source into the editor, show a file chip, and automatically run the full pipeline. The sample picker includes larger C-style examples such as linked lists, BSTs, hash tables, matrix multiply, and quick sort.

## Frontend Design

The UI is styled from the VoiceBox design system:

- Palette: black `#0A0A0A`, white `#FAFAFA`, neutral surfaces, and red `#EF4444` for active/error emphasis.
- Typography: display/headline stack uses Archivo Black fallbacks; body UI uses Work Sans fallbacks; code uses Space Mono fallbacks.
- Components: flat surfaces, no shadows, no rounded corners, 2px borders for controls and panels, uppercase labels, red underline/accent treatment for active states.
- Monaco: custom light theme using the VoiceBox palette and monospace editor typography.
- React Flow: square nodes, heavy black borders, flat backgrounds, and themed controls.

## Known Limitations

- This is not a full C compiler and does not implement all ISO C grammar or semantic rules.
- The preprocessor is minimal: includes are recorded but not resolved, and macro/conditional behavior is intentionally conservative.
- Type layout data is exposed in the response shape, but detailed struct/union/enum layout reporting is still limited.
- Complex C constructs are parsed and visualized conservatively; unsupported details should produce diagnostics or partial output rather than crashing.
- No uploaded or editor-provided code is ever executed.
- No machine code, persistence, authentication, or server-side file storage is generated.
- The VoiceBox font names are configured as font stacks/fallbacks; the app does not currently download web fonts at build time.

## Notes From Local Verification

- Frontend production build passes with `npm run build`.
- Frontend dev server starts at `http://localhost:3000`; Next may print a non-fatal version-check `fetch failed` warning when network access is blocked.
- FastAPI `/api/compile/full` smoke checks pass for the original simple program and a struct/pointer-style program.
- FastAPI `/api/compile/upload` smoke check returns `200` for a valid `.c` upload and includes upload metadata.
- Backend pytest prints all 23 tests passing at `100%`, but the local Windows runner process still does not exit cleanly after completion, so it may need to be interrupted after the pass line appears.
