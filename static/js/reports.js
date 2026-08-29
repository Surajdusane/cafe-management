(function () {
  "use strict";

  const REPORTS_URL = "/api/reports";

  const MODE_OPTIONS = {
    sales: [
      { value: "daily", label: "Daily" },
      { value: "weekly", label: "Weekly (last 7 days)" },
      { value: "monthly", label: "Monthly" }
    ],
    orders: [],
    inventory: [
      { value: "current", label: "Current stock" },
      { value: "low", label: "Low stock only" },
      { value: "movements", label: "Stock movements" }
    ],
    purchases: [
      { value: "date", label: "By date" },
      { value: "supplier", label: "By supplier" }
    ],
    salaries: [],
    expenses: [
      { value: "category", label: "By category" },
      { value: "date", label: "By date" }
    ],
    profit: []
  };

  const REPORT_LABELS = {
    sales: "Sales",
    orders: "Orders",
    inventory: "Inventory",
    purchases: "Purchases",
    salaries: "Salaries",
    expenses: "Expenses",
    profit: "Profit"
  };

  let activeReport = "sales";

  let startDate;
  let endDate;
  let modeSelect;
  let reportLabel;
  let tabs;

  function paramsFor(report) {
    const params = new URLSearchParams();
    if (startDate.value) params.set("start_date", startDate.value);
    if (endDate.value) params.set("end_date", endDate.value);
    const mode = modeSelect.value;
    if (report === "sales" && mode) params.set("period", mode);
    if (report === "inventory" && mode) params.set("report_type", mode);
    if ((report === "purchases" || report === "expenses") && mode) params.set("group_by", mode);
    return params.toString();
  }

  async function fetchReport(report) {
    const query = paramsFor(report);
    const response = await API.get(`${REPORTS_URL}/${report}${query ? `?${query}` : ""}`);
    return response.data;
  }

  // ---------- renderers ----------

  function summaryCard(label, value, { total = false } = {}) {
    return `<div class="mini ${total ? "is-total" : ""}"><dt>${label}</dt><dd>${value}</dd></div>`;
  }

  function dayLabel(isoDate) {
    return new Date(`${isoDate}T00:00:00`).toLocaleDateString("en-IN",
      { day: "numeric", month: "short", year: "numeric" });
  }

  function setEmpty(target, message) {
    target.innerHTML = `<tr class="empty-row"><td colspan="9"><div class="empty-state"><h4>${message}</h4></div></td></tr>`;
  }

  function renderSales(data) {
    document.getElementById("salesPeriodBadge").textContent = data.period_label;
    const s = data.summary;
    document.getElementById("salesSummary").innerHTML =
      summaryCard("Sales total", UI.formatMoney(s.sales_total), { total: true }) +
      summaryCard("Paid orders", String(s.orders)) +
      summaryCard("Average order", UI.formatMoney(s.avg_order));

    drawBarChart("salesChart", data.series.labels, data.series.amounts);

    const body = document.querySelector("#salesTable tbody");
    if (!data.series.labels.length) {
      setEmpty(body, "No paid sales in this period yet.");
    } else {
      body.innerHTML = data.series.labels
        .map((label, i) => `
          <tr>
            <td>${UI.escapeHtml(label)}</td>
            <td class="num">${data.series.orders[i]}</td>
            <td class="num"><strong>${UI.formatMoney(data.series.amounts[i])}</strong></td>
          </tr>`)
        .join("");
    }
  }

  function renderOrders(data) {
    const s = data.summary;
    document.getElementById("ordersSummary").innerHTML =
      summaryCard("Orders", String(s.count)) +
      summaryCard("Total value", UI.formatMoney(s.total), { total: true });

    const statusBody = document.querySelector("#ordersStatusTable tbody");
    if (!data.by_status.length) {
      setEmpty(statusBody, "No orders in this period.");
    } else {
      statusBody.innerHTML = data.by_status
        .map((r) => `
          <tr>
            <td><span class="badge badge-muted">${UI.escapeHtml(r.status)}</span></td>
            <td class="num">${r.count}</td>
            <td class="num"><strong>${UI.formatMoney(r.total)}</strong></td>
          </tr>`)
        .join("");
    }

    const dateBody = document.querySelector("#ordersDateTable tbody");
    if (!data.by_date.length) {
      setEmpty(dateBody, "No orders in this period.");
    } else {
      dateBody.innerHTML = data.by_date
        .map((r) => `
          <tr>
            <td>${dayLabel(r.date)}</td>
            <td class="num">${r.count}</td>
            <td class="num"><strong>${UI.formatMoney(r.total)}</strong></td>
          </tr>`)
        .join("");
    }
  }

  function renderInventory(data) {
    const s = data.summary;
    document.getElementById("inventorySummary").innerHTML =
      summaryCard("Active materials", String(s.active_items)) +
      summaryCard("Low stock", String(s.low_stock)) +
      summaryCard("Stock value", UI.formatMoney(s.total_value), { total: true });

    const body = document.querySelector("#inventoryTable tbody");
    if (!data.items.length) {
      setEmpty(body, "No materials matched this report.");
      return;
    }

    const isMovements = data.report_type === "movements";
    if (isMovements) {
      const thead = document.querySelector("#inventoryTable thead");
      thead.innerHTML = "<tr><th>Material</th><th>Type</th><th class='num'>Qty</th><th class='num'>Balance</th><th>Note</th><th>Date</th><th></th></tr>";
      body.innerHTML = data.items
        .map((m) => `
          <tr>
            <td><strong>${UI.escapeHtml(m.item_name)}</strong></td>
            <td>${typeBadge(m.transaction_type)}</td>
            <td class="num">${m.quantity}</td>
            <td class="num"><strong>${m.balance_after}</strong></td>
            <td>${m.note ? UI.escapeHtml(m.note) : "—"}</td>
            <td>${UI.formatDate(m.created_at)}</td>
            <td></td>
          </tr>`)
        .join("");
    } else {
      const thead = document.querySelector("#inventoryTable thead");
      thead.innerHTML = "<tr><th>Name</th><th>Category</th><th class='num'>Stock</th><th class='num'>Min</th><th class='num'>Cost/unit</th><th>Status</th><th class='num'>Value</th></tr>";
      body.innerHTML = data.items
        .map((m) => {
          const stockBadge = m.is_low_stock
            ? '<span class="badge badge-low">Low stock</span>'
            : '<span class="badge badge-ok">In stock</span>';
          return `
            <tr>
              <td><strong>${UI.escapeHtml(m.name)}</strong></td>
              <td>${UI.escapeHtml(m.category)}</td>
              <td class="num">${m.current_quantity} ${UI.escapeHtml(m.unit)}</td>
              <td class="num">${m.minimum_stock}</td>
              <td class="num">${UI.formatMoney(m.purchase_price)}</td>
              <td>${stockBadge}</td>
              <td class="num">${UI.formatMoney(m.current_quantity * m.purchase_price)}</td>
            </tr>`;
        })
        .join("");
    }
  }

  function typeBadge(type) {
    const cls = type === "Stock In" ? "badge-ok" : type === "Stock Out" ? "badge-low" : "badge-muted";
    return `<span class="badge ${cls}">${UI.escapeHtml(type)}</span>`;
  }

  function renderPurchases(data) {
    renderGrouped("purchases", data, "Purchases", (r) =>
      r.name ? UI.escapeHtml(r.name) : dayLabel(r.date));
  }

  function renderExpenses(data) {
    renderGrouped("expenses", data, "Entries", (r) =>
      r.category ? UI.escapeHtml(r.category) : dayLabel(r.date));
  }

  function renderGrouped(id, data, countLabel, nameFn) {
    const s = data.summary;
    document.getElementById(`${id}Summary`).innerHTML =
      summaryCard("Record count", String(s.count)) +
      summaryCard("Total", UI.formatMoney(s.total), { total: true });

    const body = document.querySelector(`#${id}Table tbody`);
    if (!data.items.length) {
      setEmpty(body, "No records in this period.");
      return;
    }
    body.innerHTML = data.items
      .map((r) => `
        <tr>
          <td><strong>${nameFn(r)}</strong></td>
          <td class="num">${r.count}</td>
          <td class="num"><strong>${UI.formatMoney(r.total)}</strong></td>
        </tr>`)
      .join("");
  }

  function renderSalaries(data) {
    const s = data.summary;
    document.getElementById("salariesSummary").innerHTML =
      summaryCard("Records", String(s.records)) +
      summaryCard("Total paid", UI.formatMoney(s.total), { total: true });

    const body = document.querySelector("#salariesTable tbody");
    if (!data.items.length) {
      setEmpty(body, "No salary records yet.");
      return;
    }
    body.innerHTML = data.items
      .map((r) => `
        <tr>
          <td><strong>${UI.escapeHtml(r.month)}</strong></td>
          <td class="num">${r.count}</td>
          <td class="num"><strong>${UI.formatMoney(r.total)}</strong></td>
        </tr>`)
      .join("");
  }

  function renderProfit(data) {
    const c = data.components;
    const profit = data.estimated_profit;
    const positive = profit >= 0;
    document.getElementById("profitGrid").innerHTML = `
      <div class="profit-cell sales"><dt>Sales</dt><dd>${UI.formatMoney(c.sales)}</dd></div>
      <div class="profit-cell out"><dt>− Purchases</dt><dd>${UI.formatMoney(c.purchases)}</dd></div>
      <div class="profit-cell out"><dt>− Salaries</dt><dd>${UI.formatMoney(c.salaries)}</dd></div>
      <div class="profit-cell out"><dt>− Expenses</dt><dd>${UI.formatMoney(c.expenses)}</dd></div>
      <div class="profit-cell result ${positive ? "positive" : ""}" style="grid-column: span 4">
        <dt>Estimated profit</dt>
        <dd>${positive ? "+" : ""}${UI.formatMoney(profit)}</dd>
        <span class="sub">Sales − Purchases − Salaries − Expenses (month-based salary estimate)</span>
      </div>`;
  }

  const RENDERERS = {
    sales: renderSales,
    orders: renderOrders,
    inventory: renderInventory,
    purchases: renderPurchases,
    salaries: renderSalaries,
    expenses: renderExpenses,
    profit: renderProfit
  };

  // ---------- plain-JS bar chart ----------

  function drawBarChart(canvasId, labels, amounts) {
    const canvas = document.getElementById(canvasId);
    const parent = canvas.parentElement;
    parent.querySelector(".chart-empty")?.remove();

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(rect.width, 320);
    const height = 220;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    if (!amounts.length) {
      parent.insertAdjacentHTML("beforeend",
        '<div class="chart-empty">No data to chart yet — record some paid orders.</div>');
      canvas.style.display = "none";
      return;
    }
    canvas.style.display = "block";

    const max = Math.max(...amounts, 1);
    const padL = 52, padR = 12, padT = 14, padB = 30;
    const chartW = width - padL - padR;
    const chartH = height - padT - padB;
    const barW = Math.max(6, (chartW / amounts.length) * 0.6);

    // y-axis gridlines
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
      const val = Math.round((max * i) / 4);
      ctx.fillText(String(val), padL - 6, gy);
    }

    // bars
    amounts.forEach((amount, i) => {
      const barH = (amount / max) * chartH;
      const x = padL + (chartW / amounts.length) * i + (chartW / amounts.length - barW) / 2;
      const y = padT + chartH - barH;
      ctx.fillStyle = amount > 0 ? "#b96a32" : "#e9e1d4";
      ctx.fillRect(x, y, barW, barH);
    });

    // x labels
    ctx.textAlign = "center";
    ctx.fillStyle = "#8b7d6e";
    labels.forEach((label, i) => {
      const x = padL + (chartW / amounts.length) * i + (chartW / amounts.length) / 2;
      ctx.fillText(label, x, height - 10);
    });
  }

  // ---------- loading / error ----------

  function sectionEl(report) {
    return document.getElementById(`report-${report}`);
  }

  async function loadActive() {
    const render = RENDERERS[activeReport];
    const target = sectionEl(activeReport);
    target.querySelectorAll("tbody").forEach((tb) => {
      tb.innerHTML = '<tr class="skeleton-row"></tr>';
    });
    try {
      const data = await fetchReport(activeReport);
      render(data);
    } catch (error) {
      target.querySelector("tbody") &&
        setExpandedError(target, error.message);
      if (!target.querySelector("tbody")) {
        const body = target.querySelector(".profit-grid");
        if (body) body.innerHTML = `<p class="chart-empty">${UI.escapeHtml(error.message)}</p>`;
      }
    }
  }

  function setExpandedError(target, message) {
    target.querySelectorAll("tbody").forEach((tb) => {
      tb.innerHTML = `<tr class="empty-row"><td colspan="9"><div class="empty-state"><h4>Could not load report</h4><p>${UI.escapeHtml(message)}</p></div></td></tr>`;
    });
  }

  function setModeOptions(report) {
    const options = MODE_OPTIONS[report] || [];
    modeSelect.innerHTML = '<option value="">' +
      (options.length ? "Report options…" : "No extra options") + '</option>' +
      options.map((o) => `<option value="${o.value}">${o.label}</option>`).join("");
    modeSelect.disabled = options.length === 0;
  }

  function switchReport(report) {
    activeReport = report;
    tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.report === report));
    document.querySelectorAll(".report-section").forEach((sec) => {
      sec.hidden = sec.dataset.section !== report;
    });
    reportLabel.textContent = REPORT_LABELS[report] + " report";
    setModeOptions(report);
    loadActive();
  }

  document.addEventListener("DOMContentLoaded", () => {
    startDate = document.getElementById("startDate");
    endDate = document.getElementById("endDate");
    modeSelect = document.getElementById("modeSelect");
    reportLabel = document.querySelector("[data-report-label]");
    tabs = Array.from(document.querySelectorAll("#reportTabs .tab"));

    tabs.forEach((tab) =>
      tab.addEventListener("click", () => switchReport(tab.dataset.report)));

    document.getElementById("reportFilterForm").addEventListener("submit", (event) => {
      event.preventDefault();
      loadActive();
    });

    document.getElementById("resetFiltersBtn").addEventListener("click", () => {
      startDate.value = "";
      endDate.value = "";
      loadActive();
    });

    document.getElementById("printBtn").addEventListener("click", () => window.print());

    switchReport("sales");
  });
})();
