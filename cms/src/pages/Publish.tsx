import { useQuery, useMutation } from "@tanstack/react-query";
import api from "../api";
import { useState } from "react";

export default function Publish() {
  const [publishResult, setPublishResult] = useState<any>(null);
  const role = localStorage.getItem("role");

  const {
    data: report,
    isLoading,
    isError: reportError,
    refetch,
  } = useQuery({
    queryKey: ["validation-report"],
    queryFn: async () => {
      const res = await api.get("/admin/validation-report");
      return res.data;
    },
  });
  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ["publish-runs"],
    queryFn: async () => (await api.get("/admin/catalog/runs")).data,
  });

  const publishMut = useMutation({
    mutationFn: async () => {
      const res = await api.post("/admin/catalog/publish", null, {
        headers: { "Idempotency-Key": crypto.randomUUID() },
      });
      return res.data;
    },
    onSuccess: (data) => {
      setPublishResult({ type: "success", data });
      refetch();
    },
    onError: (err: any) => {
      setPublishResult({
        type: "error",
        message: err.response?.data?.detail || "Publish failed",
      });
    },
  });

  if (isLoading) return <div className="p-8">Loading...</div>;
  if (reportError)
    return (
      <div className="p-8 text-red-600">
        Could not load the validation report. Check your session and try again.
      </div>
    );

  const hasErrors = report?.total_errors > 0;
  const isAdmin = role === "admin";

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Catalogue Publishing</h1>
        <button
          onClick={() => publishMut.mutate()}
          disabled={hasErrors || !isAdmin || publishMut.isPending}
          className={`px-4 py-2 rounded font-bold text-white ${
            hasErrors || !isAdmin
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {publishMut.isPending ? "Publishing..." : "Publish Catalogue"}
        </button>
      </div>

      {!isAdmin && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <p className="text-yellow-700">
            You are logged in as an <strong>Editor</strong>. Only Admins can
            publish the catalogue.
          </p>
        </div>
      )}

      {publishResult && (
        <div
          className={`p-4 mb-6 rounded ${publishResult.type === "success" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"}`}
        >
          {publishResult.type === "success"
            ? `Successfully published! Run ID: ${publishResult.data.run_id} (${publishResult.data.shows_count} shows)`
            : publishResult.message}
        </div>
      )}

      <div className="bg-white rounded shadow p-6">
        <h2 className="text-lg font-bold mb-4">Validation Report</h2>
        {hasErrors ? (
          <div>
            <p className="text-red-600 mb-4 font-semibold">
              There are {report.total_errors} blocking issues preventing
              publication.
            </p>
            {Object.entries(report.categories).map(
              ([cat, errors]: [string, any]) => {
                if (errors.length === 0) return null;
                return (
                  <div key={cat} className="mb-6">
                    <h3 className="font-bold text-gray-700 capitalize border-b pb-2 mb-3">
                      {cat.replace(/_/g, " ")}
                    </h3>
                    <ul className="space-y-3">
                      {errors.map((err: any, i: number) => (
                        <li key={i} className="bg-red-50 p-3 rounded">
                          <div className="font-semibold text-red-800">
                            {err.entity_type}: {err.entity_name}
                          </div>
                          <div className="text-red-700">{err.problem}</div>
                          <div className="text-sm mt-1 text-red-600 font-medium">
                            Fix: {err.fix}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              },
            )}
          </div>
        ) : (
          <div className="text-green-600 font-bold p-4 bg-green-50 rounded">
            All content is valid! Ready to publish.
          </div>
        )}
      </div>

      <div className="bg-white rounded shadow p-6 mt-6">
        <h2 className="text-lg font-bold mb-4">Publish history</h2>
        {runsLoading && (
          <p className="text-gray-500">Loading publish history...</p>
        )}
        {!runsLoading && !runs?.items?.length && (
          <p className="text-gray-500">No publish runs yet.</p>
        )}
        {!!runs?.items?.length && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2">Status</th>
                  <th className="p-2">Started</th>
                  <th className="p-2">Shows</th>
                  <th className="p-2">Episodes</th>
                </tr>
              </thead>
              <tbody>
                {runs.items.map((run: any) => (
                  <tr key={run.id} className="border-b">
                    <td className="p-2">
                      {run.status}
                      {run.is_current ? " (current)" : ""}
                    </td>
                    <td className="p-2">
                      {run.started_at
                        ? new Date(run.started_at).toLocaleString()
                        : "-"}
                    </td>
                    <td className="p-2">{run.shows_count}</td>
                    <td className="p-2">{run.episodes_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
