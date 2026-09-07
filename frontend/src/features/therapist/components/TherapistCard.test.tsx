import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test_utils";
import { TherapistCard } from "./TherapistCard";
import type { TherapistSummary } from "../types/therapist.types";

describe("TherapistCard", () => {
  const sampleTherapist: TherapistSummary = {
    id: "th-101",
    display_name: "Dr. Anita Menon",
    profile_image_url: null,
    designation: "Clinical Psychologist",
    specialization: "clinical_psychologist",
    experience_years: 8,
    therapy_hours: 1500,
    languages: ["en", "ml"],
    expertises: ["anxiety", "depression"],
    session_modes: ["online"],
    pricing: {
      amount: 1500,
      currency: "INR",
      duration_minutes: 60,
    },
    is_verified: true,
    status: "active",
  };

  it("renders therapist details correctly", () => {
    renderWithProviders(<TherapistCard therapist={sampleTherapist} />);

    expect(screen.getByText("Dr. Anita Menon")).toBeInTheDocument();
    expect(
      screen.getAllByText("Clinical Psychologist").length
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/1,500/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view profile/i })).toHaveAttribute(
      "href",
      "/therapists/th-101"
    );
    expect(
      screen.getByRole("link", { name: /book a session|book now/i })
    ).toHaveAttribute("href", "/therapists/th-101");
  });
});
