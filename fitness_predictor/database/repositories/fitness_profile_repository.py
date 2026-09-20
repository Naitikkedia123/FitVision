from datetime import date
from typing import Any

from database.client import get_supabase_client


class FitnessProfileRepository:
    """
    Handles database operations for a user's fitness profile.
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    def create(
        self,
        user_id: str,
        date_of_birth: date | str,
        sex: str,
        height_cm: float,
        weight_kg: float,
        fitness_level: int,
        activity_level: int,
        goal: str,
        workout_time_min: int,
    ) -> dict[str, Any]:
        """
        Create a fitness profile for a user.
        """

        self._validate_user_id(user_id)

        record = {
            "user_id": user_id,
            "date_of_birth": self._normalize_date(date_of_birth),
            "sex": sex.strip().lower(),
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "fitness_level": fitness_level,
            "activity_level": activity_level,
            "goal": goal.strip().lower(),
            "workout_time_min": workout_time_min,
        }

        self._validate_record(record)

        response = (
            self.supabase
            .table("fitness_profiles")
            .insert(record)
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Fitness profile was not created."
            )

        return response.data[0]

    def get_by_user_id(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        """
        Return the fitness profile belonging to a user.
        """

        self._validate_user_id(user_id)

        response = (
            self.supabase
            .table("fitness_profiles")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def update(
        self,
        user_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update an existing fitness profile.

        Only allowed profile fields can be modified.
        """

        self._validate_user_id(user_id)

        allowed_fields = {
            "date_of_birth",
            "sex",
            "height_cm",
            "weight_kg",
            "fitness_level",
            "activity_level",
            "goal",
            "workout_time_min",
        }

        unknown_fields = set(updates) - allowed_fields

        if unknown_fields:
            raise ValueError(
                f"Unsupported fitness profile fields: "
                f"{sorted(unknown_fields)}"
            )

        if not updates:
            raise ValueError(
                "At least one field is required for update."
            )

        cleaned_updates = dict(updates)

        if "date_of_birth" in cleaned_updates:
            cleaned_updates["date_of_birth"] = self._normalize_date(
                cleaned_updates["date_of_birth"]
            )

        if "sex" in cleaned_updates:
            cleaned_updates["sex"] = (
                str(cleaned_updates["sex"]).strip().lower()
            )

        if "goal" in cleaned_updates:
            cleaned_updates["goal"] = (
                str(cleaned_updates["goal"]).strip().lower()
            )

        # Validate the final values against our DB constraints.
        existing = self.get_by_user_id(user_id)

        if existing is None:
            raise ValueError(
                "Fitness profile does not exist. "
                "Use create() first."
            )

        final_record = {
            **existing,
            **cleaned_updates,
        }

        self._validate_record(final_record)

        response = (
            self.supabase
            .table("fitness_profiles")
            .update(cleaned_updates)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Fitness profile was not updated."
            )

        return response.data[0]

    def _validate_record(
        self,
        record: dict[str, Any],
    ) -> None:
        """
        Validate values before sending them to Supabase.

        Database CHECK constraints remain the final protection.
        """

        valid_sex = {
            "male",
            "female",
            "other",
            "prefer_not_to_say",
        }

        valid_goals = {
            "general_fitness",
            "weight_management",
            "strength",
            "endurance",
        }

        if record["sex"] not in valid_sex:
            raise ValueError(
                f"Invalid sex: {record['sex']}"
            )

        if record["goal"] not in valid_goals:
            raise ValueError(
                f"Invalid goal: {record['goal']}"
            )

        height = float(record["height_cm"])
        weight = float(record["weight_kg"])

        if not 100 <= height <= 250:
            raise ValueError(
                "height_cm must be between 100 and 250."
            )

        if not 30 <= weight <= 300:
            raise ValueError(
                "weight_kg must be between 30 and 300."
            )

        fitness_level = int(record["fitness_level"])
        activity_level = int(record["activity_level"])

        if not 1 <= fitness_level <= 5:
            raise ValueError(
                "fitness_level must be between 1 and 5."
            )

        if not 1 <= activity_level <= 5:
            raise ValueError(
                "activity_level must be between 1 and 5."
            )

        workout_time = int(record["workout_time_min"])

        if not 10 <= workout_time <= 120:
            raise ValueError(
                "workout_time_min must be between 10 and 120."
            )

    @staticmethod
    def _normalize_date(value: date | str) -> str:
        """
        Convert a date or ISO date string to YYYY-MM-DD.
        """

        if isinstance(value, date):
            return value.isoformat()

        if isinstance(value, str):
            try:
                return date.fromisoformat(value).isoformat()
            except ValueError as exc:
                raise ValueError(
                    "date_of_birth must be a valid date in "
                    "YYYY-MM-DD format."
                ) from exc

        raise TypeError(
            "date_of_birth must be a date or YYYY-MM-DD string."
        )

    @staticmethod
    def _validate_user_id(user_id: str) -> None:
        if not user_id or not user_id.strip():
            raise ValueError("user_id cannot be empty.")