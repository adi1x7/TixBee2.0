"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { login, register } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      const session = mode === "login" ? await login(email, password) : await register(fullName, email, password);
      window.localStorage.setItem("tixbee-session", JSON.stringify(session));
      router.push(session.user.role === "customer" ? "/bookings" : "/operations");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to continue.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="account-page"><nav className="site-nav shell"><Link className="brand" href="/"><span className="brand-mark">T</span>TixBee</Link><Link className="back-link" href="/">← Explore experiences</Link></nav><section className="account-shell shell"><div><p className="kicker">Your TixBee account</p><h1>{mode === "login" ? "Welcome back." : "Make your first plan."}</h1><p>Sign in to see your tickets, complete held bookings, and manage your day out in one place.</p></div><form className="account-form" onSubmit={submit}><div className="mode-switch"><button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Sign in</button><button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>Create account</button></div>{mode === "register" ? <label>Full name<input value={fullName} onChange={(event) => setFullName(event.target.value)} minLength={2} required /></label> : null}<label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={mode === "register" ? 8 : 1} required /></label>{error ? <p className="form-error">{error}</p> : null}<button className="checkout-button" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</button>{mode === "login" ? <Link className="account-link" href="/forgot-password">Forgot your password?</Link> : null}<p className="account-note">Venue staff and administrators use the same secure sign-in and are redirected to their permitted workspace.</p></form></section></main>;
}
