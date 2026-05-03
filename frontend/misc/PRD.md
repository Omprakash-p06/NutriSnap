# Product Requirements Document (PRD) - NutriSnap

## 1. Product Vision

"An app that uses AI to identify food from photos and track daily nutrition. A calorie counter that makes healthy eating fun with gamification. It is made to make fitness easy without a lot of hassle. Calorie counting and food weight analysis is just a photo snap away from your website. It is also made to use offline."

## 2. Target Audience

- **Age Range:** All ages (young to old)
- **Fitness Level:** Beginners to gym-goers
- **Platform:** Web-only website (PWA for offline support)

## 3. Core Features (v1 Scope)

1. **📸 Food Photo Scan:**
   - Take a photo or upload an image.
   - AI identifies food, estimates portions, and provides full nutritional breakdown (Calories, Protein, Carbs, Fat, Fiber, Sugar, Sodium, Cholesterol, Vitamins, Minerals, Serving size, Weight).
   - Allows users to mechanically adjust portion sizes.
   - Uses an abstract AI Provider interface (supports Gemini Vision, OpenAI, or local browser models).
2. **📊 Daily Dashboard:**
   - Display today's total calories, macros (protein, carbs, fat), and visual progress towards daily goals.
3. **📅 Meal History / Log:**
   - Browse past logs by day or week.
4. **🎯 Goal Setting:**
   - Set and track daily calorie, macronutrient, and micronutrient targets.
5. **🏆 Gamification:**
   - **Streaks:** Days tracked in a row.
   - **Badges/Achievements:** Milestone badges (e.g., "First Scan", "Macro Master").
   - **XP & Levels:** Earn points for tracking consistency to level up.
   - **Challenges:** Daily challenges ("Eat under 2000 cal", "Log 3 meals").
6. **👥 Leaderboard & Social:**
   - Global and Friends-only leaderboards.
   - Shareable achievements (badges/streaks to social platforms).
   - Social feed for commenting, liking friends' meals, and motivation.
7. **👤 User Accounts & Sync:**
   - Email/password authentication and Google OAuth.
   - Backend data syncing to custom server + offline-first sync (e.g., via Firebase/IndexedDB abstraction).
8. **🌙 System Toggles:**
   - Dark Mode / Light Mode toggle.
9. **📈 Reporting (Weekly/Monthly):**
   - Nutrition trend charts over time.
10. **🍽️ Manual Entry & Meal Suggestions:**
    - Fallback manual entry searching.
    - Suggests healthy alternatives and provides full meal planning recommendations.

## 4. Non-Functional Requirements

### 4.1. Offline Mode (PWA)

- **Service Worker Coverage:** Caches the Progressive Web App shell for complete offline loading.
- **Offline AI Analysis:** Uses a lightweight local, browser-based AI model to identify food when off the grid. Re-syncs and refines with cloud AI when back online.
- **Offline Caching:** Caches all meal history, so users can browse their complete past logs without the internet. Uses background sync to push offline changes.

### 4.2. Design Aesthetic

- **Style:** Glassmorphism (primary cards and structure) + Clay Morphism (gamification and badges) Hybrid.
- **Theme:** "Sunset Botanica" premium palette.
- **Vibe:** Stunning, vibrant, welcoming, premium design that stands out from typical generic fitness apps.
