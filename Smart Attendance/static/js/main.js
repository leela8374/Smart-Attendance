/* ═══════════════════════════════════════════════════════
   SmartAttend – main.js  (vanilla, no dependencies)
   ═══════════════════════════════════════════════════════ */

// Auto-dismiss flash messages after 5 seconds
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((f) => {
    setTimeout(() => f.remove(), 5000);
  });
});
