import { useState } from "react";
import { triggerPipeline } from "../api";

export default function PipelineButton() {
  const [state, setState] = useState("idle");

  async function handleClick() {
    setState("running");
    try {
      await triggerPipeline();
      setState("done");
      setTimeout(() => setState("idle"), 3000);
    } catch {
      setState("error");
      setTimeout(() => setState("idle"), 3000);
    }
  }

  const labels = {
    idle: "▶ Executar pipeline",
    running: "Iniciando...",
    done: "✓ Iniciado",
    error: "✗ Erro",
  };
  const styles = {
    idle: "bg-blue-600 hover:bg-blue-700 text-white",
    running: "bg-gray-400 text-white cursor-not-allowed",
    done: "bg-green-600 text-white",
    error: "bg-red-600 text-white",
  };

  return (
    <button
      onClick={handleClick}
      disabled={state !== "idle"}
      className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${styles[state]}`}
    >
      {labels[state]}
    </button>
  );
}
