"""Seeds the exercise catalog (reference/master data, not user data) so the
onboarding plan generator and admin Exercise Library page have something
real to work with on a fresh install."""
from django.db import migrations

EXERCISES = [
    # name, muscle_group, equipment, difficulty, sets, reps, rest_sec, cal/set
    ("Bench Press", "Chest", "Barbell, Bench", "Intermediate", 4, 10, 90, 9),
    ("Incline Dumbbell Press", "Chest", "Dumbbells, Bench", "Intermediate", 3, 12, 75, 8),
    ("Cable Fly", "Chest", "Cable Machine", "Beginner", 3, 12, 60, 6),
    ("Push-up", "Chest", "", "Beginner", 3, 15, 45, 6),
    ("Tricep Pushdown", "Arms", "Cable Machine", "Beginner", 3, 15, 60, 6),
    ("Barbell Curl", "Arms", "Barbell", "Beginner", 3, 12, 60, 6),
    ("Hammer Curl", "Arms", "Dumbbells", "Beginner", 3, 12, 60, 6),
    ("Overhead Tricep Extension", "Arms", "Dumbbells", "Beginner", 3, 12, 60, 6),
    ("Deadlift", "Back", "Barbell", "Advanced", 4, 6, 120, 12),
    ("Lat Pulldown", "Back", "Cable Machine", "Beginner", 4, 10, 75, 8),
    ("Bent Over Row", "Back", "Barbell", "Intermediate", 4, 10, 90, 9),
    ("Pull-up", "Back", "Pull-up Bar", "Advanced", 3, 8, 90, 10),
    ("Seated Cable Row", "Back", "Cable Machine", "Beginner", 3, 12, 75, 7),
    ("Squat", "Legs", "Barbell", "Intermediate", 4, 10, 120, 11),
    ("Leg Press", "Legs", "Machine", "Beginner", 4, 12, 90, 9),
    ("Lunges", "Legs", "Dumbbells", "Beginner", 3, 12, 60, 8),
    ("Leg Curl", "Legs", "Machine", "Beginner", 3, 12, 60, 6),
    ("Calf Raise", "Legs", "Machine", "Beginner", 4, 15, 45, 5),
    ("Bodyweight Squat", "Legs", "", "Beginner", 4, 15, 45, 7),
    ("Overhead Press", "Shoulders", "Barbell", "Intermediate", 4, 10, 90, 8),
    ("Lateral Raise", "Shoulders", "Dumbbells", "Beginner", 3, 15, 60, 5),
    ("Front Raise", "Shoulders", "Dumbbells", "Beginner", 3, 12, 60, 5),
    ("Face Pull", "Shoulders", "Cable Machine", "Beginner", 3, 15, 60, 5),
    ("Plank", "Core", "", "Beginner", 3, 1, 45, 5),
    ("Crunches", "Core", "", "Beginner", 3, 20, 45, 5),
    ("Russian Twist", "Core", "", "Beginner", 3, 20, 45, 5),
    ("Hanging Leg Raise", "Core", "Pull-up Bar", "Advanced", 3, 12, 60, 7),
    ("Treadmill Run", "Cardio", "Treadmill", "Beginner", 1, 1, 0, 10),
    ("Jump Rope", "Cardio", "Jump Rope", "Beginner", 4, 60, 45, 9),
    ("Burpees", "Cardio", "", "Intermediate", 4, 15, 45, 10),
    ("Cycling", "Cardio", "Stationary Bike", "Beginner", 1, 1, 0, 8),
    ("Mountain Climbers", "Cardio", "", "Beginner", 3, 20, 40, 8),
]


def seed_exercises(apps, schema_editor):
    Exercise = apps.get_model("core", "Exercise")
    for name, group, equip, diff, sets, reps, rest, cal in EXERCISES:
        Exercise.objects.get_or_create(
            name=name,
            defaults=dict(
                muscle_group=group, equipment=equip, difficulty=diff,
                default_sets=sets, default_reps=reps, default_rest_seconds=rest,
                calories_per_set=cal,
            ),
        )


def unseed_exercises(apps, schema_editor):
    Exercise = apps.get_model("core", "Exercise")
    Exercise.objects.filter(name__in=[e[0] for e in EXERCISES]).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(seed_exercises, unseed_exercises)]
