"use client";

import Link from "next/link";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { confirmPasswordReset } from "@/lib/api";

function ResetPasswordContent() {
  const router = useRouter();
  const token = useSearchParams().get("token") || "";
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [complete, setComplete] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setError("");
    if (!token) { setError("This password-reset link is missing its token."); return; }
    if (password !== confirmPassword) { setError("The passwords do not match."); return; }
    setBusy(true);
    try { await confirmPasswordReset(token, password); setComplete(true); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to reset your password."); }
    finally { setBusy(false); }
  }
  return <main className="account-page"><nav className="site-nav shell"><Link className="brand" href="/"><span className="brand-mark">T</span>TixBee</Link><Link className="back-link" href="/login">← Back to sign in</Link></nav><section className="account-shell shell"><div><p className="kicker">Account recovery</p><h1>Choose a new password.</h1><p>Your reset link is valid for 15 minutes and can be used once.</p></div>{complete ? <div className="account-form"><h2>Password updated</h2><p className="account-note">Your password has been changed. You can now sign in with it.</p><button className="checkout-button" onClick={() => router.push("/login")}>Go to sign in</button></div> : <form className="account-form" onSubmit={submit}><label>New password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required /></label><label>Confirm new password<input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} minLength={8} required /></label>{error ? <p className="form-error">{error}</p> : null}<button className="checkout-button" disabled={busy}>{busy ? "Updating…" : "Update password"}</button></form>}</section></main>;
}

export default function ResetPasswordPage() {
  return <Suspense fallback={<main className="account-page shell"><p className="loading-line">Opening password reset…</p></main>}><ResetPasswordContent /></Suspense>;
}
