import { describe, it, expect, vi, afterEach } from "vitest";
import { fetchEditais, fetchEdital, fetchEvaluationSummary, triggerPipeline } from "./api";

const mockFetch = (data) =>
  vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(data) });

afterEach(() => vi.unstubAllGlobals());

describe("fetchEditais", () => {
  it("calls /editais", async () => {
    vi.stubGlobal("fetch", mockFetch([]));
    await fetchEditais();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/editais"));
  });

  it("passes fonte filter", async () => {
    vi.stubGlobal("fetch", mockFetch([]));
    await fetchEditais({ fonte: "fapdf" });
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("fonte=fapdf"));
  });

  it("passes min_score filter", async () => {
    vi.stubGlobal("fetch", mockFetch([]));
    await fetchEditais({ min_score: 0.7 });
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("min_score=0.7"));
  });
});

describe("fetchEdital", () => {
  it("calls /editais/{id}", async () => {
    vi.stubGlobal("fetch", mockFetch({ edital: {}, evaluation: null }));
    await fetchEdital("abc123");
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/editais/abc123"));
  });
});

describe("triggerPipeline", () => {
  it("uses POST method", async () => {
    vi.stubGlobal("fetch", mockFetch({ status: "started" }));
    await triggerPipeline();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/pipeline/run"),
      { method: "POST" }
    );
  });
});
