from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_assets_returns_items(client: TestClient) -> None:
    response = client.get("/api/assets")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 2
    assert len(payload["items"]) <= payload["limit"]
    assert any(item["tag"] == "AST-0001" for item in payload["items"])


def test_search_assets_filters_results(client: TestClient) -> None:
    response = client.get("/api/assets", params={"search": "0002"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["tag"] == "AST-0002"


def test_get_asset_detail(client: TestClient) -> None:
    listing = client.get("/api/assets").json()
    asset_id = listing["items"][0]["id"]
    detail = client.get(f"/api/assets/{asset_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == asset_id
    assert "custom_fields" in body


def test_get_asset_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/api/assets/999999")
    assert response.status_code == 404
