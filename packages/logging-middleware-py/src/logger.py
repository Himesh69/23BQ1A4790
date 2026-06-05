import asyncio
import json
from typing import Optional
from datetime import datetime
import httpx

from .types import (
    LogRequest,
    LogResponse,
    LoggerConfig,
    LogLevel,
    Stack,
    Package,
    LogContextOptions,
)


class Logger:

    def __init__(self, config: LoggerConfig) -> None:
        self.config = config
        self.logQueue: list[LogRequest] = []
        self.flushTimer: Optional[asyncio.Task] = None
        self.contextStack: list[LogContextOptions] = []

    async def log(
        self,
        level: LogLevel,
        package: Package,
        message: str,
        context: Optional[LogContextOptions] = None,
    ) -> Optional[LogResponse]:

        log_entry = LogRequest(
            stack=self.config.stack,
            level=level,
            package=package,
            message=self._enrich_message(message, context),
        )

        if self.config.enableConsoleOutput:
            self._output_to_console(log_entry, context)

        self.logQueue.append(log_entry)

        if len(self.logQueue) >= self.config.batchSize or level == "fatal":
            return await self._flush()

        if not self.flushTimer and len(self.logQueue) > 0:
            self.flushTimer = asyncio.create_task(self._schedule_flush())

        return None

    async def _schedule_flush(self) -> None:
        await asyncio.sleep(self.config.flushInterval / 1000)
        await self._flush()

    async def debug(self, package: Package, message: str, context=None):
        return await self.log("debug", package, message, context)

    async def info(self, package: Package, message: str, context=None):
        return await self.log("info", package, message, context)

    async def warn(self, package: Package, message: str, context=None):
        return await self.log("warn", package, message, context)

    async def error(self, package: Package, message: str, context=None):
        return await self.log("error", package, message, context)

    async def fatal(self, package: Package, message: str, context=None):
        return await self.log("fatal", package, message, context)

    def push_context(self, context: LogContextOptions) -> None:
        self.contextStack.append(context)

    def pop_context(self) -> Optional[LogContextOptions]:
        return self.contextStack.pop() if self.contextStack else None

    def _get_current_context(self) -> LogContextOptions:
        return self.contextStack[-1] if self.contextStack else LogContextOptions()

    def _enrich_message(self, message: str, context=None) -> str:
        merged_context = self._get_current_context().copy()
        if context:
            if isinstance(context, dict):
                merged_context = merged_context.copy(update=context)
            else:
                merged_context = merged_context.copy(update=context.dict())

        context_parts = []

        if merged_context.userId:
            context_parts.append(f"[U:{merged_context.userId}]")
        if merged_context.requestId:
            context_parts.append(f"[R:{merged_context.requestId}]")
        if merged_context.traceId:
            context_parts.append(f"[T:{merged_context.traceId}]")

        prefix = " ".join(context_parts) + " " if context_parts else ""
        enriched_message = prefix + message

        if merged_context.additionalContext:
            enriched_message += (
                f" | Context: {json.dumps(merged_context.additionalContext)}"
            )

        return enriched_message

    def _output_to_console(self, log_entry: LogRequest, context=None) -> None:
        timestamp = datetime.utcnow().isoformat()

        level_colors = {
            "debug": "\033[36m",
            "info": "\033[32m",
            "warn": "\033[33m",
            "error": "\033[31m",
            "fatal": "\033[35m",
        }
        reset = "\033[0m"
        color = level_colors.get(log_entry.level, reset)

        print(
            f"{color}[{timestamp}] {log_entry.level.upper()} [{log_entry.package}]{reset} {log_entry.message}"
        )

    async def _flush(self) -> Optional[LogResponse]:
        if self.flushTimer:
            self.flushTimer.cancel()
            self.flushTimer = None

        if not self.logQueue:
            return None

        logs_to_send = self.logQueue.copy()
        self.logQueue = []

        try:
            last_log = logs_to_send[-1]
            response = await self._send_to_api(last_log)
            return response
        except Exception as e:
            err = str(e)
            print(f"[Logger Error] {err}")
            if "401" in err or "Authorization" in err or "unauthor" in err.lower():
                print(
                    "[Logger Warning] Unauthorized to send logs to API; falling back to console-only logging."
                )
                return None

            self.logQueue = logs_to_send + self.logQueue
            return None

    async def _send_to_api(self, log_entry: LogRequest) -> LogResponse:
        headers = {"Content-Type": "application/json"}

        if self.config.apiKey:
            headers["Authorization"] = f"Bearer {self.config.apiKey}"

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.config.apiEndpoint,
                    headers=headers,
                    json=log_entry.model_dump(by_alias=False),
                )

            if response.status_code not in (200, 201):
                raise Exception(
                    f"API request failed with status {response.status_code}: {response.text}"
                )

            return LogResponse(**response.json())
        except httpx.RequestError as re:
            raise Exception(f"Network error when sending logs: {str(re)}")

    async def force_flush(self) -> None:
        if self.flushTimer:
            self.flushTimer.cancel()
            self.flushTimer = None

        while self.logQueue:
            await self._flush()


_logger_instance: Optional[Logger] = None


def create_logger(config: LoggerConfig) -> Logger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger(config)
    return _logger_instance


def get_logger() -> Logger:
    if _logger_instance is None:
        raise RuntimeError("Logger not initialized. Call create_logger first.")
    return _logger_instance
