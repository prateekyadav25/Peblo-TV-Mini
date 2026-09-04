import { useQuery } from '@tanstack/react-query';
import { fetchCatalogue } from '../api';
import { Link } from 'react-router-dom';
import ImageLoader from '../components/ImageLoader';

const BASE_URL = import.meta.env.VITE_API_URL || '';

export default function Home() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['catalogue'],
    queryFn: fetchCatalogue,
    retry: false
  });

  if (isLoading) return <div className="p-8 text-center animate-pulse">Loading catalogue...</div>;
  if (isError) return <div className="p-8 text-center text-red-500">Catalogue is currently unavailable. Please ask an Admin to publish it.</div>;

  const sections = data?.sections || {};
  const firstFeatured = sections.featured?.[0];

  return (
    <div>
      {firstFeatured && (
        <div className="relative h-[60vh] w-full overflow-hidden bg-slate-900">
          <ImageLoader 
            src={`${BASE_URL}/api/storage/${firstFeatured.artwork?.banner}`} 
            alt={firstFeatured.title} 
            className="w-full h-full opacity-60"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-brand-dark via-brand-dark/50 to-transparent"></div>
          <div className="absolute bottom-0 p-8 md:p-16 w-full max-w-7xl mx-auto">
            <h1 className="text-4xl md:text-6xl font-extrabold mb-4 drop-shadow-lg">{firstFeatured.title}</h1>
            <p className="max-w-2xl text-lg text-gray-200 mb-8 line-clamp-3 drop-shadow">{firstFeatured.synopsis}</p>
            <Link to={`/show/${firstFeatured.slug}`} className="bg-brand-accent text-white px-8 py-3 rounded-full font-bold hover:bg-blue-500 transition-colors shadow-lg">Watch Now</Link>
          </div>
        </div>
      )}

      <div className="p-8 md:p-16 space-y-16 max-w-7xl mx-auto -mt-16 relative z-10">
        {Object.entries(sections).map(([sectionName, shows]: [string, any]) => (
          <section key={sectionName}>
            <h2 className="text-2xl font-bold capitalize mb-6 px-2">{sectionName.replace(/_/g, ' ')}</h2>
            <div className="flex gap-4 md:gap-6 overflow-x-auto pb-6 snap-x no-scrollbar">
              {shows.map((show: any) => (
                <Link to={`/show/${show.slug}`} key={show.slug} className="snap-start shrink-0 w-36 md:w-48 group">
                  <div className="aspect-[2/3] rounded-lg overflow-hidden mb-3 shadow-lg">
                    {show.artwork?.poster ? (
                      <ImageLoader 
                        src={`${BASE_URL}/api/storage/${show.artwork.poster}`} 
                        alt={show.title}
                        className="w-full h-full group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full bg-slate-800 flex items-center justify-center text-gray-500">No Image</div>
                    )}
                  </div>
                  <h3 className="font-semibold text-gray-200 group-hover:text-brand-accent transition-colors truncate">{show.title}</h3>
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
