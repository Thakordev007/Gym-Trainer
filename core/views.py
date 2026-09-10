"""
core/views.py

Real backend logic for every page. Grouped like the templates: public,
accounts, onboarding, dashboard, ai, admin_panel.
"""
import json
from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import models as m
from .forms import (
    AdminLoginForm, BodyDetailsForm, ChangePasswordForm, FitnessPreferencesEditForm,
    ForgotPasswordForm, LoginForm, PreferencesForm, ProfileEditForm, RegisterForm,
)

DAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_LABEL = {"monday": "MON", "tuesday": "TUE", "wednesday": "WED", "thursday": "THU",
             "friday": "FRI", "saturday": "SAT", "sunday": "SUN"}

WORKOUT_DAY_PATTERNS = {
    1: ["wednesday"],
    2: ["tuesday", "friday"],
    3: ["monday", "wednesday", "friday"],
    4: ["monday", "tuesday", "thursday", "friday"],
    5: ["monday", "tuesday", "wednesday", "thursday", "friday"],
    6: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
    7: DAY_ORDER,
}

SPLIT_MUSCLES = {
    "Chest + Triceps": ["Chest", "Arms"],
    "Back + Biceps": ["Back", "Arms"],
    "Legs": ["Legs"],
    "Shoulders + Abs": ["Shoulders", "Core"],
    "Cardio": ["Cardio"],
    "Full Body": ["Chest", "Back", "Legs", "Shoulders", "Core"],
}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return {}


def form_errors(form):
    return {field: errs[0] for field, errs in form.errors.items()}


def staff_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_staff):
            return redirect("admin_login")
        return view_func(request, *args, **kwargs)
    return wrapped


def split_titles_for_goal(goal):
    if goal in ("Muscle Building", "Strength", "Weight Gain"):
        return ["Chest + Triceps", "Back + Biceps", "Legs", "Shoulders + Abs", "Full Body"]
    if goal in ("Weight Loss", "Fat Loss"):
        return ["Full Body", "Cardio", "Legs", "Full Body", "Cardio"]
    return ["Full Body", "Cardio", "Chest + Triceps", "Back + Biceps", "Legs"]


def build_default_plan(user, profile):
    """Generates a real weekly WorkoutPlan from the user's onboarding answers."""
    m.WorkoutPlan.objects.filter(user=user, is_active=True).update(is_active=False)
    plan = m.WorkoutPlan.objects.create(user=user, title=f"{profile.goal or 'My'} Weekly Plan")
    workout_days = WORKOUT_DAY_PATTERNS.get(profile.workout_days, WORKOUT_DAY_PATTERNS[5])
    titles = split_titles_for_goal(profile.goal)
    equipment = [e.lower() for e in (profile.equipment or [])]
    wi = 0
    for order, day in enumerate(DAY_ORDER):
        is_workout = day in workout_days
        title = titles[wi % len(titles)] if is_workout else "Rest / Mobility"
        wd = m.WorkoutDay.objects.create(plan=plan, day=day, title=title, is_rest=not is_workout, order=order)
        if is_workout:
            wi += 1
            groups = SPLIT_MUSCLES.get(title, ["Full Body"])
            qs = list(m.Exercise.objects.filter(muscle_group__in=groups))
            matched = [e for e in qs if not equipment or not e.equipment or
                       any(eq in e.equipment.lower() for eq in equipment)]
            pool = matched or qs or list(m.Exercise.objects.all())
            chosen = (pool * 4)[:4] if pool else []
            for i, ex in enumerate(chosen):
                m.WorkoutDayExercise.objects.create(
                    day=wd, exercise=ex, sets=ex.default_sets, reps=ex.default_reps,
                    rest_seconds=ex.default_rest_seconds, target_weight_kg=0, order=i,
                )
    return plan


def build_default_diet(user, profile):
    weight = profile.weight_kg or 70
    goal = profile.goal
    if goal in ("Weight Loss", "Fat Loss"):
        cals = round(weight * 24)
    elif goal in ("Muscle Building", "Weight Gain", "Strength"):
        cals = round(weight * 34)
    else:
        cals = round(weight * 30)
    protein = round(weight * 2.2)
    fat = round(cals * 0.25 / 9)
    carbs = max(50, round((cals - protein * 4 - fat * 9) / 4))

    target, _ = m.DietTarget.objects.update_or_create(
        user=user,
        defaults=dict(calorie_target=cals, protein_target=protein, carbs_target=carbs, fat_target=fat),
    )
    m.Meal.objects.filter(user=user).delete()
    meals = [
        ("Breakfast", ["Oats", "Eggs", "Banana"], 0.2),
        ("Lunch", ["Rice", "Chicken", "Vegetables"], 0.35),
        ("Snack", ["Greek Yogurt", "Nuts"], 0.15),
        ("Dinner", ["Paneer / Chicken", "Roti", "Salad"], 0.3),
    ]
    for i, (mtype, items, share) in enumerate(meals):
        m.Meal.objects.create(
            user=user, meal_type=mtype, items=items, order=i,
            calories=round(cals * share), protein_g=round(protein * share),
            carbs_g=round(carbs * share), fat_g=round(fat * share),
        )
    return target


def log_activity(user, type_, text, icon="bi-check-circle-fill", tone="lime"):
    m.ActivityLog.objects.create(user=user, type=type_, text=text, icon=icon, icon_tone=tone)


def check_achievements(user):
    total_sessions = m.WorkoutSessionCompletion.objects.filter(user=user).count()
    unlocks = []
    if total_sessions >= 1:
        unlocks.append("first_workout")
    if total_sessions >= 10:
        unlocks.append("ten_workouts")
    today = timezone.now().date()
    streak = 0
    d = today
    dates = set(m.WorkoutSessionCompletion.objects.filter(user=user).values_list("date", flat=True))
    while d in dates:
        streak += 1
        d = d.fromordinal(d.toordinal() - 1)
    if streak >= 7:
        unlocks.append("streak_7")
    if streak >= 30:
        unlocks.append("consistency_30")
    for key in unlocks:
        obj, created = m.Achievement.objects.get_or_create(user=user, key=key)
        if created or not obj.unlocked:
            obj.unlocked = True
            obj.unlocked_at = timezone.now()
            obj.save()
            log_activity(user, "achievement", f'Earned "{obj.get_key_display()}" badge', "bi-trophy-fill", "amber")


# ---------------------------------------------------------------------------
# Public marketing site
# ---------------------------------------------------------------------------
def home(request):
    return render(request, "index.html")


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------
def login_view(request):
    if request.method == "POST":
        data = json_body(request)
        form = LoginForm(data)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form_errors(form)}, status=400)
        identifier = form.cleaned_data["loginId"].strip()
        password = form.cleaned_data["loginPassword"]
        username = identifier
        if "@" in identifier:
            user_match = User.objects.filter(email__iexact=identifier).first()
            if user_match:
                username = user_match.username
        user = authenticate(request, username=username, password=password)
        if user is None:
            return JsonResponse({"ok": False, "errors": {"loginPassword": "Invalid username/email or password."}}, status=400)
        login(request, user)
        profile, _ = m.UserProfile.objects.get_or_create(user=user)
        dest = "/dashboard/" if profile.onboarding_complete else "/onboarding/goal/"
        return JsonResponse({"ok": True, "redirect": dest})
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "accounts/login.html")


def register_view(request):
    if request.method == "POST":
        data = json_body(request)
        form = RegisterForm(data)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form_errors(form)}, status=400)
        cd = form.cleaned_data
        full_name = cd["fullName"].strip()
        first, _, last = full_name.partition(" ")
        user = User.objects.create_user(
            username=cd["username"], email=cd["email"], password=cd["password"],
            first_name=first, last_name=last,
        )
        m.UserProfile.objects.create(user=user, mobile=cd["mobile"])
        login(request, user)
        return JsonResponse({"ok": True, "redirect": "/onboarding/goal/"})
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "accounts/register.html")


def logout_view(request):
    logout(request)
    return redirect("home")


def forgot_password_view(request):
    if request.method == "POST":
        data = json_body(request)
        form = ForgotPasswordForm(data)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form_errors(form)}, status=400)
        # Always respond success (don't reveal whether the email exists).
        user = User.objects.filter(email__iexact=form.cleaned_data["resetEmail"]).first()
        if user:
            from django.core.mail import send_mail
            send_mail(
                "Reset your FitAI password",
                "A password reset was requested for your account. "
                "This demo build logs the email to the console instead of sending it.",
                "no-reply@fitai.app", [user.email], fail_silently=True,
            )
        return JsonResponse({"ok": True})
    return render(request, "accounts/forgot_password.html")


# ---------------------------------------------------------------------------
# Onboarding wizard (each step stores into the session; the last step saves
# everything to the DB at once via /onboarding/generate/)
# ---------------------------------------------------------------------------
ONB_KEY = "onboarding_data"


@login_required
def onboarding_goal(request):
    if request.method == "POST":
        data = json_body(request)
        goal = data.get("goal")
        if not goal:
            return JsonResponse({"ok": False, "errors": {"goal": "Please select a fitness goal."}}, status=400)
        state = request.session.get(ONB_KEY, {})
        state["goal"] = goal
        request.session[ONB_KEY] = state
        return JsonResponse({"ok": True, "redirect": "/onboarding/body-details/"})
    return render(request, "onboarding/fitness_goal.html")


@login_required
def onboarding_body_details(request):
    if request.method == "POST":
        data = json_body(request)
        form = BodyDetailsForm(data)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form_errors(form)}, status=400)
        cd = form.cleaned_data
        height_cm = cd["height"] * 2.54 if cd.get("heightUnit") == "ft/in" else cd["height"]
        weight_kg = cd["weight"] * 0.4536 if cd.get("weightUnit") == "lbs" else cd["weight"]
        target_kg = cd["targetWeight"] * 0.4536 if cd.get("targetWeightUnit") == "lbs" else cd["targetWeight"]
        state = request.session.get(ONB_KEY, {})
        state.update({
            "age": cd["age"], "gender": cd["gender"], "height_cm": height_cm,
            "weight_kg": weight_kg, "target_weight_kg": target_kg,
            "fitness_level": cd["fitnessLevel"], "activity_level": cd["activityLevel"],
            "measurements": cd.get("measurements", ""),
        })
        request.session[ONB_KEY] = state
        return JsonResponse({"ok": True, "redirect": "/onboarding/workout-preferences/"})
    return render(request, "onboarding/body_details.html")


@login_required
def onboarding_preferences(request):
    if request.method == "POST":
        data = json_body(request)
        form = PreferencesForm(data)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form_errors(form)}, status=400)
        cd = form.cleaned_data
        state = request.session.get(ONB_KEY, {})
        state.update({
            "workout_location": cd["workoutLocation"], "workout_days": cd["workoutDays"],
            "workout_duration": cd["workoutDuration"], "workout_time": cd["workoutTime"],
        })
        request.session[ONB_KEY] = state
        return JsonResponse({"ok": True, "redirect": "/onboarding/equipment/"})
    return render(request, "onboarding/workout_preferences.html")


@login_required
def onboarding_equipment(request):
    if request.method == "POST":
        data = json_body(request)
        equipment = data.get("equipment") or []
        if not equipment:
            return JsonResponse({"ok": False, "errors": {"equipment": "Select at least one equipment option."}}, status=400)
        state = request.session.get(ONB_KEY, {})
        state["equipment"] = equipment
        request.session[ONB_KEY] = state
        return JsonResponse({"ok": True, "redirect": "/onboarding/summary/"})
    return render(request, "onboarding/equipment.html")


@login_required
def onboarding_summary(request):
    state = request.session.get(ONB_KEY, {})
    summary_items = [
        {"label": "Goal", "value": state.get("goal", "—")},
        {"label": "Age", "value": state.get("age", "—")},
        {"label": "Height", "value": f"{state.get('height_cm', '—')} cm" if state.get("height_cm") else "—"},
        {"label": "Weight", "value": f"{state.get('weight_kg', '—')} kg" if state.get("weight_kg") else "—"},
        {"label": "Target Weight", "value": f"{state.get('target_weight_kg', '—')} kg" if state.get("target_weight_kg") else "—"},
        {"label": "Fitness Level", "value": state.get("fitness_level", "—")},
        {"label": "Workout", "value": f"{state.get('workout_days', 5)} days/week"},
        {"label": "Duration", "value": state.get("workout_duration", "—")},
        {"label": "Location", "value": state.get("workout_location", "—")},
    ]
    return render(request, "onboarding/summary.html", {
        "summary_items": summary_items,
        "equipment": state.get("equipment", []),
    })


@login_required
@require_POST
def onboarding_generate(request):
    state = request.session.get(ONB_KEY, {})
    profile, _ = m.UserProfile.objects.get_or_create(user=request.user)
    profile.goal = state.get("goal", "")
    profile.age = state.get("age")
    profile.gender = state.get("gender", "")
    profile.height_cm = state.get("height_cm")
    profile.weight_kg = state.get("weight_kg")
    profile.target_weight_kg = state.get("target_weight_kg")
    profile.fitness_level = state.get("fitness_level", "Beginner")
    profile.activity_level = state.get("activity_level", "Moderately Active")
    profile.measurements = state.get("measurements", "")
    profile.workout_location = state.get("workout_location", "Gym")
    profile.workout_days = state.get("workout_days", 5)
    profile.workout_duration = state.get("workout_duration", "60 min")
    profile.workout_time = state.get("workout_time", "Evening")
    profile.equipment = state.get("equipment", [])
    profile.onboarding_complete = True
    profile.save()

    build_default_plan(request.user, profile)
    build_default_diet(request.user, profile)
    if profile.weight_kg:
        m.ProgressEntry.objects.get_or_create(user=request.user, date=timezone.now().date(),
                                               defaults={"weight_kg": profile.weight_kg})
    m.Notification.objects.create(user=request.user, text="Your workout is ready 💪",
                                   icon="bi-lightning-charge-fill", icon_tone="lime")
    log_activity(request.user, "progress", "Completed onboarding and generated a fitness plan",
                 "bi-stars", "violet")
    request.session.pop(ONB_KEY, None)
    return JsonResponse({"ok": True, "redirect": "/dashboard/"})


# ---------------------------------------------------------------------------
# Dashboard (user-facing app)
# ---------------------------------------------------------------------------
@login_required
def dashboard(request):
    user = request.user
    profile, _ = m.UserProfile.objects.get_or_create(user=user)
    if not profile.onboarding_complete:
        return redirect("onboarding_goal")

    plan = m.WorkoutPlan.objects.filter(user=user, is_active=True).prefetch_related("days__exercises__exercise").first()
    today_key = DAY_ORDER[timezone.now().weekday()]
    today = timezone.now().date()

    weekly_cards = []
    today_wd = None
    if plan:
        completed_days = set(m.WorkoutSessionCompletion.objects.filter(user=user, day__plan=plan).values_list("day_id", flat=True))
        for wd in plan.days.all():
            if wd.day == today_key:
                today_wd = wd
                status = "today"
            elif wd.is_rest:
                status = "rest"
            elif wd.id in completed_days:
                status = "completed"
            else:
                status = "upcoming"
            weekly_cards.append({"day": DAY_LABEL[wd.day], "title": wd.title, "status": status,
                                  "url": f"/dashboard/workout-detail/{wd.day}/"})

    today_exercises = []
    today_duration = 0
    if today_wd and not today_wd.is_rest:
        logs_today = {l.day_exercise_id: l for l in m.WorkoutLog.objects.filter(user=user, date=today, day_exercise__day=today_wd)}
        for de in today_wd.exercises.select_related("exercise"):
            log = logs_today.get(de.id)
            done = bool(log and log.completed)
            today_exercises.append({"id": de.id, "name": de.exercise.name, "sets": de.sets, "reps": de.reps,
                                     "rest": de.rest_label, "duration": de.duration_label, "done": done})
            today_duration += int(de.duration_label.split()[0])

    workouts_done = m.WorkoutSessionCompletion.objects.filter(user=user).count()
    week_start = today - timezone.timedelta(days=today.weekday())
    week_done = m.WorkoutSessionCompletion.objects.filter(user=user, date__gte=week_start).count()
    calories_today = m.ProgressEntry.objects.filter(user=user, date=today).values_list("calories", flat=True).first() or 0
    streak = 0
    d = today
    dates = set(m.WorkoutSessionCompletion.objects.filter(user=user).values_list("date", flat=True))
    while d in dates:
        streak += 1
        d = d - timezone.timedelta(days=1)

    weight_to_go = None
    ring_pct = 0
    if profile.weight_kg and profile.target_weight_kg:
        weight_to_go = round(abs(profile.target_weight_kg - profile.weight_kg), 1)
        start_weight = m.ProgressEntry.objects.filter(user=user).order_by("date").values_list("weight_kg", flat=True).first() or profile.weight_kg
        total_span = abs(start_weight - profile.target_weight_kg) or 1
        traveled = abs(start_weight - profile.weight_kg)
        ring_pct = min(100, round((traveled / total_span) * 100))

    mini_schedule = []
    if plan:
        completed_days = set(m.WorkoutSessionCompletion.objects.filter(user=user, day__plan=plan).values_list("day_id", flat=True))
        for wd in list(plan.days.all())[:5]:
            if wd.day == today_key:
                state = "is-today"
            elif wd.id in completed_days:
                state = "is-done"
            else:
                state = ""
            mini_schedule.append({"short": DAY_LABEL[wd.day].title(), "title": wd.title, "state": state,
                                   "is_rest": wd.is_rest, "past": wd.order < timezone.now().weekday()})

    ai_tip = "Log a couple of workouts and I'll start giving you tailored tips here."
    strongest = m.StrengthRecord.objects.filter(user=user).order_by("-best_weight_kg").first()
    if strongest:
        ai_tip = f'"You\'re making progress on {strongest.exercise.name} — want a slightly heavier set today?"'

    context = {
        "profile": profile,
        "greeting_name": user.first_name or user.username,
        "weekly_cards": weekly_cards,
        "today_workout": today_wd,
        "today_exercises": today_exercises,
        "today_duration": today_duration,
        "workouts_done": workouts_done,
        "week_done": week_done,
        "weekly_goal": profile.workout_days,
        "weekly_progress_label": f"{week_done}/{profile.workout_days}",
        "calories_today": calories_today,
        "streak": streak,
        "weight_to_go": weight_to_go,
        "ring_pct": ring_pct,
        "mini_schedule": mini_schedule,
        "ai_tip": ai_tip,
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required
def workout_plan(request):
    profile, _ = m.UserProfile.objects.get_or_create(user=request.user)
    plan = m.WorkoutPlan.objects.filter(user=request.user, is_active=True).prefetch_related("days").first()
    today_key = DAY_ORDER[timezone.now().weekday()]
    weekly_cards = []
    completed = 0
    total_minutes = 0
    total_calories = 0
    if plan:
        completed_days = set(m.WorkoutSessionCompletion.objects.filter(user=request.user, day__plan=plan).values_list("day_id", flat=True))
        for wd in plan.days.all():
            if wd.day == today_key:
                status = "today"
            elif wd.is_rest:
                status = "rest"
            elif wd.id in completed_days:
                status = "completed"
                completed += 1
            else:
                status = "upcoming"
            weekly_cards.append({"day": DAY_LABEL[wd.day], "title": wd.title, "status": status,
                                  "url": f"/dashboard/workout-detail/{wd.day}/"})
        for de in m.WorkoutDayExercise.objects.filter(day__plan=plan):
            total_minutes += int(de.duration_label.split()[0])
            total_calories += de.exercise.calories_per_set * de.sets
    return render(request, "dashboard/workout_plan.html", {
        "profile": profile, "weekly_cards": weekly_cards, "completed": completed,
        "total_days": len(weekly_cards) or 7, "total_minutes": total_minutes, "total_calories": total_calories,
        "completed_unit": f"/ {len(weekly_cards) or 7} days",
    })


@login_required
def workout_detail(request, day):
    day = day.lower()
    profile, _ = m.UserProfile.objects.get_or_create(user=request.user)
    plan = m.WorkoutPlan.objects.filter(user=request.user, is_active=True).first()
    wd = m.WorkoutDay.objects.filter(plan=plan, day=day).prefetch_related("exercises__exercise").first() if plan else None
    exercises = []
    duration = 0
    calories = 0
    if wd:
        today = timezone.now().date()
        logs = {l.day_exercise_id: l for l in m.WorkoutLog.objects.filter(user=request.user, date=today, day_exercise__day=wd)}
        for de in wd.exercises.select_related("exercise"):
            log = logs.get(de.id)
            exercises.append({
                "id": de.id, "name": de.exercise.name, "sets": de.sets, "reps": de.reps,
                "rest": de.rest_label, "weight": log.weight_kg if log else de.target_weight_kg,
                "done": bool(log and log.completed),
            })
            duration += int(de.duration_label.split()[0])
            calories += de.exercise.calories_per_set * de.sets
    return render(request, "dashboard/workout_detail.html", {
        "profile": profile, "day": day, "day_label": day.title(), "workout_day": wd,
        "exercises": exercises, "duration": duration, "calories": calories, "exercise_count": len(exercises),
    })


@login_required
@require_POST
def toggle_exercise(request, de_id):
    de = get_object_or_404(m.WorkoutDayExercise, pk=de_id, day__plan__user=request.user)
    today = timezone.now().date()
    log, _ = m.WorkoutLog.objects.get_or_create(user=request.user, day_exercise=de, date=today)
    log.completed = not log.completed
    log.sets_completed = de.sets if log.completed else 0
    log.save()

    if log.completed:
        log_activity(request.user, "workout", f"Completed {de.exercise.name}")
        wd = de.day
        all_done = not wd.exercises.exclude(
            id__in=m.WorkoutLog.objects.filter(user=request.user, date=today, completed=True).values_list("day_exercise_id", flat=True)
        ).exists()
        if all_done:
            completion, created = m.WorkoutSessionCompletion.objects.get_or_create(
                user=request.user, day=wd, date=today,
                defaults={"duration_minutes": sum(int(e.duration_label.split()[0]) for e in wd.exercises.all()),
                          "calories": sum(e.exercise.calories_per_set * e.sets for e in wd.exercises.all())},
            )
            if created:
                log_activity(request.user, "workout", f"Completed {wd.title} Workout")
                check_achievements(request.user)
    return JsonResponse({"ok": True, "done": log.completed})


@login_required
@require_POST
def log_exercise(request, de_id):
    de = get_object_or_404(m.WorkoutDayExercise, pk=de_id, day__plan__user=request.user)
    data = json_body(request)
    today = timezone.now().date()
    log, _ = m.WorkoutLog.objects.get_or_create(user=request.user, day_exercise=de, date=today)
    if "weight_kg" in data:
        log.weight_kg = float(data["weight_kg"])
    if "reps" in data:
        log.reps = int(data["reps"])
    if "notes" in data:
        log.notes = data["notes"]
    log.save()
    rec, _ = m.StrengthRecord.objects.get_or_create(user=request.user, exercise=de.exercise,
                                                      defaults={"reference_weight_kg": max(log.weight_kg * 1.4, 20)})
    if log.weight_kg > rec.best_weight_kg:
        rec.best_weight_kg = log.weight_kg
        rec.save()
    return JsonResponse({"ok": True, "weight_kg": log.weight_kg, "reps": log.reps})


@login_required
def workout_session(request):
    profile, _ = m.UserProfile.objects.get_or_create(user=request.user)
    day = request.GET.get("day", DAY_ORDER[timezone.now().weekday()])
    plan = m.WorkoutPlan.objects.filter(user=request.user, is_active=True).first()
    wd = m.WorkoutDay.objects.filter(plan=plan, day=day).first() if plan else None
    exercises = list(wd.exercises.select_related("exercise").order_by("order")) if wd else []
    ex_id = request.GET.get("ex")
    current = None
    if ex_id:
        current = next((e for e in exercises if str(e.id) == str(ex_id)), None)
    if not current and exercises:
        current = exercises[0]
    today = timezone.now().date()
    sets_done = 0
    if current:
        log = m.WorkoutLog.objects.filter(user=request.user, day_exercise=current, date=today).first()
        sets_done = log.sets_completed if log else 0
    return render(request, "dashboard/workout_session.html", {
        "profile": profile, "day": day, "current": current, "sets_done": sets_done,
        "exercises": exercises, "set_range": range(current.sets) if current else range(0),
        "back_url": f"/dashboard/workout-detail/{day}/",
    })


@login_required
@require_POST
def complete_set(request):
    data = json_body(request)
    de = get_object_or_404(m.WorkoutDayExercise, pk=data.get("ex"), day__plan__user=request.user)
    weight = float(data.get("weight_kg") or 0)
    reps = int(data.get("reps") or 0)
    today = timezone.now().date()
    log, _ = m.WorkoutLog.objects.get_or_create(user=request.user, day_exercise=de, date=today)
    log.sets_completed = min(de.sets, log.sets_completed + 1)
    log.weight_kg = weight or log.weight_kg
    log.reps = reps or log.reps
    if log.sets_completed >= de.sets:
        log.completed = True
    log.save()
    if log.weight_kg:
        rec, _ = m.StrengthRecord.objects.get_or_create(user=request.user, exercise=de.exercise,
                                                          defaults={"reference_weight_kg": max(log.weight_kg * 1.4, 20)})
        if log.weight_kg > rec.best_weight_kg:
            rec.best_weight_kg = log.weight_kg
            rec.save()
    return JsonResponse({"ok": True, "sets_completed": log.sets_completed, "total_sets": de.sets, "done": log.completed})


@login_required
def diet_plan(request):
    profile, _ = m.UserProfile.objects.get_or_create(user=request.user)
    target = m.DietTarget.objects.filter(user=request.user).first()
    meals = m.Meal.objects.filter(user=request.user)
    meals_list = list(meals)
    total_cal = sum(x.calories for x in meals_list)
    calorie_pct = min(100, round(total_cal / target.calorie_target * 100)) if target and target.calorie_target else 0
    protein_pct = min(100, round(sum(x.protein_g for x in meals_list) / target.protein_target * 100)) if target and target.protein_target else 0
    carbs_pct = min(100, round(sum(x.carbs_g for x in meals_list) / target.carbs_target * 100)) if target and target.carbs_target else 0
    fat_pct = min(100, round(sum(x.fat_g for x in meals_list) / target.fat_target * 100)) if target and target.fat_target else 0
    return render(request, "dashboard/diet_plan.html", {
        "profile": profile, "target": target, "meals": meals,
        "calorie_pct": calorie_pct, "protein_pct": protein_pct, "carbs_pct": carbs_pct, "fat_pct": fat_pct,
    })


@login_required
def progress_view(request):
    profile, _ = m.UserProfile.objects.get_or_create(user=request.user)
    entries = list(m.ProgressEntry.objects.filter(user=request.user).order_by("date"))
    weight_history = [{"label": e.date.strftime("%b %d"), "value": e.weight_kg} for e in entries[-8:]]
    weight_change = None
    if len(entries) >= 2:
        weight_change = round(entries[-1].weight_kg - entries[0].weight_kg, 1)
    avg_calories = None
    cal_entries = [e.calories for e in entries if e.calories]
    if cal_entries:
        avg_calories = round(sum(cal_entries) / len(cal_entries))
    total_days = (timezone.now().date() - entries[0].date).days + 1 if entries else 1
    logged_days = len(entries)
    consistency = min(100, round((logged_days / max(total_days, 1)) * 100)) if entries else 0
    strength_records = m.StrengthRecord.objects.filter(user=request.user).select_related("exercise")
    photos = m.ProgressPhoto.objects.filter(user=request.user)
    photo_by_angle = {p.angle: p for p in photos}
    return render(request, "dashboard/progress.html", {
        "profile": profile, "weight_history": weight_history,
        "weight_history_json": json.dumps(weight_history),
        "weight_change": weight_change,
        "avg_calories": avg_calories, "consistency": consistency, "strength_records": strength_records,
        "photo_by_angle": photo_by_angle,
    })


@login_required
@require_POST
def add_progress_photo(request):
    angle = request.POST.get("angle", "front")
    image = request.FILES.get("image")
    photo, _ = m.ProgressPhoto.objects.update_or_create(user=request.user, angle=angle, defaults={"image": image})
    return JsonResponse({"ok": True})


@login_required
def activity_view(request):
    profile, _ = m.UserProfile.objects.get_or_create(user=request.user)
    logs = m.ActivityLog.objects.filter(user=request.user)[:60]
    grouped = {}
    today = timezone.now().date()
    for log in logs:
        d = log.created_at.date()
        if d == today:
            label = "Today"
        elif d == today - timezone.timedelta(days=1):
            label = "Yesterday"
        else:
            label = d.strftime("%A")
        grouped.setdefault(label, []).append(log)
    achievements = m.Achievement.objects.filter(user=request.user)
    achievement_map = {a.key: a for a in achievements}
    all_defs = m.Achievement.KEY_CHOICES
    achievement_cards = []
    for key, display in all_defs:
        a = achievement_map.get(key)
        achievement_cards.append({
            "icon": m.Achievement.ICONS.get(key, "⭐"), "title": display,
            "unlocked": bool(a and a.unlocked),
        })
    return render(request, "dashboard/activity.html", {
        "profile": profile, "grouped_activity": grouped, "achievement_cards": achievement_cards,
    })


@login_required
def profile_view(request):
    profile, _ = m.UserProfile.objects.get_or_create(user=request.user)
    return render(request, "dashboard/profile.html", {"profile": profile})


@login_required
def profile_edit(request):
    profile, _ = m.UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        data = json_body(request)
        form = ProfileEditForm(data)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form_errors(form)}, status=400)
        cd = form.cleaned_data
        first, _, last = cd["fullName"].strip().partition(" ")
        request.user.first_name = first
        request.user.last_name = last
        request.user.email = cd["email"]
        request.user.save()
        profile.mobile = cd.get("mobile", profile.mobile)
        if cd.get("age"):
            profile.age = cd["age"]
        if cd.get("gender"):
            profile.gender = cd["gender"]
        if cd.get("height"):
            profile.height_cm = cd["height"]
        profile.save()
        return JsonResponse({"ok": True, "redirect": "/dashboard/profile/"})
    return render(request, "accounts/profile_edit.html", {"profile": profile})


@login_required
def profile_preferences(request):
    profile, _ = m.UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        data = json_body(request)
        form = FitnessPreferencesEditForm(data)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form_errors(form)}, status=400)
        cd = form.cleaned_data
        profile.weight_kg = cd["weight"]
        profile.target_weight_kg = cd["targetWeight"]
        profile.goal = cd["goal"]
        profile.fitness_level = cd["fitnessLevel"]
        profile.workout_days = cd["workoutDays"]
        profile.workout_location = cd["workoutLocation"]
        profile.save()
        m.ProgressEntry.objects.get_or_create(user=request.user, date=timezone.now().date(),
                                               defaults={"weight_kg": cd["weight"]})
        return JsonResponse({"ok": True, "redirect": "/dashboard/profile/"})
    return render(request, "accounts/profile_preferences.html", {
        "profile": profile,
        "goal_choices": m.GOAL_CHOICES,
        "fitness_level_choices": m.FITNESS_LEVEL_CHOICES,
        "location_choices": m.LOCATION_CHOICES,
    })


@login_required
def profile_change_password(request):
    if request.method == "POST":
        data = json_body(request)
        form = ChangePasswordForm(data)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form_errors(form)}, status=400)
        if not request.user.check_password(form.cleaned_data["currentPassword"]):
            return JsonResponse({"ok": False, "errors": {"currentPassword": "Current password is incorrect."}}, status=400)
        request.user.set_password(form.cleaned_data["newPassword"])
        request.user.save()
        login(request, request.user)
        return JsonResponse({"ok": True, "redirect": "/dashboard/profile/"})
    return render(request, "accounts/change_password.html")


@login_required
@require_POST
def mark_all_read(request):
    m.Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"ok": True})


# ---------------------------------------------------------------------------
# AI Assistant (rule-based, backed by the user's own real data)
# ---------------------------------------------------------------------------
def get_ai_reply(user, text):
    key = text.strip().lower()
    profile = m.UserProfile.objects.filter(user=user).first()
    plan = m.WorkoutPlan.objects.filter(user=user, is_active=True).first()
    today_key = DAY_ORDER[timezone.now().weekday()]
    today_wd = plan.days.filter(day=today_key).first() if plan else None
    target = m.DietTarget.objects.filter(user=user).first()
    meals = m.Meal.objects.filter(user=user)

    def diet_reply():
        if not target:
            return "You don't have a diet plan yet — finish onboarding and I'll build one around your goal.", "diet"
        parts = "; ".join(f"{meal.meal_type.lower()}: {', '.join(meal.items)}" for meal in meals)
        return f"Based on your {profile.goal or 'fitness'} goal, aim for ~{target.calorie_target} kcal today: {parts}.", "diet"

    def workout_reply():
        if not today_wd or today_wd.is_rest:
            return "Today is a rest day on your plan — some light mobility work or a short walk is a good call.", "workout"
        exs = today_wd.exercises.select_related("exercise")
        parts = ", ".join(f"{e.exercise.name} {e.sets}x{e.reps}" for e in exs)
        return f"Today is {today_wd.title}: {parts}.", "workout"

    def progress_reply():
        entries = list(m.ProgressEntry.objects.filter(user=user).order_by("-date")[:2])
        if len(entries) < 2:
            return "Log a couple of weigh-ins on the Progress page and I can tell you whether you're trending the right way.", "progress"
        diff = round(entries[0].weight_kg - entries[1].weight_kg, 1)
        direction = "up" if diff > 0 else ("down" if diff < 0 else "unchanged,")
        return (f"Your weight is {direction} {abs(diff)} kg since your last log. Check your weekly average "
                f"instead of daily swings before changing anything."), "progress"

    if any(w in key for w in ("diet", "eat", "meal")):
        return diet_reply()
    if any(w in key for w in ("workout", "exercise")):
        return workout_reply()
    if any(w in key for w in ("weight", "losing", "progress")):
        return progress_reply()
    if any(w in key for w in ("recover", "sore")):
        return ("Try 10 minutes of light mobility, foam roll the muscles you trained, and get 7-8 hours "
                "of sleep tonight — that's when the actual recovery happens."), "general"
    if any(w in key for w in ("stamina", "cardio")):
        return ("Add two 20-minute steady-state cardio sessions this week, and finish two workouts with "
                "a short higher-heart-rate circuit."), "general"
    return ('I can help with your workout plan, diet, and progress — try asking things like "give me '
            'today\'s workout" or "what should I eat today?"'), "general"


@login_required
def ai_assistant(request):
    profile, _ = m.UserProfile.objects.get_or_create(user=request.user)
    history = m.ChatMessage.objects.filter(user=request.user)
    return render(request, "ai/ai_assistant.html", {"profile": profile, "history": history})


@login_required
@require_POST
def ai_assistant_send(request):
    data = json_body(request)
    text = (data.get("message") or "").strip()
    if not text:
        return JsonResponse({"ok": False, "errors": {"message": "Message can't be empty."}}, status=400)
    m.ChatMessage.objects.create(user=request.user, sender="user", text=text)
    reply, category = get_ai_reply(request.user, text)
    m.ChatMessage.objects.create(user=request.user, sender="ai", text=reply, category=category)
    return JsonResponse({"ok": True, "reply": reply})


# ---------------------------------------------------------------------------
# Custom admin panel (separate from Django's built-in /admin/, which is
# still available for full CRUD on every model at /admin/).
# ---------------------------------------------------------------------------
def admin_login(request):
    if request.method == "POST":
        data = json_body(request)
        form = AdminLoginForm(data)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form_errors(form)}, status=400)
        user = authenticate(request, username=form.cleaned_data["adminUser"], password=form.cleaned_data["adminPassword"])
        if user is None or not user.is_staff:
            return JsonResponse({"ok": False, "errors": {"adminPassword": "Invalid admin credentials."}}, status=400)
        login(request, user)
        return JsonResponse({"ok": True, "redirect": "/admin-panel/"})
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_dashboard")
    return render(request, "admin_panel/login.html")


def admin_logout(request):
    logout(request)
    return redirect("admin_login")


@staff_required
def admin_dashboard(request):
    total_users = User.objects.count()
    week_ago = timezone.now() - timezone.timedelta(days=7)
    active_cutoff = timezone.now() - timezone.timedelta(days=14)
    active_users = User.objects.filter(
        id__in=m.WorkoutSessionCompletion.objects.filter(date__gte=active_cutoff.date()).values_list("user_id", flat=True)
    ).count()
    new_users = User.objects.filter(date_joined__gte=week_ago).count()
    completed_workouts = m.WorkoutSessionCompletion.objects.count()
    ai_requests = m.ChatMessage.objects.filter(sender="user").count()
    active_plans = m.WorkoutPlan.objects.filter(is_active=True).count()

    now = timezone.now()
    month_counts = []
    for i in range(5, -1, -1):
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        month_counts.append(User.objects.filter(date_joined__year=year, date_joined__month=month).count())
    earliest_year, earliest_month = now.year, now.month - 5
    while earliest_month <= 0:
        earliest_month += 12
        earliest_year -= 1
    running = User.objects.filter(
        Q(date_joined__year__lt=earliest_year) | Q(date_joined__year=earliest_year, date_joined__month__lt=earliest_month)
    ).count()
    growth_cumulative = []
    for c in month_counts:
        running += c
        growth_cumulative.append(running)

    recent_signups = User.objects.order_by("-date_joined")[:4]
    return render(request, "admin_panel/dashboard.html", {
        "total_users": total_users, "active_users": active_users, "new_users": new_users,
        "completed_workouts": completed_workouts, "ai_requests": ai_requests, "active_plans": active_plans,
        "growth_data": growth_cumulative, "growth_data_json": json.dumps(growth_cumulative), "recent_signups": recent_signups,
    })


@staff_required
def admin_users(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.select_related("profile").order_by("-date_joined")
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query))
    return render(request, "admin_panel/users.html", {"users": users[:100], "total_users": User.objects.count(), "query": query})


@staff_required
def admin_user_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = m.UserProfile.objects.get_or_create(user=target_user)
    workouts_done = m.WorkoutSessionCompletion.objects.filter(user=target_user).count()
    ai_requests = m.ChatMessage.objects.filter(user=target_user, sender="user").count()
    return render(request, "admin_panel/user_detail.html", {
        "target_user": target_user, "profile": profile, "workouts_done": workouts_done, "ai_requests": ai_requests,
    })


@staff_required
@require_POST
def admin_toggle_user(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    if target_user != request.user:
        target_user.is_active = not target_user.is_active
        target_user.save()
    return JsonResponse({"ok": True, "is_active": target_user.is_active})


@staff_required
def admin_ai_activity(request):
    total_requests = m.ChatMessage.objects.filter(sender="user").count()
    today = timezone.now().date()
    requests_today = m.ChatMessage.objects.filter(sender="user", created_at__date=today).count()
    recent = m.ChatMessage.objects.filter(sender="user").select_related("user").order_by("-created_at")[:30]
    return render(request, "admin_panel/ai_activity.html", {
        "total_requests": total_requests, "requests_today": requests_today, "recent": recent,
    })


@staff_required
def admin_workouts(request):
    plans = m.WorkoutPlan.objects.filter(is_active=True).select_related("user__profile")
    grouped = {}
    for p in plans:
        key = (p.title, p.user.profile.goal if hasattr(p.user, "profile") else "")
        entry = grouped.setdefault(key, {"title": p.title, "goal": key[1], "users": 0, "days": p.days.count()})
        entry["users"] += 1
    return render(request, "admin_panel/workouts.html", {"plan_groups": list(grouped.values())})


@staff_required
def admin_exercises(request):
    exercises = m.Exercise.objects.all().order_by("muscle_group", "name")
    return render(request, "admin_panel/exercises.html", {"exercises": exercises, "total": exercises.count()})


@staff_required
def admin_diet_plans(request):
    targets = m.DietTarget.objects.select_related("user__profile")
    grouped = {}
    for t in targets:
        goal = t.user.profile.goal if hasattr(t.user, "profile") else "General"
        key = (goal, t.calorie_target)
        entry = grouped.setdefault(key, {
            "name": f"{goal or 'General'} — {t.calorie_target} kcal", "goal": goal,
            "calories": t.calorie_target, "protein": t.protein_target, "carbs": t.carbs_target,
            "fat": t.fat_target, "users": 0,
        })
        entry["users"] += 1
    return render(request, "admin_panel/diet_plans.html", {"plan_groups": list(grouped.values())})


@staff_required
def admin_progress(request):
    total_sessions = m.WorkoutSessionCompletion.objects.count()
    month_start = timezone.now().replace(day=1).date()
    sessions_this_month = m.WorkoutSessionCompletion.objects.filter(date__gte=month_start).count()
    users_with_streaks = m.UserProfile.objects.count() or 1
    avg_consistency = min(100, round((total_sessions / max(users_with_streaks * 7, 1)) * 100))
    activity_series = []
    for i in range(6, -1, -1):
        day = timezone.now().date() - timezone.timedelta(days=i)
        activity_series.append(m.WorkoutSessionCompletion.objects.filter(date=day).count())
    return render(request, "admin_panel/progress.html", {
        "avg_consistency": avg_consistency, "sessions_this_month": sessions_this_month,
        "activity_series": activity_series, "activity_series_json": json.dumps(activity_series),
    })


@staff_required
def admin_notifications(request):
    broadcasts = m.Notification.objects.filter(is_broadcast=True).order_by("-created_at")[:20]
    return render(request, "admin_panel/notifications.html", {"broadcasts": broadcasts})


@staff_required
@require_POST
def admin_broadcast(request):
    data = json_body(request)
    text = (data.get("text") or "").strip()
    if not text:
        return JsonResponse({"ok": False, "errors": {"text": "Broadcast message can't be empty."}}, status=400)
    users = User.objects.filter(is_staff=False)
    m.Notification.objects.bulk_create([
        m.Notification(user=u, text=text, icon="bi-megaphone-fill", icon_tone="violet", is_broadcast=True)
        for u in users
    ])
    return JsonResponse({"ok": True, "sent_to": users.count()})


@staff_required
def admin_settings(request):
    settings_obj = m.SiteSettings.load()
    return render(request, "admin_panel/settings.html", {"site_settings": settings_obj})


@staff_required
@require_POST
def admin_settings_save(request):
    data = json_body(request)
    if "name" in data or "email" in data:
        first, _, last = (data.get("name") or "").strip().partition(" ")
        if first:
            request.user.first_name = first
            request.user.last_name = last
        if data.get("email"):
            request.user.email = data["email"]
        request.user.save()
    settings_obj = m.SiteSettings.load()
    if "allow_registrations" in data:
        settings_obj.allow_registrations = bool(data["allow_registrations"])
    if "ai_assistant_enabled" in data:
        settings_obj.ai_assistant_enabled = bool(data["ai_assistant_enabled"])
    if "maintenance_mode" in data:
        settings_obj.maintenance_mode = bool(data["maintenance_mode"])
    settings_obj.save()
    return JsonResponse({"ok": True})
