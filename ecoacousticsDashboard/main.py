# Setup Logging
import os
import sys
import uvicorn

from fastapi import Request
from loguru import logger
from config import root_dir

os.makedirs('log',exist_ok=True)
logger.add("log/{time}.log", rotation="00:00", retention="90 days")

logger.debug(f"Python Version: {sys.version}")

logger.info("Setup datasets...")
from utils.data import DatasetLoader
dataset_loader = DatasetLoader(root_dir)

logger.info("Setup Dash server...")
from app import create_dash_app
app = create_dash_app(requests_pathname_prefix="/")
app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)

# NB: must be done after dash so /api takes precedence
logger.info("Setup API server...")
import fastapi
from fastapi.middleware.wsgi import WSGIMiddleware
api = fastapi.FastAPI()

STATE = {}

@api.get("/api/v1/datasets")
def get_datasets():
    datasets = list(dataset_loader.datasets.keys())
    logger.debug(f"Listing datasets {datasets}")
    return datasets

@api.post("/api/v1/dataset")
async def set_dataset(request: Request):
    data = await request.json()
    dataset_name = data.get("dataset_name", None)
    logger.debug(f"Setting dataset {dataset_name}")
    STATE["current_dataset"] = dataset_name
    return dict(dataset_name=dataset_name)

api.mount("/", WSGIMiddleware(app.server))

if __name__ == "__main__":
    logger.info("Running server...")
    uvicorn.run("__main__:api", host="0.0.0.0", port=8000, reload=True)
    logger.info("Shutdown")
