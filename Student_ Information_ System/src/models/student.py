"""Student data model and serialization helpers."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class Student:
    """A student record persisted by the application."""

    student_id: str
    name: str
    email: str
    course: str
    year_level: str
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serializable representation of this student."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Student":
        """Create a student from a previously serialized record."""
        required = ("student_id", "name", "email", "course", "year_level")
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(
                "Student record is missing required fields: "
                + ", ".join(missing)
            )

        created_at = data.get("created_at") or _timestamp()
        return cls(
            student_id=str(data["student_id"]),
            name=str(data["name"]),
            email=str(data["email"]),
            course=str(data["course"]),
            year_level=str(data["year_level"]),
            created_at=str(created_at),
            updated_at=str(data.get("updated_at") or created_at),
        )

    def __str__(self) -> str:
        """Return a readable summary suitable for the command-line UI."""
        return (
            f"ID: {self.student_id}\n"
            f"Name: {self.name}\n"
            f"Email: {self.email}\n"
            f"Course: {self.course}\n"
            f"Year Level: {self.year_level}"
        )
