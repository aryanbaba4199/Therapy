"""Comprehensive test suite for Therapist discovery, management, and verification."""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_therapist_creation_and_get_me(client: AsyncClient) -> None:
    """Test authenticated user creating a therapist profile and retrieving it via /me."""
    # 1. Register a user
    reg_payload = {
        "first_name": "Ananya",
        "last_name": "Nair",
        "email": "ananya.nair@example.com",
        "password": "Password123!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create therapist profile
    create_payload = {
        "first_name": "Ananya",
        "last_name": "Nair",
        "display_name": "Dr. Ananya Nair",
        "bio": "Compassionate clinical psychologist with a focus on holistic mental health.",
        "designation": "Clinical Psychologist",
        "specialization": "clinical_psychologist",
        "qualifications": ["M.Sc Clinical Psychology", "M.Phil", "RCI Registered"],
        "experience_years": 8,
        "therapy_hours": 1500,
        "languages": ["ml", "en"],
        "expertises": ["anxiety", "depression", "trauma"],
        "session_modes": ["online", "offline_kozhikode"],
        "pricing": {"amount": 1200, "currency": "INR", "duration_minutes": 60},
    }
    create_res = await client.post("/api/v1/therapists", headers=headers, json=create_payload)
    assert create_res.status_code == 201
    data = create_res.json()["data"]
    therapist_id = data["id"]
    assert data["status"] == "pending_verification"
    assert data["verification"]["status"] == "pending"

    # 3. Retrieve via /me
    me_res = await client.get("/api/v1/therapists/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["data"]["id"] == therapist_id

    # 4. Duplicate creation attempt fails
    dup_res = await client.post("/api/v1/therapists", headers=headers, json=create_payload)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "THERAPIST_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_therapist_discovery_filtering_and_sorting(client: AsyncClient, mock_db: Any) -> None:
    """Test public discovery with indexed filters, pagination, and sorting."""
    # Seed 3 verified active therapists and 1 unverified therapist
    seed_therapists = [
        {
            "id": "t1",
            "user_id": "u1",
            "first_name": "Fathima",
            "last_name": "Rahman",
            "display_name": "Dr. Fathima Rahman",
            "bio": "Experienced consultant psychologist specializing in trauma and relationships.",
            "designation": "Consultant Psychologist",
            "specialization": "consultant_psychologist",
            "qualifications": ["M.Sc", "Ph.D"],
            "experience_years": 10,
            "therapy_hours": 2000,
            "languages": ["ml", "en"],
            "expertises": ["trauma", "relationship", "anxiety"],
            "session_modes": ["online"],
            "pricing": {"amount": 1500, "currency": "INR", "duration_minutes": 60},
            "verification": {"status": "verified", "verified_at": "2026-01-01T00:00:00Z"},
            "status": "active",
        },
        {
            "id": "t2",
            "user_id": "u2",
            "first_name": "Karthik",
            "last_name": "Subramanian",
            "display_name": "Dr. Karthik Subramanian",
            "bio": "Clinical psychologist offering queer-affirmative and ADHD support.",
            "designation": "Clinical Psychologist",
            "specialization": "clinical_psychologist",
            "qualifications": ["M.Phil Clinical Psychology"],
            "experience_years": 5,
            "therapy_hours": 800,
            "languages": ["ta", "en"],
            "expertises": ["adhd", "queer_affirmative"],
            "session_modes": ["online", "offline_bangalore"],
            "pricing": {"amount": 1000, "currency": "INR", "duration_minutes": 60},
            "verification": {"status": "verified", "verified_at": "2026-01-01T00:00:00Z"},
            "status": "active",
        },
        {
            "id": "t3",
            "user_id": "u3",
            "first_name": "Priya",
            "last_name": "Menon",
            "display_name": "Dr. Priya Menon",
            "bio": "Sexual health specialist with deep expertise in couples therapy.",
            "designation": "Sexual Health Specialist",
            "specialization": "sexual_health_specialist",
            "qualifications": ["MD Psychiatry", "FECSM"],
            "experience_years": 15,
            "therapy_hours": 3500,
            "languages": ["ml", "en", "ta"],
            "expertises": ["relationship", "work_stress"],
            "session_modes": ["online", "offline_kozhikode"],
            "pricing": {"amount": 2500, "currency": "INR", "duration_minutes": 60},
            "verification": {"status": "verified", "verified_at": "2026-01-01T00:00:00Z"},
            "status": "active",
        },
        {
            "id": "t4_unverified",
            "user_id": "u4",
            "first_name": "Hidden",
            "last_name": "Therapist",
            "display_name": "Dr. Hidden",
            "bio": "Not yet verified profile.",
            "designation": "Intern Psychologist",
            "specialization": "clinical_psychologist",
            "qualifications": ["B.Sc"],
            "experience_years": 1,
            "therapy_hours": 50,
            "languages": ["en"],
            "expertises": ["anxiety"],
            "session_modes": ["online"],
            "pricing": {"amount": 500, "currency": "INR", "duration_minutes": 60},
            "verification": {"status": "pending"},
            "status": "pending_verification",
        },
    ]
    for t in seed_therapists:
        await mock_db["therapists"].insert_one(t)

    # 1. Base listing should return only 3 verified active therapists
    all_res = await client.get("/api/v1/therapists")
    assert all_res.status_code == 200
    all_data = all_res.json()["data"]
    assert all_data["pagination"]["total_items"] == 3
    assert len(all_data["items"]) == 3
    assert all(item["id"] != "t4_unverified" for item in all_data["items"])

    # 2. Filter by Language: Malayalam ("ml")
    ml_res = await client.get("/api/v1/therapists?language=ml")
    assert ml_res.status_code == 200
    ml_items = ml_res.json()["data"]["items"]
    assert len(ml_items) == 2  # Fathima & Priya

    # 3. Filter by Specialization: clinical_psychologist
    clin_res = await client.get("/api/v1/therapists?specialization=clinical_psychologist")
    assert clin_res.status_code == 200
    clin_items = clin_res.json()["data"]["items"]
    assert len(clin_items) == 1
    assert clin_items[0]["id"] == "t2"

    # 4. Filter by Session Mode: offline_bangalore
    bng_res = await client.get("/api/v1/therapists?session_mode=offline_bangalore")
    assert bng_res.status_code == 200
    bng_items = bng_res.json()["data"]["items"]
    assert len(bng_items) == 1
    assert bng_items[0]["id"] == "t2"

    # 5. Search: "Subramanian"
    search_res = await client.get("/api/v1/therapists?search=Subramanian")
    assert search_res.status_code == 200
    search_items = search_res.json()["data"]["items"]
    assert len(search_items) == 1
    assert search_items[0]["id"] == "t2"

    # 6. Sorting: price_asc
    sort_res = await client.get("/api/v1/therapists?sort=price_asc")
    assert sort_res.status_code == 200
    sorted_items = sort_res.json()["data"]["items"]
    assert sorted_items[0]["pricing"]["amount"] == 1000
    assert sorted_items[-1]["pricing"]["amount"] == 2500

    # 7. Pagination limit test
    page_res = await client.get("/api/v1/therapists?page=1&limit=2")
    assert page_res.status_code == 200
    page_data = page_res.json()["data"]
    assert len(page_data["items"]) == 2
    assert page_data["pagination"]["total_pages"] == 2
    assert page_data["pagination"]["has_next"] is True


@pytest.mark.asyncio
async def test_therapist_detail_and_access_control(client: AsyncClient, mock_db: Any) -> None:
    """Test public access to verified profile vs private access to pending profile."""
    # Seed pending therapist
    await mock_db["therapists"].insert_one(
        {
            "id": "pending_therapist_1",
            "user_id": "owner_user_1",
            "first_name": "Pending",
            "last_name": "Doc",
            "display_name": "Dr. Pending Doc",
            "bio": "Just applied.",
            "designation": "Counselor",
            "specialization": "consultant_psychologist",
            "qualifications": ["MSW"],
            "experience_years": 2,
            "therapy_hours": 100,
            "languages": ["en"],
            "expertises": ["anxiety"],
            "session_modes": ["online"],
            "pricing": {"amount": 800, "currency": "INR", "duration_minutes": 60},
            "verification": {"status": "pending"},
            "status": "pending_verification",
        }
    )

    # Public anonymous detail check for pending therapist should return 404
    anon_res = await client.get("/api/v1/therapists/pending_therapist_1")
    assert anon_res.status_code == 404

    # Seed verified therapist
    await mock_db["therapists"].insert_one(
        {
            "id": "verified_therapist_1",
            "user_id": "verified_user_1",
            "first_name": "Active",
            "last_name": "Doc",
            "display_name": "Dr. Active Doc",
            "bio": "Verified therapist ready for sessions.",
            "designation": "Psychologist",
            "specialization": "clinical_psychologist",
            "qualifications": ["M.Phil"],
            "experience_years": 4,
            "therapy_hours": 400,
            "languages": ["en"],
            "expertises": ["depression"],
            "session_modes": ["online"],
            "pricing": {"amount": 1000, "currency": "INR", "duration_minutes": 60},
            "verification": {"status": "verified"},
            "status": "active",
        }
    )

    # Public anonymous detail check for verified therapist should succeed
    public_res = await client.get("/api/v1/therapists/verified_therapist_1")
    assert public_res.status_code == 200
    assert public_res.json()["data"]["display_name"] == "Dr. Active Doc"


@pytest.mark.asyncio
async def test_therapist_update_and_admin_verification(client: AsyncClient, mock_db: Any) -> None:
    """Test therapist self-update and admin verification approval."""
    # 1. Register therapist user
    t_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Rahul",
            "last_name": "Varma",
            "email": "rahul.varma@example.com",
            "password": "Password123!",
        },
    )
    t_token = t_reg.json()["data"]["access_token"]
    t_headers = {"Authorization": f"Bearer {t_token}"}

    # 2. Register admin user
    admin_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Admin",
            "last_name": "Boss",
            "email": "admin.boss@example.com",
            "password": "Password123!",
        },
    )
    admin_token = admin_reg.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    # Promote admin user in mock_db
    await mock_db["users"].update_one(
        {"email": "admin.boss@example.com"},
        {"$set": {"roles": ["admin"]}},
    )

    # 3. Create therapist profile
    create_res = await client.post(
        "/api/v1/therapists",
        headers=t_headers,
        json={
            "first_name": "Rahul",
            "last_name": "Varma",
            "bio": "Initial bio text goes here.",
            "designation": "Psychologist",
            "specialization": "consultant_psychologist",
            "qualifications": ["M.A. Psychology"],
            "experience_years": 3,
            "therapy_hours": 300,
            "languages": ["en", "ml"],
            "expertises": ["anxiety"],
            "session_modes": ["online"],
            "pricing": {"amount": 1000, "currency": "INR", "duration_minutes": 60},
        },
    )
    therapist_id = create_res.json()["data"]["id"]

    # 4. Self update bio and pricing
    update_res = await client.patch(
        f"/api/v1/therapists/{therapist_id}",
        headers=t_headers,
        json={
            "bio": "Updated comprehensive clinical bio.",
            "pricing": {"amount": 1400, "currency": "INR", "duration_minutes": 60},
        },
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["bio"] == "Updated comprehensive clinical bio."
    assert update_res.json()["data"]["pricing"]["amount"] == 1400

    # 5. Non-admin cannot self-verify or activate unverified profile
    bad_verify = await client.patch(
        f"/api/v1/therapists/{therapist_id}/verification",
        headers=t_headers,
        json={"status": "verified"},
    )
    assert bad_verify.status_code == 403

    # 6. Admin verifies therapist
    admin_verify = await client.patch(
        f"/api/v1/therapists/{therapist_id}/verification",
        headers=admin_headers,
        json={"status": "verified"},
    )
    assert admin_verify.status_code == 200
    data = admin_verify.json()["data"]
    assert data["verification"]["status"] == "verified"
    assert data["status"] == "active"
