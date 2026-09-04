import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';

export default function ShowForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const isEdit = !!id;

  const [formData, setFormData] = useState({
    slug: '', title: '', section: '', status: 'draft', categories: '', synopsis: ''
  });

  const { data: show, isLoading } = useQuery({
    queryKey: ['show', id],
    queryFn: async () => (await api.get(`/admin/shows/${id}`)).data,
    enabled: isEdit
  });

  useEffect(() => {
    if (show) {
      setFormData({
        slug: show.slug, title: show.title, section: show.section || '', 
        status: show.status, categories: show.categories?.join(', ') || '', 
        synopsis: show.synopsis || ''
      });
    }
  }, [show]);

  const mut = useMutation({
    mutationFn: async (data: any) => {
      const payload = { ...data, categories: data.categories.split(',').map((s:string)=>s.trim()).filter(Boolean) };
      if (isEdit) return await api.put(`/admin/shows/${id}`, payload);
      return await api.post('/admin/shows', payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['shows']});
      navigate('/shows');
    }
  });

  if (isEdit && isLoading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">{isEdit ? 'Edit Show' : 'Create Show'}</h1>
      <form onSubmit={e => { e.preventDefault(); mut.mutate(formData); }} className="space-y-4 bg-white p-6 rounded shadow">
        <div><label className="block text-sm font-bold mb-1">Title</label>
          <input required className="w-full border p-2 rounded" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} /></div>
        <div><label className="block text-sm font-bold mb-1">Slug</label>
          <input required className="w-full border p-2 rounded" value={formData.slug} onChange={e => setFormData({...formData, slug: e.target.value})} /></div>
        <div><label className="block text-sm font-bold mb-1">Section</label>
          <select className="w-full border p-2 rounded" value={formData.section} onChange={e => setFormData({...formData, section: e.target.value})}>
            <option value="">None</option>
            <option value="featured">Featured</option>
            <option value="series">Series</option>
            <option value="minisodes">Minisodes</option>
            <option value="songs">Songs</option>
          </select></div>
        <div><label className="block text-sm font-bold mb-1">Status</label>
          <select className="w-full border p-2 rounded" value={formData.status} onChange={e => setFormData({...formData, status: e.target.value})}>
            <option value="draft">Draft</option><option value="published">Published</option>
          </select></div>
        <div><label className="block text-sm font-bold mb-1">Categories (comma separated)</label>
          <input className="w-full border p-2 rounded" value={formData.categories} onChange={e => setFormData({...formData, categories: e.target.value})} /></div>
        <div><label className="block text-sm font-bold mb-1">Synopsis</label>
          <textarea className="w-full border p-2 rounded h-24" value={formData.synopsis} onChange={e => setFormData({...formData, synopsis: e.target.value})} /></div>
        <button type="submit" disabled={mut.isPending} className="bg-blue-600 text-white px-4 py-2 rounded font-bold w-full">{mut.isPending ? 'Saving...' : 'Save Show'}</button>
      </form>
    </div>
  );
}
