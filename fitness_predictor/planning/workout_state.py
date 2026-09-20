from dataclasses import dataclass


@dataclass
class WorkoutState:

    current_workout: int = 1
    current_week: int = 1

    status: str = "available"

    total_workouts: int = 28

    def start_workout(self):

        if self.status != "available":
            return False

        self.status = "in_progress"

        return True

    def complete_workout(self):

        if self.status != "in_progress":
            return False

        self.status = "completed"

        return True

    def advance_to_next_workout(self):

        if self.status != "completed":
            return False

        if (
            self.current_workout
            >= self.total_workouts
        ):
            return False

        self.current_workout += 1

        self.current_week = (
            (self.current_workout - 1)
            // 7
        ) + 1

        self.status = "available"

        return True

    @property
    def is_plan_complete(self):

        return (
            self.current_workout
            >= self.total_workouts
            and self.status == "completed"
        )