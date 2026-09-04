import { Outlet, Link } from 'react-router-dom';

export default function Dashboard() {
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.href = '/login';
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-4 font-bold text-xl border-b border-slate-700">Peblo CMS</div>
        <nav className="flex-1 p-4 flex flex-col gap-2">
          <Link to="/shows" className="hover:bg-slate-800 p-2 rounded">Shows</Link>
          <Link to="/publish" className="hover:bg-slate-800 p-2 rounded">Publish</Link>
        </nav>
        <div className="p-4 border-t border-slate-700">
          <button onClick={logout} className="text-slate-400 hover:text-white">Logout</button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
