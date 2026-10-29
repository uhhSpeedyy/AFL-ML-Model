document.querySelectorAll(".explanation-toggle").forEach((button) => {
  button.addEventListener("click", () => {
    const details = document.getElementById(button.getAttribute("aria-controls"));
    const expanded = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!expanded));
    details.hidden = expanded;
    button.querySelector(".toggle-icon").textContent = expanded ? "+" : "−";
  });
});

const fixtureRoundSelect = document.getElementById("fixture-round-select");
if (fixtureRoundSelect) {
  fixtureRoundSelect.addEventListener("change", () => {
    document.querySelectorAll("[data-fixture-round]").forEach((panel) => {
      panel.hidden = panel.dataset.fixtureRound !== fixtureRoundSelect.value;
    });
  });
}
