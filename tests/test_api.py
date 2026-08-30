"""Integration tests for GeoTani FastAPI backend service."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_check():
    """Verify health endpoint returns status, database connectivity, and record counts."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["version"] == "0.1.0"
    assert "database" in data
    assert data["total_villages"] > 0
    assert data["total_scores"] > 0


def test_list_crops():
    """Verify crops metadata catalogue."""
    response = client.get("/crops")
    assert response.status_code == 200
    crops = response.json()
    assert len(crops) >= 3
    crop_ids = [c["crop_id"] for c in crops]
    assert "coffee" in crop_ids
    assert "cocoa" in crop_ids
    assert "sugarcane" in crop_ids

    coffee = next(c for c in crops if c["crop_id"] == "coffee")
    assert "temperature" in coffee["factors"]
    assert "soil" in coffee["weights"]


def test_get_single_crop():
    """Verify single crop detail endpoint and 404 behavior."""
    response = client.get("/crops/coffee")
    assert response.status_code == 200
    data = response.json()
    assert data["crop_id"] == "coffee"
    assert data["display_name"] == "Coffee (Robusta)"

    err_response = client.get("/crops/nonexistent_crop")
    assert err_response.status_code == 404


def test_get_village_by_id():
    """Verify fetching village details, centroid, bbox, and crop score breakdown."""
    response = client.get("/villages/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "adm_pcode" in data
    assert "name" in data
    assert "province" in data
    assert data["center_lat"] is not None
    assert data["center_lon"] is not None
    assert len(data["bbox"]) == 4
    assert len(data["scores"]) >= 3

    score_crops = [s["crop"] for s in data["scores"]]
    assert "coffee" in score_crops
    assert "sugarcane" in score_crops


def test_get_village_by_pcode():
    """Verify fetching village by BPS administrative code."""
    v1 = client.get("/villages/1").json()
    pcode = v1["adm_pcode"]

    response = client.get(f"/villages/by-pcode/{pcode}")
    assert response.status_code == 200
    data = response.json()
    assert data["adm_pcode"] == pcode
    assert data["id"] == v1["id"]

    err_response = client.get("/villages/by-pcode/INVALID_PCODE_123")
    assert err_response.status_code == 404


def test_search_villages():
    """Verify searching villages by name or keyword."""
    response = client.get("/villages/search?q=Ardirejo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "Ardirejo" in data[0]["name"]


def test_query_scores_basic():
    """Verify score query with crop filter and pagination."""
    response = client.get("/scores?crop=sugarcane&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["crop"] == "sugarcane"
    assert data["total"] > 0
    assert len(data["items"]) > 0
    scores = [item["score"] for item in data["items"]]
    assert scores == sorted(scores, reverse=True)


def test_query_scores_with_filters():
    """Verify filtering by province, min_score, and ascending sort."""
    url = "/scores?crop=coffee&province=Jawa%20Timur&min_score=80.0&order=asc&limit=5"
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for item in data["items"]:
        assert item["province"].lower() == "jawa timur"
        assert item["score"] >= 80.0


def test_query_scores_with_bbox():
    """Verify spatial bounding box filtering."""
    # Bounding box covering East Java region: [112.0, -8.0, 113.0, -7.0]
    response = client.get("/scores?crop=sugarcane&bbox=112.0,-8.0,113.0,-7.0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 10


def test_query_scores_invalid_parameters():
    """Verify proper validation errors for invalid crop or bbox."""
    err1 = client.get("/scores?crop=invalid_crop")
    assert err1.status_code == 400

    err2 = client.get("/scores?crop=coffee&bbox=invalid_bbox_string")
    assert err2.status_code == 400
