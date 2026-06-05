# Question 1 - Vehicle Maintenance Scheduler

Fetches depot and vehicle task data from evaluation APIs, then uses a knapsack-based algorithm to find the optimal daily maintenance schedule within a given mechanic-hour budget.

## Files

- `app.py` — FastAPI application with `/schedule` endpoint
- `scheduler.py` — API integration, task normalization, and knapsack solver
- `requirements.txt` — Python dependencies

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```ini
EVAL_API_BASE_URL=http://4.224.186.213/evaluation-service
DEPOTS_ENDPOINT=depots
TASK_LIST_ENDPOINT=vehicles
DEPOT_TASKS_ENDPOINT=depots/{depot_id}/tasks
EVAL_API_AUTH_HEADER_NAME=Authorization
EVAL_API_AUTH_HEADER_VALUE=Bearer <your-token>
```

## Run

```bash
uvicorn app:app --reload --port 8001
```

## Usage

```
GET http://127.0.0.1:8001/schedule?mechanic_hours=8
```

Optional query parameter `depot_id` to filter tasks by a specific depot.

## Response

```json
{
  "budget_hours": 8.0,
  "total_hours": 8.0,
  "total_score": 340.0,
  "selected_tasks": [
    {
      "task_id": "21",
      "depot_id": "3",
      "hours": 4.0,
      "score": 180.0
    }
  ]
}
```

## Notes

- The evaluation APIs require authorization via the `Authorization` header with a Bearer token.
- The scheduler converts hours to minute-level granularity for the DP solver.
