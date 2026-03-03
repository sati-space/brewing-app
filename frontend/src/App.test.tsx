import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { APIError, apiRequest } from "./api";
import type { User } from "./types";

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return {
    ...actual,
    apiRequest: vi.fn(),
  };
});

const mockApiRequest = vi.mocked(apiRequest);

const testUser: User = {
  id: 1,
  username: "testbrewer",
  email: "brewer@example.com",
  preferred_unit_system: "metric",
  preferred_temperature_unit: "C",
  preferred_language: "en",
  created_at: "2026-01-01T00:00:00Z",
};

function installAuthAndDashboardMocks(): void {
  mockApiRequest.mockImplementation((path, _options, token) => {
    if (path === "/auth/login") {
      return Promise.resolve({
        access_token: "token-123",
        token_type: "bearer",
        user: testUser,
      });
    }
    if (path === "/auth/me") {
      expect(token).toBe("token-123");
      return Promise.resolve(testUser);
    }
    if (path === "/batches") {
      return Promise.resolve([]);
    }
    if (path === "/equipment") {
      return Promise.resolve([]);
    }
    if (path === "/water-profiles") {
      return Promise.resolve([]);
    }
    if (path === "/ingredients") {
      return Promise.resolve([]);
    }
    if (path === "/recipes") {
      return Promise.resolve([]);
    }
    return Promise.reject(new Error(`Unexpected path: ${path}`));
  });
}

function installDashboardOnlyMocks(): void {
  mockApiRequest.mockImplementation((path, _options, token) => {
    if (path === "/auth/me") {
      expect(token).toBe("stored-token");
      return Promise.resolve(testUser);
    }
    if (path === "/batches") {
      return Promise.resolve([]);
    }
    if (path === "/equipment") {
      return Promise.resolve([]);
    }
    if (path === "/water-profiles") {
      return Promise.resolve([]);
    }
    if (path === "/ingredients") {
      return Promise.resolve([]);
    }
    if (path === "/recipes") {
      return Promise.resolve([]);
    }
    return Promise.reject(new Error(`Unexpected path: ${path}`));
  });
}

describe("App integration", () => {
  beforeEach(() => {
    localStorage.removeItem("brewpilot.token");
    localStorage.removeItem("brewpilot.user");
    mockApiRequest.mockReset();
  });

  it("authenticates through login and then loads dashboard data", async () => {
    const user = userEvent.setup();
    installAuthAndDashboardMocks();

    render(<App />);

    await user.type(screen.getByLabelText("Email"), "brewer@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      expect(screen.getByText("Authenticated.")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Preferences" })).toBeInTheDocument();
    });

    expect(localStorage.getItem("brewpilot.token")).toBe("token-123");
    expect(localStorage.getItem("brewpilot.user")).toContain("testbrewer");

    expect(mockApiRequest).toHaveBeenCalledWith(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({
          email: "brewer@example.com",
          password: "password123",
        }),
      },
    );
    expect(mockApiRequest).toHaveBeenCalledWith("/auth/me", {}, "token-123");
    expect(mockApiRequest).toHaveBeenCalledWith("/batches", {}, "token-123");
    expect(mockApiRequest).toHaveBeenCalledWith("/equipment", {}, "token-123");
    expect(mockApiRequest).toHaveBeenCalledWith("/water-profiles", {}, "token-123");
    expect(mockApiRequest).toHaveBeenCalledWith("/ingredients", {}, "token-123");
    expect(mockApiRequest).toHaveBeenCalledWith("/recipes", {}, "token-123");
  });

  it("shows API errors when registration fails", async () => {
    const user = userEvent.setup();
    mockApiRequest.mockRejectedValue(new APIError(409, "Email already exists"));

    render(<App />);

    await user.click(screen.getByRole("button", { name: "Register" }));
    await user.type(screen.getByLabelText("Username"), "newbrewer");
    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      expect(screen.getByText("409: Email already exists")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Register" })).toBeInTheDocument();
    expect(localStorage.getItem("brewpilot.token")).toBeNull();
  });

  it("loads dashboard on startup when token exists in local storage", async () => {
    localStorage.setItem("brewpilot.token", "stored-token");
    localStorage.setItem("brewpilot.user", JSON.stringify(testUser));
    installDashboardOnlyMocks();

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Preferences" })).toBeInTheDocument();
    });

    expect(mockApiRequest).not.toHaveBeenCalledWith("/auth/login", expect.anything(), expect.anything());
    expect(mockApiRequest).toHaveBeenCalledWith("/auth/me", {}, "stored-token");
  });
});
