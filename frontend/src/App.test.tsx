import { render, screen, waitFor, within } from "@testing-library/react";
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

function installDashboardMocksForToken(expectedToken: string): void {
  mockApiRequest.mockImplementation((path, _options, token) => {
    if (path === "/auth/me") {
      expect(token).toBe(expectedToken);
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
    if (path === "/auth/me/preferences") {
      expect(token).toBe(expectedToken);
      return Promise.resolve({
        ...testUser,
        preferred_unit_system: "imperial",
        preferred_temperature_unit: "F",
        preferred_language: "es",
      });
    }
    return Promise.reject(new Error(`Unexpected path: ${path}`));
  });
}

function installDashboardWithIngredientCreateMocks(expectedToken: string): void {
  mockApiRequest.mockImplementation((path, options, token) => {
    if (path === "/auth/me") {
      expect(token).toBe(expectedToken);
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
      if (options?.method === "POST") {
        const body = JSON.parse(String(options.body)) as {
          name: string;
          ingredient_type: string;
          default_unit: string;
          notes: string;
        };
        return Promise.resolve({
          id: 42,
          ...body,
        });
      }
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

  it("saves preferences and persists updated user locally", async () => {
    const user = userEvent.setup();
    localStorage.setItem("brewpilot.token", "stored-token");
    localStorage.setItem("brewpilot.user", JSON.stringify(testUser));
    installDashboardMocksForToken("stored-token");

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
    });

    const preferencesHeading = screen.getByRole("heading", { name: "Preferences" });
    const preferencesPanel = preferencesHeading.closest("section");
    if (!preferencesPanel) {
      throw new Error("Preferences panel not found");
    }
    const panel = within(preferencesPanel);

    await user.selectOptions(panel.getByLabelText("Unit System"), "imperial");
    await user.selectOptions(panel.getByLabelText("Temperature Unit"), "F");
    await user.selectOptions(panel.getByLabelText("Language"), "es");
    await user.click(panel.getByRole("button", { name: "Save Preferences" }));

    await waitFor(() => {
      expect(screen.getByText("Preferences saved.")).toBeInTheDocument();
    });

    expect(mockApiRequest).toHaveBeenCalledWith(
      "/auth/me/preferences",
      {
        method: "PATCH",
        body: JSON.stringify({
          preferred_unit_system: "imperial",
          preferred_temperature_unit: "F",
          preferred_language: "es",
        }),
      },
      "stored-token",
    );
    expect(localStorage.getItem("brewpilot.user")).toContain("\"preferred_unit_system\":\"imperial\"");
    expect(localStorage.getItem("brewpilot.user")).toContain("\"preferred_temperature_unit\":\"F\"");
    expect(localStorage.getItem("brewpilot.user")).toContain("\"preferred_language\":\"es\"");
  });

  it("logs out and clears local session state", async () => {
    const user = userEvent.setup();
    localStorage.setItem("brewpilot.token", "stored-token");
    localStorage.setItem("brewpilot.user", JSON.stringify(testUser));
    installDashboardOnlyMocks();

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Logout" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Login" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Register" })).toBeInTheDocument();
    });
    expect(localStorage.getItem("brewpilot.token")).toBeNull();
    expect(localStorage.getItem("brewpilot.user")).toBeNull();
  });

  it("creates ingredient from data manager and shows it in the list", async () => {
    const user = userEvent.setup();
    localStorage.setItem("brewpilot.token", "stored-token");
    localStorage.setItem("brewpilot.user", JSON.stringify(testUser));
    installDashboardWithIngredientCreateMocks("stored-token");

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
    });

    const dataManagerHeading = screen.getByRole("heading", { name: "Data Manager" });
    const dataManagerPanel = dataManagerHeading.closest("section");
    if (!dataManagerPanel) {
      throw new Error("Data manager panel not found");
    }
    const panel = within(dataManagerPanel);

    await user.click(panel.getByRole("button", { name: "Ingredients" }));
    await user.type(panel.getByLabelText("Ingredient Name"), "Simcoe");
    await user.clear(panel.getByLabelText("Ingredient Type"));
    await user.type(panel.getByLabelText("Ingredient Type"), "hop");
    await user.clear(panel.getByLabelText("Default Unit"));
    await user.type(panel.getByLabelText("Default Unit"), "oz");
    await user.type(panel.getByLabelText("Notes"), "pine and citrus");
    await user.click(panel.getByRole("button", { name: "Create" }));

    await waitFor(() => {
      expect(screen.getByText("Ingredient created.")).toBeInTheDocument();
      expect(panel.getByText(/Simcoe \(hop\) - oz/)).toBeInTheDocument();
    });

    expect(panel.getByLabelText("Ingredient Name")).toHaveValue("");
    expect(panel.getByLabelText("Notes")).toHaveValue("");
    expect(mockApiRequest).toHaveBeenCalledWith(
      "/ingredients",
      {
        method: "POST",
        body: JSON.stringify({
          name: "Simcoe",
          ingredient_type: "hop",
          default_unit: "oz",
          notes: "pine and citrus",
        }),
      },
      "stored-token",
    );
  });

  it("shows client validation errors for invalid equipment form values", async () => {
    const user = userEvent.setup();
    localStorage.setItem("brewpilot.token", "stored-token");
    localStorage.setItem("brewpilot.user", JSON.stringify(testUser));
    installDashboardOnlyMocks();

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
    });

    const dataManagerHeading = screen.getByRole("heading", { name: "Data Manager" });
    const dataManagerPanel = dataManagerHeading.closest("section");
    if (!dataManagerPanel) {
      throw new Error("Data manager panel not found");
    }
    const panel = within(dataManagerPanel);

    await user.click(panel.getByRole("button", { name: "Equipment" }));
    await user.type(panel.getByLabelText("Equipment"), "Garage Kettle");
    await user.clear(panel.getByLabelText("Batch Volume (L)"));
    await user.type(panel.getByLabelText("Batch Volume (L)"), "0");
    await user.click(panel.getByRole("button", { name: "Create" }));

    await waitFor(() => {
      expect(screen.getByText("Equipment volume and efficiency must be valid positive numbers.")).toBeInTheDocument();
    });

    const equipmentCreateCalls = mockApiRequest.mock.calls.filter(
      ([path, options]) => path === "/equipment" && options?.method === "POST",
    );
    expect(equipmentCreateCalls).toHaveLength(0);
  });
});
