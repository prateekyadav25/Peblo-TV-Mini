import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Publish from './pages/Publish';
import ShowList from './pages/ShowList';
import ShowDetail from './pages/ShowDetail';
import ShowForm from './pages/ShowForm';
import EpisodeForm from './pages/EpisodeForm';

function App() {
  const token = localStorage.getItem('token');

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        {token ? (
          <Route path="/" element={<Dashboard />}>
            <Route index element={<Navigate to="/shows" replace />} />
            <Route path="shows" element={<ShowList />} />
            <Route path="shows/new" element={<ShowForm />} />
            <Route path="shows/:id" element={<ShowDetail />} />
            <Route path="shows/:id/edit" element={<ShowForm />} />
            <Route path="shows/:showId/seasons/:seasonId/episodes/new" element={<EpisodeForm />} />
            <Route path="publish" element={<Publish />} />
          </Route>
        ) : (
          <Route path="*" element={<Navigate to="/login" replace />} />
        )}
      </Routes>
    </BrowserRouter>
  );
}

export default App;
