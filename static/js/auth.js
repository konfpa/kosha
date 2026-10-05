const reveals = document.querySelectorAll("[data-reveal]");

const setRevealed = (reveal, shown) => {
  reveal.parentElement.querySelector("input").type = shown ? "text" : "password";
  // toggleAttribute, not .hidden: SVG elements have no hidden property.
  reveal.querySelector("[data-eye]").toggleAttribute("hidden", shown);
  reveal.querySelector("[data-eye-off]").toggleAttribute("hidden", !shown);
  reveal.setAttribute("aria-pressed", shown);
  reveal.setAttribute("aria-label", shown ? "Hide password" : "Show password");
};

reveals.forEach((reveal) => {
  reveal.addEventListener("click", () => {
    setRevealed(reveal, reveal.getAttribute("aria-pressed") !== "true");
  });
  // Password managers only offer to save a password field, and a revealed one
  // would stay on screen while the next page loads.
  reveal.closest("form").addEventListener("submit", () => setRevealed(reveal, false));
});

// Going back restores the page from cache, revealed password included.
window.addEventListener("pageshow", (e) => {
  if (e.persisted) reveals.forEach((reveal) => setRevealed(reveal, false));
});

document.querySelectorAll("[data-caps]").forEach((hint) => {
  const input = hint.closest("form").querySelector("input[type=password]");
  const update = (e) => { hint.hidden = !e.getModifierState("CapsLock"); };
  input.addEventListener("keydown", update);
  input.addEventListener("keyup", update);
  input.addEventListener("blur", () => { hint.hidden = true; });
});

document.querySelectorAll("form[data-busy]").forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector("[type=submit]");
    button.disabled = true;
    button.textContent = form.dataset.busy;
  });
});

document.querySelectorAll("[data-rules-for]").forEach((list) => {
  const input = document.getElementById(list.dataset.rulesFor);
  const checks = {
    length: (v) => v.length >= 8,
    numeric: (v) => v.length > 0 && !/^\d+$/.test(v),
  };
  input.addEventListener("input", () => {
    for (const [rule, check] of Object.entries(checks)) {
      const item = list.querySelector(`[data-rule=${rule}]`);
      const pass = check(input.value);
      item.classList.toggle("text-brand-ink", pass);
      item.firstElementChild.classList.toggle("bg-brand", pass);
      item.firstElementChild.classList.toggle("bg-stone-300", !pass);
    }
  });
});

// An email has just gone out, so hold off a resend for a short while.
document.querySelectorAll("[data-cooldown]").forEach((button) => {
  const label = button.textContent;
  let left = Number(button.dataset.cooldown);
  button.disabled = true;
  const tick = () => {
    button.textContent = left ? `${label} in ${left}s` : label;
    if (left-- > 0) setTimeout(tick, 1000);
    else button.disabled = false;
  };
  tick();
});
