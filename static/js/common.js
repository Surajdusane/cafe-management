(function () {
  "use strict";

  const ICONS = {
    dashboard: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7.5" height="9" rx="1.5"/><rect x="13.5" y="3" width="7.5" height="5.5" rx="1.5"/><rect x="13.5" y="11.5" width="7.5" height="9.5" rx="1.5"/><rect x="3" y="15" width="7.5" height="6" rx="1.5"/></svg>',
    menu: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5V6a2 2 0 0 1 2-2h14v14H6a2 2 0 0 0-2 2z"/><path d="M8 8h8M8 12h5"/></svg>',
    globe: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.7 3.8 9S14.5 18.4 12 21c-2.5-2.6-3.8-5.7-3.8-9S9.5 5.6 12 3z"/></svg>',
    receipt: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2h12v20l-3-2-3 2-3-2-3 2V2z"/><path d="M10 7h4M10 11h4"/></svg>',
    billing: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.6"/><path d="M5.5 9.5h.01M18.5 14.5h.01"/></svg>',
    inventory: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m7.5 4 4.5 2.5L16.5 4 21 6.5v5L16.5 14 12 11.5 7.5 14 3 11.5v-5L7.5 4z"/><path d="M3 16.5 7.5 19l4.5-2.5 4.5 2.5 4.5-2.5"/><path d="m7.5 14v5M16.5 14v5"/></svg>',
    truck: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M2 6h12v10H2zM14 9h4l4 3.5V16h-8"/><circle cx="7" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/></svg>',
    suppliers: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M21 6H3l9 6-9 6h18l-9-6 9-6z"/></svg>',
    employees: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.2"/><path d="M2.8 20c.7-3.2 3.2-5 6.2-5s5.5 1.8 6.2 5"/><circle cx="17" cy="9" r="2.4"/><path d="M16.4 15.2c2.5.2 4.3 1.7 4.8 4.3"/></svg>',
    salaries: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M3 11h18M8 7V5.5A1.5 1.5 0 0 1 9.5 4h5A1.5 1.5 0 0 1 16 5.5V7"/><circle cx="12" cy="14.5" r="1.6"/></svg>',
    expenses: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 6.5c-.8-1.4-2.6-2-5-2-2.9 0-5 1.3-5 3.6 0 4.9 10 2.4 10 7.3 0 2.3-2.2 3.6-5 3.6-2.4 0-4.2-.7-5-2"/></svg>',
    reports: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/></svg>',
    clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.2 2"/></svg>',
    trend: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="m3 17 6-6 4 4 8-8"/><path d="M14 7h7v7"/></svg>',
    settings: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3.2"/><path d="M19 12c0-.6.4-1.4 1.2-1.9l-1.5-3.4c-.8.2-1.7 0-2.1-.4-.4-.4-.6-1.3-.4-2.1L12.8 3h-.1c-.5.8-1.3 1.2-1.9 1.2S9.4 3.8 8.9 3L5.5 4.5c.2.8 0 1.7-.4 2.1-.4.4-1.3.6-2.1.4L1.5 10.4c.8.5 1.2 1.3 1.2 1.9s-.4 1.4-1.2 1.9l1.5 3.4c.8-.2 1.7 0 2.1.4.4.4.6 1.3.4 2.1l3.4 1.5c.5-.8 1.3-1.2 1.9-1.2s1.4.4 1.9 1.2l3.4-1.5c-.2-.8 0-1.7.4-2.1.4-.4 1.3-.6 2.1-.4l1.5-3.4c-.8-.5-1.1-1.3-1.1-1.9z" transform="translate(1.2) scale(.92)"/></svg>',
    cup: '<svg viewBox="0 0 24 24" fill="none" stroke="#e0965b" stroke-width="1.7" stroke-linecap="round"><path d="M4.5 9h12v7a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V9z"/><path d="M16.5 10.5h1.6a2.4 2.4 0 0 1 0 4.8h-1.6"/><path d="M8 2.5c1 .8 1 1.7 0 2.5M12 2.5c1 .8 1 1.7 0 2.5"/></svg>'
  };

  const NAV = [
    {
      label: "Overview",
      items: [{ href: "/", page: "dashboard", title: "Dashboard", icon: "dashboard" }]
    },
    {
      label: "Sales",
      items: [
        { href: "/menu", page: "menu", title: "Menu Management", icon: "menu" },
        { href: "/customer-menu", page: "customer-menu", title: "Customer Menu", icon: "globe" },
        { href: "/orders", page: "orders", title: "Orders", icon: "receipt" },
        { href: "/billing", page: "billing", title: "Billing", icon: "billing" }
      ]
    },
    {
      label: "Stock & Supply",
      items: [
        { href: "/inventory", page: "inventory", title: "Inventory", icon: "inventory" },
        { href: "/purchases", page: "purchases", title: "Purchases", icon: "truck" },
        { href: "/suppliers", page: "suppliers", title: "Suppliers", icon: "suppliers" }
      ]
    },
    {
      label: "People",
      items: [
        { href: "/employees", page: "employees", title: "Employees", icon: "employees" },
        { href: "/salaries", page: "salaries", title: "Salaries", icon: "salaries" }
      ]
    },
    {
      label: "Money & Insight",
      items: [
        { href: "/expenses", page: "expenses", title: "Expenses", icon: "expenses" },
        { href: "/reports", page: "reports", title: "Reports", icon: "reports" }
      ]
    },
    {
      label: "System",
      items: [{ href: "/settings", page: "settings", title: "Settings", icon: "settings" }]
    }
  ];

  function el(html) {
    const template = document.createElement("template");
    template.innerHTML = html.trim();
    return template.content.firstElementChild;
  }

  function renderSidebar(currentPage) {
    const groups = NAV.map((group) => {
      const links = group.items
        .map((item) => {
          const active = item.page === currentPage ? ' class="active" aria-current="page"' : "";
          return `<a href="${item.href}"${active}>${ICONS[item.icon]}<span>${item.title}</span></a>`;
        })
        .join("");
      return `<div class="nav-group-label">${group.label}</div>${links}`;
    }).join("");

    return `
      <aside class="sidebar" id="sidebar">
        <div class="brand">
          <div class="brand-mark">${ICONS.cup}</div>
          <div>
            <div class="brand-name">Cafe Desk</div>
            <span class="brand-sub">Management</span>
          </div>
        </div>
        <nav class="nav" aria-label="Main navigation">${groups}</nav>
        <div class="sidebar-foot"></div>
      </aside>`;
  }

  function renderTopbar(currentPage) {
    const current = NAV.flatMap((g) => g.items).find((i) => i.page === currentPage);
    const title = current ? current.title : document.title;
    return `
      <header class="topbar">
        <button type="button" class="hamburger" id="navToggle" aria-label="Open navigation">${ICONS.dashboard.replace('viewBox', 'width="18" height="18" viewBox')}</button>
        <span class="crumb-sep">Cafe Desk</span>
        <h1>/ ${title}</h1>
        <div class="top-right">
          <span id="todayLabel"></span>
          <span class="status-chip" id="apiStatus"><span class="dot"></span><span data-label>Checking…</span></span>
        </div>
      </header>`;
  }

  function wireNavigation() {
    const toggle = document.getElementById("navToggle");
    const overlay = document.querySelector(".sidebar-overlay");
    if (!toggle || !overlay) return;
    const close = () => document.body.classList.remove("nav-open");
    toggle.addEventListener("click", () => document.body.classList.toggle("nav-open"));
    overlay.addEventListener("click", close);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") close();
    });
  }

  async function checkApiStatus() {
    const chip = document.getElementById("apiStatus");
    if (!chip) return;
    try {
      await API.get("/api/health");
      chip.classList.add("is-ok");
      chip.querySelector("[data-label]").textContent = "System online";
    } catch (error) {
      chip.classList.add("is-down");
      chip.querySelector("[data-label]").textContent = "Offline";
    }
  }

  const TOAST_ICONS = {
    success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="m8.5 12 2.4 2.4L15.5 9.5"/></svg>',
    error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5h.01"/></svg>',
    warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 2.5 20h19L12 3z"/><path d="M12 10v4M12 17h.01"/></svg>',
    info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.5h.01"/></svg>'
  };

  function toast(message, type = "info", duration = 3800) {
    let stack = document.querySelector(".toast-stack");
    if (!stack) {
      stack = el('<div class="toast-stack" role="status" aria-live="polite"></div>');
      document.body.appendChild(stack);
    }
    const node = el(`
      <div class="toast toast-${type}">
        ${TOAST_ICONS[type] || TOAST_ICONS.info}
        <span>${message}</span>
      </div>`);
    stack.appendChild(node);
    setTimeout(() => {
      node.classList.add("hide");
      setTimeout(() => node.remove(), 250);
    }, duration);
  }

  function confirmDialog({ title = "Are you sure?", message = "", confirmText = "Confirm", cancelText = "Cancel" }) {
    return new Promise((resolve) => {
      const overlay = el(`
        <div class="modal-overlay" role="dialog" aria-modal="true">
          <div class="modal-box">
            <h4>${title}</h4>
            <p>${message}</p>
            <div class="modal-actions">
              <button type="button" class="btn btn-ghost" data-cancel>${cancelText}</button>
              <button type="button" class="btn btn-danger" data-confirm>${confirmText}</button>
            </div>
          </div>
        </div>`);

      const close = (result) => {
        overlay.remove();
        resolve(result);
      };
      overlay.addEventListener("click", (event) => {
        if (event.target === overlay) close(false);
      });
      overlay.querySelector("[data-cancel]").addEventListener("click", () => close(false));
      overlay.querySelector("[data-confirm]").addEventListener("click", () => close(true));
      document.addEventListener("keydown", function onKey(event) {
        if (event.key === "Escape") {
          document.removeEventListener("keydown", onKey);
          close(false);
        }
      });
      document.body.appendChild(overlay);
      overlay.querySelector("[data-confirm]").focus();
    });
  }

  function formatMoney(amount, symbol = "₹") {
    const value = Number(amount) || 0;
    return `${symbol}${value.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  function escapeHtml(value) {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return String(value === null || value === undefined ? "" : value).replace(/[&<>"']/g, (ch) => map[ch]);
  }

  function formatDate(value) {
    const date = value ? new Date(value) : new Date();
    return date.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric" });
  }

  const UI = { toast, confirmDialog, formatMoney, formatDate, escapeHtml, ICONS, NAV };

  window.UI = UI;

  document.addEventListener("DOMContentLoaded", () => {
    const page = document.body.dataset.page;
    if (!page) return;

    document.body.insertAdjacentHTML("afterbegin", '<div class="sidebar-overlay"></div>');
    document.body.insertAdjacentHTML("afterbegin", renderTopbar(page));
    document.body.insertAdjacentHTML("afterbegin", renderSidebar(page));

    const todayLabel = document.getElementById("todayLabel");
    if (todayLabel) todayLabel.textContent = formatDate(new Date());

    document.querySelectorAll("[data-icon]").forEach((node) => {
      const icon = ICONS[node.dataset.icon];
      if (icon) node.innerHTML = icon;
    });

    wireNavigation();
    checkApiStatus();
  });
})();
