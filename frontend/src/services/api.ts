import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Auth ---
export const authAPI = {
  register: (data: { aadhaar_number: string; name: string; district: string; constituency: string; phone: string }) =>
    api.post('/api/auth/register', data),
  verifyOTP: (data: { voter_id: string; otp: string }) =>
    api.post('/api/auth/verify-otp', data),
  biometric: (data: { voter_id: string; fingerprint_hash: string }) =>
    api.post('/api/auth/biometric', data),
  demoLogin: (name: string = 'Demo Voter') =>
    api.post('/api/auth/demo-login', { demo_voter_name: name }),
  me: (token: string) =>
    api.get(`/api/auth/me?token=${token}`),
};

// --- Election ---
export const electionAPI = {
  getActive: () => api.get('/api/election/active'),
  getAll: () => api.get('/api/election/all'),
  getById: (id: string) => api.get(`/api/election/${id}`),
  getCandidates: (id: string) => api.get(`/api/election/${id}/candidates`),
  create: (data: any) => api.post('/api/election/create', data),
  addCandidate: (electionId: string, data: any) => api.post(`/api/election/${electionId}/candidate`, data),
  updateStatus: (electionId: string, status: string) => api.put(`/api/election/${electionId}/status/${status}`),
};

// --- Vote ---
export const voteAPI = {
  getPublicParams: () => api.get('/api/vote/public-params'),
  requestToken: (data: { election_id: string; blinded_token: string }) =>
    api.post('/api/vote/request-token', data),
  submit: (data: {
    election_id: string;
    encrypted_ballot: string;
    token_signature: string;
    token_value: string;
    zkp_proof?: string;
  }) => api.post('/api/vote/submit', data),
  verify: (receipt_hash: string) =>
    api.post('/api/vote/verify', { receipt_hash }),
  getReceipt: (hash: string) =>
    api.get(`/api/vote/receipt/${hash}`),
};

// --- Audit ---
export const auditAPI = {
  getResults: (electionId: string) =>
    api.get(`/api/audit/results/${electionId}`),
  getBlockchain: (electionId: string) =>
    api.get(`/api/audit/blockchain/${electionId}`),
  validateChain: (electionId: string) =>
    api.get(`/api/audit/chain-valid/${electionId}`),
  getTrail: (electionId: string) =>
    api.get(`/api/audit/trail/${electionId}`),
  getFraudAlerts: (electionId?: string) =>
    api.get(`/api/audit/fraud-alerts${electionId ? `?election_id=${electionId}` : ''}`),
  runAnalysis: (electionId: string) =>
    api.post(`/api/audit/run-analysis/${electionId}`),
};

// --- Demo ---
export const demoAPI = {
  setup: () => api.post('/api/demo/setup'),
  quickVote: (candidateIndex: number) =>
    api.post(`/api/demo/quick-vote?candidate_index=${candidateIndex}`),
  status: () => api.get('/api/demo/status'),
  reset: () => api.post('/api/demo/reset'),
};

export default api;
