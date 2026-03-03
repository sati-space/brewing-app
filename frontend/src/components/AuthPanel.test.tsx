import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuthPanel } from "./AuthPanel";

const labels = {
  login: "Login",
  register: "Register",
  username: "Username",
  email: "Email",
  password: "Password",
  submit: "Submit",
} as const;

describe("AuthPanel", () => {
  it("submits login payload and clears only password on success", async () => {
    const user = userEvent.setup();
    const onAuthenticate = vi.fn().mockResolvedValue(true);
    const tr = (key: string): string => labels[key as keyof typeof labels] ?? key;

    render(<AuthPanel loading={false} tr={tr} onAuthenticate={onAuthenticate} />);

    expect(screen.queryByLabelText(labels.username)).not.toBeInTheDocument();

    await user.type(screen.getByLabelText(labels.email), "brewer@example.com");
    await user.type(screen.getByLabelText(labels.password), "secret123");
    await user.click(screen.getByRole("button", { name: labels.submit }));

    await waitFor(() => {
      expect(onAuthenticate).toHaveBeenCalledWith({
        mode: "login",
        username: "",
        email: "brewer@example.com",
        password: "secret123",
      });
    });

    expect(screen.getByLabelText(labels.email)).toHaveValue("brewer@example.com");
    expect(screen.getByLabelText(labels.password)).toHaveValue("");
  });

  it("submits register payload and clears username + password on success", async () => {
    const user = userEvent.setup();
    const onAuthenticate = vi.fn().mockResolvedValue(true);
    const tr = (key: string): string => labels[key as keyof typeof labels] ?? key;

    render(<AuthPanel loading={false} tr={tr} onAuthenticate={onAuthenticate} />);

    await user.click(screen.getByRole("button", { name: labels.register }));

    const usernameInput = screen.getByLabelText(labels.username);
    await user.type(usernameInput, "brewer123");
    await user.type(screen.getByLabelText(labels.email), "register@example.com");
    await user.type(screen.getByLabelText(labels.password), "secret123");
    await user.click(screen.getByRole("button", { name: labels.submit }));

    await waitFor(() => {
      expect(onAuthenticate).toHaveBeenCalledWith({
        mode: "register",
        username: "brewer123",
        email: "register@example.com",
        password: "secret123",
      });
    });

    expect(screen.getByLabelText(labels.username)).toHaveValue("");
    expect(screen.getByLabelText(labels.email)).toHaveValue("register@example.com");
    expect(screen.getByLabelText(labels.password)).toHaveValue("");
  });
});
