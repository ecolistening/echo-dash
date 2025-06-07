# Setup Logging
import os
import sys
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from loguru import logger

from app import create_dash_app

os.makedirs('log',exist_ok=True)
logger.add("log/{time}.log", rotation="00:00", retention="90 days")

logger.debug(f"Python Version: {sys.version}")
logger.info("Setup API server...")

api = FastAPI()

@api.get("/api/status")
def get_status():
    return dict(status="ok")

app = create_dash_app(requests_pathname_prefix="/dash/")
app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)
api.mount("/dash", WSGIMiddleware(app.server))

if __name__ == "__main__":
    logger.info("Start server...")
    uvicorn.run("__main__:api", host="0.0.0.0", port=8000, reload=True, workers=2)
    logger.info("Server shutdown.")
