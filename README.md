# 23BQ1A4790 - Backend Logging Middleware & Scheduler

## Project Structure

```
├── backend-py/              # FastAPI backend with logging middleware
│   ├── app/
│   │   ├── config/          # Environment-based settings
│   │   ├── models/          # Pydantic data models
│   │   ├── handlers/        # Request handlers
│   │   ├── middleware/       # HTTP logging middleware
│   │   ├── repository/      # In-memory database layer
│   │   ├── service/         # Business logic
│   │   ├── cache/           # TTL-based caching
│   │   ├── tasks/           # Background jobs
│   │   └── routes/          # API route definitions
│   └── main.py              # Entry point
├── packages/
│   └── logging-middleware-py/  # Reusable logging package
├── Question 1/              # Vehicle Maintenance Scheduler
└── README.md
```

## Backend (Question 2) - Logging Middleware

A FastAPI application with a custom logging middleware that sends structured logs to an external evaluation API.

### Setup

```bash
cd backend-py
pip install -r requirements.txt
```

Create a `.env` file from the provided configuration and set your API key.

### Run

```bash
python main.py
```

Server starts at `http://localhost:8000`.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/users` | List all users |
| GET | `/api/users/{id}` | Get user by ID |
| POST | `/api/users` | Create a new user |
| PUT | `/api/users/{id}` | Update a user |

### Logging API

All logs are sent to `http://4.224.186.213/evaluation-service/logs` in this format:

```json
{
  "stack": "backend",
  "level": "info",
  "package": "handler",
  "message": "User created successfully"
}
```

---

## Question 1 - Vehicle Maintenance Scheduler

Fetches depot and vehicle data from the evaluation APIs and computes an optimal maintenance schedule using a knapsack algorithm.

### External APIs Used

- `http://4.224.186.213/evaluation-service/depots` - List of depots
- `http://4.224.186.213/evaluation-service/vehicles` - Vehicle task data

### Run

```bash
cd "Question 1"
pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

### Usage

```
GET /schedule?mechanic_hours=8
```

Returns the optimal set of maintenance tasks that fit within the given mechanic-hour budget.

---

## Screenshots

![Postman Testing](Screenshot%202026-06-05%20105601.png)
![API Response](Screenshot%202026-06-05%20110743.png)
![Log Output](Screenshot%202026-06-05%20111126.png)
