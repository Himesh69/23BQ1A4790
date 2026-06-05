from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


Stack = Literal["backend", "frontend"]

LogLevel = Literal["debug", "info", "warn", "error", "fatal"]

BackendPackage = Literal[
    "cache",
    "controller",
    "cron_job",
    "db",
    "domain",
    "handler",
    "repository",
    "route",
    "service",
]

FrontendPackage = Literal[
    "api",
    "component",
    "hook",
    "page",
    "state",
    "style",
]

SharedPackage = Literal["auth", "config", "middleware", "utils"]

Package = BackendPackage | FrontendPackage | SharedPackage


class LogRequest(BaseModel):
    stack: Stack
    level: LogLevel
    package: Package
    message: str


class LogResponse(BaseModel):
    logID: str
    message: str


class LogContextOptions(BaseModel):
    userId: Optional[str] = None
    requestId: Optional[str] = None
    traceId: Optional[str] = None
    additionalContext: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"


class LoggerConfig(BaseModel):
    apiEndpoint: str
    stack: Stack
    apiKey: Optional[str] = None
    batchSize: int = Field(default=10, ge=1)
    flushInterval: int = Field(default=5000, ge=100)  # milliseconds
    enableConsoleOutput: bool = True
