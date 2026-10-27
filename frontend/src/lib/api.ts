export type Attraction = {
  id: string;
  slug: string;
  name: string;
  city: string;
  category: string;
  short_description: string;
  starting_price: number;
  image_url: string | null;
};
export type AttractionDetail = Attraction & {
  description: string;
  opening_hours: string;
  facilities: string[];
  visitor_rules: string[];
  directions_url: string | null;
  ticket_types: { id: string; code: string; label: string; price: number; eligibility_note: string | null }[];
  faqs: { question: string; answer: string }[];
};
export type TimeSlot = { id: string; visit_date: string; start_time: string; end_time: string; remaining_capacity: number };

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

function responseErrorMessage(payload: unknown, fallback: string) {
  if (!payload || typeof payload !== "object") return fallback;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => item && typeof item === "object" && "msg" in item ? String(item.msg) : "")
      .filter(Boolean);
    return messages.join(" ") || fallback;
  }
  if (detail && typeof detail === "object" && "message" in detail) return String(detail.message);
  return fallback;
}

export async function getAttractions(filters: { city?: string; category?: string; q?: string } = {}) {
  const params = new URLSearchParams();
  if (filters.city) params.set("city", filters.city);
  if (filters.category) params.set("category", filters.category);
  if (filters.q) params.set("search", filters.q);
  const response = await fetch(`${apiUrl}/attractions?${params.toString()}`);
  if (!response.ok) throw new Error("Unable to load attractions");
  return response.json() as Promise<Attraction[]>;
}

export async function getAttraction(id: string) {
  const response = await fetch(`${apiUrl}/attractions/${id}`);
  if (!response.ok) throw new Error("Unable to load attraction");
  return response.json() as Promise<AttractionDetail>;
}
export async function getSlots(id: string) {
  const response = await fetch(`${apiUrl}/attractions/${id}/slots`);
  if (!response.ok) throw new Error("Unable to load visit times");
  return response.json() as Promise<TimeSlot[]>;
}

export type ConciergeReply = { session_id: string; answer: string | null; status: "available" | "unavailable"; model: string | null };
export async function sendConciergeMessage(sessionId: string, message: string, attractionId?: string, token?: string) {
  const response = await fetch(`${apiUrl}/chat/messages`, { method: "POST", headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify({ session_id: sessionId, message, attraction_id: attractionId }) });
  if (!response.ok) throw new Error("Unable to reach concierge");
  return response.json() as Promise<ConciergeReply>;
}

export type Session = { access_token: string; token_type: "bearer"; user: { id: string; full_name: string; email: string; role: string; assigned_attraction_id: string | null; assigned_attraction_name: string | null } };
export type Booking = { id: string; reference: string; status: string; total_amount: number; hold_expires_at: string | null; items: { ticket_type_code: string; quantity: number; unit_price: number }[] };
export type IssuedTicket = { booking: Booking; ticket_code: string; ticket_status: string; email_delivery_status: "SENT" | "NOT_CONFIGURED" | "FAILED" };
async function post<T>(path: string, body: unknown, token?: string) {
  const response = await fetch(`${apiUrl}${path}`, { method: "POST", headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify(body) });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(responseErrorMessage(payload, "Something went wrong. Please try again."), response.status);
  return payload as T;
}
export const register = (full_name: string, email: string, password: string) => post<Session>("/auth/register", { full_name, email, password });
export const login = (email: string, password: string) => post<Session>("/auth/login", { email, password });
export const requestPasswordReset = (email: string) => post<{ message: string }>("/auth/password-reset/request", { email });
export const confirmPasswordReset = (token: string, password: string) => post<void>("/auth/password-reset/confirm", { token, password });
export const createBooking = (attraction_id: string, slot_id: string, quantities: { ticket_type_code: string; quantity: number }[], token: string) => post<Booking>("/bookings", { attraction_id, slot_id, quantities }, token);
export const cancelHeldBooking = (bookingId: string, token: string) => post<Booking>(`/bookings/${bookingId}/cancel`, {}, token);
export type ConfirmedCancellation = { booking_reference:string; refund_amount:number; refund_status:string; email_delivery_status:"SENT"|"NOT_CONFIGURED"|"FAILED" };
export const cancelConfirmedBooking = (bookingId: string, token: string) => post<ConfirmedCancellation>(`/bookings/${bookingId}/cancel-confirmed`, {}, token);
export const demoPay = (bookingId: string, token: string) => post<IssuedTicket>(`/bookings/${bookingId}/demo-pay`, {}, token);
export async function getUpiPaymentQr(bookingId: string, token: string) { const response = await fetch(`${apiUrl}/bookings/${bookingId}/upi-qr`, { headers: { Authorization: `Bearer ${token}` } }); if (!response.ok) { const data = await response.json().catch(() => null); throw new ApiError(responseErrorMessage(data, "Unable to prepare the payment QR."), response.status); } return response.text(); }
export type MyBooking = { id: string; reference: string; status: string; attraction_name: string; city: string; visit_date: string; start_time: string; total_amount: number; ticket_code: string | null; ticket_status: string | null; cancellation_deadline: string | null };
export async function getMyBookings(token: string) { const response = await fetch(`${apiUrl}/me/bookings`, { headers: { Authorization: `Bearer ${token}` } }); if (!response.ok) throw new ApiError("Please sign in to view your bookings.", response.status); return response.json() as Promise<MyBooking[]>; }
export async function getQrTicket(ticketCode: string, token: string) { const response = await fetch(`${apiUrl}/tickets/${ticketCode}/qr`, { headers: { Authorization: `Bearer ${token}` } }); if (!response.ok) throw new Error("Unable to load ticket pass."); return response.text(); }
export async function getOperations(token: string) { const response = await fetch(`${apiUrl}/operations/summary`, { headers: { Authorization: `Bearer ${token}` } }); const data = await response.json(); if (!response.ok) throw new Error(responseErrorMessage(data, "Unable to open staff desk.")); return data as { issued:number; redeemed:number; confirmed_bookings:number; scope:string; scope_type:"single_attraction"|"all_attractions" }; }
export type OperationActivity = { booking_reference:string; ticket_code:string | null; ticket_status:string | null; attraction_name:string; city:string; visit_date:string; start_time:string; customer_name:string | null; total_amount:number; created_at:string; redeemed_at:string | null };
export async function getOperationActivity(kind: "issued" | "redeemed" | "confirmed", token: string) { const response = await fetch(`${apiUrl}/operations/activity?kind=${kind}`, { headers: { Authorization: `Bearer ${token}` } }); const data = await response.json(); if (!response.ok) throw new Error(responseErrorMessage(data, "Unable to load activity details.")); return data as OperationActivity[]; }
export async function redeemTicket(ticketCode: string, token: string) { return post<{ticket_code:string;status:string}>(`/operations/tickets/${ticketCode}/redeem`, {}, token); }
export type ManagedSlot = { id:string; attraction_id:string; attraction_name:string; visit_date:string; start_time:string; end_time:string; capacity:number; remaining_capacity:number; is_active:boolean };
export type ManagedCustomer = { id:string; full_name:string; email:string; is_active:boolean; booking_count:number; confirmed_booking_count:number; latest_booking_at:string | null };
export async function getManagedSlots(token: string) { const response = await fetch(`${apiUrl}/operations/slots`, { headers: { Authorization: `Bearer ${token}` } }); const data = await response.json(); if (!response.ok) throw new Error(responseErrorMessage(data, "Unable to load slot controls.")); return data as ManagedSlot[]; }
export async function getManagedCustomers(token: string) { const response = await fetch(`${apiUrl}/operations/customers`, { headers: { Authorization: `Bearer ${token}` } }); const data = await response.json(); if (!response.ok) throw new Error(responseErrorMessage(data, "Unable to load customer directory.")); return data as ManagedCustomer[]; }
export async function updateManagedSlot(slotId: string, body: { capacity?: number; is_active?: boolean }, token: string) { const response = await fetch(`${apiUrl}/operations/slots/${slotId}`, { method: "PATCH", headers: { "Content-Type":"application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify(body) }); const data = await response.json(); if (!response.ok) throw new Error(responseErrorMessage(data, "Unable to update the visit slot.")); return data as ManagedSlot; }
