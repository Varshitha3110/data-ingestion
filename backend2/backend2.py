from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

from opentelemetry import metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from otel_logging import setup

from db import init_db, save_name, engine

# ---------------- SETUP ----------------
setup("backend-2")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)

logger = logging.getLogger("backend-2")

# ---------------- METRICS ----------------
meter = metrics.get_meter("backend-2")

http_request_counter = meter.create_counter(
    name="http_requests_total",
    description="Total HTTP requests",
    unit="1",
)

db_operation_counter = meter.create_counter(
    name="db_operations_total",
    description="Database operations",
    unit="1",
)

error_counter = meter.create_counter(
    name="backend2_errors_total",
    description="Backend-2 errors",
    unit="1",
)

# ---------------- STARTUP ----------------
@app.on_event("startup")
def startup():
    init_db()
    logger.info("Database initialized")

# ---------------- API ----------------
@app.post("/process")
def process(payload: dict):
    start_time = time.time()

    http_request_counter.add(1, {"service": "backend-2", "endpoint": "/process"})
    logger.info("Request received at /process")

    name = payload.get("name")
    if not name:
        error_counter.add(1, {"type": "validation"})
        logger.warning("Missing name")
        raise HTTPException(status_code=400, detail="Missing name")

    if name.lower() == "error":
        error_counter.add(1, {"type": "business"})
        logger.exception("Intentional error triggered")
        raise HTTPException(status_code=500, detail="Simulated failure")

    logger.info("Saving name to DB")
    save_name(name)
    db_operation_counter.add(1, {"operation": "insert"})

    elapsed = round(time.time() - start_time, 3)
    logger.info("Request completed in %ss", elapsed)

    return {"status": "ok"}
