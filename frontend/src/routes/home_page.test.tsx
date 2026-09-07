import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test_utils";
import { HomePage } from "./home_page";

describe("HomePage", () => {
  it("renders hero titles, stat proof points and featured therapist section header", () => {
    renderWithProviders(<HomePage />);

    // Proof point metric cards
    expect(
      screen.getAllByText(/50,000\+ therapy hours/i).length
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText(/120\+ Verified Psychologists/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/System Status/i)).toBeInTheDocument();

    // Featured section header
    expect(
      screen.getByText(/Book a Session with Verified Therapists/i)
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: /view all therapists/i }).length
    ).toBeGreaterThanOrEqual(1);
  });
});
