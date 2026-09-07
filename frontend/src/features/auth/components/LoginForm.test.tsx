import { screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { LoginForm } from "./LoginForm";
import { renderWithProviders } from "@/test/test_utils";

describe("LoginForm", () => {
  it("renders OTP tab and password tab", () => {
    renderWithProviders(<LoginForm />);

    expect(screen.getByRole("tab", { name: /otp/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /password/i })).toBeInTheDocument();
  });

  it("switches to password login when tab clicked", () => {
    renderWithProviders(<LoginForm />);

    const passwordTab = screen.getByRole("tab", { name: /password/i });
    fireEvent.click(passwordTab);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log in/i })).toBeInTheDocument();
  });

  it("calls onSuccess when provided", () => {
    const onSuccess = vi.fn();
    renderWithProviders(<LoginForm onSuccess={onSuccess} />);
    expect(onSuccess).not.toHaveBeenCalled();
  });
});
