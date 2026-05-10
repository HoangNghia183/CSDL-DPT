import { useState } from 'react';
import './styles.css';

function App() {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!file) {
      setError('Vui lòng chọn một video trước khi tìm kiếm.');
      return;
    }

    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setResults(data.results || []);
    } catch (fetchError) {
      setError(`Không thể tìm kiếm: ${fetchError.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Video Retrieval System</p>
          <h1>Hệ thống tìm kiếm video hoa</h1>
          <p className="subcopy">
            Tải một video mẫu lên để tìm các video tương đồng trong cơ sở dữ liệu.
          </p>
        </div>

        <div className="panel">
          <label className="file-picker">
            <span>Chọn video</span>
            <input type="file" accept="video/*" onChange={(e) => setFile(e.target.files[0] || null)} />
          </label>

          <button onClick={handleSearch} className="primary-button" disabled={loading}>
            {loading ? 'Đang tìm...' : 'Tìm kiếm tương đồng'}
          </button>

          {file ? <p className="selected-file">Đã chọn: {file.name}</p> : null}
          {error ? <p className="error-message">{error}</p> : null}
        </div>
      </section>

      <div className="results-grid">
        {results.map((res, index) => (
          <article key={index} className="result-card">
            <div className="result-meta">
              <p className="result-name">{res.name}</p>
              <p className="result-score">Độ tương đồng: {(res.score * 100).toFixed(2)}%</p>
            </div>
            <video controls preload="metadata">
              <source src={`http://localhost:8000/${res.path}`} type="video/mp4" />
            </video>
          </article>
        ))}
      </div>
    </div>
  );
}
export default App;