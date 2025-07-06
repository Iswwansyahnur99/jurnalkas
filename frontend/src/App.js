import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Format currency in Indonesian Rupiah
const formatRupiah = (amount) => {
  if (amount === null || amount === undefined) return "-";
  return `Rp ${amount.toLocaleString('id-ID')}`;
};

// Convert English month names to Indonesian
const formatIndonesianDate = (dateString) => {
  const months = {
    'January': 'Januari', 'February': 'Februari', 'March': 'Maret',
    'April': 'April', 'May': 'Mei', 'June': 'Juni',
    'July': 'Juli', 'August': 'Agustus', 'September': 'September',
    'October': 'Oktober', 'November': 'November', 'December': 'Desember'
  };
  
  let result = dateString;
  Object.keys(months).forEach(eng => {
    result = result.replace(eng, months[eng]);
  });
  return result;
};

// Header Component
const Header = ({ title }) => (
  <header className="header">
    <div className="container">
      <div className="header-content">
        <div className="logo">
          <h1>TVRI BERKERINGAT</h1>
          <p>Edisi Badminton</p>
        </div>
        <nav className="nav">
          <Link to="/" className="nav-link">Jurnal Kas</Link>
          <Link to="/bayar" className="nav-link">Bayar Iuran</Link>
        </nav>
      </div>
      <h2 className="page-title">{title}</h2>
    </div>
  </header>
);

// Main Cash Journal Page
const HomePage = () => {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState({
    total_pemasukan: 0,
    total_pengeluaran: 0,
    saldo: 0
  });
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    fetchData();
    checkAdminStatus();
  }, []);

  const checkAdminStatus = () => {
    const token = localStorage.getItem('adminToken');
    setIsAdmin(!!token);
  };

  const fetchData = async () => {
    try {
      const [transactionsRes, summaryRes] = await Promise.all([
        axios.get(`${API}/transactions`),
        axios.get(`${API}/summary`)
      ]);
      
      setTransactions(transactionsRes.data);
      setSummary(summaryRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const handleDeleteTransaction = async (transactionId) => {
    if (!window.confirm('Apakah Anda yakin ingin menghapus transaksi ini?')) {
      return;
    }

    try {
      const token = localStorage.getItem('adminToken');
      await axios.delete(`${API}/transactions/${transactionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      // Refresh data after deletion
      fetchData();
      alert('Transaksi berhasil dihapus');
    } catch (error) {
      alert('Gagal menghapus transaksi');
      console.error('Error deleting transaction:', error);
    }
  };

  if (loading) {
    return (
      <div className="App">
        <Header title="Jurnal Kas TVRI Berkeringat edisi Badminton" />
        <div className="loading">Memuat data...</div>
      </div>
    );
  }

  return (
    <div className="App">
      <Header title="Jurnal Kas TVRI Berkeringat Edisi Badminton" />
      
      <main className="main-content">
        <div className="container">
          {/* Summary Boxes */}
          <div className="summary-grid">
            <div className="summary-card pemasukan">
              <h3>Total Pemasukan</h3>
              <p className="amount">{formatRupiah(summary.total_pemasukan)}</p>
            </div>
            <div className="summary-card pengeluaran">
              <h3>Total Pengeluaran</h3>
              <p className="amount">{formatRupiah(summary.total_pengeluaran)}</p>
            </div>
            <div className="summary-card saldo">
              <h3>Saldo Akhir</h3>
              <p className="amount">{formatRupiah(summary.saldo)}</p>
            </div>
          </div>

          {/* Transactions Table */}
          <div className="table-container">
            <h3>Riwayat Transaksi</h3>
            {transactions.length === 0 ? (
              <div className="empty-state">
                <p>Belum ada transaksi yang tercatat.</p>
              </div>
            ) : (
              <div className="table-wrapper">
                <table className="transactions-table">
                  <thead>
                    <tr>
                      <th>No.</th>
                      <th>Tanggal</th>
                      <th>Keterangan</th>
                      <th>Pemasukan</th>
                      <th>Pengeluaran</th>
                      {isAdmin && <th>Aksi</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((transaction, index) => (
                      <tr key={transaction.id} className={index % 2 === 0 ? 'even' : 'odd'}>
                        <td>{index + 1}</td>
                        <td>{formatIndonesianDate(transaction.tanggal)}</td>
                        <td>{transaction.keterangan}</td>
                        <td className="amount-cell pemasukan">
                          {transaction.pemasukan ? formatRupiah(transaction.pemasukan) : '-'}
                        </td>
                        <td className="amount-cell pengeluaran">
                          {transaction.pengeluaran ? formatRupiah(transaction.pengeluaran) : '-'}
                        </td>
                        {isAdmin && (
                          <td>
                            <button 
                              onClick={() => handleDeleteTransaction(transaction.id)}
                              className="delete-button"
                              title="Hapus transaksi"
                            >
                              🗑️
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
      
      <footer className="footer">
        <div className="container">
          <p>&copy; 2025 Kumuda Experience (PT. Kumuda Kreasi Nusantara)</p>
          <Link to="/admin" className="admin-link">Admin Login</Link>
        </div>
      </footer>
    </div>
  );
};

// Payment Page
const PaymentPage = () => {
  const handleWhatsAppConfirmation = () => {
    const message = "Halo, saya sudah melakukan pembayaran iuran kas komunitas TVRI Berkeringat Badminton. Mohon dikonfirmasi. Terima kasih.";
    const whatsappUrl = `https://wa.me/6285173177156?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
  };

  return (
    <div className="App">
      <Header title="Pembayaran Iuran Kas" />
      
      <main className="main-content">
        <div className="container">
          <div className="payment-container">
            <div className="payment-instructions">
              <h3>Cara Pembayaran</h3>
              <p>Silakan pindai (scan) kode QRIS di bawah ini menggunakan aplikasi E-Wallet atau Mobile Banking Anda untuk membayar iuran kas.</p>
            </div>
            
            <div className="qris-container">
              <div className="qris-code">
                <img 
                  src="https://customer-assets.emergentagent.com/job_badminton-journal/artifacts/0c5goi0a_IMG_7513.PNG" 
                  alt="QRIS Code untuk Pembayaran"
                  className="qris-image"
                />
              </div>
              <div className="qris-info">
                <p><strong>Nama Penerima:</strong> Muhammad Iswansyah Nur (PIC)</p>
                <p><strong>Untuk:</strong> Iuran Kas TVRI Berkeringat Edisi Badminton</p>
              </div>
            </div>
            
            <div className="confirmation-section">
              <button 
                onClick={handleWhatsAppConfirmation}
                className="whatsapp-button"
              >
                <span className="whatsapp-icon">📱</span>
                Sudah Bayar? Konfirmasi ke PIC
              </button>
            </div>
          </div>
        </div>
      </main>
      
      <footer className="footer">
        <div className="container">
          <p>&copy; 2025 Kumuda Experience (PT. Kumuda Kreasi Nusantara)</p>
        </div>
      </footer>
    </div>
  );
};

// Admin Login Page
const AdminLoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/login`, {
        username,
        password
      });

      if (response.data.token) {
        localStorage.setItem('adminToken', response.data.token);
        navigate('/admin-input');
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'Login gagal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="login-container">
        <div className="login-form">
          <h2>Admin Access</h2>
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" disabled={loading}>
              {loading ? 'Memuat...' : 'Login'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

// Admin Input Page
const AdminInputPage = () => {
  const [formData, setFormData] = useState({
    tanggal: new Date().toISOString().split('T')[0],
    keterangan: '',
    jenis: 'pemasukan',
    jumlah: ''
  });
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('adminToken');
    if (!token) {
      navigate('/admin');
    }
  }, [navigate]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('adminToken');
      const submitData = {
        ...formData,
        tanggal: new Date(formData.tanggal).toISOString(),
        jumlah: parseFloat(formData.jumlah)
      };

      await axios.post(`${API}/transactions`, submitData, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setSuccess('Transaksi berhasil disimpan!');
      setFormData({
        tanggal: new Date().toISOString().split('T')[0],
        keterangan: '',
        jenis: 'pemasukan',
        jumlah: ''
      });

      setTimeout(() => {
        navigate('/');
      }, 1500);
    } catch (error) {
      setError(error.response?.data?.detail || 'Gagal menyimpan transaksi');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    navigate('/');
  };

  return (
    <div className="App">
      <div className="admin-container">
        <div className="admin-header">
          <h2>Input Transaksi Baru</h2>
          <button onClick={handleLogout} className="logout-button">Logout</button>
        </div>
        
        <form onSubmit={handleSubmit} className="admin-form">
          <div className="form-group">
            <label>Tanggal Transaksi</label>
            <input
              type="date"
              name="tanggal"
              value={formData.tanggal}
              onChange={handleInputChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Keterangan</label>
            <input
              type="text"
              name="keterangan"
              value={formData.keterangan}
              onChange={handleInputChange}
              placeholder="Contoh: Iuran kas Budi, Pembelian shuttlecock"
              required
            />
          </div>
          
          <div className="form-group">
            <label>Jenis Transaksi</label>
            <div className="radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="jenis"
                  value="pemasukan"
                  checked={formData.jenis === 'pemasukan'}
                  onChange={handleInputChange}
                />
                Pemasukan (Debit)
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="jenis"
                  value="pengeluaran"
                  checked={formData.jenis === 'pengeluaran'}
                  onChange={handleInputChange}
                />
                Pengeluaran (Kredit)
              </label>
            </div>
          </div>
          
          <div className="form-group">
            <label>Jumlah (Rp)</label>
            <input
              type="number"
              name="jumlah"
              value={formData.jumlah}
              onChange={handleInputChange}
              placeholder="50000"
              min="0"
              step="1000"
              required
            />
          </div>
          
          {success && <div className="success-message">{success}</div>}
          {error && <div className="error-message">{error}</div>}
          
          <button type="submit" disabled={loading} className="submit-button">
            {loading ? 'Menyimpan...' : 'Simpan Transaksi'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/bayar" element={<PaymentPage />} />
        <Route path="/admin" element={<AdminLoginPage />} />
        <Route path="/admin-input" element={<AdminInputPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
