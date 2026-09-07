import { screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { BookingStatusChip } from "./BookingStatusChip";
import { renderWithProviders } from "@/test/test_utils";

describe("BookingStatusChip", () => {
  it("renders confirmed booking status with appropriate styling", () => {
    renderWithProviders(<BookingStatusChip status="confirmed" />);
    expect(screen.getByText(/confirmed/i)).toBeInTheDocument();
  });

  it("renders cancelled booking status", () => {
    renderWithProviders(<BookingStatusChip status="cancelled" />);
    expect(screen.getByText(/cancelled/i)).toBeInTheDocument();
  });

  it("renders pending booking status", () => {
    renderWithProviders(<BookingStatusChip status="pending" />);
    expect(screen.getByText(/pending/i)).toBeInTheDocument();
  });
});
