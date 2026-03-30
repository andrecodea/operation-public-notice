import { useState, useEffect, useRef } from "react";
import { fetchEditais, fetchEdital } from "./api";
import FilterBar from "./components/FilterBar";
import EditalList from "./components/EditalList";
import EditalDetail from "./components/EditalDetail";
import Dashboard from "./components/Dashboard";
import PipelineButton from "./components/PipelineButton";

export default function App() {
  const [activeTab, setActiveTab] = useState("editais");
  const [filters, setFilters] = useState({ fonte: "", min_score: "" });
  const [editais, setEditais] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [dashboardKey, setDashboardKey] = useState(0);
  const refreshIntervalRef = useRef(null);

  function startLiveRefresh() {
    clearInterval(refreshIntervalRef.current);
    refreshIntervalRef.current = setInterval(() => {
      setFilters(f => ({ ...f }));
    }, 10_000);
  }

  function stopLiveRefresh() {
    clearInterval(refreshIntervalRef.current);
    setFilters(f => ({ ...f }));
    setDashboardKey(k => k + 1);
  }

  useEffect(() => {
    setLoading(true);
    const params = {};
    if (filters.fonte) params.fonte = filters.fonte;
    if (filters.min_score) params.min_score = parseFloat(filters.min_score);
    fetchEditais(params)
      .then(setEditais)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => {
    if (!selectedId) { setDetail(null); return; }
    fetchEdital(selectedId)
      .then(setDetail)
      .catch(console.error);
  }, [selectedId]);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-6">
          <h1 className="text-base font-bold text-gray-900">Operação Edital</h1>
          <nav className="flex gap-1">
            {[["editais", "Editais"], ["dashboard", "Dashboard"]].map(([tab, label]) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? "bg-blue-100 text-blue-700"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
        <PipelineButton
          onStart={startLiveRefresh}
          onDone={stopLiveRefresh}
        />
      </header>

      {activeTab === "editais" ? (
        <div className="flex-1 flex overflow-hidden">
          <div className="w-80 flex flex-col border-r bg-white shrink-0">
            <FilterBar filters={filters} onChange={setFilters} />
            {loading ? (
              <p className="p-4 text-sm text-gray-400">Carregando...</p>
            ) : (
              <EditalList
                editais={editais}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            )}
          </div>
          <div className="flex-1 flex overflow-hidden">
            <EditalDetail detail={detail} />
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <Dashboard key={dashboardKey} />
        </div>
      )}
    </div>
  );
}
