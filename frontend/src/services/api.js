/**
 * API services for NutriSnap
 * Handles Authentication, Image Scanning, and Food Search.
 */

const getAuthHeaders = () => {
  const token = localStorage.getItem("nutrisnap-token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

export const authAPI = {
  login: async (email, password) => {
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", password);

    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: params,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    const data = await response.json();
    // In a real app, we'd fetch user profile separately or decode JWT
    const user = { email, name: email.split("@")[0], level: 1, xp: 0 };
    return {
      token: data.access_token,
      user,
    };
  },

  googleAuth: async (credential) => {
    const response = await fetch("/api/auth/google", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: credential }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Google authentication failed");
    }

    const data = await response.json();
    return {
      token: data.access_token,
      user: data.user,
    };
  },

  register: async (name, email, password) => {
    const response = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: name,
        email,
        password,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Registration failed");
    }

    const userData = await response.json();
    return userData;
  },

  scanImage: async (base64Uri) => {
    if (!base64Uri) throw new Error("No Image Payload");

    // 1. Convert base64 to Blob
    const fetchRes = await fetch(base64Uri);
    const blob = await fetchRes.blob();
    const file = new File([blob], "capture.jpg", { type: "image/jpeg" });

    // 2. Submit for prediction
    const formData = new FormData();
    formData.append("file", file);

    const token = localStorage.getItem("nutrisnap-token");
    const submitResponse = await fetch("/api/predict/", {
      method: "POST",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
    });

    if (!submitResponse.ok) {
      const error = await submitResponse.json();
      throw new Error(error.detail || "Image submission failed");
    }

    const { job_id } = await submitResponse.json();

    // 3. Poll for results
    const pollResult = async (id) => {
      const statusResponse = await fetch(`/api/predict/status/${id}`, {
        headers: getAuthHeaders(),
      });
      const data = await statusResponse.json();

      if (data.status === "done") {
        const result = data.result;
        // The ML pipeline returns multi-food items. For MVP simplicity, we sum them up or take the first.
        // Or we can return the whole result and let the UI handle it.
        return {
          title: result.items?.[0]?.label || "Identified Dish",
          calories: result.total_calories || 0,
          protein: result.total_protein || 0,
          carbs: result.total_carbs || 0,
          fat: result.total_fat || 0,
          mass_g: result.total_mass_g || 0,
          items: result.items || [],
        };
      } else if (data.status === "failed") {
        throw new Error(data.error || "AI analysis failed");
      } else {
        // Still processing
        await new Promise((r) => setTimeout(r, 2000));
        return pollResult(id);
      }
    };

    return pollResult(job_id);
  },

  searchFood: async (query) => {
    if (!query || query.trim().length === 0)
      throw new Error("Invalid query string");

    const response = await fetch(
      `/api/food/search?query=${encodeURIComponent(query.trim())}`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      },
    );

    if (!response.ok) {
      throw new Error("Food search failed");
    }

    const data = await response.json();
    if (!data || data.length === 0) throw new Error("No food found");

    const food = data[0]; // Take the first result
    return {
      title: food.description || query,
      calories: food.calories || 0,
      protein: food.protein || 0,
      carbs: food.carbohydrates || 0,
      fat: food.fat || 0,
    };
  },
};
