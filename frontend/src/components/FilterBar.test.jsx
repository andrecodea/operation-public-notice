import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import FilterBar from "./FilterBar";

const defaultFilters = { fonte: "", min_score: "" };

describe("FilterBar", () => {
  it("renders fonte select with all source options", () => {
    render(<FilterBar filters={defaultFilters} onChange={vi.fn()} />);
    expect(screen.getByRole("combobox")).toBeInTheDocument();
    expect(screen.getByText("FAPDF")).toBeInTheDocument();
    expect(screen.getByText("FUNCAP")).toBeInTheDocument();
    expect(screen.getByText("CAPES")).toBeInTheDocument();
  });

  it("calls onChange with updated fonte when select changes", () => {
    const onChange = vi.fn();
    render(<FilterBar filters={defaultFilters} onChange={onChange} />);
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "fapdf" } });
    expect(onChange).toHaveBeenCalledWith({ fonte: "fapdf", min_score: "" });
  });

  it("calls onChange with updated min_score when input changes", () => {
    const onChange = vi.fn();
    render(<FilterBar filters={defaultFilters} onChange={onChange} />);
    fireEvent.change(screen.getByRole("spinbutton"), { target: { value: "0.7" } });
    expect(onChange).toHaveBeenCalledWith({ fonte: "", min_score: "0.7" });
  });
});
