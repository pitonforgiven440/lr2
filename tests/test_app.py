# -*- coding: utf-8 -*-
"""Модульные тесты веб-сервиса (ЛР2)."""

import pytest

from main import app


@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as c:
        yield c


def test_get_records(client):
    resp = client.get("/records")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 10


def test_get_records_sorting(client):
    resp = client.get("/records?sort_by=infected&order=desc")
    assert resp.status_code == 200
    values = [r["infected"] for r in resp.get_json()]
    assert values == sorted(values, reverse=True)


def test_get_record_found(client):
    resp = client.get("/records/1")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == 1


def test_get_record_not_found(client):
    resp = client.get("/records/9999")
    assert resp.status_code == 404


def test_post_adds_record(client):
    payload = {
        "country": "Japan", "disease": "COVID-19", "year": 2021,
        "infected": 50000, "recovered": 45000, "deceased": 1000,
    }
    resp = client.post("/records", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["country"] == "Japan"


def test_post_missing_field(client):
    resp = client.post("/records", json={"country": "Japan"})
    assert resp.status_code == 400


def test_put_updates_record(client):
    resp = client.put("/records/1", json={"infected": 111111})
    assert resp.status_code == 200
    assert resp.get_json()["infected"] == 111111


def test_delete_record(client):
    resp = client.delete("/records/10")
    assert resp.status_code == 200
    assert client.get("/records/10").status_code == 404


def test_stats(client):
    resp = client.get("/stats")
    assert resp.status_code == 200
    stats = resp.get_json()
    assert "year" in stats and "infected" in stats
    assert "avg" in stats["year"] and "max" in stats["year"]


def test_patch_updates_single_field(client):
    resp = client.patch("/records/2", json={"infected": 12345})
    assert resp.status_code == 200
    updated = resp.get_json()
    assert updated["infected"] == 12345
    assert updated["country"] == "USA"
