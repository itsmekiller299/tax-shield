import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Backend (FastAPI/Pydantic) serializes Mongo ids as `_id`; the frontend
// types use `id`. Normalize once here so every list key and every
// update/delete id-match works instead of silently comparing undefined.
function normalize<T>(value: T): T {
  if (Array.isArray(value)) return value.map(normalize) as unknown as T;
  if (value && typeof value === 'object') {
    const obj = value as Record<string, unknown>;
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(obj)) out[k] = normalize(v);
    if (typeof out._id === 'string' && typeof out.id !== 'string') out.id = out._id;
    return out as T;
  }
  return value;
}

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getToken(): string | null {
    if (!this.token && typeof window !== 'undefined') {
      this.token = localStorage.getItem('token');
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/login', { email, password });
    return normalize(response.data);
  }

  async register(data: { email: string; password: string; name: string }) {
    const response = await this.client.post('/register', data);
    return normalize(response.data);
  }

  async getCurrentUser() {
    const response = await this.client.get('/me');
    return normalize(response.data);
  }

  async getTransactions() {
    const response = await this.client.get('/transactions');
    return normalize(response.data);
  }

  async createTransaction(data: any) {
    const response = await this.client.post('/transactions', data);
    return normalize(response.data);
  }

  async uploadTransactionsCsv(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await this.client.post('/transactions/upload-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return normalize(response.data);
  }

  async deleteTransaction(id: string) {
    const response = await this.client.delete(`/transactions/${id}`);
    return normalize(response.data);
  }

  async getInvestments() {
    const response = await this.client.get('/investments');
    return normalize(response.data);
  }

  async createInvestment(data: any) {
    const response = await this.client.post('/investments', data);
    return normalize(response.data);
  }

  async getDeductions() {
    const response = await this.client.get('/deductions');
    return normalize(response.data);
  }

  async createDeduction(data: any) {
    const response = await this.client.post('/deductions', data);
    return normalize(response.data);
  }

  async uploadDocument(file: File, data: any) {
    const formData = new FormData();
    formData.append('file', file);
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, String(value));
      }
    });
    const response = await this.client.post('/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return normalize(response.data);
  }

  async getDocuments() {
    const response = await this.client.get('/documents');
    return normalize(response.data);
  }

  downloadDocumentUrl(id: string) {
    return `${API_URL}/documents/${id}/download`;
  }

  async deleteDocument(id: string) {
    const response = await this.client.delete(`/documents/${id}`);
    return response.data;
  }

  async getObligations() {
    const response = await this.client.get('/obligations');
    return normalize(response.data);
  }

  async updateObligationStatus(id: string, status: string) {
    const response = await this.client.patch(`/obligations/${id}`, { status });
    return normalize(response.data);
  }

  async getDeadlines() {
    const response = await this.client.get('/deadlines');
    return normalize(response.data);
  }

  async updateDeadlineStatus(id: string, is_completed: boolean) {
    const response = await this.client.patch(`/deadlines/${id}`, { is_completed });
    return normalize(response.data);
  }

  async getScenarios() {
    const response = await this.client.get('/scenarios');
    return normalize(response.data);
  }

  async createScenario(data: any) {
    const response = await this.client.post('/scenarios', data);
    return normalize(response.data);
  }

  async compareScenarios(scenarioIds: string[]) {
    const response = await this.client.post('/scenarios/compare', { scenario_ids: scenarioIds });
    return normalize(response.data);
  }

  async getDashboard(regime: string = 'old') {
    const response = await this.client.get(`/dashboard?regime=${regime}`);
    return normalize(response.data);
  }

  async getReadinessScore() {
    const response = await this.client.get('/readiness-score');
    return normalize(response.data);
  }

  async seedDemoData() {
    const response = await this.client.get('/demo/seed');
    return normalize(response.data);
  }

  async getTaxPayments() {
    const response = await this.client.get('/tax-payments');
    return normalize(response.data);
  }

  async createTaxPayment(data: any) {
    const response = await this.client.post('/tax-payments', data);
    return normalize(response.data);
  }

  async getAisRecords() {
    const response = await this.client.get('/ais-records');
    return normalize(response.data);
  }

  async createAisRecord(data: any) {
    const response = await this.client.post('/ais-records', data);
    return normalize(response.data);
  }

  async getForm26ASRecords() {
    const response = await this.client.get('/form26as-records');
    return normalize(response.data);
  }

  async createForm26ASRecord(data: any) {
    const response = await this.client.post('/form26as-records', data);
    return normalize(response.data);
  }

  async getReconciliation() {
    const response = await this.client.get('/reconciliation');
    return normalize(response.data);
  }

  async getRisks() {
    const response = await this.client.get('/risks');
    return normalize(response.data);
  }

  async getActions() {
    const response = await this.client.get('/actions');
    return normalize(response.data);
  }

  async getTaxDetail(regime: string = 'old') {
    const response = await this.client.get(`/tax-detail?regime=${regime}`);
    return normalize(response.data);
  }

  async chatMessage(message: string) {
    const response = await this.client.post('/chat/message', { message });
    return normalize(response.data);
  }

  async chatHistory(limit = 50) {
    const response = await this.client.get(`/chat/history?limit=${limit}`);
    return normalize(response.data);
  }

  async voiceTranscribe(transcript: string, lang?: string) {
    const response = await this.client.post('/chat/voice/transcribe', { transcript, lang });
    return normalize(response.data);
  }

  async voiceSynthesize(text: string) {
    const response = await this.client.post('/chat/voice/synthesize', { text });
    return normalize(response.data);
  }

  async chatScenario(extra_deduction: number = 50000) {
    const response = await this.client.post('/chat/scenario', { extra_deduction });
    return normalize(response.data);
  }
}

export const api = new ApiClient();