from __future__ import annotations

from pathlib import Path

from app.integrations.base import run_with_fallback
from app.integrations.crm import CRMIntegration, CachedCRMIntegration
from app.monitoring.metrics import metrics_summary


def test_list_integrations_returns_catalog(client) -> None:
    response = client.get("/api/integrations")
    assert response.status_code == 200
    payload = response.json()
    names = {item["name"] for item in payload}
    assert {"crm_sync", "crm_cached", "notifications", "object_storage"}.issubset(names)


def test_enqueue_integration_executes_task(client) -> None:
    response = client.post("/api/integrations/crm_sync/enqueue")
    assert response.status_code == 202
    task_id = response.json()["task_id"]
    progress = client.get(f"/api/integrations/tasks/{task_id}")
    assert progress.status_code == 200
    data = progress.json()
    assert data["state"] in {"SUCCESS", "PENDING"}
    if data["state"] == "SUCCESS":
        assert data["result"]["name"] == "crm_sync"


def test_run_with_fallback_uses_cache(tmp_path: Path) -> None:
    primary = CRMIntegration(data_source=tmp_path / "missing.json")
    cache_dir = tmp_path / "cache"
    fallback = CachedCRMIntegration(cache_dir=cache_dir)
    cache_file = fallback.cache_file
    cache_file.write_text("{\"contacts\": 1}\n", encoding="utf-8")
    result = run_with_fallback(primary, fallback=fallback)
    assert result.status == "ok"
    assert "fallback" in result.metadata


def test_metrics_endpoint_reports_prometheus(client) -> None:
    response = client.get("/api/metrics")
    assert response.status_code == 200
    body = response.text
    summary = metrics_summary()
    for metric in summary["metrics"]:
        assert metric in body
