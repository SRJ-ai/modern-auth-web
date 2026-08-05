// ---- features data + render ----
const FEATURES = [
  ["🔑", "Passkeys, native", "WebAuthn done right. Face ID, Touch ID, and security keys with zero passwords to leak."],
  ["🛡️", "Adaptive MFA", "Step up only when risk does. Device, geo, and behavior signals decide — not your users."],
  ["⚡", "Drop-in SDK", "Ship sign-in in an afternoon. Typed SDKs for Python, Node, and the edge."],
  ["🌍", "Global by default", "Sessions replicated to the edge. Sub-50ms token checks anywhere on earth."],
  ["📜", "SOC 2 + GDPR", "Audit logs, data residency, and compliance baked in from line one."],
  ["🧩", "Yours to theme", "Headless primitives or prebuilt UI. Match your brand down to the pixel."],
];

const grid = document.getElementById("feature-grid");
FEATURES.forEach(([icon, title, body], i) => {
  const el = document.createElement("div");
  el.className = "feature reveal-up";
  el.style.transitionDelay = `${i * 70}ms`;
  el.innerHTML = `<div class="ico">${icon}</div><h3>${title}</h3><p>${body}</p>`;
  grid.appendChild(el);
});

document.getElementById("copy").textContent =
  `© ${new Date().getFullYear()} Aegis Labs. All rights reserved.`;

// ---- scroll reveal ----
const io = new IntersectionObserver(
  (entries) => {
    for (const e of entries) {
      if (e.isIntersecting) {
        e.target.classList.add("in");
        io.unobserve(e.target);
      }
    }
  },
  { threshold: 0.15, rootMargin: "-40px" }
);
document.querySelectorAll(".reveal-up").forEach((el) => io.observe(el));

// ---- toast ----
function toast(message, kind = "success") {
  const wrap = document.getElementById("toast-wrap");
  const t = document.createElement("div");
  t.className = `toast ${kind}`;
  t.textContent = message;
  wrap.appendChild(t);
  setTimeout(() => {
    t.style.transition = "opacity .3s, transform .3s";
    t.style.opacity = "0";
    t.style.transform = "translateY(-10px)";
    setTimeout(() => t.remove(), 320);
  }, 4200);
}

// ---- client validation (mirrors server) ----
function validate(v) {
  const errs = {};
  if (!v.name || v.name.trim().length < 2) errs.name = "Name too short";
  else if (v.name.trim().length > 80) errs.name = "Name too long";

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.email || "")) errs.email = "Enter a valid email";

  const phone = (v.phone || "").trim();
  const digits = (phone.match(/\d/g) || []).length;
  if (phone.length < 7 || digits < 7) errs.phone = "Enter a valid phone";
  else if (phone.length > 20) errs.phone = "Phone too long";
  else if (!/^[+\d][\d\s\-().]*$/.test(phone)) errs.phone = "Digits, spaces, + - ( ) only";

  return errs;
}

const form = document.getElementById("waitlist-form");
const btn = document.getElementById("submit-btn");

function setErr(field, msg) {
  const p = document.querySelector(`[data-err="${field}"]`);
  const input = document.getElementById(field);
  if (p) p.textContent = msg || "";
  if (input) input.classList.toggle("invalid", !!msg);
}

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const data = Object.fromEntries(new FormData(form).entries());
  ["name", "email", "phone"].forEach((f) => setErr(f, ""));

  const errs = validate(data);
  if (Object.keys(errs).length) {
    for (const [f, m] of Object.entries(errs)) setErr(f, m);
    return;
  }

  btn.disabled = true;
  const label = btn.textContent;
  btn.textContent = "Sending…";

  try {
    const res = await fetch("/api/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const out = await res.json().catch(() => ({}));

    if (!res.ok) {
      // pydantic 422 → surface field messages
      if (res.status === 422 && Array.isArray(out.detail)) {
        out.detail.forEach((d) => {
          const f = d.loc?.[d.loc.length - 1];
          if (f) setErr(f, d.msg?.replace(/^Value error, /, ""));
        });
        toast("Please fix the highlighted fields.", "error");
      } else {
        toast(out.error || "Something went wrong.", "error");
      }
      return;
    }

    if (out.warning) toast(out.warning, "warning");
    else toast("You're in! Check your inbox for a welcome email.", "success");
    showSuccess();
  } catch {
    toast("Network error. Please try again.", "error");
  } finally {
    btn.disabled = false;
    btn.textContent = label;
  }
});

function showSuccess() {
  const card = form.closest(".form-card");
  card.innerHTML = `
    <div class="form-success">
      <div class="tick">✓</div>
      <h3>You're on the list</h3>
      <p>We sent a welcome email. When your invite is ready, it lands in the same inbox.</p>
      <button class="btn btn-outline btn-sm" id="again">Add another</button>
    </div>`;
  document.getElementById("again").addEventListener("click", () => location.reload());
}
