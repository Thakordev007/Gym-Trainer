/**
 * demo-data.js
 * Temporary front-end-only demo data.
 * Replace each object/array below with data from the Django backend
 * (context variables or a REST/API response) once available.
 * Keeping this separate from UI code means no other file needs to change.
 */

const DEMO_USER_PROFILE = {
  name: "Dev",
  username: "devsharma",
  email: "dev@example.com",
  goal: "Muscle Building",
  age: 24,
  gender: "Male",
  height: 175,
  heightUnit: "cm",
  weight: 70,
  weightUnit: "kg",
  targetWeight: 78,
  fitnessLevel: "Beginner",
  activityLevel: "Moderately Active",
  workoutDays: 5,
  workoutDuration: "60 min",
  workoutTime: "Evening",
  workoutLocation: "Gym",
  equipment: ["Dumbbells", "Barbell", "Bench", "Cable Machine"]
};

const DEMO_WEEKLY_PLAN = [
  { day: "Monday", title: "Chest + Triceps", status: "completed" },
  { day: "Tuesday", title: "Back + Biceps", status: "today" },
  { day: "Wednesday", title: "Rest / Mobility", status: "rest" },
  { day: "Thursday", title: "Legs", status: "upcoming" },
  { day: "Friday", title: "Shoulders + Abs", status: "upcoming" },
  { day: "Saturday", title: "Cardio", status: "upcoming" },
  { day: "Sunday", title: "Rest", status: "rest" }
];

const DEMO_TODAY_WORKOUT = {
  title: "Chest & Triceps",
  duration: 55,
  exercises: [
    { name: "Bench Press", sets: 4, reps: 10, rest: "90 sec", duration: "8 min", done: true },
    { name: "Incline Dumbbell Press", sets: 3, reps: 12, rest: "75 sec", duration: "7 min", done: false },
    { name: "Cable Fly", sets: 3, reps: 12, rest: "60 sec", duration: "6 min", done: false },
    { name: "Tricep Pushdown", sets: 3, reps: 15, rest: "60 sec", duration: "6 min", done: false }
  ]
};

const DEMO_WEIGHT_HISTORY = [
  { label: "Week 1", value: 72 },
  { label: "Week 2", value: 71.5 },
  { label: "Week 3", value: 71 },
  { label: "Week 4", value: 70 }
];

const DEMO_AI_RESPONSES = {
  "what should i eat today?": "Based on your Muscle Building goal, aim for ~2,400 kcal today: oats and eggs for breakfast, rice with chicken and vegetables for lunch, Greek yogurt with nuts as a snack, and paneer or chicken with roti and salad for dinner.",
  "give me today's workout": "Today is Chest & Triceps: Bench Press 4x10, Incline Dumbbell Press 3x12, Cable Fly 3x12, and Tricep Pushdown 3x15 — about 55 minutes total.",
  "how can i improve my stamina?": "Add two 20-minute steady-state cardio sessions this week, and finish two workouts with a 10-minute circuit at a higher heart rate. Stamina builds fastest with consistency, not intensity spikes.",
  "suggest a home workout": "With your dumbbells and resistance bands: Goblet Squats 3x12, Dumbbell Rows 3x12, Push-ups 3x15, Band Pull-Aparts 3x15, and a 5-minute core finisher.",
  "why am i not losing weight?": "A few common causes: calories creeping above your target on rest days, under-logging snacks, or water retention masking fat loss. Check your weekly average weight instead of daily numbers before changing anything.",
  "give me a recovery routine": "Try 10 minutes of light mobility work, foam rolling your quads and lats, 5 minutes of static stretching, and prioritize 7-8 hours of sleep tonight — recovery is where the actual muscle growth happens."
};

const DEMO_NOTIFICATIONS = [
  { text: "Your workout is ready 💪", time: "2 min ago", unread: true },
  { text: "You completed your 7-day streak 🔥", time: "3 hrs ago", unread: true },
  { text: "Don't forget today's workout.", time: "Yesterday", unread: false },
  { text: "Your weekly progress has been updated.", time: "2 days ago", unread: false }
];

/* Expose as window properties since these are declared with const/let
   (top-level const/let do not attach to window automatically). */
window.DEMO_USER_PROFILE = DEMO_USER_PROFILE;
window.DEMO_WEEKLY_PLAN = DEMO_WEEKLY_PLAN;
window.DEMO_TODAY_WORKOUT = DEMO_TODAY_WORKOUT;
window.DEMO_WEIGHT_HISTORY = DEMO_WEIGHT_HISTORY;
window.DEMO_AI_RESPONSES = DEMO_AI_RESPONSES;
window.DEMO_NOTIFICATIONS = DEMO_NOTIFICATIONS;
