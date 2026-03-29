export default function FilterBar({ filters, onChange }) {
  return (
    <div className="flex gap-3 p-3 bg-white border-b">
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-gray-600">Fonte</label>
        <select
          className="border rounded px-2 py-1 text-sm"
          value={filters.fonte}
          onChange={e => onChange({ ...filters, fonte: e.target.value })}
        >
          <option value="">Todas</option>
          <option value="fapdf">FAPDF</option>
          <option value="funcap">FUNCAP</option>
          <option value="capes">CAPES</option>
        </select>
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-gray-600">Score mínimo</label>
        <input
          type="number"
          min="0"
          max="1"
          step="0.1"
          className="border rounded px-2 py-1 text-sm w-20"
          value={filters.min_score}
          onChange={e => onChange({ ...filters, min_score: e.target.value })}
          placeholder="0.0"
        />
      </div>
    </div>
  );
}
