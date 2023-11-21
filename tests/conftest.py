# pylint: disable=redefined-outer-name
from datetime import timedelta

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from service.api.app import create_app
from service.api.auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from service.settings import ServiceConfig, get_config


@pytest.fixture
def service_config() -> ServiceConfig:
    return get_config()


@pytest.fixture
def app(
    service_config: ServiceConfig,
) -> FastAPI:
    app = create_app(service_config)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": "johndoe"}, expires_delta=access_token_expires)
    return TestClient(app=app, headers={"Authorization": f"Bearer {access_token}"})
