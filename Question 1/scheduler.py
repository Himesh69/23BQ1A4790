from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    api_base_url: str = Field(
        "http://4.224.186.213/evaluation-service",
        env="EVAL_API_BASE_URL",
    )
    depots_endpoint: str = Field("depots", env="DEPOTS_ENDPOINT")
    task_list_endpoint: Optional[str] = Field("vehicles", env="TASK_LIST_ENDPOINT")
    depot_tasks_endpoint: Optional[str] = Field(
        "depots/{depot_id}/tasks", env="DEPOT_TASKS_ENDPOINT"
    )
    api_auth_header_name: Optional[str] = Field(None, env="EVAL_API_AUTH_HEADER_NAME")
    api_auth_header_value: Optional[str] = Field(None, env="EVAL_API_AUTH_HEADER_VALUE")


settings = Settings()


@dataclass
class Task:
    task_id: str
    depot_id: Optional[str]
    hours: float
    score: float
    metadata: Dict[str, Any]


class SchedulerError(Exception):
    pass


def build_http_client() -> httpx.Client:
    headers: Dict[str, str] = {}
    if settings.api_auth_header_name and settings.api_auth_header_value:
        headers[settings.api_auth_header_name] = settings.api_auth_header_value

    return httpx.Client(headers=headers, timeout=10.0)


def fetch_json(client: httpx.Client, url: str) -> Any:
    response = client.get(url)
    response.raise_for_status()
    return response.json()


def list_from_payload(payload: Any) -> List[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise SchedulerError("API response is not list-like or dict-like")

    for key in ("tasks", "vehicles", "items", "data", "results", "depots"):
        if key in payload and isinstance(payload[key], list):
            return payload[key]

    # If the payload itself contains only objects and no wrapper list,
    # there is no safe way to turn it into a list of tasks.
    raise SchedulerError("Unable to extract list from API response")


def normalize_id(raw: Dict[str, Any]) -> Optional[str]:
    for key in ("ID", "Id", "id", "taskId", "TaskID", "vehicleId", "task_id"):
        if key in raw:
            return str(raw[key])
    return None


def normalize_hours(raw: Dict[str, Any]) -> Optional[float]:
    for key in (
        "MechanicHours",
        "mechanicHours",
        "hours",
        "durationHours",
        "duration",
        "Duration",
        "time",
    ):
        if key in raw:
            try:
                return float(raw[key])
            except (TypeError, ValueError):
                pass
    return None


def normalize_score(raw: Dict[str, Any]) -> Optional[float]:
    for key in (
        "Score",
        "score",
        "Impact",
        "importance",
        "impactScore",
        "operationalImpact",
    ):
        if key in raw:
            try:
                return float(raw[key])
            except (TypeError, ValueError):
                pass
    return None


def normalize_depot_id(raw: Dict[str, Any]) -> Optional[str]:
    for key in ("depotId", "DepotId", "depot_id", "Depot_ID", "ID", "id"):
        if key in raw:
            return str(raw[key])
    return None


def build_tasks_from_raw(raw_tasks: List[Any], depot_id: Optional[str] = None) -> List[Task]:
    tasks: List[Task] = []
    for raw in raw_tasks:
        if not isinstance(raw, dict):
            continue
        task_id = normalize_id(raw)
        hours = normalize_hours(raw)
        score = normalize_score(raw)
        actual_depot_id = normalize_depot_id(raw) or depot_id
        if task_id is None or hours is None or score is None:
            continue
        if hours <= 0 or score < 0:
            continue
        tasks.append(Task(task_id=task_id, depot_id=actual_depot_id, hours=hours, score=score, metadata=raw))
    return tasks


def fetch_depots(client: httpx.Client) -> List[Dict[str, Any]]:
    url = f"{settings.api_base_url.rstrip('/')}/{settings.depots_endpoint.lstrip('/')}"
    response = fetch_json(client, url)
    return list_from_payload(response)


def fetch_tasks_for_depot(client: httpx.Client, depot_id: str) -> List[Task]:
    if not settings.depot_tasks_endpoint:
        raise SchedulerError("DEPOT_TASKS_ENDPOINT must be configured to fetch tasks by depot")

    endpoint = settings.depot_tasks_endpoint.format(depot_id=depot_id)
    url = f"{settings.api_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    response = fetch_json(client, url)
    return build_tasks_from_raw(list_from_payload(response), depot_id=depot_id)


def fetch_all_tasks(client: httpx.Client, depot_ids: Optional[List[str]] = None) -> List[Task]:
    tasks: List[Task] = []
    if settings.task_list_endpoint:
        url = f"{settings.api_base_url.rstrip('/')}/{settings.task_list_endpoint.lstrip('/')}"
        response = fetch_json(client, url)
        tasks = build_tasks_from_raw(list_from_payload(response))
        if tasks:
            return tasks

    depots = fetch_depots(client)
    if depot_ids:
        depots = [depot for depot in depots if str(normalize_depot_id(depot) or normalize_id(depot)) in depot_ids]
    for depot in depots:
        depot_id = normalize_depot_id(depot) or normalize_id(depot)
        if depot_id is None:
            continue
        tasks.extend(fetch_tasks_for_depot(client, depot_id))
    return tasks


def to_capacity_units(hours: float, unit_size: int = 60) -> int:
    return int(round(hours * unit_size))


def schedule_tasks(tasks: List[Task], budget_hours: float) -> List[Task]:
    capacity = to_capacity_units(budget_hours)
    if capacity <= 0 or not tasks:
        return []

    costs = [to_capacity_units(task.hours) for task in tasks]
    values = [int(task.score) for task in tasks]

    dp = [0] * (capacity + 1)
    prev_index = [-1] * (capacity + 1)
    prev_weight = [-1] * (capacity + 1)

    for index, (cost, value) in enumerate(zip(costs, values)):
        if cost <= 0 or cost > capacity:
            continue
        for weight in range(capacity, cost - 1, -1):
            candidate = dp[weight - cost] + value
            if candidate > dp[weight]:
                dp[weight] = candidate
                prev_index[weight] = index
                prev_weight[weight] = weight - cost

    best_weight = max(range(capacity + 1), key=lambda w: dp[w])
    selected: List[Task] = []
    w = best_weight
    used = set()
    while w > 0 and prev_index[w] != -1:
        task_index = prev_index[w]
        if task_index in used:
            break
        used.add(task_index)
        selected.append(tasks[task_index])
        w = prev_weight[w]

    return list(reversed(selected))
