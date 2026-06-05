from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from scheduler import Settings, Task, build_http_client, fetch_all_tasks, schedule_tasks


class ScheduledTask(BaseModel):
    task_id: str
    depot_id: Optional[str]
    hours: float
    score: float


class ScheduleResponse(BaseModel):
    budget_hours: float
    total_hours: float
    total_score: float
    selected_tasks: List[ScheduledTask]


app = FastAPI(
    title="Vehicle Maintenance Scheduler",
    description="Fetch depot/task data from evaluation APIs and choose the highest-impact maintenance schedule within mechanic-hour limits.",
    version="1.0.0",
)


@app.get("/schedule", response_model=ScheduleResponse)
def schedule(
    mechanic_hours: float = Query(..., gt=0, description="Available mechanic hours for the day."),
    depot_id: Optional[str] = Query(None, description="Optional depot ID to restrict scheduling."),
):
    settings = Settings()
    client = build_http_client()

    try:
        tasks = fetch_all_tasks(client, depot_ids=[depot_id] if depot_id else None)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        client.close()

    if not tasks:
        raise HTTPException(status_code=404, detail="No task data could be loaded from the configured API endpoints.")

    selected = schedule_tasks(tasks, mechanic_hours)
    total_hours = sum(task.hours for task in selected)
    total_score = sum(task.score for task in selected)

    return ScheduleResponse(
        budget_hours=mechanic_hours,
        total_hours=total_hours,
        total_score=total_score,
        selected_tasks=[
            ScheduledTask(
                task_id=task.task_id,
                depot_id=task.depot_id,
                hours=task.hours,
                score=task.score,
            )
            for task in selected
        ],
    )
