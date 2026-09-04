import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Search from './pages/Search';
import ShowDetail from './pages/ShowDetail';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-brand-dark text-white font-sans">
        <header className="p-4 flex justify-between items-center bg-slate-900 sticky top-0 z-50">
          <Link to="/" className="text-2xl font-bold text-brand-accent tracking-tighter">Peblo TV</Link>
          <nav className="flex gap-4">
            <Link to="/" className="hover:text-brand-accent transition-colors">Home</Link>
            <Link to="/search" className="hover:text-brand-accent transition-colors">Search</Link>
          </nav>
        </header>
        <main className="pb-16">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<Search />} />
            <Route path="/show/:slug" element={<ShowDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
