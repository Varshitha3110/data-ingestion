from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import logging
import requests

from opentelemetry import metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from otel_logging import setup

# ---------------- SETUP ----------------
setup("frontend")

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

logger = logging.getLogger("frontend")

# ---------------- METRICS ----------------
meter = metrics.get_meter("frontend")

ui_request_counter = meter.create_counter(
    name="ui_requests_total",
    description="Frontend UI requests",
    unit="1",
)

# ---------------- ROUTES ----------------
@app.get("/", response_class=HTMLResponse)
def index():
    ui_request_counter.add(1, {"page": "index"})
    logger.info("Frontend UI loaded")
    return open("index.html").read()

@app.post("/submit")
async def submit(request: Request):
    ui_request_counter.add(1, {"action": "submit"})

    body = await request.json()
    name = body.get("name")

    logger.info("Form submitted, name=%s", name)

    r = requests.post(
        "http://backend-1:8000/submit",
        params={"name": name},
        timeout=5,
    )

    logger.info("Response received from backend-1")
    return r.json()
