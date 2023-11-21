import asyncio
import json
import os
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvloop
from fastapi import FastAPI

from ..log import app_logger, setup_logging
from ..settings import ServiceConfig
from .exception_handlers import add_exception_handlers
from .middlewares import add_middlewares
from .popular import PopularRecommender, get_df
from .views import add_views

__all__ = ("create_app",)


def setup_asyncio(thread_name_prefix: str) -> None:
    uvloop.install()

    loop = asyncio.get_event_loop()

    executor = ThreadPoolExecutor(thread_name_prefix=thread_name_prefix)
    loop.set_default_executor(executor)

    def handler(_, context: Dict[str, Any]) -> None:
        message = "Caught asyncio exception: {message}".format_map(context)
        app_logger.warning(message)

    loop.set_exception_handler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """This function is used to save the OpenAPI documentation
    data of the FastAPI application to a JSON file.
    The purpose of saving the OpenAPI documentation data is to have
    a permanent and offline record of the API specification,
    which can be used for documentation purposes or
    to generate client libraries. It is not necessarily needed,
    but can be helpful in certain scenarios."""
    os.makedirs("recsys", exist_ok=True)
    openapi_data = app.openapi()
    # Change "openapi.json" to desired filename
    with open("./recsys/openapi.json", "w", encoding="utf-8") as file:
        json.dump(openapi_data, file)

    pop_model = PopularRecommender(days=7, dt_column="last_watch_dt")
    train = get_df("./data/interactions.csv")
    pop_model.fit(train)
    app.state.recsys_models["pop_model"] = pop_model
    yield
    # Clean up the RecSys models and release the resources
    app.state.recsys_models.clear()


def create_app(config: ServiceConfig) -> FastAPI:
    setup_logging(config)
    setup_asyncio(thread_name_prefix=config.service_name)

    app = FastAPI(
        debug=False,
        lifespan=lifespan,
        title="Reco Service",
        description="""All recommendation systems completed during the course are presented in this service""",
        version="2023.1.31",
        docs_url="/recsys/docs",
        openapi_url="/recsys/openapi.json",
    )

    app.state.k_recs = config.k_recs
    app.state.recsys_models = {}

    add_views(app)
    add_middlewares(app)
    add_exception_handlers(app)

    return app
