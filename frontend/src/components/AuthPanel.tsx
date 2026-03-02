import { FormEvent, useState } from "react";

import type { Translator } from "../i18n";

export type AuthMode = "login" | "register";

export interface AuthSubmitPayload {
  mode: AuthMode;
  username: string;
  email: string;
  password: string;
}

interface AuthPanelProps {
  loading: boolean;
  tr: Translator;
  onAuthenticate: (payload: AuthSubmitPayload) => Promise<boolean>;
}

export function AuthPanel({ loading, tr, onAuthenticate }: AuthPanelProps) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const success = await onAuthenticate({
      mode,
      username,
      email,
      password,
    });
    if (success) {
      setPassword("");
      if (mode === "register") {
        setUsername("");
      }
    }
  }

  return (
    <section className="panel auth-panel">
      <div className="tab-row">
        <button className={mode === "login" ? "tab active" : "tab"} onClick={() => setMode("login")}>
          {tr("login")}
        </button>
        <button className={mode === "register" ? "tab active" : "tab"} onClick={() => setMode("register")}>
          {tr("register")}
        </button>
      </div>

      <form onSubmit={(event) => void handleSubmit(event)}>
        {mode === "register" ? (
          <label>
            {tr("username")}
            <input value={username} onChange={(event) => setUsername(event.target.value)} required />
          </label>
        ) : null}

        <label>
          {tr("email")}
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>

        <label>
          {tr("password")}
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>

        <button className="primary-button" type="submit" disabled={loading}>
          {tr("submit")}
        </button>
      </form>
    </section>
  );
}
