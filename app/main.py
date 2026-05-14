from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import ensure_database_exists, run_alembic_migrations
from app.routers import locais, reservas, salas

settings = get_settings()
CHROME_DEVTOOLS_PROBE_PATH = (
    "/.well-known/appspecific/com.chrome.devtools.json"
)


@asynccontextmanager
async def lifespan(_: "FastAPI"):
    """
    Executado uma vez na inicialização do servidor.
    Garante que o banco PostgreSQL e todas as tabelas existam antes de
    aceitar requisições — elimina a necessidade de setup manual após clone.
    """
    ensure_database_exists()
    run_alembic_migrations()
    yield


app = FastAPI(
    title="Banana Reservas API",
    version="1.0.0",
    description=(
        "API de reservas de salas com validação JWT emitido pelo "
        "serviço de autenticação."
    ),
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(locais.router)
app.include_router(salas.router)
app.include_router(reservas.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def suppress_map_requests(request: Request, call_next):
    # Source maps are optional; returning 204 avoids noisy 404 logs in demos.
    if request.url.path.endswith(".map"):
        return Response(status_code=204)

    return await call_next(request)


@app.get("/redoc", include_in_schema=False)
def redoc_html() -> HTMLResponse:
    openapi_url = app.openapi_url or "/openapi.json"
    return get_redoc_html(
        openapi_url=openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "banana-reservas-api"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get(CHROME_DEVTOOLS_PROBE_PATH, include_in_schema=False)
def chrome_devtools_probe() -> Response:
    return Response(status_code=204)
