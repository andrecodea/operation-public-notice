import { useState, useEffect, useRef } from "react";
import { triggerPipeline, fetchPipelineStatus } from "../api";

export default function PipelineButton({ onStart, onDone }) {
  const [state, setState] = useState("idle");
  const pollRef = useRef(null);

  useEffect(() => {
    return () => clearInterval(pollRef.current);
  }, []);

  function startPolling() {
    pollRef.current = setInterval(async () => {
      try {
        const { running } = await fetchPipelineStatus();
        if (!running) {
          clearInterval(pollRef.current);
          setState("done");
          onDone?.();
          setTimeout(() => setState("idle"), 3000);
        }
      } catch {
        clearInterval(pollRef.current);
        setState("error");
        setTimeout(() => setState("idle"), 3000);
      }
    }, 3000);
  }

  async function handleClick() {
    setState("running");
    try {
      await triggerPipeline();
      onStart?.();
      startPolling();
    } catch (e) {
      const alreadyRunning = e.message.includes("409");
      if (alreadyRunning) {
        onStart?.();
        startPolling();
      } else {
        setState("error");
        setTimeout(() => setState("idle"), 3000);
      }
    }
  }

  const labels = {
    idle: "▶ Executar pipeline",
    running: "Executando...",
    done: "✓ Concluído",
    error: "✗ Erro",
  };
  const styles = {
    idle: "bg-blue-600 hover:bg-blue-700 text-white",
    running: "bg-blue-500 text-white cursor-not-allowed",
    done: "bg-green-600 text-white",
    error: "bg-red-600 text-white",
  };

  return (
    <button
      onClick={handleClick}
      disabled={state !== "idle"}
      className={`flex items-center gap-2 px-4 py-1.5 rounded text-sm font-medium transition-colors ${styles[state]}`}
    >
      {state === "running" && (
        <svg className="animate-spin h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
      )}
      {labels[state]}
    </button>
  );
}
