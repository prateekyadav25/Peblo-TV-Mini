import { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';

export default function ArtworkUploader({ showId, type, label, current }: { showId: string, type: string, label: string, current: any }) {
  const qc = useQueryClient();
  const fileInput = useRef<HTMLInputElement>(null);
  const [error, setError] = useState('');
  
  const mut = useMutation({
    mutationFn: async (file: File) => {
      const fd = new FormData();
      fd.append('file', file);
      return await api.post(`/admin/shows/${showId}/artwork/${type}`, fd);
    },
    onSuccess: () => {
      setError('');
      qc.invalidateQueries({queryKey: ['show_full', showId]});
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Upload failed');
    }
  });

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) mut.mutate(file);
  };

  const currentUrl = current ? `/api/storage/${current.storage_key}` : null;

  return (
    <div className="border border-slate-200 rounded-lg p-4 flex flex-col items-center bg-gray-50 relative group">
      <div className="text-sm font-bold text-slate-700 mb-2 w-full text-center border-b pb-2">{label}</div>
      
      <div className="w-full aspect-square md:aspect-auto h-48 bg-slate-200 flex items-center justify-center rounded overflow-hidden relative cursor-pointer" onClick={() => fileInput.current?.click()}>
        {currentUrl ? (
          <img src={currentUrl} className="w-full h-full object-cover group-hover:opacity-50 transition-opacity" />
        ) : (
          <span className="text-slate-400 font-medium">Click to Upload</span>
        )}
        
        <div className="absolute inset-0 bg-black/50 hidden group-hover:flex items-center justify-center text-white font-bold transition-all">
          {mut.isPending ? 'Uploading...' : 'Replace Image'}
        </div>
      </div>

      {error && <div className="text-red-500 text-xs mt-2 w-full font-semibold">{error}</div>}
      
      <input type="file" className="hidden" ref={fileInput} accept="image/jpeg, image/png, image/webp" onChange={handleFile} />
    </div>
  );
}
