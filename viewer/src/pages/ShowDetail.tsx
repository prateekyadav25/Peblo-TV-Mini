import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchCatalogue } from "../api";
import ImageLoader from "../components/ImageLoader";

const BASE_URL = import.meta.env.VITE_API_URL || "";

export default function ShowDetail() {
  const { slug } = useParams();

  const { data, isLoading } = useQuery({
    queryKey: ["catalogue"],
    queryFn: fetchCatalogue,
  });

  if (isLoading) return <div className="p-8">Loading...</div>;

  let show: any = null;
  if (data?.sections) {
    for (const section of Object.values(data.sections) as any[]) {
      const found = section.find((s: any) => s.slug === slug);
      if (found) {
        show = found;
        break;
      }
    }
  }

  if (!show) return <div className="p-8 text-center">Show not found</div>;

  return (
    <div>
      <div className="relative h-[40vh] bg-slate-900 border-b border-slate-800">
        {show.artwork?.banner && (
          <ImageLoader
            src={`${BASE_URL}/api/storage/${show.artwork.banner}`}
            className="w-full h-full opacity-40"
            alt={show.title}
          />
        )}
        <div className="absolute bottom-0 p-8 flex gap-6 items-end max-w-7xl mx-auto w-full">
          <ImageLoader
            src={`${BASE_URL}/api/storage/${show.artwork?.poster}`}
            className="w-32 h-48 rounded shadow-lg border border-slate-700"
            alt="Poster"
          />
          <div className="pb-2">
            <h1 className="text-4xl font-bold mb-2">{show.title}</h1>
            <div className="flex gap-2 text-sm text-gray-400 mb-2">
              {show.categories.map((c: string) => (
                <span key={c} className="bg-slate-800 px-2 py-1 rounded">
                  {c}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="p-8 max-w-4xl">
        <p className="text-gray-300 text-lg mb-12">{show.synopsis}</p>

        {show.trailers?.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-6 text-brand-accent">
              Trailers
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {show.trailers.map((tr: any) => (
                <div
                  key={tr.content_group}
                  className="bg-slate-800 rounded overflow-hidden"
                >
                  <div className="aspect-video bg-slate-700"></div>
                  <div className="p-3">
                    <h3 className="font-semibold">{tr.title}</h3>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {show.seasons?.map((season: any) => (
          <div key={season.season_number} className="mb-10">
            <h2 className="text-2xl font-bold mb-6 border-b border-slate-800 pb-2">
              Season {season.season_number}
            </h2>
            <div className="space-y-4">
              {season.episodes.map((ep: any) => (
                <div
                  key={ep.content_group}
                  className="bg-slate-800/50 p-4 rounded-lg flex gap-4 hover:bg-slate-800 transition-colors"
                >
                  {ep.artwork?.thumbnail ? (
                    <ImageLoader
                      src={`${BASE_URL}/api/storage/${ep.artwork.thumbnail}`}
                      alt={ep.title}
                      className="w-24 h-14 rounded shrink-0"
                    />
                  ) : (
                    <div className="w-24 h-14 bg-slate-700 rounded flex items-center justify-center font-bold text-slate-400 shrink-0">
                      {ep.episode_number}
                    </div>
                  )}
                  <div className="flex-1">
                    <h3 className="font-bold text-lg">{ep.title}</h3>
                    <div className="flex justify-between text-sm text-gray-400 mt-1">
                      <span>{Math.floor(ep.duration_seconds / 60)} min</span>
                      <div className="flex gap-2">
                        {ep.languages.map((l: string) => (
                          <span
                            key={l}
                            className="uppercase bg-slate-700 px-1 rounded text-xs"
                          >
                            {l}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
