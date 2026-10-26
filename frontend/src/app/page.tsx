"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getAttractions, type Attraction } from "@/lib/api";

const cities = ["All cities", "Bengaluru", "Delhi", "Mumbai"];
const categories = ["All experiences", "museum", "heritage", "gallery", "nature"];
const titleCase = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);

function ExperienceCard({ attraction }: { attraction: Attraction }) {
  return <Link href={`/attractions/${attraction.id}`} className="experience-card">
    <div className={`card-art card-art-${attraction.category}`} style={attraction.image_url ? { backgroundImage: `linear-gradient(0deg, rgba(7,23,32,.58), rgba(7,23,32,.08)), url(${attraction.image_url})`, backgroundSize: "cover", backgroundPosition: "center" } : undefined}><span>{titleCase(attraction.category)}</span><div className="card-monogram">{attraction.name.slice(0, 1)}</div></div>
    <div className="card-copy"><div className="eyebrow">{attraction.city} · {titleCase(attraction.category)}</div><h3>{attraction.name}</h3><p>{attraction.short_description}</p><div className="card-footer"><span>From ₹{Number(attraction.starting_price).toFixed(0)}</span><span>Explore ↗</span></div></div>
  </Link>;
}

export default function Home() {
  const [city, setCity] = useState("All cities");
  const [category, setCategory] = useState("All experiences");
  const [query, setQuery] = useState("");
  const [attractions, setAttractions] = useState<Attraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false; setLoading(true); setError("");
    getAttractions({ city: city === "All cities" ? undefined : city, category: category === "All experiences" ? undefined : category, q: query || undefined })
      .then((data) => !cancelled && setAttractions(data))
      .catch(() => !cancelled && setError("The collection is taking a moment to load. Please try again."))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [city, category, query]);
  const resultLabel = useMemo(() => `${attractions.length} experience${attractions.length === 1 ? "" : "s"}`, [attractions.length]);
  return <main>
    <nav className="site-nav shell"><Link className="brand" href="/" aria-label="TixBee home"><span className="brand-mark">T</span>TixBee</Link><div className="nav-links"><a href="#discover">Discover</a><Link href="/bookings">My bookings</Link><Link href="/operations">Venue operations</Link><span className="nav-muted">Culture, made easy</span></div></nav>
    <section className="hero shell"><div className="hero-copy"><p className="kicker">A better way to spend your day</p><h1>Make room for <em>wonder.</em></h1><p className="hero-lede">Thoughtfully chosen museums, heritage landmarks, and cultural escapes—ready when you are.</p><a className="text-link" href="#discover">Find your next place <span>↓</span></a></div><div className="hero-image" role="img" aria-label="Visitors exploring a historic cultural courtyard" /></section>
    <section id="discover" className="discovery-shell shell"><div className="section-intro"><div><p className="kicker">Explore the collection</p><h2>Find a place that stays with you.</h2></div><p>Simple, transparent ticketing for India&apos;s most memorable cultural spaces.</p></div>
      <div className="filter-bar" aria-label="Filter experiences"><label><span>Where</span><select value={city} onChange={(event) => setCity(event.target.value)}>{cities.map((item) => <option key={item}>{item}</option>)}</select></label><label><span>What interests you</span><select value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map((item) => <option key={item} value={item === "All experiences" ? item : item.toLowerCase()}>{item}</option>)}</select></label><label><span>Search</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Museum, palace, gallery…" /></label></div>
      <div className="collection-heading"><p>{loading ? "Looking for places…" : resultLabel}</p><span>All tickets include instant confirmation</span></div>{error ? <div className="message-box">{error}</div> : null}
      <div className="experience-grid">{loading ? [0, 1, 2].map((item) => <div className="experience-card skeleton" key={item} />) : attractions.map((attraction) => <ExperienceCard attraction={attraction} key={attraction.id} />)}</div>{!loading && !error && attractions.length === 0 ? <div className="message-box">No experiences match that search. Try a different city or theme.</div> : null}
    </section>
    <section className="promise shell"><span className="promise-number">01</span><p>Clear prices. Flexible planning. <em>No booking maze.</em></p><span className="promise-note">A modern ticket desk for real places.</span></section><footer className="site-footer shell"><span className="brand">TixBee</span><span>Culture, at your pace.</span><span>© 2026</span></footer>
  </main>;
}
