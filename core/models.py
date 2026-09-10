"""
core/models.py

Full data model backing the FitAI app. Every dashboard page, onboarding
step, and admin panel screen reads/writes real rows here instead of the
old hardcoded template values / demo-data.js.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

GOAL_CHOICES = [
    ("Weight Loss", "Weight Loss"),
    ("Weight Gain", "Weight Gain"),
    ("Muscle Building", "Muscle Building"),
    ("Fat Loss", "Fat Loss"),
    ("Strength", "Strength"),
    ("General Fitness", "General Fitness"),
    ("Improve Stamina", "Improve Stamina"),
    ("Maintain Weight", "Maintain Weight"),
]
GENDER_CHOICES = [("Male", "Male"), ("Female", "Female"), ("Other", "Other")]
FITNESS_LEVEL_CHOICES = [("Beginner", "Beginner"), ("Intermediate", "Intermediate"), ("Advanced", "Advanced")]
ACTIVITY_LEVEL_CHOICES = [
    ("Sedentary", "Sedentary"),
    ("Lightly Active", "Lightly Active"),
    ("Moderately Active", "Moderately Active"),
    ("Very Active", "Very Active"),
]
LOCATION_CHOICES = [("Gym", "Gym"), ("Home", "Home"), ("Both", "Both")]
DAY_CHOICES = [
    ("monday", "Monday"), ("tuesday", "Tuesday"), ("wednesday", "Wednesday"),
    ("thursday", "Thursday"), ("friday", "Friday"), ("saturday", "Saturday"), ("sunday", "Sunday"),
]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    mobile = models.CharField(max_length=20, blank=True)
    goal = models.CharField(max_length=30, choices=GOAL_CHOICES, blank=True)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    target_weight_kg = models.FloatField(null=True, blank=True)
    fitness_level = models.CharField(max_length=20, choices=FITNESS_LEVEL_CHOICES, default="Beginner")
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_LEVEL_CHOICES, default="Moderately Active")
    measurements = models.CharField(max_length=255, blank=True)
    workout_location = models.CharField(max_length=10, choices=LOCATION_CHOICES, blank=True)
    workout_days = models.PositiveSmallIntegerField(default=5)
    workout_duration = models.CharField(max_length=20, blank=True)
    workout_time = models.CharField(max_length=20, blank=True)
    equipment = models.JSONField(default=list, blank=True)
    onboarding_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def bmi(self):
        if self.height_cm and self.weight_kg:
            m = self.height_cm / 100
            return round(self.weight_kg / (m * m), 1)
        return None

    @property
    def initial(self):
        name = (self.user.get_full_name() or self.user.username or "?").strip()
        return name[0].upper() if name else "?"


class Exercise(models.Model):
    name = models.CharField(max_length=120, unique=True)
    muscle_group = models.CharField(max_length=60, blank=True)
    equipment = models.CharField(max_length=120, blank=True)
    difficulty = models.CharField(max_length=20, choices=FITNESS_LEVEL_CHOICES, default="Beginner")
    default_sets = models.PositiveSmallIntegerField(default=3)
    default_reps = models.PositiveSmallIntegerField(default=10)
    default_rest_seconds = models.PositiveSmallIntegerField(default=60)
    calories_per_set = models.PositiveSmallIntegerField(default=8)

    def __str__(self):
        return self.name

    @property
    def rest_label(self):
        return f"{self.default_rest_seconds} sec"


class WorkoutPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workout_plans")
    title = models.CharField(max_length=120, default="My Weekly Plan")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"


class WorkoutDay(models.Model):
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name="days")
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    title = models.CharField(max_length=120)
    is_rest = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("plan", "day")
        ordering = ["order"]

    def __str__(self):
        return f"{self.get_day_display()} — {self.title}"


class WorkoutDayExercise(models.Model):
    day = models.ForeignKey(WorkoutDay, on_delete=models.CASCADE, related_name="exercises")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.PositiveSmallIntegerField(default=3)
    reps = models.PositiveSmallIntegerField(default=10)
    rest_seconds = models.PositiveSmallIntegerField(default=60)
    target_weight_kg = models.FloatField(default=0)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.exercise.name} ({self.day})"

    @property
    def rest_label(self):
        return f"{self.rest_seconds} sec"

    @property
    def duration_label(self):
        minutes = max(1, round(self.sets * 1.6))
        return f"{minutes} min"


class WorkoutLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workout_logs")
    day_exercise = models.ForeignKey(WorkoutDayExercise, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField(default=timezone.now)
    weight_kg = models.FloatField(default=0)
    reps = models.PositiveSmallIntegerField(default=0)
    sets_completed = models.PositiveSmallIntegerField(default=0)
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class WorkoutSessionCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="session_completions")
    day = models.ForeignKey(WorkoutDay, on_delete=models.CASCADE, related_name="completions")
    date = models.DateField(default=timezone.now)
    duration_minutes = models.PositiveSmallIntegerField(default=0)
    calories = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("user", "day", "date")


class DietTarget(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="diet_target")
    calorie_target = models.PositiveSmallIntegerField(default=2400)
    protein_target = models.PositiveSmallIntegerField(default=150)
    carbs_target = models.PositiveSmallIntegerField(default=250)
    fat_target = models.PositiveSmallIntegerField(default=70)


class Meal(models.Model):
    MEAL_TYPES = [("Breakfast", "Breakfast"), ("Lunch", "Lunch"), ("Snack", "Snack"), ("Dinner", "Dinner")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="meals")
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    items = models.JSONField(default=list)
    calories = models.PositiveSmallIntegerField(default=0)
    protein_g = models.PositiveSmallIntegerField(default=0)
    carbs_g = models.PositiveSmallIntegerField(default=0)
    fat_g = models.PositiveSmallIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.meal_type} — {self.user.username}"


class ProgressEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="progress_entries")
    date = models.DateField(default=timezone.now)
    weight_kg = models.FloatField()
    calories = models.PositiveSmallIntegerField(null=True, blank=True)
    steps = models.PositiveIntegerField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["date"]


class StrengthRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="strength_records")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    best_weight_kg = models.FloatField(default=0)
    reference_weight_kg = models.FloatField(default=100)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "exercise")

    @property
    def percent(self):
        if self.reference_weight_kg:
            return min(100, round((self.best_weight_kg / self.reference_weight_kg) * 100))
        return 0


class ProgressPhoto(models.Model):
    ANGLE_CHOICES = [("front", "Front"), ("side", "Side"), ("back", "Back")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="progress_photos")
    angle = models.CharField(max_length=10, choices=ANGLE_CHOICES)
    image = models.ImageField(upload_to="progress_photos/", null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Achievement(models.Model):
    KEY_CHOICES = [
        ("streak_7", "7 Day Streak"),
        ("first_workout", "First Workout"),
        ("ten_workouts", "10 Workouts Completed"),
        ("goal_progress", "Goal Progress"),
        ("consistency_30", "30 Day Consistency"),
    ]
    ICONS = {
        "streak_7": "🔥", "first_workout": "💪", "ten_workouts": "🏆",
        "goal_progress": "🎯", "consistency_30": "⚡",
    }
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="achievements")
    key = models.CharField(max_length=30, choices=KEY_CHOICES)
    unlocked = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "key")

    @property
    def icon(self):
        return self.ICONS.get(self.key, "⭐")


class ActivityLog(models.Model):
    TYPE_CHOICES = [("workout", "Workout"), ("diet", "Diet"), ("progress", "Progress"), ("achievement", "Achievement")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_logs")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    text = models.CharField(max_length=255)
    icon = models.CharField(max_length=60, default="bi-check-circle-fill")
    icon_tone = models.CharField(max_length=20, default="lime")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    text = models.CharField(max_length=255)
    icon = models.CharField(max_length=60, default="bi-bell-fill")
    icon_tone = models.CharField(max_length=20, default="violet")
    is_read = models.BooleanField(default=False)
    is_broadcast = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ChatMessage(models.Model):
    SENDER_CHOICES = [("user", "User"), ("ai", "AI")]
    CATEGORY_CHOICES = [("workout", "Workout"), ("diet", "Diet"), ("progress", "Progress"), ("general", "General")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class SiteSettings(models.Model):
    """Singleton row for platform-wide preferences shown on the admin Settings page."""
    allow_registrations = models.BooleanField(default=True)
    ai_assistant_enabled = models.BooleanField(default=True)
    maintenance_mode = models.BooleanField(default=False)

    def __str__(self):
        return "Site Settings"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
