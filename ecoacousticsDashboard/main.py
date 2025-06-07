# Setup Logging
import os
import sys
import uvicorn

from loguru import logger

os.makedirs('log',exist_ok=True)
logger.add("log/{time}.log", rotation="00:00", retention="90 days")

logger.debug(f"Python Version: {sys.version}")

logger.info("Setup Dash server...")
from app import create_dash_app
app = create_dash_app(requests_pathname_prefix="/")
app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)

# NB: must be done after dash so /api takes precedence
logger.info("Setup API server...")
import fastapi
from fastapi.middleware.wsgi import WSGIMiddleware
api = fastapi.FastAPI()

@api.get("/api/v1/status")
def get_status():
    return dict(status="ok")

api.mount("/", WSGIMiddleware(app.server))

if __name__ == "__main__":
    logger.info("Start server...")
    uvicorn.run("__main__:api", host="0.0.0.0", port=8000, reload=True)
    logger.info("Server shutdown.")
