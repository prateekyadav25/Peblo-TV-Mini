import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchCatalogue } from "../api";
import { Link } from "react-router-dom";
import ImageLoader from "../components/ImageLoader";

const BASE_URL = import.meta.env.VITE_API_URL || "";

export default function Search() {
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [category, setCategory] = useState("");
  const [language, setLanguage] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQ(q), 300);
    return () => clearTimeout(timer);
  }, [q]);

  const { data, isLoading } = useQuery({
    queryKey: ["search", debouncedQ, category, language],
    queryFn: () => searchCatalogue({ q: debouncedQ, category, language }),
    enabled: true,
  });

  return (
    <div className="p-8 md:p-16 max-w-7xl mx-auto min-h-screen">
      <div className="mb-12 flex flex-col md:flex-row gap-4">
        <input
          type="text"
          placeholder="Search shows or episodes..."
          className="flex-1 bg-slate-800 border-none p-4 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-brand-accent outline-none text-lg"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="bg-slate-800 p-4 rounded-xl outline-none border-none focus:ring-2 focus:ring-brand-accent text-lg"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All Categories</option>
          <option value="adventure">Adventure</option>
          <option value="science">Science</option>
          <option value="fantasy">Fantasy</option>
        </select>
        <select
          aria-label="Language filter"
          className="bg-slate-800 p-4 rounded-xl outline-none border-none focus:ring-2 focus:ring-brand-accent text-lg"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        >
          <option value="">All Languages</option>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
        </select>
      </div>

      {isLoading && (
        <div className="text-center py-12 animate-pulse text-xl text-gray-400">
          Searching the cosmos...
        </div>
      )}

      {!isLoading && data?.results?.length === 0 && (
        <div className="text-center py-12 text-gray-400 text-xl">
          No results found. Try adjusting your filters.
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6 md:gap-8">
        {data?.results?.map((show: any) => (
          <Link to={`/show/${show.slug}`} key={show.slug} className="group">
            <div className="aspect-[2/3] rounded-lg overflow-hidden mb-3 shadow-lg">
              {show.artwork?.poster ? (
                <ImageLoader
                  src={`${BASE_URL}/api/storage/${show.artwork.poster}`}
                  alt={show.title}
                  className="w-full h-full group-hover:scale-105 transition-transform duration-500"
                />
              ) : (
                <div className="w-full h-full bg-slate-800 flex items-center justify-center text-gray-500">
                  No Image
                </div>
              )}
            </div>
            <h3 className="font-semibold group-hover:text-brand-accent transition-colors truncate">
              {show.title}
            </h3>
          </Link>
        ))}
      </div>
    </div>
  );
}
