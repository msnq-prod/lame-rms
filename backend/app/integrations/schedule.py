from __future__ import annotations

try:
    from celery.schedules import crontab  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for environments without Celery installed yet
    def crontab(*args: object, **kwargs: object) -> dict[str, object]:  # type: ignore[override]
        payload = {"type": "crontab"}
        payload.update({"args": args, "kwargs": kwargs})
        return payload


def get_beat_schedule() -> dict[str, dict[str, object]]:
    """Return Celery beat schedule for periodic integrations."""

    return {
        "crm_sync_daily": {
            "task": "app.integrations.tasks.run_crm_sync",
            "schedule": crontab(hour=2, minute=0),
        },
        "storage_cleanup": {
            "task": "app.integrations.tasks.archive_storage_snapshot",
            "schedule": crontab(minute="0", hour="*/6"),
        },
        "notification_digest": {
            "task": "app.integrations.tasks.deliver_notifications",
            "schedule": crontab(minute="*/30"),
        },
    }


__all__ = ["get_beat_schedule"]
