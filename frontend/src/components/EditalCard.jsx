function scoreColor(score) {
  if (score == null) return "bg-gray-100 text-gray-500";
  if (score >= 0.8) return "bg-green-100 text-green-700";
  if (score >= 0.6) return "bg-yellow-100 text-yellow-700";
  return "bg-red-100 text-red-700";
}

const FONTE_LABELS = { fapdf: "FAPDF", funcap: "FUNCAP", capes: "CAPES" };

export default function EditalCard({ edital, selected, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-3 border-b hover:bg-gray-50 transition-colors ${
        selected ? "bg-blue-50 border-l-4 border-l-blue-500" : ""
      }`}
    >
      <p className="text-sm font-medium text-gray-900 line-clamp-2">{edital.titulo}</p>
      <div className="flex items-center gap-2 mt-1 flex-wrap">
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
          {FONTE_LABELS[edital.fonte] ?? edital.fonte}
        </span>
        {edital.overall_score != null && (
          <span className={`text-xs px-2 py-0.5 rounded font-medium ${scoreColor(edital.overall_score)}`}>
            {(edital.overall_score * 100).toFixed(0)}%
          </span>
        )}
        {edital.prazo_submissao && (
          <span className="text-xs text-gray-500 truncate">
            Prazo: {edital.prazo_submissao}
          </span>
        )}
      </div>
    </button>
  );
}
