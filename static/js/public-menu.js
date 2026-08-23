(function () {
  "use strict";

  const CUP_ICON =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M4.5 9h12v7a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V9z"/><path d="M16.5 10.5h1.6a2.4 2.4 0 0 1 0 4.8h-1.6"/><path d="M8 2.5c1 .8 1 1.7 0 2.5M12 2.5c1 .8 1 1.7 0 2.5"/></svg>';
  const EMPTY_ICON =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M4 19.5V6a2 2 0 0 1 2-2h14v14H6a2 2 0 0 0-2 2z"/><path d="M8 8h8M8 12h5"/></svg>';
  const ERROR_ICON =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 3 2.5 20h19L12 3z"/><path d="M12 10v4M12 17h.01"/></svg>';

  let menu = null;
  let activeCategory = "all";
  let searchTimer = null;

  const main = document.getElementById("pmMain");
  const chips = document.getElementById("pmChips");
  const searchInput = document.getElementById("pmSearchInput");
  const LOADING_HTML = main.innerHTML; // kept for retry after an error replaces it

  function escapeHtml(value) {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return String(value === null || value === undefined ? "" : value).replace(/[&<>"']/g, (ch) => map[ch]);
  }

  function money(amount) {
    const symbol = menu && menu.cafe.currency ? menu.cafe.currency : "\u20B9";
    const value = Number(amount) || 0;
    return `${escapeHtml(symbol)}${value.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  function vegMark(isVegetarian) {
    return `<span class="pm-dot-mark ${isVegetarian ? "pm-dot-veg" : "pm-dot-nonveg"}"
      title="${isVegetarian ? "Vegetarian" : "Non-vegetarian"}" role="img"
      aria-label="${isVegetarian ? "Vegetarian" : "Non-vegetarian"}"></span>`;
  }

  function itemImage(item) {
    if (item.image_url) {
      return `<img class="pm-img" src="${escapeHtml(item.image_url)}" alt="${escapeHtml(item.name)}" loading="lazy" />`;
    }
    return `<div class="pm-img-fallback" aria-hidden="true">${CUP_ICON}</div>`;
  }

  function itemTags(item) {
    const tags = [];
    if (!item.is_available) tags.push('<span class="pm-tag pm-tag-soldout">Sold out</span>');
    else if (item.is_popular) tags.push('<span class="pm-tag pm-tag-popular">★ Popular</span>');
    return tags.length ? `<div class="pm-tags">${tags.join("")}</div>` : "";
  }

  function itemCard(item) {
    const soldOut = item.is_available ? "" : " is-soldout";
    return `
      <article class="pm-item${soldOut}">
        ${itemImage(item)}
        <div class="pm-item-body">
          <div class="pm-item-line">
            <h3 class="pm-item-name">${escapeHtml(item.name)}${vegMark(item.is_vegetarian)}</h3>
            <span class="pm-dots" aria-hidden="true"></span>
            <span class="pm-price">${money(item.price)}</span>
          </div>
          ${item.description ? `<p class="pm-item-desc">${escapeHtml(item.description)}</p>` : ""}
          ${itemTags(item)}
        </div>
      </article>`;
  }

  function matchesSearch(item, term) {
    const haystack = `${item.name} ${item.description || ""}`.toLowerCase();
    return haystack.includes(term);
  }

  function visibleSections() {
    const term = searchInput.value.trim().toLowerCase();
    let sections = menu.categories;
    if (activeCategory !== "all" && !term) {
      sections = sections.filter((category) => category.name === activeCategory);
    }
    if (term) {
      sections = sections
        .map((category) => ({
          ...category,
          items: category.items.filter((item) => matchesSearch(item, term))
        }))
        .filter((category) => category.items.length > 0);
    }
    return { sections, term };
  }

  function stateHtml(icon, heading, message, extra = "") {
    return `
      <div class="pm-state">
        <div class="pm-state-icon">${icon}</div>
        <h2>${heading}</h2>
        <p>${message}</p>
        ${extra}
      </div>`;
  }

  function render() {
    if (!menu) return;
    renderChips();

    const { sections, term } = visibleSections();

    if (sections.length === 0) {
      main.innerHTML =
        term !== ""
          ? stateHtml(EMPTY_ICON, "Nothing matches your search", `No dishes match “${escapeHtml(term)}”. Try a different word.`)
          : stateHtml(CUP_ICON, "Menu coming soon", "Our chef is still plating this page. Please check back shortly.");
      return;
    }

    const note =
      term !== ""
        ? `<p class="pm-results-note"><strong>${sections.reduce((sum, s) => sum + s.items.length, 0)}</strong> result(s) for “${escapeHtml(term)}”</p>`
        : "";

    const body = sections
      .map((category) => {
        const spanFull = sections.length === 1 ? " span-full" : "";
        return `
          <section class="pm-section${spanFull}">
            <div class="pm-section-head">
              <h2 class="pm-section-title">${escapeHtml(category.name)}</h2>
              <span class="pm-section-rule" aria-hidden="true"></span>
            </div>
            ${category.description ? `<p class="pm-section-desc">${escapeHtml(category.description)}</p>` : ""}
            ${category.items.map(itemCard).join("")}
          </section>`;
      })
      .join("");

    main.innerHTML = `<div class="pm-sections-grid">${note}${body}</div>`;

    // Broken image URLs fall back to the cup mark without leaving broken-image icons.
    main.querySelectorAll("img.pm-img").forEach((img) => {
      img.addEventListener("error", () => {
        const fallback = document.createElement("div");
        fallback.className = "pm-img-fallback";
        fallback.setAttribute("aria-hidden", "true");
        fallback.innerHTML = CUP_ICON;
        img.replaceWith(fallback);
      });
    });
  }

  function renderChips() {
    if (chips.dataset.rendered === "true") return;
    const names = menu.categories.map((category) => category.name);
    chips.innerHTML = ["all", ...names]
      .map(
        (name) =>
          `<button type="button" class="pm-chip${name === activeCategory ? " is-active" : ""}"
            data-category="${escapeHtml(name)}">${name === "all" ? "All" : escapeHtml(name)}</button>`
      )
      .join("");
    chips.dataset.rendered = "true";
    chips.addEventListener("click", (event) => {
      const button = event.target.closest("[data-category]");
      if (!button) return;
      activeCategory = button.dataset.category;
      chips.querySelectorAll(".pm-chip").forEach((chip) => chip.classList.toggle("is-active", chip === button));
      render();
    });
  }

  function renderBranding() {
    const cafe = menu.cafe;
    document.title = `Menu · ${cafe.name}`;
    document.querySelector('meta[property="og:title"]').setAttribute("content", `Menu · ${cafe.name}`);

    const nameNode = document.getElementById("pmCafeName");
    nameNode.textContent = cafe.name;

    const metaParts = [
      cafe.address ? escapeHtml(cafe.address) : null,
      cafe.phone ? `<a href="tel:${escapeHtml(cafe.phone)}">${escapeHtml(cafe.phone)}</a>` : null
    ];
    const metaText = metaParts.filter(Boolean).join(" · ");
    const metaNode = document.getElementById("pmCafeMeta");
    if (metaText) metaNode.innerHTML = metaText;

    if (cafe.logo_url) {
      const logo = document.getElementById("pmLogo");
      logo.src = cafe.logo_url;
      logo.alt = `${cafe.name} logo`;
      logo.hidden = false;
      logo.addEventListener("error", () => {
        logo.hidden = true;
        showMonogram(cafe.name);
      });
    } else {
      showMonogram(cafe.name);
    }
    document.querySelector('meta[property="og:description"]').setAttribute(
      "content",
      `Browse the menu at ${cafe.name}`
    );

    const foot = document.getElementById("pmFoot");
    document.getElementById("pmFootName").textContent = cafe.name;
    document.getElementById("pmFootMeta").textContent =
      [cafe.address, cafe.email].filter(Boolean).join(" · ") || "";
    foot.hidden = false;
  }

  function showMonogram(name) {
    const monogram = document.getElementById("pmMonogram");
    monogram.textContent = (name || "?").trim().charAt(0).toUpperCase();
    monogram.hidden = false;
  }

  async function loadMenu() {
    try {
      const payload = await API.get("/api/public/menu");
      menu = payload.data;
      renderBranding();
      render();
    } catch (error) {
      main.innerHTML = stateHtml(
        ERROR_ICON,
        "We couldn't load the menu",
        "Please check your connection and try again.",
        '<button type="button" class="pm-retry" id="pmRetry">Try again</button>'
      );
      document.getElementById("pmRetry").addEventListener("click", () => {
        main.innerHTML = LOADING_HTML;
        loadMenu();
      });
    }
  }

  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(render, 180); // small debounce keeps typing smooth on phones
  });

  loadMenu();
})();
