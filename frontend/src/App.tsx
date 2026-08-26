import { Route, Routes } from "react-router-dom";

import NavBar from "./components/NavBar";
import AdminPage from "./pages/AdminPage";
import DocumentDetailPage from "./pages/DocumentDetailPage";
import SearchPage from "./pages/SearchPage";

export default function App() {
  return (
    <div className="min-h-screen bg-background text-text">
      <NavBar />
      <main>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/document/:id" element={<DocumentDetailPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
    </div>
  );
}
