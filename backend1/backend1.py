from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import requests
import time

from opentelemetry import metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from otel_logging import setup

# ---------------- SETUP ----------------
setup("backend-1")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

logger = logging.getLogger("backend-1")

# ---------------- METRICS ----------------
meter = metrics.get_meter("backend-1")

http_request_counter = meter.create_counter(
    name="http_requests_total",
    description="Total HTTP requests",
    unit="1",
)

backend2_error_counter = meter.create_counter(
    name="backend2_errors_total",
    description="Errors while calling backend-2",
    unit="1",
)

# ---------------- API ----------------
@app.post("/submit")
def submit(name: str):
    start_time = time.time()

    http_request_counter.add(1, {"service": "backend-1", "endpoint": "/submit"})
    logger.info("Request received at /submit")

    if not name:
        logger.warning("Empty name received")
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    try:
        logger.info("Calling backend-2")
        r = requests.post(
            "http://backend-2:8000/process",
            json={"name": name},
            timeout=5,
        )

        logger.info("Received response from backend-2 status=%s", r.status_code)

        elapsed = round(time.time() - start_time, 3)
        logger.info("Request completed in %ss", elapsed)

        return r.json()

    except requests.exceptions.Timeout:
        backend2_error_counter.add(1, {"type": "timeout"})
        logger.error("Timeout while calling backend-2")
        raise HTTPException(status_code=504, detail="backend-2 timeout")

    except Exception:
        backend2_error_counter.add(1, {"type": "exception"})
        logger.exception("backend-2 failed")
        raise HTTPException(status_code=500, detail="backend-2 failed")
