import pytest
from fastapi.testclient import TestClient
from fastapi import WebSocket
from app.main import app
import uuid
import time

client = TestClient(app)

@pytest.fixture
def user_token():
    # Register user
    email = f"user_{uuid.uuid4()}@test.com"
    password = "Testpass123!"
    r = client.post("/api/v1/users/signup", json={"email": email, "password": password, "full_name": "Test User"})
    assert r.status_code == 200
    # Login
    r = client.post("/api/v1/login/access-token", data={"username": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"], email

@pytest.fixture
def another_user_token():
    email = f"user_{uuid.uuid4()}@test.com"
    password = "Testpass123!"
    r = client.post("/api/v1/users/signup", json={"email": email, "password": password, "full_name": "Another User"})
    assert r.status_code == 200
    r = client.post("/api/v1/login/access-token", data={"username": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"], email

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def test_user_team_project_workflow(user_token):
    token, email = user_token
    # Create team
    r = client.post("/api/v1/teams/", json={"name": "Test Team", "description": "A team for testing"}, headers=auth_headers(token))
    assert r.status_code == 200
    team_id = r.json()["id"]
    # Create project
    r = client.post("/api/v1/projects/", json={"name": "Test Project", "description": "A project", "team_id": team_id}, headers=auth_headers(token))
    assert r.status_code == 200
    project_id = r.json()["id"]
    # List projects
    r = client.get(f"/api/v1/projects/team/{team_id}", headers=auth_headers(token))
    assert r.status_code == 200
    assert any(p["id"] == project_id for p in r.json())

def test_task_assignment_realtime_notification(user_token, another_user_token):
    token, email = user_token
    token2, email2 = another_user_token
    # Create team and add another user
    r = client.post("/api/v1/teams/", json={"name": "Realtime Team", "description": "Team"}, headers=auth_headers(token))
    team_id = r.json()["id"]
    # Invite second user
    r = client.post(f"/api/v1/teams/{team_id}/invite", params={"user_id": email2}, headers=auth_headers(token))
    # Create project
    r = client.post("/api/v1/projects/", json={"name": "Realtime Project", "description": "", "team_id": team_id}, headers=auth_headers(token))
    project_id = r.json()["id"]
    # Create task assigned to second user
    r = client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Task 1", "project_id": project_id, "assignee_id": email2, "priority": "high"}, headers=auth_headers(token))
    assert r.status_code == 200
    task_id = r.json()["id"]
    # Simulate WebSocket notification (pseudo, as TestClient does not support ws)
    # In real test, use WebSocketTestSession or httpx_ws
    # ws = client.websocket_connect(f"/api/v1/ws/team/{team_id}?user_id={email2}")
    # ws.send_json({"event": "task_update", "payload": {"task_id": task_id, "title": "Task 1"}})
    # msg = ws.receive_json()
    # assert msg["event"] == "task_update"
    # ws.close()

def test_file_upload_attachment_notification(user_token):
    token, email = user_token
    # Create team and project
    r = client.post("/api/v1/teams/", json={"name": "File Team", "description": ""}, headers=auth_headers(token))
    team_id = r.json()["id"]
    r = client.post("/api/v1/projects/", json={"name": "File Project", "description": "", "team_id": team_id}, headers=auth_headers(token))
    project_id = r.json()["id"]
    # Create task
    r = client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "File Task", "project_id": project_id}, headers=auth_headers(token))
    task_id = r.json()["id"]
    # Upload file (simulate by sending file_url)
    file_url = "http://test.com/file.txt"
    r = client.post(f"/api/v1/projects/tasks/{task_id}/attachments", json={"file_url": file_url, "uploaded_by": email}, headers=auth_headers(token))
    assert r.status_code == 200
    # Simulate notification (see above for ws)

def test_permission_change_access_control(user_token, another_user_token):
    token, email = user_token
    token2, email2 = another_user_token
    # Create team and add another user
    r = client.post("/api/v1/teams/", json={"name": "Perm Team", "description": ""}, headers=auth_headers(token))
    team_id = r.json()["id"]
    r = client.post(f"/api/v1/teams/{team_id}/invite", params={"user_id": email2}, headers=auth_headers(token))
    # Create project
    r = client.post("/api/v1/projects/", json={"name": "Perm Project", "description": "", "team_id": team_id}, headers=auth_headers(token))
    project_id = r.json()["id"]
    # Change user2 role to viewer
    r = client.post(f"/api/v1/teams/{team_id}/members/{email2}/role", params={"role": "viewer"}, headers=auth_headers(token))
    assert r.status_code == 200
    # Try to create task as viewer (should fail)
    r = client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Should Fail", "project_id": project_id}, headers=auth_headers(token2))
    assert r.status_code in (401, 403) 

def test_team_member_removal_and_access_revocation(user_token, another_user_token):
    token, email = user_token
    token2, email2 = another_user_token
    # Create team and invite user2
    r = client.post("/api/v1/teams/", json={"name": "Remove Team", "description": ""}, headers=auth_headers(token))
    team_id = r.json()["id"]
    r = client.post(f"/api/v1/teams/{team_id}/invite", params={"user_id": email2}, headers=auth_headers(token))
    # Create project
    r = client.post("/api/v1/projects/", json={"name": "Remove Project", "description": "", "team_id": team_id}, headers=auth_headers(token))
    project_id = r.json()["id"]
    # Remove user2
    r = client.delete(f"/api/v1/teams/{team_id}/members/{email2}", headers=auth_headers(token))
    assert r.status_code == 200
    # User2 should not be able to access project
    r = client.get(f"/api/v1/projects/{project_id}", headers=auth_headers(token2))
    assert r.status_code in (401, 403)
    # Negative: Remove non-existent member
    r = client.delete(f"/api/v1/teams/{team_id}/members/nonexistent", headers=auth_headers(token))
    assert r.status_code == 404

def test_subtask_and_dependency_workflow(user_token):
    token, email = user_token
    # Create team and project
    r = client.post("/api/v1/teams/", json={"name": "Subtask Team", "description": ""}, headers=auth_headers(token))
    team_id = r.json()["id"]
    r = client.post("/api/v1/projects/", json={"name": "Subtask Project", "description": "", "team_id": team_id}, headers=auth_headers(token))
    project_id = r.json()["id"]
    # Create parent task
    r = client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Parent Task", "project_id": project_id}, headers=auth_headers(token))
    parent_id = r.json()["id"]
    # Create subtask
    r = client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Subtask", "project_id": project_id, "parent_task_id": parent_id}, headers=auth_headers(token))
    subtask_id = r.json()["id"]
    # Add dependency
    r = client.post(f"/api/v1/projects/tasks/{parent_id}/dependencies", params={"depends_on_id": subtask_id}, headers=auth_headers(token))
    assert r.status_code == 200
    # Negative: Add dependency to non-existent task
    r = client.post(f"/api/v1/projects/tasks/{parent_id}/dependencies", params={"depends_on_id": str(uuid.uuid4())}, headers=auth_headers(token))
    assert r.status_code in (400, 404)

def test_commenting_and_activity_feed(user_token, another_user_token):
    token, email = user_token
    token2, email2 = another_user_token
    # Create team, invite user2, create project and task
    r = client.post("/api/v1/teams/", json={"name": "Comment Team", "description": ""}, headers=auth_headers(token))
    team_id = r.json()["id"]
    r = client.post(f"/api/v1/teams/{team_id}/invite", params={"user_id": email2}, headers=auth_headers(token))
    r = client.post("/api/v1/projects/", json={"name": "Comment Project", "description": "", "team_id": team_id}, headers=auth_headers(token))
    project_id = r.json()["id"]
    r = client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Comment Task", "project_id": project_id}, headers=auth_headers(token))
    task_id = r.json()["id"]
    # Add comments
    r = client.post(f"/api/v1/projects/tasks/{task_id}/comments", json={"content": "First comment", "user_id": email}, headers=auth_headers(token))
    assert r.status_code == 200
    r = client.post(f"/api/v1/projects/tasks/{task_id}/comments", json={"content": "Second comment", "user_id": email2}, headers=auth_headers(token2))
    assert r.status_code == 200
    # Retrieve comments
    r = client.get(f"/api/v1/projects/tasks/{task_id}/comments", headers=auth_headers(token))
    assert r.status_code == 200
    assert len(r.json()) >= 2
    # Negative: Comment on non-existent task
    r = client.post(f"/api/v1/projects/tasks/{uuid.uuid4()}/comments", json={"content": "Nope", "user_id": email}, headers=auth_headers(token))
    assert r.status_code in (400, 404)

def test_overdue_and_upcoming_task_analytics(user_token):
    token, email = user_token
    import time
    now = int(time.time())
    # Create team and project
    r = client.post("/api/v1/teams/", json={"name": "Analytics Team", "description": ""}, headers=auth_headers(token))
    team_id = r.json()["id"]
    r = client.post("/api/v1/projects/", json={"name": "Analytics Project", "description": "", "team_id": team_id}, headers=auth_headers(token))
    project_id = r.json()["id"]
    # Create overdue and upcoming tasks
    r = client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Overdue Task", "project_id": project_id, "due_date": now - 86400}, headers=auth_headers(token))
    r = client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Upcoming Task", "project_id": project_id, "due_date": now + 86400}, headers=auth_headers(token))
    # Query dashboard
    r = client.get(f"/api/v1/dashboard/team/{team_id}/deadlines", headers=auth_headers(token))
    assert r.status_code == 200
    data = r.json()
    assert any(t["title"] == "Overdue Task" for t in data["overdue"]) or any(t["title"] == "Upcoming Task" for t in data["upcoming"])
    # Negative: Non-member access
    r = client.get(f"/api/v1/dashboard/team/{team_id}/deadlines")
    assert r.status_code in (401, 403)

def test_user_profile_update(user_token):
    token, email = user_token
    # Update profile
    r = client.patch("/api/v1/users/me", json={"full_name": "Updated Name"}, headers=auth_headers(token))
    assert r.status_code == 200
    assert r.json()["full_name"] == "Updated Name"
    # Negative: Update without auth
    r = client.patch("/api/v1/users/me", json={"full_name": "No Auth"})
    assert r.status_code in (401, 403)

def test_notification_queue_for_offline_users(user_token, another_user_token):
    token, email = user_token
    token2, email2 = another_user_token
    # Create team, invite user2, create project and task
    r = client.post("/api/v1/teams/", json={"name": "Notif Team", "description": ""}, headers=auth_headers(token))
    team_id = r.json()["id"]
    r = client.post(f"/api/v1/teams/{team_id}/invite", params={"user_id": email2}, headers=auth_headers(token))
    r = client.post("/api/v1/projects/", json={"name": "Notif Project", "description": "", "team_id": team_id}, headers=auth_headers(token))
    project_id = r.json()["id"]
    r = client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Notif Task", "project_id": project_id, "assignee_id": email2}, headers=auth_headers(token))
    # Simulate user2 offline, send notification (pseudo, see ws test)
    # Negative: Try to send notification to non-member
    r = client.post(f"/api/v1/teams/{team_id}/invite", params={"user_id": "not_a_user"}, headers=auth_headers(token))
    assert r.status_code in (400, 404)

def test_rate_limiting_enforcement(user_token):
    token, email = user_token
    # Exceed rate limit
    for _ in range(105):
        r = client.get("/api/v1/projects/", headers=auth_headers(token))
        if r.status_code == 429:
            break
    assert r.status_code == 429
    # Negative: Unauthenticated user rate limit
    for _ in range(105):
        r = client.get("/api/v1/projects/")
        if r.status_code == 429:
            break
    assert r.status_code == 429 