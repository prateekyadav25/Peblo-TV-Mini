import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";

export default function ShowList() {
  const [q, setQ] = useState("");
  const [section, setSection] = useState("");
  const [status, setStatus] = useState("");
  const [language, setLanguage] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useQuery({
    queryKey: ["shows", q, section, status, language, page],
    queryFn: async () =>
      (
        await api.get("/admin/shows", {
          params: {
            q: q || undefined,
            section: section || undefined,
            status: status || undefined,
            language: language || undefined,
            page,
            size: 20,
          },
        })
      ).data,
  });

  if (isLoading) return <div className="p-8">Loading shows...</div>;
  if (isError)
    return (
      <div className="p-8 text-red-600">
        Could not load shows. Check your session and try again.
      </div>
    );

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Shows</h1>
        <Link
          to="/shows/new"
          className="bg-blue-600 text-white px-4 py-2 rounded font-bold hover:bg-blue-700"
        >
          Create New Show
        </Link>
      </div>
      <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-3">
        <input
          aria-label="Search shows"
          placeholder="Search titles"
          className="border p-2 rounded"
          value={q}
          onChange={(event) => {
            setQ(event.target.value);
            setPage(1);
          }}
        />
        <select
          aria-label="Filter section"
          className="border p-2 rounded"
          value={section}
          onChange={(event) => {
            setSection(event.target.value);
            setPage(1);
          }}
        >
          <option value="">All sections</option>
          <option value="featured">Featured</option>
          <option value="series">Series</option>
          <option value="minisodes">Minisodes</option>
          <option value="songs">Songs</option>
        </select>
        <select
          aria-label="Filter status"
          className="border p-2 rounded"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPage(1);
          }}
        >
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
        </select>
        <select
          aria-label="Filter language"
          className="border p-2 rounded"
          value={language}
          onChange={(event) => {
            setLanguage(event.target.value);
            setPage(1);
          }}
        >
          <option value="">All languages</option>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
        </select>
      </div>
      <div className="bg-white rounded shadow">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-gray-50 border-b">
              <th className="p-4">Title</th>
              <th className="p-4">Section</th>
              <th className="p-4">Status</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.items?.map((show: any) => (
              <tr key={show.id} className="border-b hover:bg-gray-50">
                <td className="p-4 font-semibold">{show.title}</td>
                <td className="p-4">{show.section || "-"}</td>
                <td className="p-4">
                  <span
                    className={`px-2 py-1 rounded text-xs ${show.status === "published" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}
                  >
                    {show.status}
                  </span>
                </td>
                <td className="p-4 flex gap-2">
                  <Link
                    to={`/shows/${show.id}`}
                    className="text-blue-600 hover:underline"
                  >
                    Manage
                  </Link>
                  <Link
                    to={`/shows/${show.id}/edit`}
                    className="text-slate-600 hover:underline"
                  >
                    Edit
                  </Link>
                </td>
              </tr>
            ))}
            {!data?.items?.length && (
              <tr>
                <td colSpan={4} className="p-8 text-center text-gray-500">
                  No shows match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center justify-between text-sm">
        <span>
          Page {data?.page || page} of {data?.pages || 0}
        </span>
        <div className="space-x-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="border px-3 py-1 rounded disabled:opacity-40"
          >
            Previous
          </button>
          <button
            disabled={page >= (data?.pages || 0)}
            onClick={() => setPage(page + 1)}
            className="border px-3 py-1 rounded disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
