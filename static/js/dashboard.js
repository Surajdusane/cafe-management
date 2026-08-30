(function () {
  "use strict";

  const STATUS_BADGE = {
    Pending: "badge-pending",
    Preparing: "badge-preparing",
    Ready: "badge-ready",
    Completed: "badge-completed",
    Cancelled: "badge-cancelled"
  };

  const money = (amount, currency) => UI.formatMoney(amount, currency || "₹");
  const fmtDateTime = (value) => {
    const date = new Date(value);
    return date.toLocaleString("en-IN", {
      day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
    });
  };

  // ---------- plain-JS bar chart (same style as the Reports page) ----------

  function drawBarChart(canvasId, labels, amounts) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const parent = canvas.parentElement;
    parent.querySelector(".chart-empty")?.remove();

    const dpr = window.devicePixelRatio || 1;
    const width = Math.max(canvas.getBoundingClientRect().width, 320);
    const height = 220;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    if (!amounts.length || amounts.every((a) => a === 0)) {
      parent.insertAdjacentHTML("beforeend",
        '<div class="chart-empty">No paid sales in the last 7 days yet — the bars fill in as orders are paid.</div>');
      canvas.style.display = "none";
      return;
    }
    canvas.style.display = "block";

    const max = Math.max(...amounts, 1);
    const padL = 52, padR = 12, padT = 14, padB = 30;
    const chartW = width - padL - padR;
    const chartH = height - padT - padB;
    const barW = Math.max(6, (chartW / amounts.length) * 0.6);

    ctx.font = "11px Inter, sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.strokeStyle = "#e9e1d4";
    ctx.fillStyle = "#8b7d6e";
    for (let i = 0; i <= 4; i += 1) {
      const gy = padT + chartH - (chartH * (i / 4));
      ctx.beginPath();
      ctx.moveTo(padL, gy);
      ctx.lineTo(width - padR, gy);
      ctx.stroke();
      ctx.fillText(String(Math.round((max * i) / 4)), padL - 6, gy);
    }

    amounts.forEach((amount, i) => {
      const barH = (amount / max) * chartH;
      const x = padL + (chartW / amounts.length) * i + (chartW / amounts.length - barW) / 2;
      const y = padT + chartH - barH;
      ctx.fillStyle = amount > 0 ? "#b96a32" : "#e9e1d4";
      ctx.fillRect(x, y, barW, barH);
    });

    ctx.textAlign = "center";
    labels.forEach((label, i) => {
      const x = padL + (chartW / amounts.length) * i + (chartW / amounts.length) / 2;
      ctx.fillText(label, x, height - 10);
    });
  }

  // ---------- renderers ----------

  function renderStats(stats, currency) {
    const values = {
      today_sales: money(stats.today_sales, currency),
      today_orders: String(stats.today_orders),
      pending_orders: String(stats.pending_orders),
      unpaid_bills: money(stats.unpaid_bills, currency),
      menu_items: String(stats.menu_items),
      low_stock: String(stats.low_stock),
      employees: String(stats.employees),
      monthly_expenses: money(stats.monthly_expenses, currency)
    };
    document.querySelectorAll(".stat-value[data-stat]").forEach((node) => {
      const value = values[node.dataset.stat];
      if (value !== undefined) node.textContent = value;
      node.classList.remove("pending");
      node.classList.add("is-set");
    });
  }

  function renderTopSellers(items) {
    const box = document.getElementById("topSellers");
    if (!items.length) {
      box.innerHTML = `
        <div class="empty-state compact">
          <div class="es-icon">${UI.ICONS.receipt}</div>
          <h4>No sales yet</h4>
          <p>Top sellers appear here once orders start rolling in.</p>
        </div>`;
      return;
    }
    box.innerHTML = items
      .map((item, index) => `
        <div class="seller-row">
          <span class="seller-rank">${index + 1}</span>
          <span class="seller-name">${UI.escapeHtml(item.name)}</span>
          <span class="seller-qty">× ${item.quantity}</span>
        </div>`)
      .join("");
  }

  function renderRecentOrders(orders, currency) {
    const body = document.getElementById("recentOrdersBody");
    if (!orders.length) {
      body.innerHTML = `
        <tr class="empty-row"><td colspan="6"><div class="empty-state">
          <div class="es-icon">${UI.ICONS.receipt}</div>
          <h4>No orders yet</h4>
          <p>Orders you take will show up here. Ring in the first one from the Orders page.</p>
        </div></td></tr>`;
      return;
    }
    body.innerHTML = orders
      .map((order) => {
        const place = order.order_type === "Dine-in"
          ? `Dine-in <span class="table-no">T${order.table_number}</span>`
          : "Takeaway";
        const payment = order.payment_status === "Paid"
          ? `<span class="badge badge-pay-paid">Paid${order.payment_method ? ` · ${order.payment_method}` : ""}</span>`
          : '<span class="badge badge-pay-unpaid">Unpaid</span>';
        return `
          <tr>
            <td><strong>${UI.escapeHtml(order.order_number)}</strong></td>
            <td><span class="type-chip">${place}</span></td>
            <td class="num"><strong>${money(order.total, currency)}</strong></td>
            <td><span class="badge ${STATUS_BADGE[order.status] || ""}">${order.status}</span></td>
            <td>${payment}</td>
            <td>${fmtDateTime(order.created_at)}</td>
          </tr>`;
      })
      .join("");
  }

  // ---------- load ----------

  function showError(message) {
    document.querySelectorAll("#statGrid, #trendCard, #topCard, #recentOrdersCard")
      .forEach((node) => node.classList.add("is-dimmed"));
    const errorPanel = document.getElementById("dashError");
    if (!errorPanel) return;
    errorPanel.hidden = false;
    errorPanel.classList.add("visible");
    errorPanel.innerHTML = `
      <div class="es-icon">${UI.ICONS.receipt}</div>
      <h4>Could not load the dashboard</h4>
      <p>${UI.escapeHtml(message)}</p>
      <button type="button" class="btn btn-primary" id="retryBtn">Try again</button>`;
    document.getElementById("retryBtn").addEventListener("click", loadDashboard);
  }

  async function loadDashboard() {
    const errorPanel = document.getElementById("dashError");
    try {
      const response = await API.get("/api/dashboard");
      const data = response.data;

      const subtitle = document.querySelector("[data-subtitle]");
      if (subtitle) {
        subtitle.textContent = `Here's how ${data.cafe.name} is doing today.`;
      }
      renderStats(data.stats, data.cafe.currency);
      renderTopSellers(data.top_items);
      renderRecentOrders(data.recent_orders, data.cafe.currency);
      drawBarChart("trendChart", data.sales_trend.labels, data.sales_trend.amounts);

      errorPanel.hidden = true;
      errorPanel.classList.remove("visible");
      document.querySelectorAll("#statGrid, #trendCard, #topCard, #recentOrdersCard")
        .forEach((node) => node.classList.remove("is-dimmed"));
    } catch (error) {
      showError(error.message);
    }
  }

  window.addEventListener("error", (event) => {
    showError(event.message || "Unexpected JavaScript error on this page.");
  });

  document.addEventListener("DOMContentLoaded", loadDashboard);
})();