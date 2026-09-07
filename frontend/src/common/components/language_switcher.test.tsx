import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/test_utils";
import { LanguageSwitcher } from "./language_switcher";

describe("LanguageSwitcher", () => {
  it("renders the language selector button and opens menu on click", async () => {
    const user = userEvent.setup();
    renderWithProviders(<LanguageSwitcher />);

    const button = screen.getByRole("button", { name: /select language/i });
    expect(button).toBeInTheDocument();

    await user.click(button);

    const menu = screen.getByRole("menu");
    expect(menu).toBeInTheDocument();
    expect(screen.getAllByText("English").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("മലയാളം")).toBeInTheDocument();
    expect(screen.getByText("தமிழ்")).toBeInTheDocument();
  });
});
