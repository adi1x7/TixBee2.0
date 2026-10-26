"use client";

import { FormEvent, useState } from "react";
import { sendConciergeMessage } from "@/lib/api";

type Message = { role: "visitor" | "assistant"; text: string };
const intro = "Tell me what kind of day you’d like to have. I’ll help you find the right place.";

export function Concierge({ attractionId }: { attractionId?: string }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([{ role: "assistant", text: intro }]);
  const [draft, setDraft] = useState("");
  const [waiting, setWaiting] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  function sessionId() { const key = "tixbee-concierge-session"; const existing = window.localStorage.getItem(key); if (existing) return existing; const next = crypto.randomUUID(); window.localStorage.setItem(key, next); return next; }
  async function submit(event: FormEvent) {
    event.preventDefault(); const message = draft.trim(); if (!message || waiting) return;
    setMessages((current) => [...current, { role: "visitor", text: message }]); setDraft(""); setWaiting(true); setUnavailable(false);
    try { const reply = await sendConciergeMessage(sessionId(), message, attractionId); if (reply.status !== "available" || !reply.answer) { setUnavailable(true); } else { setMessages((current) => [...current, { role: "assistant", text: reply.answer! }]); } }
    catch { setUnavailable(true); } finally { setWaiting(false); }
  }
  return <aside className={open ? "concierge open" : "concierge"} aria-label="TixBee Concierge">
    {open ? <section className="concierge-panel"><header><div><span className="concierge-dot" /> TixBee Concierge</div><button onClick={() => setOpen(false)} aria-label="Close concierge">×</button></header><div className="chat-thread">{messages.map((message, index) => <p className={message.role} key={`${message.role}-${index}`}>{message.text}</p>)}{waiting ? <p className="assistant typing">Thinking…</p> : null}{unavailable ? <p className="chat-notice">The concierge is temporarily unavailable. You can still explore and book from the collection.</p> : null}</div><form onSubmit={submit}><input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask about a visit…" aria-label="Message concierge" /><button type="submit" disabled={waiting || !draft.trim()}>Send</button></form></section> : null}
    <button className="concierge-launch" onClick={() => setOpen((value) => !value)}>{open ? "Close" : "Ask TixBee"}<span>✦</span></button>
  </aside>;
}
