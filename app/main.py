from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.api.routes import build_router
from app.core.config import get_settings
from app.storage.flow_repository import FlowRepository


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    repository = FlowRepository(settings.flow_dir)
    app.include_router(build_router(repository))

    # 挂载前端 UI 静态目录
    app.mount("/ui", StaticFiles(directory="ui"), name="ui")

    @app.get("/")
    def root():
        return RedirectResponse(url="/ui/index.html")

    return app

app = create_app()
