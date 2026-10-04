import json
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.db import get_db
from src.models.task import Base, Task, TaskPriority, TaskStatus
from src.routes.tasks import router


class TaskUpdateTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        with self.sessions() as db:
            db.add(Task(
                id="task-1", title="Original", description="Keep me",
                status=TaskStatus.IN_PROGRESS, priority=TaskPriority.HIGH,
                tags=json.dumps(["work"]), due_date=datetime(2026, 10, 5),
            ))
            db.commit()

        def override_db():
            with self.sessions() as db:
                yield db

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.addCleanup(self.engine.dispose)
        vector = patch("src.services.task_service.get_vector_service", return_value=Mock())
        self.addCleanup(vector.stop)
        self.vector = vector.start().return_value
        ai = patch("src.services.task_service.get_ai_service", return_value=Mock())
        self.addCleanup(ai.stop)
        self.ai = ai.start().return_value
        self.ai.suggest_tags.return_value = ["suggested"]

    def test_partial_updates_preserve_omitted_fields(self):
        for payload in ({}, {"title": "Renamed"}, {"status": "completed"}, {"priority": "low"}):
            with self.subTest(payload=payload):
                before = self.client.get("/api/tasks/task-1").json()
                response = self.client.put("/api/tasks/task-1", json=payload)
                self.assertEqual(response.status_code, 200)
                after = response.json()
                for field in ("title", "status", "priority", "description", "due_date"):
                    self.assertEqual(after[field], payload.get(field, before[field]))

    def test_explicit_null_is_rejected_without_writes(self):
        before = self.client.get("/api/tasks/task-1").json()
        for field in ("title", "status", "priority"):
            with self.subTest(field=field):
                response = self.client.put(
                    "/api/tasks/task-1", json={field: None, "description": "Must not persist"},
                )
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["detail"][0]["loc"], ["body", field])
                self.assertEqual(self.client.get("/api/tasks/task-1").json(), before)
        self.vector.update_task.assert_not_called()
        self.ai.suggest_tags.assert_not_called()

    def test_nullable_fields_can_be_cleared(self):
        response = self.client.put("/api/tasks/task-1", json={
            "title": "Renamed", "description": None, "tags": None, "due_date": None,
        })
        self.assertEqual(response.status_code, 200)
        persisted = self.client.get("/api/tasks/task-1").json()
        for field in ("description", "tags", "due_date"):
            self.assertIsNone(persisted[field])
        self.assertEqual(persisted["title"], "Renamed")
        self.assertEqual(persisted["status"], "in_progress")
        self.assertEqual(persisted["priority"], "high")
        self.ai.suggest_tags.assert_not_called()

    def test_missing_task_still_returns_404(self):
        self.assertEqual(self.client.put("/api/tasks/missing", json={}).status_code, 404)

    def test_database_rejects_null_required_fields(self):
        columns = {column["name"]: column for column in inspect(self.engine).get_columns("tasks")}
        for field in ("title", "status", "priority"):
            with self.subTest(field=field):
                self.assertFalse(columns[field]["nullable"])
                with self.sessions() as db:
                    with self.assertRaises(IntegrityError):
                        db.execute(update(Task).where(Task.id == "task-1").values({field: None}))
                        db.commit()
                    db.rollback()


if __name__ == "__main__":
    unittest.main()
