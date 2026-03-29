import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import Dashboard from "./Dashboard";
import * as api from "../api";

const MOCK_SUMMARY = {
  total_editais: 10,
  avg_score: 0.75,
  avg_score_by_source: { fapdf: 0.8, funcap: 0.7 },
  fields_with_low_fidelidade: ["objetivo"],
  fields_with_low_completude: ["valor_financiamento"],
  json_valid_pct: 0.9,
  text_truncated_pct: 0.2,
  avg_filled_fields: 9.5,
  corrected_pct: 0.3,
};

afterEach(() => vi.restoreAllMocks());

describe("Dashboard", () => {
  it("renders total_editais KPI", async () => {
    vi.spyOn(api, "fetchEvaluationSummary").mockResolvedValue(MOCK_SUMMARY);
    render(<Dashboard />);
    await waitFor(() => expect(screen.getByText("10")).toBeInTheDocument());
  });

  it("renders avg_score as percentage", async () => {
    vi.spyOn(api, "fetchEvaluationSummary").mockResolvedValue(MOCK_SUMMARY);
    render(<Dashboard />);
    await waitFor(() => expect(screen.getByText("75%")).toBeInTheDocument());
  });

  it("shows low fidelidade fields", async () => {
    vi.spyOn(api, "fetchEvaluationSummary").mockResolvedValue(MOCK_SUMMARY);
    render(<Dashboard />);
    await waitFor(() => expect(screen.getByText(/objetivo/)).toBeInTheDocument());
  });

  it("shows low completude fields", async () => {
    vi.spyOn(api, "fetchEvaluationSummary").mockResolvedValue(MOCK_SUMMARY);
    render(<Dashboard />);
    await waitFor(() =>
      expect(screen.getByText(/valor_financiamento/)).toBeInTheDocument()
    );
  });

  it("shows loading state before data arrives", () => {
    vi.spyOn(api, "fetchEvaluationSummary").mockReturnValue(new Promise(() => {}));
    render(<Dashboard />);
    expect(screen.getByText(/Carregando/)).toBeInTheDocument();
  });
});
