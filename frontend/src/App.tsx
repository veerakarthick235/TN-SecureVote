import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/common/Navbar';
import Footer from './components/common/Footer';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import VotePage from './pages/VotePage';
import ReceiptPage from './pages/ReceiptPage';
import VerifyPage from './pages/VerifyPage';
import ResultsPage from './pages/ResultsPage';
import AdminPage from './pages/AdminPage';
import './i18n';

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/vote" element={<VotePage />} />
        <Route path="/receipt" element={<ReceiptPage />} />
        <Route path="/verify" element={<VerifyPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
      <Footer />
    </BrowserRouter>
  );
}

export default App;
