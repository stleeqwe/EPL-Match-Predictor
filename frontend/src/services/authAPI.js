const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

export const authAPI = {
  async login(email, password) {
    const res = await fetch(`${API_BASE}/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) throw new Error('Login failed');
    return res.json();
  },

  async signup(email, password, displayName) {
    const res = await fetch(`${API_BASE}/v1/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name: displayName })
    });
    if (!res.ok) throw new Error('Signup failed');
    return res.json();
  },

  async refreshToken(refreshToken) {
    const res = await fetch(`${API_BASE}/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    if (!res.ok) throw new Error('Token refresh failed');
    return res.json();
  }
};

export const simulationAPI = {
  async simulate(homeTeam, awayTeam, weights = null) {
    const token = localStorage.getItem('accessToken');
    const body = { home_team: homeTeam, away_team: awayTeam };

    // Add weights if provided
    if (weights) {
      body.weights = weights;
    }

    const res = await fetch(`${API_BASE}/v1/simulation/simulate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      if (res.status === 429) throw new Error('Rate limit exceeded');
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.error || 'Simulation failed');
    }
    return res.json();
  },

  async aiPredict(homeTeam, awayTeam, userEvaluation, sharpOdds = null, recentForm = null) {
    const body = {
      home_team: homeTeam,
      away_team: awayTeam,
      user_evaluation: userEvaluation
    };

    if (sharpOdds) {
      body.sharp_odds = sharpOdds;
    }

    if (recentForm) {
      body.recent_form = recentForm;
    }

    const res = await fetch(`${API_BASE}/ai-simulation/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.error || 'AI prediction failed');
    }

    return res.json();
  },

  async getAIHealth() {
    const res = await fetch(`${API_BASE}/ai-simulation/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    if (!res.ok) {
      throw new Error('AI health check failed');
    }
    return res.json();
  },

  async getAIInfo() {
    const res = await fetch(`${API_BASE}/ai-simulation/info`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    if (!res.ok) {
      throw new Error('Failed to get AI info');
    }
    return res.json();
  },

  async getWeightPresets() {
    const res = await fetch(`${API_BASE}/v1/simulation/weight-presets`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    if (!res.ok) {
      throw new Error('Failed to load presets');
    }
    return res.json();
  }
};

export const paymentAPI = {
  async createCheckoutSession(tier) {
    const token = localStorage.getItem('accessToken');
    const res = await fetch(`${API_BASE}/v1/payment/create-checkout-session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ tier })
    });
    if (!res.ok) throw new Error('Checkout failed');
    return res.json();
  },

  async createPortalSession() {
    const token = localStorage.getItem('accessToken');
    const res = await fetch(`${API_BASE}/v1/payment/create-portal-session`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    if (!res.ok) throw new Error('Portal creation failed');
    return res.json();
  }
};
