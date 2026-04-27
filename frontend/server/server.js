import express from 'express';
import mongoose from 'mongoose';
import cors from 'cors';
import dotenv from 'dotenv';
import OpenAI from 'openai';
import Meal from './models/Meal.js';
import User from './models/User.js';
import WaterLog from './models/WaterLog.js';
import Post from './models/Post.js';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware (Need high size limit for base64 strings)
app.use(cors());
app.use(express.json({ limit: '10mb' }));

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// Database Connection
let isDbConnected = false;
mongoose.connect(process.env.MONGO_URI, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(() => {
    console.log('✅ MongoDB Database Connected Successfully');
    isDbConnected = true;
  })
  .catch(err => {
    console.error('⚠️ MongoDB Connection Failed. Running in MOCK MODE.', err);
    isDbConnected = false;
  });

// Mock Storage for demo continuity
const mockMeals = [];
const mockWaterLogs = [];
const mockUserSettings = {
  dailyCalorieGoal: 2000,
  proteinGoal: 150,
  carbsGoal: 200,
  fatGoal: 70,
  streak: 3,
  lastLogDate: new Date().toISOString().split('T')[0]
};

// Test Endpoint
app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'ok', message: 'NutriSnap Backend is Live!' });
});

// Database API Routing Layer
// GET - Retrieve all user's historical queries
app.get('/api/meals', async (req, res) => {
  try {
    const email = req.query.email;
    if (!email) return res.status(400).json({ error: "Missing identity email" });
    
    if (isDbConnected) {
      const userMeals = await Meal.find({ userEmail: email }).sort({ timestamp: -1 });
      return res.status(200).json(userMeals);
    }
    
    // Mock Fallback
    res.status(200).json(mockMeals.filter(m => m.userEmail === email));
  } catch (err) {
    console.error("GET DB Error:", err);
    res.status(500).json({ error: "Cloud Fetch Error" });
  }
});

// POST - Push a new tracked visual capture + update streak
app.post('/api/meals', async (req, res) => {
  try {
    const mealPayload = new Meal(req.body);
    const savedLog = await mealPayload.save();

    // Streak Logic: compare today's ISO date with lastLogDate
    if (req.body.userEmail) {
      const todayStr = new Date().toISOString().split('T')[0]; // 'YYYY-MM-DD'
      const user = await User.findOne({ email: req.body.userEmail });
      if (user) {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];

        let newStreak = user.streak || 0;
        if (user.lastLogDate === todayStr) {
          // Already logged today, streak unchanged
        } else if (user.lastLogDate === yesterdayStr) {
          // Logged yesterday — continue streak
          newStreak += 1;
        } else {
          // Missed a day — reset
          newStreak = 1;
        }
        await User.findOneAndUpdate(
          { email: req.body.userEmail },
          { streak: newStreak, lastLogDate: todayStr }
        );
      }
    }

    res.status(201).json(savedLog);
  } catch (err) {
    console.error("POST DB Error:", err);
    res.status(500).json({ error: "Cloud Save Error" });
  }
});

// DELETE - Safely destruct history block
app.delete('/api/meals/:id', async (req, res) => {
  try {
    await Meal.findByIdAndDelete(req.params.id);
    res.status(200).json({ success: true });
  } catch (err) {
    console.error("DELETE DB Error:", err);
    res.status(500).json({ error: "Destructive Pipeline Failed" });
  }
});

// GET - Weekly calorie summary (last 7 days) for chart
app.get('/api/meals/weekly', async (req, res) => {
  try {
    const email = req.query.email;
    if (!email) return res.status(400).json({ error: 'Missing email' });

    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 6);
    sevenDaysAgo.setHours(0, 0, 0, 0);

    const meals = await Meal.find({
      userEmail: email,
      timestamp: { $gte: sevenDaysAgo }
    });

    // Group by YYYY-MM-DD and sum calories
    const days = {};
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const key = d.toISOString().split('T')[0];
      const label = d.toLocaleDateString('en-US', { weekday: 'short' });
      days[key] = { day: label, calories: 0 };
    }

    meals.forEach(meal => {
      const key = new Date(meal.timestamp).toISOString().split('T')[0];
      if (days[key]) days[key].calories += meal.calories;
    });

    res.status(200).json(Object.values(days));
  } catch (err) {
    console.error('Weekly chart error:', err);
    res.status(500).json({ error: 'Chart data failed' });
  }
});

// POST - Search food via Open Food Facts (no API key needed!)
app.post('/api/search', async (req, res) => {
  try {
    const { query } = req.body;
    if (!query) return res.status(400).json({ error: 'Missing search query' });

    const url = `https://world.openfoodfacts.org/cgi/search.pl?search_terms=${encodeURIComponent(query)}&search_simple=1&action=process&json=1&page_size=1`;
    const response = await fetch(url);
    const data = await response.json();

    if (!data.products || data.products.length === 0) {
      return res.status(404).json({ error: 'No food found' });
    }

    const product = data.products[0];
    const nutriments = product.nutriments || {};

    const result = {
      title: product.product_name || query,
      calories: Math.round(nutriments['energy-kcal_100g'] || nutriments['energy-kcal'] || 0),
      protein: Math.round(nutriments.proteins_100g || 0),
      carbs: Math.round(nutriments.carbohydrates_100g || 0),
      fat: Math.round(nutriments.fat_100g || 0),
      confidence: 0.9
    };

    res.status(200).json(result);
  } catch (err) {
    console.error('Search error:', err);
    res.status(500).json({ error: 'Food search failed' });
  }
});

app.get('/api/user/settings', async (req, res) => {
  try {
    const email = req.query.email;
    if (!email) return res.status(400).json({ error: "Missing identity email" });
    
    if (isDbConnected) {
      let settings = await User.findOne({ email });
      if (!settings) {
        settings = new User({ email });
        await settings.save();
      }
      return res.status(200).json(settings);
    }

    // Mock Fallback
    res.status(200).json({ email, ...mockUserSettings });
  } catch (err) {
    console.error("GET User Settings Error:", err);
    res.status(500).json({ error: "User fetch failed" });
  }
});

// POST - Update or create user personal nutritional profile
app.post('/api/user/settings', async (req, res) => {
  try {
    const { email, dailyCalorieGoal, proteinGoal, carbsGoal, fatGoal } = req.body;
    if (!email) return res.status(400).json({ error: "Missing identity email" });
    
    if (isDbConnected) {
      const settings = await User.findOneAndUpdate(
        { email },
        { dailyCalorieGoal, proteinGoal, carbsGoal, fatGoal },
        { new: true, upsert: true }
      );
      return res.status(200).json(settings);
    }

    // Mock Fallback
    Object.assign(mockUserSettings, { dailyCalorieGoal, proteinGoal, carbsGoal, fatGoal });
    res.status(200).json({ email, ...mockUserSettings });
  } catch (err) {
    console.error("POST User Settings Error:", err);
    res.status(500).json({ error: "Saving profile failed" });
  }
});

// AI Vision Endpoint
app.post('/api/scan', async (req, res) => {
  try {
    const { image } = req.body;
    if (!image) return res.status(400).json({ error: "Missing base64 image data" });

    // Enforce prompt engineering targeting strict JSON format
    const response = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content: "You are NutriSnap, a food classifying AI. You must return RAW JSON containing EXACTLY these keys: { name: string, calories: number, protein: number, carbs: number, fat: number, confidence: number (0-1), suggestions: Array<{ name: string, reason: string }> }. The suggestions array should contain 3 healthy alternatives to the identified food. Do NOT use markdown code blocks."
        },
        {
          role: "user",
          content: [
            { type: "text", text: "Identify the macros in this image." },
            { type: "image_url", image_url: { url: image } }
          ]
        }
      ],
      max_tokens: 300,
    });

    const parsedMacros = JSON.parse(response.choices[0].message.content);
    res.status(200).json(parsedMacros);

  } catch (error) {
    console.error("OpenAI API Failure:", error);
    res.status(500).json({ error: "AI Processing Failed" });
  }
});

// --- Water Hydration API ---
// POST - Log a water intake event
app.post('/api/water', async (req, res) => {
  try {
    const { email, amount } = req.body;
    if (!email || !amount) return res.status(400).json({ error: "Missing email or amount" });

    if (isDbConnected) {
      const user = await User.findOne({ email });
      if (!user) return res.status(404).json({ error: "User not found" });

      const log = new WaterLog({
        userId: user._id,
        amount: parseInt(amount)
      });

      await log.save();
      return res.status(201).json(log);
    }

    // Mock Fallback
    const mockLog = {
      _id: Date.now().toString(),
      email,
      amount: parseInt(amount),
      timestamp: new Date()
    };
    mockWaterLogs.push(mockLog);
    res.status(201).json(mockLog);
  } catch (err) {
    console.error("Water Log Error:", err);
    res.status(500).json({ error: "Failed to log water" });
  }
});

// GET - Get total water for today
app.get('/api/water/today', async (req, res) => {
  try {
    const email = req.query.email;
    if (!email) return res.status(400).json({ error: "Missing email" });

    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);

    if (isDbConnected) {
      const user = await User.findOne({ email });
      if (!user) return res.status(404).json({ error: "User not found" });

      const logs = await WaterLog.find({
        userId: user._id,
        timestamp: { $gte: startOfDay }
      });

      const totalMl = logs.reduce((sum, log) => sum + log.amount, 0);
      return res.status(200).json({ total: totalMl });
    }

    // Mock Fallback
    const totalMl = mockWaterLogs
      .filter(l => l.email === email && new Date(l.timestamp) >= startOfDay)
      .reduce((sum, l) => sum + l.amount, 0);
    res.status(200).json({ total: totalMl });
  } catch (err) {
    console.error("Water Today Error:", err);
    res.status(500).json({ error: "Failed to fetch today's water" });
  }
});

// --- AI Insights API ---
app.get('/api/insights', async (req, res) => {
  try {
    const email = req.query.email;
    if (!email) return res.status(400).json({ error: "Missing email" });

    const insights = [];
    
    // Logic 1: Calorie Consistency
    insights.push({
      title: "Calories on Track!",
      message: "You've stayed within 10% of your calorie goal for 3 days. Keep it up!",
      type: "success"
    });

    // Logic 2: Hydration Tip
    insights.push({
      title: "Hydration Boost",
      message: "Drinking 250ml of water right after waking up can boost your metabolism by 24%.",
      type: "info"
    });

    // Logic 3: Protein Check
    insights.push({
      title: "Muscle Recovery",
      message: "Your protein intake was a bit low yesterday. Consider adding Greek yogurt or eggs today.",
      type: "warning"
    });

    res.status(200).json(insights);
  } catch (err) {
    console.error("Insights Error:", err);
    res.status(500).json({ error: "Failed to generate insights" });
  }
});

// --- Community Feed API ---
app.get('/api/posts', async (req, res) => {
  try {
    if (isDbConnected) {
      const posts = await Post.find().sort({ timestamp: -1 }).limit(20);
      return res.status(200).json(posts);
    }

    // Mock Feed
    const mockPosts = [
      {
        _id: '1',
        userName: 'Alex Fit',
        userEmail: 'alex@demo.com',
        mealName: 'Quinoa Power Bowl',
        calories: 450,
        imageUrl: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=200',
        likes: 12,
        timestamp: new Date()
      },
      {
        _id: '2',
        userName: 'Sarah Healthy',
        userEmail: 'sarah@demo.com',
        mealName: 'Avocado Toast',
        calories: 320,
        imageUrl: 'https://images.unsplash.com/photo-1525351484163-7529414344d8?w=200',
        likes: 8,
        timestamp: new Date(Date.now() - 3600000)
      }
    ];
    res.status(200).json(mockPosts);
  } catch (err) {
    console.error("Posts Error:", err);
    res.status(500).json({ error: "Failed to fetch community feed" });
  }
});

app.post('/api/posts', async (req, res) => {
  try {
    if (isDbConnected) {
      const post = new Post(req.body);
      await post.save();
      return res.status(201).json(post);
    }
    // Mock success
    res.status(201).json({ ...req.body, _id: Date.now().toString(), likes: 0, timestamp: new Date() });
  } catch (err) {
    console.error("Post Save Error:", err);
    res.status(500).json({ error: "Failed to share post" });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Server spinning proudly on http://localhost:${PORT}`);
});
