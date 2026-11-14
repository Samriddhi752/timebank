document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash-close").forEach((button) => {
    button.addEventListener("click", () => button.closest(".flash").remove());
  });

  // Ask for confirmation before an action that changes an exchange's status.
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const message = form.dataset.confirm;
      if (message && !window.confirm(message)) event.preventDefault();
    });
  });

  // Keep the search input focused after a search has been submitted.
  const searchInput = document.querySelector(".search-bar input");
  if (searchInput) {
    const params = new URLSearchParams(window.location.search);
    if (params.has("q") && params.get("q")) searchInput.focus();
  }
});
