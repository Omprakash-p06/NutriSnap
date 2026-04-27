# API Documentation - NutriSnap

This document details the backend REST API endpoints required by the NutriSnap frontend and outlines third-party service integration paths.

## Authentication (via Firebase / Custom Auth Server)

### `POST /api/v1/auth/login`
Authenticates a user via Email/Password.
**Request Body:** `{"email": "...", "password": "..."}`
**Response:** `{"token": "jwt_token", "user": {"id": "1", ...}}`

### `POST /api/v1/auth/google`
Authenticates via Google OAuth token.
**Request Body:** `{"id_token": "..."}`

## User Profile & Goals

### `GET /api/v1/users/me`
Retrieves current user details, daily goals, XP, and current level.
**Response:**
```json
{
  "id": "1",
  "name": "Jane",
  "level": 4,
  "xp": 1250,
  "streak_days": 14,
  "goals": { "calories": 2000, "protein": 120, "carbs": 200, "fat": 60 }
}
```

### `PATCH /api/v1/users/me/goals`
Updates macro/calorie goals.

## Food Analysis & Logging

### `POST /api/v1/food/analyze`
Sends an image to the backend for third-party AI processing (e.g., Gemini Vision/OpenAI) + USDA Database cross-referencing.
**Request:** `multipart/form-data` with `image` file.
**Response:**
```json
{
  "food_name": "Grilled Salmon Salad",
  "confidence": 0.95,
  "weight_estimate_grams": 350,
  "nutrition": {
    "calories": 420, "protein": 35, "carbs": 12, "fat": 24, "fiber": 4, "sugar": 3
  },
  "suggestions": [
     {"name": "Light Vinaigrette", "cal_saved": 100}
  ]
}
```

### `POST /api/v1/meals`
Saves an analyzed or manually entered meal to the user's log. Offline PWA clients queue this request using background sync until connection is restored.
**Request Body:** `{"food_name": "...", "nutrition": {...}, "timestamp": "...", "image_url": "..."}`

### `GET /api/v1/meals?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
Fetch meal history for a date range.

## Social & Gamification

### `GET /api/v1/leaderboard?type=[global|friends]`
Fetches the top users by XP or streak.

### `GET /api/v1/social/feed`
Retrieves a paginated list of friends' meals and achievements.

### `POST /api/v1/social/friends`
Send a friend request.

### `GET /api/v1/challenges/daily`
Fetches today's active challenges.

## Third-Party Integrations
1. **Google Gemini Vision API / OpenAI GPT-4V:** Used in the `/api/v1/food/analyze` backend service layer.
2. **USDA FoodData Central / Nutritionix API:** Used to fetch detailed micronutrients based on the AI's food identification.
3. **Local In-Browser ML (e.g., TensorFlow.js / MobileNet):** Not a backend API, but integrated on the web client to identify food classes offline seamlessly.
