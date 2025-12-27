// RAG Search API
export const ragAPI = {
  search: async (query: string, filters?: any) => {
    const response = await api.post('/api/rag-search', {
      query,
      filters,
    });
    return response.data;
  },
};
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  register: async (data: { email: string; password: string; name: string }) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  login: async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  updateRiskProfile: async (answers: Record<string, string>) => {
    const response = await api.post('/auth/risk-profile', { answers });
    return response.data;
  },
};

// Portfolio APIs
export const portfolioAPI = {
  getAll: async () => {
    const response = await api.get('/portfolio');
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/portfolio/${id}`);
    return response.data;
  },

  create: async (data: { name: string; description?: string }) => {
    const response = await api.post('/portfolio', data);
    return response.data;
  },

  update: async (id: string, data: { name?: string; description?: string }) => {
    const response = await api.put(`/portfolio/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    const response = await api.delete(`/portfolio/${id}`);
    return response.data;
  },

  addTransaction: async (portfolioId: string, transaction: {
    symbol: string;
    name: string;
    asset_type: string;
    transaction_type: string;
    quantity: number;
    price: number;
  }) => {
    const response = await api.post(`/portfolio/${portfolioId}/transaction`, transaction);
    return response.data;
  },

  importCsv: async (portfolioId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/portfolio/${portfolioId}/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  exportCsv: async (portfolioId: string) => {
    const response = await api.get(`/portfolio/${portfolioId}/export`, {
      responseType: 'blob',
    });
    return response.data;
  },

  getHoldings: async (portfolioId: string) => {
    const response = await api.get(`/portfolio/${portfolioId}/holdings`);
    return response.data;
  },
};

// Analysis APIs
export const analysisAPI = {
  analyzeStock: async (symbol: string, portfolioId?: string) => {
    const params = portfolioId ? { portfolio_id: portfolioId } : {};
    const response = await api.get(`/analysis/stock/${symbol}`, { params });
    return response.data;
  },

  peerComparison: async (symbol: string, peers: string[]) => {
    const response = await api.post(`/analysis/peer-comparison/${symbol}`, { peers });
    return response.data;
  },

  getNews: async (symbols: string[] = []) => {
    const response = await api.get('/analysis/news', {
      params: { symbols: symbols.join(',') },
    });
    return response.data;
  },

  getMarketTrends: async (portfolioId?: string) => {
    const params = portfolioId ? { portfolio_id: portfolioId } : {};
    const response = await api.get('/analysis/trends', { params });
    return response.data;
  },

  chat: async (portfolioId: string, message: string) => {
    const response = await api.post('/analysis/chat', {
      portfolio_id: portfolioId,
      message,
    });
    return response.data;
  },
};

// Market Data APIs
export const marketAPI = {
  getOverview: async () => {
    const response = await api.get('/analysis/trends');
    return response.data;
  },

  getStockData: async (symbol: string, period: string = '1mo') => {
    const response = await api.get(`/analysis/stock/${symbol}`, {
      params: { period },
    });
    return response.data;
  },

  getIndices: async () => {
    // Get major market indices
    const indices = ['^GSPC', '^DJI', '^IXIC', '^VIX'];
    const promises = indices.map(symbol => 
      api.get(`/analysis/stock/${symbol}`).catch(() => null)
    );
    const results = await Promise.all(promises);
    return results.filter(r => r !== null).map(r => r?.data);
  },
};

// WebSocket connection for real-time updates
export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  connect(portfolioId: string) {
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/${portfolioId}`;
    
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const listeners = this.listeners.get(data.type);
      if (listeners) {
        listeners.forEach(callback => callback(data.payload));
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect(portfolioId);
    };
  }

  private attemptReconnect(portfolioId: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        this.connect(portfolioId);
      }, 1000 * this.reconnectAttempts);
    }
  }

  subscribe(eventType: string, callback: (data: any) => void) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)?.add(callback);
  }

  unsubscribe(eventType: string, callback: (data: any) => void) {
    this.listeners.get(eventType)?.delete(callback);
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const wsService = new WebSocketService();

export default api;
