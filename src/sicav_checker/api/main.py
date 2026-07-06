from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sicav_checker.api.routes import documents, enterprise, health, projects, reports, simple_compare, verification
from sicav_checker.exceptions import ComparisonError, StorageError

app = FastAPI(title="FinVerify API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StorageError)
async def storage_error_handler(_: Request, exc: StorageError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ComparisonError)
async def comparison_error_handler(_: Request, exc: ComparisonError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(simple_compare.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(verification.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(enterprise.router, prefix="/api")
