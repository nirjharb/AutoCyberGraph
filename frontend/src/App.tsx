import React from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { AdvisorPage } from "./pages/AdvisorPage";
import { ChangesPage } from "./pages/ChangesPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EcuDetailPage } from "./pages/EcuDetailPage";
import { EvidencePage } from "./pages/EvidencePage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { ReleasesPage } from "./pages/ReleasesPage";
import { RequirementDetailPage } from "./pages/RequirementDetailPage";
import { RequirementsPage } from "./pages/RequirementsPage";
import { StandardsPage } from "./pages/StandardsPage";
import { SuppliersPage } from "./pages/SuppliersPage";
import { TaraPage } from "./pages/TaraPage";
import { TestsPage } from "./pages/TestsPage";
import { TraceGraphPage } from "./pages/TraceGraphPage";
import { VehicleDetailPage } from "./pages/VehicleDetailPage";
import { VehiclesPage } from "./pages/VehiclesPage";
import { VulnerabilitiesPage } from "./pages/VulnerabilitiesPage";

const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return <>{children}</>;
};

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/app"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="vehicles" element={<VehiclesPage />} />
        <Route path="vehicles/:vehicleId" element={<VehicleDetailPage />} />
        <Route path="ecus/:ecuId" element={<EcuDetailPage />} />
        <Route path="tara" element={<TaraPage />} />
        <Route path="requirements" element={<RequirementsPage />} />
        <Route path="requirements/:reqId" element={<RequirementDetailPage />} />
        <Route path="trace" element={<TraceGraphPage />} />
        <Route path="standards" element={<StandardsPage />} />
        <Route path="vulnerabilities" element={<VulnerabilitiesPage />} />
        <Route path="tests" element={<TestsPage />} />
        <Route path="evidence" element={<EvidencePage />} />
        <Route path="releases" element={<ReleasesPage />} />
        <Route path="changes" element={<ChangesPage />} />
        <Route path="advisor" element={<AdvisorPage />} />
        <Route path="suppliers" element={<SuppliersPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
