import EditalCard from "./EditalCard";

export default function EditalList({ editais, selectedId, onSelect }) {
  if (editais.length === 0) {
    return (
      <div className="p-6 text-center text-gray-400 text-sm">
        Nenhum edital encontrado.
      </div>
    );
  }
  return (
    <div className="overflow-y-auto flex-1">
      {editais.map(edital => (
        <EditalCard
          key={edital.id}
          edital={edital}
          selected={edital.id === selectedId}
          onClick={() => onSelect(edital.id)}
        />
      ))}
    </div>
  );
}
