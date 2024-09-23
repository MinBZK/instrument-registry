from fastapi import FastAPI
from task_registry.api.main import api_router
from task_registry.core.config import PROJECT_DESCRIPTION, PROJECT_NAME, VERSION
from task_registry.lifespan import lifespan


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        title=PROJECT_NAME,
        summary=PROJECT_DESCRIPTION,
        version=VERSION,
        docs_url="/",
    )

    app.include_router(api_router)

    return app


app = create_app()
