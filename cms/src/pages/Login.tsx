import { useState } from 'react';
import api from '../api';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const fd = new URLSearchParams();
      fd.append('username', username);
      fd.append('password', password);
      const res = await api.post('/admin/auth/token', fd);
      localStorage.setItem('token', res.data.access_token);
      
      // Fetch role
      const me = await api.get('/admin/auth/me');
      localStorage.setItem('role', me.data.role);
      
      window.location.href = '/';
    } catch (err) {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <form onSubmit={handleLogin} className="bg-white p-8 rounded shadow-md w-96">
        <h1 className="text-2xl font-bold mb-6 text-center">Peblo CMS Login</h1>
        {error && <div className="text-red-500 mb-4 text-center">{error}</div>}
        <input 
          type="text" 
          placeholder="Username" 
          className="w-full border p-2 rounded mb-4" 
          value={username} 
          onChange={e => setUsername(e.target.value)} 
        />
        <input 
          type="password" 
          placeholder="Password" 
          className="w-full border p-2 rounded mb-6" 
          value={password} 
          onChange={e => setPassword(e.target.value)} 
        />
        <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded font-bold">Login</button>
      </form>
    </div>
  );
}
