"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getAttraction, getSlots, type AttractionDetail, type TimeSlot } from "@/lib/api";

function dayLabel(value: string) { return new Intl.DateTimeFormat("en-IN", { weekday: "short", month: "short", day: "numeric", timeZone: "Asia/Kolkata" }).format(new Date(`${value}T12:00:00+05:30`)); }

export default function AttractionPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const [attraction, setAttraction] = useState<AttractionDetail | null>(null);
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [error, setError] = useState("");
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  useEffect(() => { params.then(({ id }) => Promise.all([getAttraction(id), getSlots(id)]).then(([detail, times]) => { setAttraction(detail); setSlots(times); }).catch(() => setError("We couldn’t find this experience."))); }, [params]);
  const dates = useMemo(() => [...new Map(slots.map((slot) => [slot.visit_date, slot])).values()], [slots]);
  const [activeDate, setActiveDate] = useState("");
  useEffect(() => { if (dates[0] && !activeDate) setActiveDate(dates[0].visit_date); }, [dates, activeDate]);
  if (error) return <main className="detail-page shell"><Link className="back-link" href="/">← Back to discovery</Link><div className="message-box">{error}</div></main>;
  if (!attraction) return <main className="detail-page shell"><Link className="back-link" href="/">← Back to discovery</Link><p className="loading-line">Loading your next place…</p></main>;
  const daySlots = slots.filter((slot) => slot.visit_date === activeDate);
  return <main className="detail-page"><nav className="site-nav shell"><Link className="brand" href="/"><span className="brand-mark">T</span>TixBee</Link><Link className="back-link" href="/">← All experiences</Link></nav>
    <section className="detail-hero shell"><div><p className="kicker">{attraction.city} · {attraction.category}</p><h1>{attraction.name}</h1><p>{attraction.description}</p><div className="detail-meta"><span>{attraction.opening_hours}</span>{attraction.directions_url ? <a href={attraction.directions_url} target="_blank" rel="noreferrer">Get directions ↗</a> : null}</div></div><div className={`detail-art card-art-${attraction.category}`}><span>{attraction.category}</span><div>{attraction.name.slice(0, 1)}</div></div></section>
    <section className="booking-panel shell"><div className="booking-heading"><p className="kicker">Plan your visit</p><h2>Choose a time that feels right.</h2><p>Tickets are shown clearly before you commit. Your selected time will be held at checkout.</p></div><div className="date-list">{dates.map((slot) => { const date = slot.visit_date; return <button key={date} className={activeDate === date ? "date-chip active" : "date-chip"} onClick={() => { setActiveDate(date); setSelectedSlot(null); }}>{dayLabel(date)}</button>; })}</div><div className="slot-list">{daySlots.map((slot) => <button key={slot.id} className={selectedSlot === slot.id ? "slot-button selected" : "slot-button"} onClick={() => setSelectedSlot(slot.id)}><span>{slot.start_time.slice(0, 5)} – {slot.end_time.slice(0, 5)}</span><small>{slot.remaining_capacity} places left</small></button>)}</div><button className="checkout-button" disabled={!selectedSlot} onClick={() => selectedSlot && router.push(`/checkout?attraction=${attraction.id}&slot=${selectedSlot}`)}>{selectedSlot ? "Continue to ticket selection →" : "Select a visit time"}</button><p className="checkout-note">A 10-minute hold starts only after you reserve your chosen tickets.</p></section>
    <section className="detail-info shell"><article><h2>Tickets, without the guessing.</h2>{attraction.ticket_types.map((type) => <div className="ticket-row" key={type.id}><div><strong>{type.label}</strong><p>{type.eligibility_note}</p></div><b>₹{Number(type.price).toFixed(0)}</b></div>)}</article><article><h2>Good to know</h2><ul>{attraction.facilities.map((item) => <li key={item}>{item}</li>)}</ul><h3>Visitor notes</h3><ul>{attraction.visitor_rules.map((item) => <li key={item}>{item}</li>)}</ul></article><article className="faq-list"><h2>Questions, answered.</h2>{attraction.faqs.map((faq) => <details key={faq.question}><summary>{faq.question}</summary><p>{faq.answer}</p></details>)}</article></section>
    <footer className="site-footer shell"><span className="brand">TixBee</span><span>Culture, at your pace.</span><span>© 2026</span></footer>
  </main>;
}
