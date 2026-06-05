# Backend - Logging Middleware Application

FastAPI backend with integrated logging middleware. Logs are sent to the evaluation service API at each application layer.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
DEBUG=True
PORT=8000
LOG_API_ENDPOINT=http://4.224.186.213/evaluation-service/logs
LOG_API_KEY=<your-jwt-token>
LOG_BATCH_SIZE=5
LOG_FLUSH_INTERVAL=3000
CACHE_TTL=300
```

## Run

```bash
python main.py
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/users` | List users |
| GET | `/api/users/{id}` | Get user by ID |
| POST | `/api/users` | Create user |
| PUT | `/api/users/{id}` | Update user |

## Logging Layers

Logging is integrated at: middleware, routes, handlers, service, repository, cache, and background tasks. Each layer uses the reusable `logging-middleware-py` package from `packages/`.
