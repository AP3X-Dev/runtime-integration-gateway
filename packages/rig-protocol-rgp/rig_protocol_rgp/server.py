from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from rig_core.registry import ToolRegistry
from rig_core.runtime import RigRuntime


class CallBody(BaseModel):
    args: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


def create_app(registry: ToolRegistry, runtime: RigRuntime) -> FastAPI:
    app = FastAPI(title="RIG Gateway Protocol", version="0.1.0")

    @app.get("/v1/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/tools")
    def tools() -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for t in registry.list_tools():
            out.append(
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.input_schema,
                    "output_schema": t.output_schema,
                    "error_schema": t.error_schema,
                    "auth_slots": t.auth_slots,
                    "risk_class": t.risk_class,
                    "tags": t.tags,
                }
            )
        return out

    @app.get("/v1/tools/{name}")
    def tool(name: str) -> Dict[str, Any]:
        t = registry.get(name)
        if not t:
            raise HTTPException(status_code=404, detail="tool not found")
        return {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
            "output_schema": t.output_schema,
            "error_schema": t.error_schema,
            "auth_slots": t.auth_slots,
            "risk_class": t.risk_class,
            "tags": t.tags,
        }

    @app.post("/v1/tools/{name}:call")
    def call(name: str, body: CallBody) -> Dict[str, Any]:
        ctx = body.context or {}
        result = runtime.call(name, body.args, ctx)  # type: ignore
        return {
            "ok": result.ok,
            "output": result.output,
            "error": None if not result.error else result.error.__dict__,
            "correlation_id": result.correlation_id,
            "pack": result.pack,
            "pack_version": result.pack_version,
            "interface_hash": result.interface_hash,
            "pack_set_version": result.pack_set_version,
        }

    @app.post("/v1/approvals/{token}:approve")
    def approve(token: str) -> Dict[str, Any]:
        result = runtime.approve_and_call(token)
        return {
            "ok": result.ok,
            "output": result.output,
            "error": None if not result.error else result.error.__dict__,
            "correlation_id": result.correlation_id,
            "pack": result.pack,
            "pack_version": result.pack_version,
            "interface_hash": result.interface_hash,
            "pack_set_version": result.pack_set_version,
        }

    return app
