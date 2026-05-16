"""Dev-only standard-library HTTP adapter for orchestration transport.

This module is intentionally small and development-only. It exposes HTTP-shaped
requests over the existing dependency-free transport handlers so a future app
can prove start, execute, and status flows without adding a web framework or
turning the repo into a production API service.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlparse

from war_room.models import SCHEMA_VERSION_DEFAULT
from war_room.orchestration_api_contracts import (
    OrchestrationErrorResponse,
    OrchestrationFailurePayload,
    orchestration_error_response_to_payload,
)
from war_room.orchestration_service import InMemoryOrchestrationService, default_service
from war_room.orchestration_transport import (
    handle_execute_run,
    handle_get_run_status,
    handle_start_run,
)


class OrchestrationDevHTTPServer(ThreadingHTTPServer):
    """Memory-only dev HTTP server for the offline orchestration transport."""

    def __init__(
        self,
        server_address: tuple[str, int],
        *,
        service: InMemoryOrchestrationService | None = None,
        scenario_id: str | None = None,
        bind_and_activate: bool = True,
    ) -> None:
        self.orchestration_service = service if service is not None else default_service()
        self.scenario_id = scenario_id
        super().__init__(
            server_address,
            OrchestrationDevHTTPRequestHandler,
            bind_and_activate=bind_and_activate,
        )


class OrchestrationDevHTTPRequestHandler(BaseHTTPRequestHandler):
    """Tiny route adapter over `war_room.orchestration_transport` handlers."""

    server: OrchestrationDevHTTPServer

    def do_GET(self) -> None:
        segments = _path_segments(self.path)
        if segments == ["healthz"]:
            self._write_json(_health_payload(), HTTPStatus.OK)
            return

        if len(segments) == 2 and segments[0] == "runs":
            run_id = segments[1]
            response = handle_get_run_status(
                run_id,
                service=self.server.orchestration_service,
                scenario_id=self.server.scenario_id,
            )
            self._write_json(
                response,
                _status_for_transport_response(response),
            )
            return

        self._write_json(
            _http_error_payload(
                operation="http_request",
                code="unknown_route",
                message=f"Unsupported dev orchestration route: {self.command} {urlparse(self.path).path}",
            ),
            HTTPStatus.NOT_FOUND,
        )

    def do_POST(self) -> None:
        segments = _path_segments(self.path)
        if segments == ["runs"]:
            payload, error_response = self._read_json_body(operation="start_run")
            if error_response is not None:
                self._write_json(error_response, HTTPStatus.BAD_REQUEST)
                return

            response = handle_start_run(
                payload or {},
                service=self.server.orchestration_service,
                scenario_id=self.server.scenario_id,
            )
            self._write_json(
                response,
                _status_for_transport_response(response, success_status=HTTPStatus.CREATED),
            )
            return

        if len(segments) == 3 and segments[0] == "runs" and segments[2] == "execute":
            response = handle_execute_run(
                segments[1],
                service=self.server.orchestration_service,
                scenario_id=self.server.scenario_id,
            )
            self._write_json(
                response,
                _status_for_transport_response(response),
            )
            return

        self._write_json(
            _http_error_payload(
                operation="http_request",
                code="unknown_route",
                message=f"Unsupported dev orchestration route: {self.command} {urlparse(self.path).path}",
            ),
            HTTPStatus.NOT_FOUND,
        )

    def do_DELETE(self) -> None:
        self._unsupported_method()

    def do_PATCH(self) -> None:
        self._unsupported_method()

    def do_PUT(self) -> None:
        self._unsupported_method()

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress noisy per-request stderr logs in tests and dev probes."""

    def send_error(
        self,
        code: int,
        message: str | None = None,
        explain: str | None = None,
    ) -> None:
        """Return JSON for BaseHTTPRequestHandler-level errors too."""

        status = HTTPStatus(code)
        error_code = "unsupported_method" if status == HTTPStatus.NOT_IMPLEMENTED else "http_error"
        self._write_json(
            _http_error_payload(
                operation="http_request",
                code=error_code,
                message=message or status.phrase,
            ),
            status,
        )

    def _unsupported_method(self) -> None:
        self._write_json(
            _http_error_payload(
                operation="http_request",
                code="unsupported_method",
                message=f"Unsupported dev orchestration method: {self.command}",
            ),
            HTTPStatus.METHOD_NOT_ALLOWED,
        )

    def _read_json_body(
        self,
        *,
        operation: str,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            content_length = int(raw_length)
        except ValueError:
            return None, _http_error_payload(
                operation=operation,
                code="invalid_content_length",
                message="Content-Length must be an integer.",
            )

        if content_length <= 0:
            return None, _http_error_payload(
                operation=operation,
                code="invalid_json",
                message="Request body must contain a JSON object.",
            )

        raw_body = self.rfile.read(content_length)
        try:
            decoded = raw_body.decode("utf-8")
            payload = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return None, _http_error_payload(
                operation=operation,
                code="invalid_json",
                message="Request body must contain valid JSON.",
                detail=str(exc),
            )

        if not isinstance(payload, Mapping):
            return None, _http_error_payload(
                operation=operation,
                code="invalid_json",
                message="Request body must be a JSON object.",
            )
        return dict(payload), None

    def _write_json(self, payload: Mapping[str, Any], status: HTTPStatus | int) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        status_code = int(status)
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
        self.close_connection = True


def create_dev_http_server(
    server_address: tuple[str, int] = ("127.0.0.1", 8765),
    *,
    service: InMemoryOrchestrationService | None = None,
    scenario_id: str | None = None,
) -> OrchestrationDevHTTPServer:
    """Create a process-local dev server around the existing transport layer."""

    return OrchestrationDevHTTPServer(
        server_address,
        service=service,
        scenario_id=scenario_id,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the dev-only orchestration HTTP adapter until interrupted."""

    parser = argparse.ArgumentParser(
        description="Dev-only HTTP adapter for offline orchestration transport."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host for local dev use.")
    parser.add_argument("--port", type=int, default=8765, help="Bind port for local dev use.")
    parser.add_argument(
        "--scenario-id",
        default=None,
        help="Optional scenario id to include in status_presentation payloads.",
    )
    args = parser.parse_args(argv)

    server = create_dev_http_server(
        (args.host, args.port),
        scenario_id=args.scenario_id,
    )
    host, port = server.server_address
    print(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION_DEFAULT,
                "ok": True,
                "operation": "server_started",
                "payload": {
                    "dev_only": True,
                    "host": host,
                    "port": port,
                    "routes": [
                        "GET /healthz",
                        "POST /runs",
                        "POST /runs/{run_id}/execute",
                        "GET /runs/{run_id}",
                    ],
                },
                "status_presentation": None,
            }
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


def _path_segments(path: str) -> list[str]:
    parsed = urlparse(path)
    return [unquote(segment) for segment in parsed.path.strip("/").split("/") if segment]


def _health_payload() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_DEFAULT,
        "ok": True,
        "operation": "healthz",
        "payload": {
            "status": "ok",
            "dev_only": True,
            "service": "war_room.orchestration_http",
            "transport": "war_room.orchestration_transport",
        },
        "status_presentation": None,
    }


def _http_error_payload(
    *,
    operation: str,
    code: str,
    message: str,
    run_id: str | None = None,
    detail: str = "",
) -> dict[str, Any]:
    response = OrchestrationErrorResponse(
        run_id=run_id,
        error=OrchestrationFailurePayload(
            code=code,
            message=message,
            retryable=False,
            detail=detail,
        ),
    )
    payload = orchestration_error_response_to_payload(response)
    return {
        "schema_version": payload.get("schema_version", SCHEMA_VERSION_DEFAULT),
        "ok": False,
        "operation": operation,
        "payload": payload,
        "status_presentation": None,
    }


def _status_for_transport_response(
    response: Mapping[str, Any],
    *,
    success_status: HTTPStatus = HTTPStatus.OK,
) -> HTTPStatus:
    if response.get("ok") is True:
        return success_status

    payload = response.get("payload")
    error = payload.get("error") if isinstance(payload, Mapping) else {}
    code = error.get("code") if isinstance(error, Mapping) else ""
    if code == "unknown_run_error":
        return HTTPStatus.NOT_FOUND
    if code in {"invalid_run_id", "invalid_start_run_request"}:
        return HTTPStatus.BAD_REQUEST
    return HTTPStatus.BAD_REQUEST


if __name__ == "__main__":
    raise SystemExit(main())
