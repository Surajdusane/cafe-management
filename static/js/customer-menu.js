(function () {
  "use strict";

  const PUBLIC_PATH = "/menu/cafe";

  const urlInput = document.getElementById("publicUrl");
  const copyBtn = document.getElementById("copyLinkBtn");
  const statGrid = document.getElementById("statGrid");
  const statTotalBadge = document.getElementById("statTotalBadge");

  function initShareLink() {
    urlInput.value = `${window.location.origin}${PUBLIC_PATH}`;
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(urlInput.value);
      } catch (clipboardError) {
        // Clipboard API can be blocked (e.g. plain HTTP); select-and-copy still works.
        urlInput.select();
        document.execCommand("copy");
      }
      UI.toast("Public menu link copied.", "success");
    });
  }

  function statCard(label, value) {
    return `
      <div class="stat-card">
        <dt>${label}</dt>
        <dd>${value}</dd>
      </div>`;
  }

  async function loadStats() {
    try {
      const [categoriesRes, itemsRes] = await Promise.all([
        API.get("/api/categories?include_inactive=false"),
        API.get("/api/menu/items")
      ]);
      const categories = categoriesRes.data.items;
      const items = itemsRes.data.items;

      const shownCategories = categories.filter(
        (category) => category.is_active && category.item_count > 0
      );
      const available = items.filter((item) => item.is_available).length;
      const soldOut = items.length - available;
      const popular = items.filter((item) => item.is_popular).length;

      statTotalBadge.textContent = `${items.length} item(s) on the live menu`;
      statGrid.innerHTML =
        statCard("Sections shown", shownCategories.length) +
        statCard("Available", available) +
        statCard("Sold out", soldOut) +
        statCard("Marked popular", popular);
    } catch (error) {
      statGrid.innerHTML = `<div class="stat-card"><dt>Status</dt><dd>Could not load stats — ${UI.escapeHtml(error.message)}</dd></div>`;
      UI.toast(error.message, "error");
    }
  }

  initShareLink();
  loadStats();
})();
