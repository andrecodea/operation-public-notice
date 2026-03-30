import { useEffect, useState } from "react";
import { fetchEvaluationSummary } from "../api";

function KPICard({ label, value }) {
  return (
    <div className="bg-white rounded-lg border p-4">
      <p className="text-xs font-medium text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function ScoreBar({ label, score }) {
  const color =
    score >= 0.8 ? "bg-green-500" : score >= 0.6 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2 mb-2">
      <span className="text-sm font-medium text-gray-700 w-20 uppercase">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${score * 100}%` }} />
      </div>
      <span className="text-sm font-medium text-gray-600 w-10 text-right">
        {(score * 100).toFixed(0)}%
      </span>
    </div>
  );
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchEvaluationSummary()
      .then(setSummary)
      .catch(e => setError(e.message));
  }, []);

  if (error) {
    return <p className="p-4 text-red-500 text-sm">Erro ao carregar: {error}</p>;
  }
  if (!summary) {
    return <p className="p-4 text-gray-400 text-sm">Carregando...</p>;
  }

  return (
    <div className="p-4 max-w-4xl">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Dashboard de Qualidade</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <KPICard label="Total de editais" value={summary.total_editais} />
        <KPICard label="Score médio" value={(summary.avg_score * 100).toFixed(0) + "%"} />
        <KPICard label="JSON válido" value={(summary.json_valid_pct * 100).toFixed(0) + "%"} />
        <KPICard label="PDFs truncados" value={(summary.text_truncated_pct * 100).toFixed(0) + "%"} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Score médio por fonte</h3>
          {Object.entries(summary.avg_score_by_source).map(([src, score]) => (
            <ScoreBar key={src} label={src} score={score} />
          ))}
        </div>

        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Métricas determinísticas</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Campos preenchidos (média)</span>
              <span className="font-medium">{summary.avg_filled_fields}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Corrigidos pelo judge</span>
              <span className="font-medium">{(summary.corrected_pct * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border p-4 mb-6">
        <h3 className="text-sm font-semibold text-blue-700 mb-3">Métricas LLM</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-gray-500 mb-1">Correção multi-turn</p>
            <p className="text-xl font-bold text-gray-900">
              {(summary.corrected_pct * 100).toFixed(0)}%
            </p>
            <p className="text-xs text-gray-400">editais com score &lt; 0.6</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Ganho médio pós-correção</p>
            <p className="text-xl font-bold text-gray-900">
              {summary.avg_correction_gain != null
                ? (summary.avg_correction_gain >= 0 ? "+" : "") +
                  (summary.avg_correction_gain * 100).toFixed(1) + "%"
                : "—"}
            </p>
            <p className="text-xs text-gray-400">delta de score</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-2">Uso de modelo</p>
            {Object.keys(summary.model_usage).length === 0 ? (
              <p className="text-sm text-gray-400">sem dados</p>
            ) : (
              <div className="space-y-1">
                {Object.entries(summary.model_usage).map(([model, count]) => (
                  <div key={model} className="flex items-center gap-2">
                    <span className={`text-xs px-1.5 py-0.5 rounded font-mono ${
                      model.startsWith("gpt") ? "bg-green-100 text-green-700" : "bg-purple-100 text-purple-700"
                    }`}>
                      {model}
                    </span>
                    <span className="text-sm font-medium text-gray-700">{count}x</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-sm font-semibold text-red-600 mb-2">
            Campos com baixa fidelidade
          </h3>
          {summary.fields_with_low_fidelidade.length === 0 ? (
            <p className="text-sm text-gray-400">Nenhum campo problemático</p>
          ) : (
            <ul className="space-y-1">
              {summary.fields_with_low_fidelidade.map(f => (
                <li key={f} className="text-sm font-mono text-gray-700">• {f}</li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-sm font-semibold text-orange-600 mb-2">
            Campos com baixa completude
          </h3>
          {summary.fields_with_low_completude.length === 0 ? (
            <p className="text-sm text-gray-400">Nenhum campo problemático</p>
          ) : (
            <ul className="space-y-1">
              {summary.fields_with_low_completude.map(f => (
                <li key={f} className="text-sm font-mono text-gray-700">• {f}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
