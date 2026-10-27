"use client";

import Link from "next/link";
import { useState } from "react";
import { requestPasswordReset } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { setMessage((await requestPasswordReset(email)).message); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to request a password reset."); }
    finally { setBusy(false); }
  }
  return <main className="account-page"><nav className="site-nav shell"><Link className="brand" href="/"><span className="brand-mark">T</span>TixBee</Link><Link className="back-link" href="/login">← Back to sign in</Link></nav><section className="account-shell shell"><div><p className="kicker">Account recovery</p><h1>Reset your password.</h1><p>Enter the email you used for your customer account. If it matches an active account, we’ll send a secure, one-time reset link.</p></div><form className="account-form" onSubmit={submit}><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>{message ? <p className="account-note">{message}</p> : null}{error ? <p className="form-error">{error}</p> : null}<button className="checkout-button" disabled={busy}>{busy ? "Sending…" : "Send reset link"}</button><p className="account-note">For your privacy, the same confirmation is shown whether or not an account exists.</p></form></section></main>;
}
