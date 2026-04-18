import { create } from 'zustand';

interface Voter {
  voter_id: string;
  name: string;
  district?: string;
  constituency?: string;
  is_demo: boolean;
}

interface VoteReceipt {
  receipt_hash: string;
  block_index: number;
  block_hash: string;
  timestamp: string;
  election_id: string;
}

interface AppState {
  // Auth
  voter: Voter | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  setVoter: (voter: Voter, token: string) => void;
  logout: () => void;

  // Voting
  currentElectionId: string | null;
  selectedCandidate: number | null;
  voteReceipt: VoteReceipt | null;
  hasVoted: boolean;
  setCurrentElection: (id: string) => void;
  setSelectedCandidate: (idx: number | null) => void;
  setVoteReceipt: (receipt: VoteReceipt) => void;
  resetVote: () => void;

  // UI
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Auth
  voter: null,
  accessToken: null,
  isAuthenticated: false,
  setVoter: (voter, token) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('voter', JSON.stringify(voter));
    set({ voter, accessToken: token, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('voter');
    set({
      voter: null,
      accessToken: null,
      isAuthenticated: false,
      hasVoted: false,
      voteReceipt: null,
      selectedCandidate: null,
    });
  },

  // Voting
  currentElectionId: null,
  selectedCandidate: null,
  voteReceipt: null,
  hasVoted: false,
  setCurrentElection: (id) => set({ currentElectionId: id }),
  setSelectedCandidate: (idx) => set({ selectedCandidate: idx }),
  setVoteReceipt: (receipt) => set({ voteReceipt: receipt, hasVoted: true }),
  resetVote: () => set({ selectedCandidate: null, voteReceipt: null, hasVoted: false }),

  // UI
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),
  error: null,
  setError: (error) => set({ error }),
}));
