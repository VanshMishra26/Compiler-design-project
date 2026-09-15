from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.compile import router as compile_router

app = FastAPI(title="Interactive Compiler Pipeline Visualizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compile_router)


@app.get("/health")
def health():
    return {"status": "ok"}
