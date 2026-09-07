import { screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ReservationTimer } from "./ReservationTimer";
import { renderWithProviders } from "@/test/test_utils";

describe("ReservationTimer", () => {
  it("renders active countdown for future expiration", () => {
    const futureDate = new Date(Date.now() + 600000).toISOString();
    renderWithProviders(<ReservationTimer expiresAt={futureDate} />);

    expect(screen.getByText(/time remaining to confirm/i)).toBeInTheDocument();
  });

  it("renders expired message for past expiration", () => {
    const pastDate = new Date(Date.now() - 60000).toISOString();
    renderWithProviders(<ReservationTimer expiresAt={pastDate} />);

    expect(screen.getByText(/expired/i)).toBeInTheDocument();
  });
});
