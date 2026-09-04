import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../api";
import ArtworkUploader from "../components/ArtworkUploader";

export default function ShowDetail() {
  const { id } = useParams();
  const qc = useQueryClient();
  const [selectedSeasonId, setSelectedSeasonId] = useState("");
  const [newSeasonNumber, setNewSeasonNumber] = useState("1");

  const { data: show, isLoading } = useQuery({
    queryKey: ["show_full", id],
    queryFn: async () => {
      const [sRes, awRes, seasonsRes] = await Promise.all([
        api.get(`/admin/shows/${id}`),
        api.get(`/admin/shows/${id}/artwork`),
        api.get(`/admin/shows/${id}/seasons?size=100`),
      ]);
      const seasonItems = seasonsRes.data.items || [];
      const episodeResponses = await Promise.all(
        seasonItems.map((season: any) =>
          api.get(`/admin/seasons/${season.id}/episodes?size=100`),
        ),
      );
      return {
        show: sRes.data,
        artwork: awRes.data.items,
        seasons: seasonItems,
        episodes: episodeResponses.flatMap(
          (response: any) => response.data.items || [],
        ),
      };
    },
  });

  useEffect(() => {
    if (show?.seasons?.length && !selectedSeasonId) {
      setSelectedSeasonId(show.seasons[0].id);
      setNewSeasonNumber(
        String(
          Math.max(...show.seasons.map((season: any) => season.season_number)) +
            1,
        ),
      );
    }
  }, [show, selectedSeasonId]);

  const createSeasonMut = useMutation({
    mutationFn: async () =>
      api.post(`/admin/shows/${id}/seasons`, {
        season_number: Number(newSeasonNumber),
      }),
    onSuccess: (response) => {
      setSelectedSeasonId(response.data.id);
      setNewSeasonNumber(String(Number(newSeasonNumber) + 1));
      qc.invalidateQueries({ queryKey: ["show_full", id] });
    },
  });

  if (isLoading) return <div className="p-8">Loading...</div>;

  const awMap = show?.artwork?.reduce(
    (acc: any, aw: any) => ({ ...acc, [aw.artwork_type]: aw }),
    {},
  );

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <Link
            to="/shows"
            className="text-blue-600 text-sm hover:underline mb-2 block"
          >
            &larr; Back to Shows
          </Link>
          <h1 className="text-3xl font-bold">{show?.show.title}</h1>
        </div>
        <Link
          to={`/shows/${id}/edit`}
          className="border px-4 py-2 rounded shadow-sm hover:bg-gray-50"
        >
          Edit Show Settings
        </Link>
      </div>

      <section className="bg-white p-6 rounded shadow border-t-4 border-blue-500">
        <h2 className="text-xl font-bold mb-4">Artwork Management</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ArtworkUploader
            showId={id!}
            type="poster"
            label="Poster (2:3 ~600x900)"
            current={awMap?.poster}
          />
          <ArtworkUploader
            showId={id!}
            type="banner"
            label="Banner (16:9 ~1280x720)"
            current={awMap?.banner}
          />
          <ArtworkUploader
            showId={id!}
            type="thumbnail"
            label="Thumbnail (16:9 ~640x360)"
            current={awMap?.thumbnail}
          />
        </div>
      </section>

      <section className="bg-white p-6 rounded shadow">
        <div className="flex justify-between mb-4">
          <h2 className="text-xl font-bold">Episodes</h2>
          <div className="space-x-2">
            <button
              onClick={() => createSeasonMut.mutate()}
              className="border px-3 py-1 rounded text-sm hover:bg-gray-50"
            >
              Add Season {newSeasonNumber}
            </button>
            {!!show?.seasons?.length && (
              <select
                aria-label="Episode season"
                value={selectedSeasonId}
                onChange={(event) => setSelectedSeasonId(event.target.value)}
                className="border px-2 py-1 rounded text-sm"
              >
                {show.seasons.map((season: any) => (
                  <option key={season.id} value={season.id}>
                    Season {season.season_number}
                  </option>
                ))}
              </select>
            )}
            <Link
              to={
                selectedSeasonId
                  ? `/shows/${id}/seasons/${selectedSeasonId}/episodes/new`
                  : "#"
              }
              onClick={(event) => {
                if (!selectedSeasonId) event.preventDefault();
              }}
              className={`bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 ${!selectedSeasonId ? "opacity-40 cursor-not-allowed" : ""}`}
            >
              Add Episode
            </Link>
          </div>
        </div>

        {!show?.episodes?.length ? (
          <div className="text-gray-500 italic py-4">
            No episodes added yet.
          </div>
        ) : (
          <table className="w-full text-left mt-4 border-t">
            <thead>
              <tr className="bg-gray-50 text-sm">
                <th className="p-2">S.Ep</th>
                <th className="p-2">Title</th>
                <th className="p-2">Content Group</th>
                <th className="p-2">Lang</th>
                <th className="p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {show?.episodes?.map((ep: any) => (
                <tr key={ep.id} className="border-t hover:bg-gray-50">
                  <td className="p-2 font-mono text-xs">
                    {ep.season_id.slice(0, 4)}... E{ep.episode_number}
                  </td>
                  <td className="p-2 font-semibold">{ep.title}</td>
                  <td className="p-2 text-gray-600">{ep.content_group}</td>
                  <td className="p-2 uppercase text-xs">{ep.language}</td>
                  <td className="p-2">
                    <span
                      className={`px-2 py-1 rounded text-xs ${ep.status === "published" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}
                    >
                      {ep.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
