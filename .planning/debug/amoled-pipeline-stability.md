Hi! I'm NutriSnap AI 🥗 — your personal nutrition coach. Ask me about your meal, macros, or health goals!
hello
🥗
Hello there! I'm NutriSnap AI, your friendly nutrition coach. It's wonderful to connect with you.

It looks like you haven't logged any meals yet today. To help me understand your eating habits and provide the best support, simply tell me what you've eaten for your next meal or snack! I'm excited to help you on your health journey.
how many calories does chicken have?
🥗
That's a wonderful question! The calorie count for chicken can vary quite a bit depending on the cut and how it's prepared.

For example, a 3-ounce (about 85g) serving of cooked, skinless chicken breast typically has around 165 calories. If you'd like a more specific estimate, tell me what part of the chicken you're curious about and how it's usually cooked!
how many calories does an egg have?
🥗
A large egg typically has about 70-80 calories. It's also packed with protein and essential nutrients!
how much protein are we talking about?
🥗
That's a great question about protein! The exact amount we're talking about really depends on the meal we're discussing and your personal health goals.

Could you share details about what you've eaten, or what kind of meal you're curious about? Once I have that context, I can give you a much more specific estimate!
no i mean the egg, how much protien does it have?
🥗
That's a great question! A large egg typically contains about **6 grams of protein**. It's a fantastic source of high-quality protein, which is so good for keeping you feeling full and helping with muscle repair.
what's my height and weight?
🥗
As NutriSnap AI, I don't have access to your personal information like height and weight. My purpose is to help you understand your meals and reach your health goals based on the food information you share with me!

How can I help you with your nutrition today?
# Debug Session: AMOLED Pipeline Stability

**Status:** Investigating
**Hypothesis:** Token is null due to failed guest auto-login, causing AI features to fail and fall back to hardcoded data. `setImage` TypeError is likely due to a stale component version in the browser or shadowing.

## Symptoms
- **Expected:**
    - Image upload works.
    - Chatbot connects to WS and responds.
    - Meal planner uses AI from backend.
- **Actual:**
    - `setImage` TypeError in `ScanPage`.
    - Chatbot is "Offline".
    - Planner shows hardcoded meals.
- **Errors:**
    - `TypeError: setImage is not a function` at `ScanPage.jsx:35`.
    - 401 Unauthorized in backend (implied).

## Timeline
Recent refactor to local state in `ScanPage` and guest auto-login in `AuthContext`.

## Reproduction
1. Open Scan page, upload file.
2. Open Chatbot, try to send.
3. Open Planner page.

## Investigation Log
- [x] Restarted `start.py`.
- [x] Verified `AuthContext.jsx` guest login. (Working on backend, fixed on frontend).
- [x] Debugged `ScanPage.jsx` `setImage` visibility. (Added defensive logging).
- [x] Verified `ChatBot.jsx` WS connection URL. (Improved robustness).
- [x] Verified `planning.py` AI generation logic. (Working).
- [x] **ROOT CAUSE:** Port 8000 occupied by Java (JDWP), blocking `llama.cpp`. Moved to 8008.

## Evidence
- `GET /auth/guest` returns 200 and a valid token.
- `llama.cpp` was returning 403 on port 8000 because it was talking to a Java debugger.
- `token` was null in frontend because the fetch to `/api/auth/guest` might have happened before backend was fully ready or due to proxy lag.
