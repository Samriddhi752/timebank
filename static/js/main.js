document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash-close").forEach((button) => {
    button.addEventListener("click", () => button.closest(".flash").remove());
  });

  // Keep the search input focused after a filter is cleared.
  const searchInput = document.querySelector(".search-bar input");
  if (searchInput) {
    const params = new URLSearchParams(window.location.search);
    if (params.has("q") && params.get("q")) searchInput.focus();
  }
});