import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import api from "../api";

export default function EpisodeForm() {
  const navigate = useNavigate();
  const { seasonId } = useParams();
  const [episodeId, setEpisodeId] = useState("");
  const [form, setForm] = useState({
    episode_number: "1",
    title: "",
    content_group: "",
    language: "en",
    duration_seconds: "",
    status: "draft",
  });
  const [error, setError] = useState("");

  const create = useMutation({
    mutationFn: async () =>
      (
        await api.post(`/admin/seasons/${seasonId}/episodes`, {
          ...form,
          episode_number: Number(form.episode_number),
          duration_seconds: form.duration_seconds
            ? Number(form.duration_seconds)
            : null,
        })
      ).data,
    onSuccess: (episode) => setEpisodeId(episode.id),
    onError: (err: any) =>
      setError(err.response?.data?.detail || "Could not create episode"),
  });

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData();
      body.append("file", file);
      return api.post(`/admin/episodes/${episodeId}/artwork/thumbnail`, body);
    },
    onError: (err: any) =>
      setError(err.response?.data?.detail || "Artwork upload failed"),
  });

  const publish = useMutation({
    mutationFn: async () =>
      api.put(`/admin/episodes/${episodeId}`, { status: "published" }),
    onError: (err: any) =>
      setError(err.response?.data?.detail || "Could not publish episode"),
    onSuccess: () => setError(""),
  });

  return (
    <div className="p-8 max-w-lg mx-auto">
      <h1 className="text-2xl font-bold mb-4">Create Episode</h1>
      <p className="text-gray-600 mb-6">
        Create the episode as a draft, then upload thumbnail artwork before
        publishing it.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          create.mutate();
        }}
        className="space-y-4 bg-white p-6 rounded shadow"
      >
        {(
          [
            "episode_number",
            "title",
            "content_group",
            "duration_seconds",
          ] as const
        ).map((field) => (
          <label key={field} className="block text-sm font-bold capitalize">
            {field.replace("_", " ")}
            <input
              required={field !== "duration_seconds"}
              type={
                field === "episode_number" || field === "duration_seconds"
                  ? "number"
                  : "text"
              }
              className="w-full border p-2 rounded mt-1 font-normal"
              value={form[field]}
              onChange={(event) =>
                setForm({ ...form, [field]: event.target.value })
              }
            />
          </label>
        ))}
        <label className="block text-sm font-bold">
          Language
          <select
            className="w-full border p-2 rounded mt-1 font-normal"
            value={form.language}
            onChange={(event) =>
              setForm({ ...form, language: event.target.value })
            }
          >
            <option value="en">English</option>
            <option value="hi">Hindi</option>
          </select>
        </label>
        <button
          disabled={create.isPending || !!episodeId}
          className="bg-blue-600 text-white px-4 py-2 rounded font-bold"
        >
          {create.isPending
            ? "Creating..."
            : episodeId
              ? "Episode created"
              : "Create draft"}
        </button>
        {episodeId && (
          <label className="block text-sm font-bold">
            Thumbnail artwork
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="block mt-1 font-normal"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) upload.mutate(file);
              }}
            />
          </label>
        )}
        {error && <p className="text-red-600">{error}</p>}
        {upload.isSuccess && (
          <div className="space-y-2">
            <p className="text-green-600">Thumbnail uploaded.</p>
            <button
              type="button"
              disabled={publish.isPending}
              onClick={() => publish.mutate()}
              className="bg-green-600 text-white px-4 py-2 rounded font-bold"
            >
              {publish.isPending ? "Publishing..." : "Publish episode"}
            </button>
          </div>
        )}
      </form>
      <button
        onClick={() => navigate(-1)}
        className="mt-4 border px-4 py-2 rounded"
      >
        Go Back
      </button>
    </div>
  );
}
