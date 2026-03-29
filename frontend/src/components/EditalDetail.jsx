function scoreColor(score) {
  if (score >= 0.8) return "text-green-600";
  if (score >= 0.6) return "text-yellow-600";
  return "text-red-600";
}

function FieldScoreRow({ field, score }) {
  const avg =
    score.fidelidade != null && score.completude != null
      ? ((score.fidelidade + score.completude) / 2)
      : null;

  return (
    <tr className="border-b last:border-0">
      <td className="py-1.5 pr-3 text-sm font-mono text-gray-700">{field}</td>
      <td className="py-1.5 pr-3 text-sm text-center text-gray-600">
        {score.fidelidade != null ? (score.fidelidade * 100).toFixed(0) + "%" : "—"}
      </td>
      <td className="py-1.5 pr-3 text-sm text-center text-gray-600">
        {score.completude != null ? (score.completude * 100).toFixed(0) + "%" : "—"}
      </td>
      <td className={`py-1.5 text-sm text-center font-medium ${avg != null ? scoreColor(avg) : "text-gray-400"}`}>
        {avg != null ? (avg * 100).toFixed(0) + "%" : "—"}
      </td>
    </tr>
  );
}

export default function EditalDetail({ detail }) {
  if (!detail) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        Selecione um edital para ver os detalhes.
      </div>
    );
  }

  const { edital, evaluation } = detail;

  return (
    <div className="flex-1 overflow-y-auto p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-1">{edital.titulo}</h2>
      <p className="text-sm text-gray-500 mb-4">
        {edital.orgao} · {edital.fonte?.toUpperCase()}
      </p>

      <div className="grid grid-cols-2 gap-3 mb-4">
        {edital.prazo_submissao && (
          <div>
            <p className="text-xs font-medium text-gray-500">Prazo</p>
            <p className="text-sm text-gray-800">{edital.prazo_submissao}</p>
          </div>
        )}
        {edital.valor_financiamento && (
          <div>
            <p className="text-xs font-medium text-gray-500">Valor</p>
            <p className="text-sm text-gray-800">{edital.valor_financiamento}</p>
          </div>
        )}
        {edital.modalidade_fomento && (
          <div>
            <p className="text-xs font-medium text-gray-500">Modalidade</p>
            <p className="text-sm text-gray-800">{edital.modalidade_fomento}</p>
          </div>
        )}
        {edital.elegibilidade && (
          <div className="col-span-2">
            <p className="text-xs font-medium text-gray-500">Elegibilidade</p>
            <p className="text-sm text-gray-800">{edital.elegibilidade}</p>
          </div>
        )}
      </div>

      {edital.objetivo && (
        <div className="mb-4">
          <p className="text-xs font-medium text-gray-500 mb-1">Objetivo</p>
          <p className="text-sm text-gray-700 leading-relaxed">{edital.objetivo}</p>
        </div>
      )}

      {edital.link_edital && (
        <div className="mb-4">
          <a
            href={edital.link_edital}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-blue-600 hover:underline"
          >
            Acessar edital →
          </a>
        </div>
      )}

      {evaluation && (
        <div className="mt-5 border-t pt-4">
          <div className="flex items-center gap-3 mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Avaliação do Judge</h3>
            <span
              className={`text-sm font-medium px-2 py-0.5 rounded ${
                evaluation.overall_score >= 0.8
                  ? "bg-green-100 text-green-700"
                  : evaluation.overall_score >= 0.6
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              Score: {(evaluation.overall_score * 100).toFixed(0)}%
            </span>
            {evaluation.corrected && (
              <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded">
                Corrigido
              </span>
            )}
          </div>

          {Object.keys(evaluation.field_scores).length > 0 && (
            <table className="w-full text-left">
              <thead>
                <tr className="border-b">
                  <th className="pb-1 pr-3 text-xs font-medium text-gray-500">Campo</th>
                  <th className="pb-1 pr-3 text-xs font-medium text-gray-500 text-center">Fidelidade</th>
                  <th className="pb-1 pr-3 text-xs font-medium text-gray-500 text-center">Completude</th>
                  <th className="pb-1 text-xs font-medium text-gray-500 text-center">Média</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(evaluation.field_scores).map(([field, score]) => (
                  <FieldScoreRow key={field} field={field} score={score} />
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
