import os
import bigtree as bt
import sys
import uvicorn

from dotenv import load_dotenv
from fastapi import Request
from loguru import logger

load_dotenv()

os.makedirs('log',exist_ok=True)
logger.add("log/{time}.log", rotation="00:00", retention="90 days")

logger.debug(f"Python Version: {sys.version}")

logger.info("Setup datasets...")
from data.dataset_loader import DatasetLoader
dataset_loader = DatasetLoader(os.environ.get("DATA_DIR"))

logger.info("Setup Dash server...")
from app import create_dash_app
app = create_dash_app(requests_pathname_prefix="/")
app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)

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
    STATE["current_dataset"] = dataset_name
    logger.debug(f"Current dataset set as {dataset_name}")
    return dict(dataset_name=dataset_name)

@api.get("/api/v1/dataset/config")
def get_config():
    dataset_name = STATE["current_dataset"]
    dataset = dataset_loader.datasets[dataset_name]
    return {section: dict(dataset.config.items(section)) for section in dataset.config.sections()}

@api.get("/api/v1/dataset/sites-tree")
def get_sites_tree():
    dataset_name = STATE["current_dataset"]
    dataset = dataset_loader.datasets[dataset_name]
    return dataset.sites_tree

api.mount("/", WSGIMiddleware(app.server))

if __name__ == "__main__":
    logger.info("Running server...")
    uvicorn.run(
        "__main__:api",
        host=os.environ.get("HOST_NAME", "0.0.0.0"),
        port=int(os.environ.get("PORT", 8050)),
        reload=True,
    )
    logger.info("Shutdown")
