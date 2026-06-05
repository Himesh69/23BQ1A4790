# Logging Middleware (Python)

Reusable logging package for Python backend applications. Sends structured logs to a remote API with batching, context stacking, and colored console output.

## Usage

```python
from src.logger import create_logger, get_logger
from src.types import LoggerConfig

config = LoggerConfig(
    apiEndpoint="http://4.224.186.213/evaluation-service/logs",
    stack="backend",
    apiKey="your-key",
    batchSize=5,
    flushInterval=3000,
    enableConsoleOutput=True,
)

logger = create_logger(config)

# then anywhere in the app:
app_logger = get_logger()
await app_logger.info("service", "User created")
await app_logger.error("handler", "Invalid input", {"additionalContext": {"field": "email"}})
```

## Log Levels

`debug`, `info`, `warn`, `error`, `fatal`

## Packages

Backend: `cache`, `controller`, `cron_job`, `db`, `domain`, `handler`, `repository`, `route`, `service`

Shared: `auth`, `config`, `middleware`, `utils`
