/**
 * API services for NutriSnap
 * Handles Authentication, Image Scanning, and Food Search.
 */

const delay = (ms) => new Promise(res => setTimeout(res, ms));

export const authAPI = {
  login: async (email, password) => {
    await delay(1000); // simulate network latency
    if (email && password) {
      return {
        token: 'fake-jwt-token-email-login',
        user: { id: '1', name: email.split('@')[0], email, level: 1, xp: 100 }
      };
    }
    throw new Error('Invalid credentials');
  },

  register: async (name, email, password) => {
    await delay(1200);
    if (name && email && password) {
      return {
        token: 'fake-jwt-token-email-signup',
        user: { id: '2', name, email, level: 1, xp: 0 }
      };
    }
    throw new Error('Invalid input');
  },

  googleAuth: async (idToken) => {
    await delay(800);
    if (idToken) {
      return {
        token: 'fake-jwt-token-google-oauth',
        user: { id: '3', name: 'Google User', email: 'google@user.com', level: 1, xp: 50 }
      };
    }
    throw new Error('Invalid Google Token');
  },

  scanImage: async (base64Uri) => {
    if (!base64Uri) throw new Error('No Image Payload');
    
    // Relay direct to our Express Server
    const response = await fetch('/api/scan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ image: base64Uri })
    });
    
    if (!response.ok) {
      throw new Error('AI_UNCERTAINTY');
    }

    const data = await response.json();
    
    return {
      title: data.name || 'Identified Dish',
      calories: data.calories || 0,
      protein: data.protein || 0,
      carbs: data.carbs || 0,
      fat: data.fat || 0
    };
  },

  searchFood: async (query) => {
    if (!query || query.trim().length === 0) throw new Error('Invalid query string');
    
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query.trim() })
    });

    if (!response.ok) {
      throw new Error('AI_UNCERTAINTY');
    }

    const data = await response.json();
    if (data.error) throw new Error('AI_UNCERTAINTY');

    return {
      title: data.title || query,
      calories: data.calories || 0,
      protein: data.protein || 0,
      carbs: data.carbs || 0,
      fat: data.fat || 0
    };
  }
};
