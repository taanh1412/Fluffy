const { useState, useEffect } = React;

const FileStorageApp = () => {
  const [userId, setUserId] = useState('');
  const [file, setFile] = useState(null);
  const [fileHash, setFileHash] = useState('');
  const [files, setFiles] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [fileList, setFileList] = useState([]);
  const [error, setError] = useState('');

  const apiCall = async (url, method, data = null) => {
    try {
      const response = await fetch(`http://api:5000${url}`, {
        method,
        headers: { 'X-User-ID': userId },
        body: data,
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (err) {
      console.error('API error:', err);
      setError(err.message);
      return null;
    }
  };

  const handleUpload = async () => {
    if (!file || !userId) {
      setError('Please provide a User ID and select a file.');
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    const result = await apiCall('/api/upload', 'POST', formData);
    if (result && result.file_hash) {
      setFileHash(result.file_hash);
      setError('');
    }
  };

  const handleDownload = async () => {
    if (!fileHash || !userId) {
      setError('Please provide a User ID and File Hash.');
      return;
    }
    const result = await apiCall(`/api/download/${fileHash}`, 'GET');
    if (result && result.data) {
      alert(`Downloaded: ${result.data}`);
      setError('');
    }
  };

  const handleSearch = async () => {
    if (!userId) {
      setError('Please provide a User ID.');
      return;
    }
    const result = await apiCall(`/api/search?query=${searchQuery}`, 'GET');
    if (result) {
      setSearchResults(result);
      setError('');
    }
  };

  const handleList = async () => {
    if (!userId) {
      setError('Please provide a User ID.');
      return;
    }
    const result = await apiCall(`/api/list`, 'GET');
    if (result) {
      setFileList(result);
      setError('');
    }
  };

  const handleDelete = async () => {
    if (!fileHash || !userId) {
      setError('Please provide a User ID and File Hash.');
      return;
    }
    const result = await apiCall(`/api/delete/${fileHash}`, 'DELETE');
    if (result && result.success) {
      setFileHash('');
      setError('');
    }
  };

  const handleUpdate = async () => {
    if (!fileHash || !file || !userId) {
      setError('Please provide a User ID, File Hash, and select a new file.');
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    const result = await apiCall(`/api/update/${fileHash}`, 'PUT', formData);
    if (result && result.success) {
      setFileHash('');
      setError('');
    }
  };

  return (
    <div className="container">
      <h1>File Storage App</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <input
        type="text"
        placeholder="User ID"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
      />
      <input
        type="file"
        onChange={(e) => setFile(e.target.files[0])}
      />
      <button onClick={handleUpload}>Upload</button>
      <input
        type="text"
        placeholder="File Hash"
        value={fileHash}
        onChange={(e) => setFileHash(e.target.value)}
      />
      <button onClick={handleDownload}>Download</button>
      <button onClick={handleDelete}>Delete</button>
      <input
        type="text"
        placeholder="Search Query"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />
      <button onClick={handleSearch}>Search</button>
      <button onClick={handleUpdate}>Update</button>
      <button onClick={handleList}>List Files</button>
      <div id="searchResults">
        <h3>Search Results</h3>
        <ul>{searchResults.map((r, i) => <li key={i}>{r.file_name} ({r.file_hash})</li>)}</ul>
      </div>
      <div id="fileList">
        <h3>Your Files</h3>
        <ul>{fileList.map((f, i) => <li key={i}>{f.file_name} ({f.file_hash})</li>)}</ul>
      </div>
    </div>
  );
};

// Use React 18's createRoot
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<FileStorageApp />);