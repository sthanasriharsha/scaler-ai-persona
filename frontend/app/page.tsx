"use client";
import { useState, useRef, useEffect } from "react";
import styles from "./page.module.css";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Message = { role: "user" | "assistant"; content: string; sources?: string[] };

const SUGGESTED = [
  "Why are you the right fit for Scaler?",
  "Tell me about your C-DAC internship",
  "What is your Pose Normalisation project?",
  "What LLM and RAG experience do you have?",
  "Book a call with Sriharsha",
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hi! I'm Sriharsha's AI representative. I can answer questions about his background, projects, and skills — or help you book a call with him. What would you like to know?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showBooking, setShowBooking] = useState(false);
  const [slots, setSlots] = useState<any[]>([]);
  const [booking, setBooking] = useState({ name: "", email: "", slot: "" });
  const [bookingStatus, setBookingStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text?: string) {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    const newMessages: Message[] = [...messages, { role: "user", content: msg }];
    setMessages(newMessages);
    setLoading(true);

    if (msg.toLowerCase().includes("book") || msg.toLowerCase().includes("schedule") || msg.toLowerCase().includes("availability")) {
      setShowBooking(true);
      fetchSlots();
      setMessages([...newMessages, { role: "assistant", content: "Sure! Let me pull up Sriharsha's availability. You can pick a slot below 👇" }]);
      setLoading(false);
      return;
    }

    const history = newMessages.slice(-8).map(m => ({ role: m.role, content: m.content }));
    try {
      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history: history.slice(0, -1) }),
      });
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let full = "";
      setMessages(prev => [...prev, { role: "assistant", content: "" }]);
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split("\n").filter(l => l.startsWith("data: "));
        for (const line of lines) {
          const data = line.slice(6);
          if (data === "[DONE]") break;
          try {
            const parsed = JSON.parse(data);
            full += parsed.text || "";
            setMessages(prev => {
              const updated = [...prev];
              updated[updated.length - 1] = { role: "assistant", content: full };
              return updated;
            });
          } catch {}
        }
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I hit an error. Please try again." }]);
    }
    setLoading(false);
  }

  async function fetchSlots() {
    try {
      const res = await fetch(`${API}/api/availability`);
      const data = await res.json();
      setSlots(data.slots || []);
    } catch {
      setSlots([]);
    }
  }

  async function confirmBooking() {
    if (!booking.name || !booking.email || !booking.slot) return;
    setBookingStatus("loading");
    try {
      const res = await fetch(`${API}/api/book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: booking.name, email: booking.email, start_time: booking.slot }),
      });
      const data = await res.json();
      if (data.success) {
        setBookingStatus("done");
        setMessages(prev => [...prev, {
          role: "assistant",
          content: `✅ Booked! Your interview with Sriharsha is confirmed. Check your email (${booking.email}) for the calendar invite.`,
        }]);
        setShowBooking(false);
      } else {
        setBookingStatus("error");
      }
    } catch {
      setBookingStatus("error");
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  }

  return (
    <main className={styles.main}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.avatar}>S</div>
          <div>
            <div className={styles.name}>Sriharsha</div>
            <div className={styles.subtitle}>AI Engineer · C-DAC Intern · <span className={styles.dot}></span> AI persona active</div>
          </div>
          <div className={styles.headerLinks}>
            <a href="https://github.com/sthanasriharsha" target="_blank" rel="noopener noreferrer" className={styles.link}>GitHub</a>
            <a href="https://linkedin.com/in/gundumalla-sthana-sriharsha" target="_blank" rel="noopener noreferrer" className={styles.link}>LinkedIn</a>
          </div>
        </div>
      </header>

      {/* Messages */}
      <section className={styles.messages}>
        {messages.map((m, i) => (
          <div key={i} className={`${styles.msg} ${m.role === "user" ? styles.user : styles.assistant}`}>
            {m.role === "assistant" && <div className={styles.msgAvatar}>S</div>}
            <div className={styles.bubble}>
              <MessageContent content={m.content} />
            </div>
          </div>
        ))}
        {loading && (
          <div className={`${styles.msg} ${styles.assistant}`}>
            <div className={styles.msgAvatar}>S</div>
            <div className={styles.bubble}><span className={styles.typing}><span/><span/><span/></span></div>
          </div>
        )}

        {/* Booking Panel */}
        {showBooking && (
          <div className={styles.bookingPanel}>
            <div className={styles.bookingTitle}>📅 Book a call with Sriharsha</div>
            <div className={styles.bookingForm}>
              <input className={styles.input2} placeholder="Your name" value={booking.name}
                onChange={e => setBooking(p => ({...p, name: e.target.value}))} />
              <input className={styles.input2} placeholder="Your email" type="email" value={booking.email}
                onChange={e => setBooking(p => ({...p, email: e.target.value}))} />
              <select className={styles.input2} value={booking.slot}
                onChange={e => setBooking(p => ({...p, slot: e.target.value}))}>
                <option value="">Select a slot</option>
                {slots.map((s, i) => (
                  <option key={i} value={s.iso || s.time}>
                    {s.date} · {s.time?.slice(11, 16)} IST
                  </option>
                ))}
              </select>
              <div className={styles.bookingActions}>
                <button className={styles.bookBtn} onClick={confirmBooking} disabled={bookingStatus === "loading"}>
                  {bookingStatus === "loading" ? "Booking..." : "Confirm booking"}
                </button>
                <button className={styles.cancelBtn} onClick={() => setShowBooking(false)}>Cancel</button>
              </div>
              {bookingStatus === "error" && <div className={styles.error}>Booking failed. Please try again.</div>}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </section>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className={styles.suggestions}>
          {SUGGESTED.map((s, i) => (
            <button key={i} className={styles.chip} onClick={() => send(s)}>{s}</button>
          ))}
        </div>
      )}

      {/* Input */}
      <footer className={styles.footer}>
        <div className={styles.inputRow}>
          <textarea
            ref={inputRef}
            className={styles.textarea}
            placeholder="Ask about Sriharsha's skills, projects, or type 'book a call'..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
          />
          <button className={styles.sendBtn} onClick={() => send()} disabled={loading || !input.trim()}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
        <div className={styles.footerNote}>RAG-grounded on Sriharsha's resume & GitHub repos</div>
      </footer>
    </main>
  );
}

function MessageContent({ content }: { content: string }) {
  const parts = content.split(/(\*\*[^*]+\*\*)/g);
  return (
    <p>
      {parts.map((p, i) =>
        p.startsWith("**") && p.endsWith("**")
          ? <strong key={i}>{p.slice(2, -2)}</strong>
          : p
      )}
    </p>
  );
}
