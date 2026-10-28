"""De HTTP-kant van de registry.

De vorm van de index volgt die van MinBZK/task-registry, zodat afnemers die daar
al tegen bouwen (zoals AMT) hetzelfde patroon kunnen hergebruiken: index ophalen,
URN's eruit filteren, per URN het document downloaden.

Alle inhoud wordt bij het opstarten ingelezen en in geheugen gehouden. De inhoud
verandert alleen bij een nieuwe deploy, dus een database voegt niets toe.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from instrument_registry import urn as urn_module
from instrument_registry.validate import ROOT, SCHEMAS_DIR

COLLECTIONS = {
    "assessments": ("dpia.yaml", "iama.yaml", "prescan.yaml"),
    "begrippenkaders": ("begrippenkader_dpia.yaml", "begrippenkader_iama.yaml"),
}


class Link(BaseModel):
    self: str


class FileInfo(BaseModel):
    type: str
    size: int
    name: str
    path: str
    urn: str | None
    download_url: str
    links: Link


class Index(BaseModel):
    type: str
    size: int
    name: str
    path: str
    download_url: str
    registry_version: str
    links: Link
    entries: list[FileInfo]


def registry_version() -> str:
    """The release of the registry itself, set by the container build."""
    return os.environ.get("REGISTRY_VERSION", "development")


def etag_for(payload: bytes) -> str:
    return f'"{hashlib.sha256(payload).hexdigest()[:32]}"'


def _document_response(request: Request, payload: bytes, media_type: str) -> Response:
    """Serve content with an ETag so consumers can poll cheaply."""
    etag = etag_for(payload)
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return Response(content=payload, media_type=media_type, headers={"ETag": etag})


def create_app(root: Path = ROOT) -> FastAPI:
    app = FastAPI(
        title="Instrument registry",
        description="Instrumenten (DPIA, IAMA, pre-scan), begrippenkaders en schema's van de Rijksdienst.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "HEAD"],
        allow_headers=["*"],
    )
    app.state.root = root

    documents: dict[str, dict[str, dict[str, Any]]] = {}
    raw: dict[str, dict[str, bytes]] = {}
    for collection, file_names in COLLECTIONS.items():
        documents[collection] = {}
        raw[collection] = {}
        for file_name in file_names:
            content = (root / "assessments" / file_name).read_bytes()
            raw[collection][file_name] = content
            documents[collection][file_name] = yaml.safe_load(content)

    schemas = {path.name: path.read_bytes() for path in sorted((root / SCHEMAS_DIR.name).glob("*.schema.json"))}

    def build_index(collection: str, base_url: str) -> Index:
        entries: list[FileInfo] = []
        for file_name, document in documents[collection].items():
            document_urn = document.get("urn")
            url = f"{base_url}/{collection}/urn/{document_urn}" if document_urn else f"{base_url}/{collection}"
            entries.append(
                FileInfo(
                    type="file",
                    size=len(raw[collection][file_name]),
                    name=file_name,
                    path=f"assessments/{file_name}",
                    urn=document_urn if isinstance(document_urn, str) else None,
                    download_url=url,
                    links=Link(self=url),
                )
            )
        collection_url = f"{base_url}/{collection}"
        return Index(
            type="dir",
            size=0,
            name=collection,
            path=collection,
            download_url=collection_url,
            registry_version=registry_version(),
            links=Link(self=collection_url),
            entries=entries,
        )

    def serve_by_urn(collection: str, identifier: str, request: Request) -> Response:
        urns = {
            file_name: document["urn"]
            for file_name, document in documents[collection].items()
            if isinstance(document.get("urn"), str)
        }
        file_name = urn_module.resolve(identifier, urns)
        if file_name is None:
            return JSONResponse(status_code=404, content={"detail": f"onbekende URN: {identifier}"})
        if request.query_params.get("format") == "yaml" or "application/yaml" in request.headers.get("accept", ""):
            return _document_response(request, raw[collection][file_name], "application/yaml; charset=utf-8")
        payload = json.dumps(documents[collection][file_name], ensure_ascii=False).encode()
        return _document_response(request, payload, "application/json")

    @app.api_route("/health", methods=["GET", "HEAD"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.api_route("/assessments", methods=["GET", "HEAD"], response_model=Index)
    def assessments_index(request: Request) -> Index:
        return build_index("assessments", str(request.base_url).rstrip("/"))

    @app.api_route("/assessments/urn/{identifier}", methods=["GET", "HEAD"])
    def assessment_by_urn(identifier: str, request: Request) -> Response:
        return serve_by_urn("assessments", identifier, request)

    @app.api_route("/begrippenkaders", methods=["GET", "HEAD"], response_model=Index)
    def begrippenkaders_index(request: Request) -> Index:
        return build_index("begrippenkaders", str(request.base_url).rstrip("/"))

    @app.api_route("/begrippenkaders/urn/{identifier}", methods=["GET", "HEAD"])
    def begrippenkader_by_urn(identifier: str, request: Request) -> Response:
        return serve_by_urn("begrippenkaders", identifier, request)

    @app.api_route("/schemas", methods=["GET", "HEAD"])
    def schemas_index(request: Request) -> dict[str, Any]:
        base_url = str(request.base_url).rstrip("/")
        return {
            "type": "dir",
            "name": "schemas",
            "path": "schemas",
            "registry_version": registry_version(),
            "entries": [
                {
                    "type": "file",
                    "size": len(content),
                    "name": name,
                    "path": f"schemas/{name}",
                    "download_url": f"{base_url}/schemas/{name}",
                    "links": {"self": f"{base_url}/schemas/{name}"},
                }
                for name, content in schemas.items()
            ],
        }

    @app.api_route("/schemas/{name}", methods=["GET", "HEAD"])
    def schema_by_name(name: str, request: Request) -> Response:
        content = schemas.get(name)
        if content is None:
            return JSONResponse(status_code=404, content={"detail": f"onbekend schema: {name}"})
        return _document_response(request, content, "application/json")

    return app


app = create_app()
