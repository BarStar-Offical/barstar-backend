from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from app.models import Venues
from tests.conftest import APITestContext

# NOTE: Codex is actively covering API endpoint tests. Please coordinate before editing CODEX-LOCK blocks.


# CODEX-LOCK: Venue endpoint coverage starts here.


def test_create_venue_endpoint(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    events.clear()

    payload = _venue_payload()

    response = client.post("/api/v1/venues", json=payload)
    assert response.status_code == 201
    data = response.json()

    venue_id = UUID(data["id"])
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["owner_id"] == payload["owner_id"]
    assert data["experience_points"] == payload["experience_points"]

    with session_factory() as session:
        stored = session.get(Venues, venue_id)
        assert stored is not None
        assert stored.name == payload["name"]
        assert stored.experience_points == payload["experience_points"]

    assert events == [("venue.created", {"id": str(venue_id)})]


def test_list_venue_endpoint(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    events.clear()

    with session_factory() as session:
        older = Venues(**_venue_payload(name="Older Venue", for_api=False))
        newer = Venues(**_venue_payload(name="Newer Venue", for_api=False))
        session.add_all([older, newer])
        session.commit()
        older_id, newer_id = older.id, newer.id

    response = client.get("/api/v1/venues")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert UUID(data[0]["id"]) == newer_id
    assert UUID(data[1]["id"]) == older_id


def test_get_venue_endpoint(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    events.clear()

    with session_factory() as session:
        venue = Venues(**_venue_payload(name="Lookup Venue", for_api=False))
        session.add(venue)
        session.commit()
        venue_id = venue.id

    response = client.get(f"/api/v1/venues/{venue_id}")
    assert response.status_code == 200
    data = response.json()
    assert UUID(data["id"]) == venue_id
    assert data["name"] == "Lookup Venue"


def test_update_venue_endpoint(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    events.clear()

    with session_factory() as session:
        venue = Venues(**_venue_payload(name="Update Venue", experience_points=50, for_api=False))
        session.add(venue)
        session.commit()
        venue_id = venue.id

    payload: dict[str, Any] = {
        "name": "Updated Venue",
        "experience_points": 120,
        "website": "https://updated.example.com",
        "is_active": False,
    }

    response = client.put(f"/api/v1/venues/{venue_id}", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == payload["name"]
    assert data["experience_points"] == payload["experience_points"]
    assert data["website"] == payload["website"]
    assert data["is_active"] is False

    with session_factory() as session:
        stored = session.get(Venues, venue_id)
        assert stored is not None
        assert stored.name == payload["name"]
        assert stored.website == payload["website"]
        assert stored.experience_points == payload["experience_points"]
        assert stored.is_active is False

    assert events == [("venue.updated", {"id": str(venue_id)})]


def test_delete_venue_endpoint(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    events.clear()

    with session_factory() as session:
        venue = Venues(**_venue_payload(name="Remove Venue", for_api=False))
        session.add(venue)
        session.commit()
        venue_id = venue.id

    response = client.delete(f"/api/v1/venues/{venue_id}")
    assert response.status_code == 204

    with session_factory() as session:
        assert session.get(Venues, venue_id) is None

    assert events == [("venue.deleted", {"id": str(venue_id)})]


def _venue_payload(
    *,
    name: str = "API Venue",
    email: str | None = None,
    owner_id: UUID | None = None,
    experience_points: int = 10,
    for_api: bool = True,
) -> dict[str, Any]:
    """Return a minimal payload for venue creation."""

    owner_identifier = owner_id or uuid4()
    payload: dict[str, Any] = {
        "name": name,
        "email": email or f"{uuid4()}@venue.example.com",
        "experience_points": experience_points,
        "phone_number": "+18885550000",
    }
    if for_api:
        payload["owner_id"] = str(owner_identifier)
    else:
        payload["owner_id"] = owner_identifier
    return payload
