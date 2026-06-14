import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import { AuthProvider } from "./AuthContext";
import AppLayout from "./components/AppLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import Cadastro from "./pages/Cadastro";
import Geracao from "./pages/Geracao";
import Login from "./pages/Login";
import Projeto from "./pages/Projeto";
import Projetos from "./pages/Projetos";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/cadastro" element={<Cadastro />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/projetos" element={<Projetos />} />
              <Route path="/projetos/:projectId" element={<Projeto />} />
              <Route
                path="/projetos/:projectId/geracoes/:generationId"
                element={<Geracao />}
              />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/projetos" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
