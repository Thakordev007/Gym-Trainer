from django.contrib import admin

from . import models


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "goal", "weight_kg", "target_weight_kg", "fitness_level", "workout_days")
    search_fields = ("user__username", "user__email")


@admin.register(models.Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "muscle_group", "equipment", "difficulty")
    search_fields = ("name", "muscle_group")
    list_filter = ("difficulty", "muscle_group")


class WorkoutDayExerciseInline(admin.TabularInline):
    model = models.WorkoutDayExercise
    extra = 1


@admin.register(models.WorkoutDay)
class WorkoutDayAdmin(admin.ModelAdmin):
    list_display = ("plan", "day", "title", "is_rest", "order")
    list_filter = ("day", "is_rest")
    inlines = [WorkoutDayExerciseInline]


class WorkoutDayInline(admin.TabularInline):
    model = models.WorkoutDay
    extra = 0


@admin.register(models.WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "user__username")
    inlines = [WorkoutDayInline]


@admin.register(models.WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ("user", "day_exercise", "date", "weight_kg", "reps", "completed")
    list_filter = ("completed", "date")


@admin.register(models.WorkoutSessionCompletion)
class WorkoutSessionCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "day", "date", "duration_minutes", "calories")


@admin.register(models.DietTarget)
class DietTargetAdmin(admin.ModelAdmin):
    list_display = ("user", "calorie_target", "protein_target", "carbs_target", "fat_target")


@admin.register(models.Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ("user", "meal_type", "calories", "protein_g", "carbs_g", "fat_g")
    list_filter = ("meal_type",)


@admin.register(models.ProgressEntry)
class ProgressEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "weight_kg", "calories", "steps")
    list_filter = ("date",)


@admin.register(models.StrengthRecord)
class StrengthRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "exercise", "best_weight_kg", "reference_weight_kg")


@admin.register(models.ProgressPhoto)
class ProgressPhotoAdmin(admin.ModelAdmin):
    list_display = ("user", "angle", "uploaded_at")


@admin.register(models.Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "key", "unlocked", "unlocked_at")
    list_filter = ("key", "unlocked")


@admin.register(models.ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "text", "created_at")
    list_filter = ("type",)


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "text", "is_read", "is_broadcast", "created_at")
    list_filter = ("is_read", "is_broadcast")


@admin.register(models.ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("user", "sender", "category", "created_at")
    list_filter = ("sender", "category")
    search_fields = ("text", "user__username")


@admin.register(models.SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("allow_registrations", "ai_assistant_enabled", "maintenance_mode")
