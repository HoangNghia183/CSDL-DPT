import { useState } from 'react';
import './styles.css';

function App() {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState([]);
  const [intermediateResults, setIntermediateResults] = useState([]);
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
      setIntermediateResults(data.intermediate_results || []);
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
          <article key={`${res.path}-${res.name}-${index}`} className="result-card">
            <div className="result-meta">
              <p className="result-name">{res.name}</p>
              <p className="result-score">Độ tương đồng: {(res.score * 100).toFixed(2)}%</p>
            </div>
            <video key={res.path} controls preload="metadata">
              <source key={res.path} src={`http://localhost:8000/${res.path}`} type="video/mp4" />
            </video>
          </article>
        ))}
      </div>

      {intermediateResults.length > 0 ? (
        <section className="intermediate-results">
          <h2>Thông số trung gian</h2>
          <div className="intermediate-list">
            {intermediateResults.map((item) => (
              <article key={`${item.id}-${item.rank}`} className="intermediate-card">
                <p>Hạng {item.rank}</p>
                <p>ID vector: {item.id}</p>
                <p className="intermediate-name">{item.name}</p>
                <p className="intermediate-path">{item.path}</p>
                <p>Độ tương đồng: {item.similarity_percent.toFixed(2)}%</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
export default App;