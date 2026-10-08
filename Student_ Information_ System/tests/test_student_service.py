"""Unit tests for student record management."""

import json
import tempfile
import unittest
from pathlib import Path

from src.services.student_service import StudentService


class StudentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data" / "students.json"
        self.service = StudentService(self.data_file)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def add_sample(self) -> dict[str, str]:
        return self.service.add_student(
            {
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "course": "Computer Science",
                "year_level": "2",
            }
        )

    def test_create_read_update_and_delete_persist(self) -> None:
        created = self.add_sample()
        self.assertEqual(created["student_id"], "STU001")
        self.assertEqual(self.service.get_student("stu001")["name"], "Ada Lovelace")

        updated = self.service.update_student(
            "STU001", {"course": "Mathematics"}
        )
        self.assertEqual(updated["course"], "Mathematics")
        self.assertEqual(self.service.get_all_students()[0]["course"], "Mathematics")

        self.assertTrue(self.service.delete_student("STU001"))
        self.assertIsNone(self.service.get_student("STU001"))
        self.assertFalse(self.service.delete_student("STU001"))

    def test_validation_rejects_invalid_email_and_empty_fields(self) -> None:
        for email in ("not-an-email", ""):
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    self.service.add_student(
                        {
                            "name": "Ada",
                            "email": email,
                            "course": "Computer Science",
                            "year_level": "2",
                        }
                    )
        self.assertEqual(self.service.get_all_students(), [])

    def test_search_export_and_id_generation_after_deletion(self) -> None:
        first = self.add_sample()
        second = self.add_sample()
        self.assertEqual(second["student_id"], "STU002")
        self.service.delete_student(first["student_id"])
        self.assertEqual(len(self.service.search_students("LOVELACE")), 1)

        export_file = Path(self.temp_dir.name) / "exports" / "students.json"
        self.service.export_students(export_file)
        self.assertEqual(json.loads(export_file.read_text(encoding="utf-8")), [second])

    def test_invalid_json_is_reported(self) -> None:
        self.data_file.write_text("{invalid", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            self.service.get_all_students()


if __name__ == "__main__":
    unittest.main()
