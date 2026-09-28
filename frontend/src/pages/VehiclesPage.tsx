import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, Vehicle } from "../api/client";
import { Card, EmptyState, ErrorBox, PageHeader, Spinner, Table } from "../components/ui";

export const VehiclesPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading, error } = useQuery<Vehicle[]>({
    queryKey: ["vehicles"],
    queryFn: () => api<Vehicle[]>("/api/vehicles"),
  });

  return (
    <div>
      <PageHeader title="Vehicle Architecture" subtitle="Vehicles, ECU topology and in-vehicle networks. Click a vehicle to explore its architecture." />
      {isLoading && <Spinner />}
      {error && <ErrorBox message={error instanceof Error ? error.message : "error"} />}
      {data && data.length === 0 && <EmptyState title="No vehicles yet" />}
      {data && data.length > 0 && (
        <Card>
          <Table headers={["Name", "Model", "Platform", "Version", "Description"]}>
            {data.map((v) => (
              <tr key={v.id} className="hover:bg-ink-850/60 cursor-pointer" onClick={() => navigate(`/app/vehicles/${v.id}`)}>
                <td className="td font-semibold text-white">{v.name}</td>
                <td className="td">{v.model}</td>
                <td className="td font-mono text-cyan-300">{v.platform}</td>
                <td className="td">{v.version}</td>
                <td className="td text-slate-400 max-w-md truncate">{v.description}</td>
              </tr>
            ))}
          </Table>
        </Card>
      )}
    </div>
  );
};
