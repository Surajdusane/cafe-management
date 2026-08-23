(function () {
  "use strict";

  const API_URL = "/api/bills";

  let bills = [];
  let searchTimer = null;
  let payingBillId = null;
  let cafeCurrency = "₹";

  let tableBody;
  let searchInput;
  let paymentFilter;
  let methodFilter;
  let payModal;
  let receiptModal;

  const money = (amount, symbol) => UI.formatMoney(amount, symbol || "₹");
  const fmtDateTime = (value) => {
    const date = new Date(value);
    return date.toLocaleString("en-IN", {
      day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
    });
  };

  function skeletonRows() {
    const rows = [];
    for (let i = 0; i < 4; i += 1) {
      rows.push(
        `<tr class="skeleton-row">${["22%", "18%", "18%", "12%", "12%", "12%", "16%", "14%", "14%", "24%"]
          .map((w) => `<td><div class="skeleton-line" style="width:${w}"></div></td>`)
          .join("")}</tr>`
      );
    }
    tableBody.innerHTML = rows.join("");
  }

  function emptyRow(filtered) {
    return `
      <tr class="empty-row"><td colspan="10"><div class="empty-state">
        <div class="es-icon">${UI.ICONS.billing}</div>
        <h4>No bills found</h4>
        <p>${filtered
          ? "Nothing matches the current filters."
          : "Bills appear here automatically when orders are placed on the Orders page."}</p>
      </div></td></tr>`;
  }

  function renderSummary(summary) {
    document.getElementById("statBilled").textContent = money(summary.billed_total);
    document.getElementById("statCollected").textContent = money(summary.collected_total);
    document.getElementById("statOutstanding").textContent = money(summary.outstanding_total);
  }

  function render() {
    if (bills.length === 0) {
      const filtered =
        Boolean(searchInput.value.trim()) ||
        paymentFilter.value !== "" ||
        methodFilter.value !== "";
      tableBody.innerHTML = emptyRow(filtered);
      return;
    }

    tableBody.innerHTML = bills
      .map((bill) => {
        const orderDesc =
          bill.order_type === "Dine-in"
            ? `Dine-in <span class="table-no">T${bill.table_number}</span>`
            : "Takeaway";
        const statusBadge =
          bill.payment_status === "Paid"
            ? '<span class="badge badge-pay-paid">Paid</span>'
            : '<span class="badge badge-pay-unpaid">Unpaid</span>';
        const payButton =
          bill.payment_status === "Unpaid"
            ? `<button type="button" class="btn btn-primary btn-row" data-action="pay" ${bill.status === "Cancelled" ? "disabled title='Cancelled order'" : ""}>Mark paid</button>`
            : "";

        return `
        <tr data-id="${bill.id}">
          <td><strong>${UI.escapeHtml(bill.order_number)}</strong></td>
          <td>${fmtDateTime(bill.created_at)}</td>
          <td><span class="type-chip">${orderDesc}</span></td>
          <td class="num">${money(bill.subtotal)}</td>
          <td class="num">− ${money(bill.discount_amount)}</td>
          <td class="num">${money(bill.tax_amount)} <span style="font-size:11px;color:var(--muted)">(${bill.tax_percent}%)</span></td>
          <td class="num"><strong>${money(bill.total)}</strong></td>
          <td>${bill.payment_method || "—"}</td>
          <td>${statusBadge}${bill.status === "Cancelled" ? ' <span class="badge badge-cancelled">Cancelled</span>' : ""}</td>
          <td><div class="row-actions">
            <button type="button" class="btn btn-ghost btn-row" data-action="receipt">Receipt</button>
            ${payButton}
          </div></td>
        </tr>`;
      })
      .join("");
  }

  async function loadBills() {
    skeletonRows();
    try {
      const params = new URLSearchParams();
      const term = searchInput.value.trim();
      if (term) params.set("search", term);
      if (paymentFilter.value) params.set("payment_status", paymentFilter.value);
      if (methodFilter.value) params.set("payment_method", methodFilter.value);
      const query = params.toString();
      const response = await API.get(query ? `${API_URL}?${query}` : API_URL);
      bills = response.data.items;
      renderSummary(response.data.summary);
      render();
    } catch (error) {
      tableBody.innerHTML = `
        <tr class="empty-row"><td colspan="10"><div class="empty-state">
          <div class="es-icon">${UI.ICONS.billing}</div>
          <h4>Could not load bills</h4><p>${UI.escapeHtml(error.message)}</p>
        </div></td></tr>`;
    }
  }

  // ------------------------------------------------------------------
  // Receipt
  // ------------------------------------------------------------------

  async function showReceipt(orderId) {
    try {
      const response = await API.get(`${API_URL}/${orderId}`);
      renderReceipt(response.data.bill, response.data.cafe);
      receiptModal.hidden = false;
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  function receiptLines(bill) {
    return bill.items
      .map(
        (line) => `
        <tr>
          <td class="r-item">${UI.escapeHtml(line.item_name)}<span>× ${line.quantity} @ ${money(line.unit_price, cafeCurrency)}</span></td>
          <td class="r-amt">${money(line.line_total, cafeCurrency)}</td>
        </tr>`
      )
      .join("");
  }

  function renderReceipt(bill, cafe) {
    cafeCurrency = cafe.currency || "₹";
    const place = bill.order_type === "Dine-in" ? `Dine-in · Table ${bill.table_number}` : "Takeaway";

    document.getElementById("receiptPaper").innerHTML = `
      <div class="receipt-head">
        <div class="r-name">${UI.escapeHtml(cafe.cafe_name)}</div>
        ${cafe.address ? `<div class="r-sub">${UI.escapeHtml(cafe.address)}</div>` : ""}
        ${cafe.phone ? `<div class="r-sub">Phone: ${UI.escapeHtml(cafe.phone)}</div>` : ""}
      </div>
      <div class="receipt-meta">
        <span>Bill №: <strong>${UI.escapeHtml(bill.order_number)}</strong></span>
        <span>${fmtDateTime(bill.paid_at || bill.created_at)}</span>
      </div>
      <div class="receipt-meta" style="border:none;padding-top:0;margin-top:0">
        <span>${place}</span>
        <span>${bill.payment_status === "Paid" ? `Paid · ${bill.payment_method}` : "UNPAID"}</span>
      </div>
      <table class="r-lines">
        ${receiptLines(bill)}
      </table>
      <div class="r-totals">
        <div class="totals-row"><span>Subtotal</span><strong>${money(bill.subtotal, cafeCurrency)}</strong></div>
        <div class="totals-row"><span>Discount</span><strong>− ${money(bill.discount_amount, cafeCurrency)}</strong></div>
        <div class="totals-row"><span>Tax @ ${bill.tax_percent}%</span><strong>${money(bill.tax_amount, cafeCurrency)}</strong></div>
        <div class="totals-row grand"><span>TOTAL</span><strong>${money(bill.total, cafeCurrency)}</strong></div>
      </div>
      <div class="r-footer">${cafe.receipt_footer ? UI.escapeHtml(cafe.receipt_footer) : "Thank you for visiting!"}</div>`;
  }

  // ------------------------------------------------------------------
  // Payment
  // ------------------------------------------------------------------

  function openPayModal(row) {
    const bill = bills.find((b) => b.id === Number(row.dataset.id));
    if (!bill) return;
    payingBillId = bill.id;
    document.getElementById("paySubtitle").innerHTML =
      `Collect <strong>${money(bill.total)}</strong> for bill <strong>${UI.escapeHtml(bill.order_number)}</strong>. Choose the payment method:`;
    payModal.hidden = false;
  }

  async function recordPayment(method) {
    try {
      await API.post(`${API_URL}/${payingBillId}/pay`, { payment_method: method });
      UI.toast(`Payment via ${method} recorded.`, "success");
      payModal.hidden = true;
      await loadBills();
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadBills, 300);
  }

  document.addEventListener("DOMContentLoaded", () => {
    tableBody = document.getElementById("billTableBody");
    searchInput = document.getElementById("billSearch");
    paymentFilter = document.getElementById("billPaymentFilter");
    methodFilter = document.getElementById("billMethodFilter");
    payModal = document.getElementById("payModal");
    receiptModal = document.getElementById("receiptModal");

    loadBills();

    searchInput.addEventListener("input", debounceSearch);
    paymentFilter.addEventListener("change", loadBills);
    methodFilter.addEventListener("change", loadBills);

    tableBody.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const row = button.closest("tr[data-id]");
      if (button.dataset.action === "receipt") showReceipt(Number(row.dataset.id));
      else if (button.dataset.action === "pay") openPayModal(row);
    });

    payModal.querySelectorAll("[data-method]").forEach((button) => {
      button.addEventListener("click", () => recordPayment(button.dataset.method));
    });

    [payModal, receiptModal].forEach((overlay) => {
      overlay.querySelector("[data-close-modal]").addEventListener("click", () => {
        overlay.hidden = true;
      });
      overlay.addEventListener("click", (event) => {
        if (event.target === overlay) overlay.hidden = true;
      });
    });

    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      if (!payModal.hidden) payModal.hidden = true;
      if (!receiptModal.hidden) receiptModal.hidden = true;
    });

    document.getElementById("printReceiptBtn").addEventListener("click", () => window.print());
  });
})();
