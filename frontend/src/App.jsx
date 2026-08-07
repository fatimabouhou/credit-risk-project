import { BrowserRouter, Routes, Route } from "react-router-dom";
import SplashScreen from "./pages/SplashScreen";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SplashScreen />} />
        <Route path="/nouvelle-analyse" element={<Landing />} />
        <Route path="/resultat/:clientId" element={<Dashboard />} />
        <Route path="/historique/:clientId" element={<History />} />
      </Routes>
    </BrowserRouter>
  );
}
