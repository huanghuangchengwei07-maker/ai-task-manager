"""HTTP regression checks; no database, AI calls, or running server required."""

import unittest
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.routes import tasks


class TaskErrorTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(tasks.router)
        app.dependency_overrides[tasks.get_db] = lambda: None
        self.client = TestClient(app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)
        self.service_patch = patch.object(tasks, "TaskService", autospec=True)
        self.service = self.service_patch.start().return_value
        self.addCleanup(self.service_patch.stop)

    def test_unexpected_errors_are_private_and_logged_for_all_crud_routes(self):
        cases = [
            ("POST", "/api/tasks", {"title": "test"}, "create"),
            ("GET", "/api/tasks", None, "get_all"),
            ("GET", "/api/tasks/missing", None, "get_by_id"),
            ("PUT", "/api/tasks/missing", {"title": "test"}, "update"),
            ("DELETE", "/api/tasks/missing", None, "delete"),
        ]
        for method, url, payload, service_method in cases:
            with self.subTest(method=method, url=url):
                error = RuntimeError("secret database detail at /srv/private/tasks.py")
                getattr(self.service, service_method).side_effect = error
                with self.assertLogs(tasks.logger, level="ERROR") as logs:
                    response = self.client.request(method, url, json=payload)
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.json(), {"detail": "Internal server error"})
                for private_text in ("Traceback", "/srv/private", "secret database", tasks.__file__):
                    self.assertNotIn(private_text, response.text)
                self.assertEqual(len(logs.records), 1)
                self.assertIs(logs.records[0].exc_info[1], error)
                self.assertIn("Traceback (most recent call last)", logs.output[0])
                self.assertIn(str(error), logs.output[0])

    def test_missing_tasks_still_return_404(self):
        self.service.get_by_id.return_value = None
        self.service.update.return_value = None
        self.service.delete.return_value = False
        with patch.object(tasks.logger, "exception") as log_exception:
            for method, payload in (("GET", None), ("PUT", {"title": "test"}), ("DELETE", None)):
                with self.subTest(method=method):
                    response = self.client.request(method, "/api/tasks/missing", json=payload)
                    self.assertEqual(response.status_code, 404)
                    self.assertEqual(response.json(), {"detail": "Task not found"})
            log_exception.assert_not_called()

    def test_invalid_requests_still_return_422_before_calling_service(self):
        cases = [
            ("POST", "/api/tasks", {"title": ""}),
            ("PUT", "/api/tasks/missing", {"priority": "invalid"}),
            ("GET", "/api/tasks?skip=-1", None),
            ("GET", "/api/tasks?limit=101", None),
            ("GET", "/api/tasks?status=invalid", None),
        ]
        with patch.object(tasks.logger, "exception") as log_exception:
            for method, url, payload in cases:
                with self.subTest(method=method, url=url):
                    response = self.client.request(method, url, json=payload)
                    self.assertEqual(response.status_code, 422)
                    self.assertIsInstance(response.json()["detail"], list)
            self.assertEqual(self.service.mock_calls, [])
            log_exception.assert_not_called()

    def test_service_http_exception_is_preserved(self):
        self.service.create.side_effect = HTTPException(status_code=404, detail="Task not found")
        with patch.object(tasks.logger, "exception") as log_exception:
            response = self.client.post("/api/tasks", json={"title": "test"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Task not found"})
        log_exception.assert_not_called()


if __name__ == "__main__":
    unittest.main()
