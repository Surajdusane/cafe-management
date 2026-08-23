(function () {
  "use strict";

  const API_URL = "/api/orders";
  const STATUS_BADGE = {
    Pending: "badge-pending",
    Preparing: "badge-preparing",
    Ready: "badge-ready",
    Completed: "badge-completed",
    Cancelled: "badge-cancelled"
  };

  let orders = [];
  let menuItems = [];
  let settings = { tax_percent: 0, currency: "₹" };
  let cart = [];
  let searchTimer = null;
  let detailId = null;

  let tableBody;
  let searchInput;
  let statusFilter;
  let typeFilter;
  let paymentFilter;
  let modal;
  let form;
  let saveBtn;
  let itemSelect;
  let itemQty;
  let discountInput;
  let tableNumberInput;
  let tableField;
  let cartBody;
  let cartEmpty;

  const byName = (name) => form.elements.namedItem(name);
  const money = (amount) => UI.formatMoney(amount, settings.currency || "₹");
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
        `<tr class="skeleton-row">${["30%", "20%", "10%", "15%", "15%", "18%", "20%", "25%"]
          .map((w) => `<td><div class="skeleton-line" style="width:${w}"></div></td>`)
          .join("")}</tr>`
      );
    }
    tableBody.innerHTML = rows.join("");
  }

  function emptyRow(filtered) {
    return `
      <tr class="empty-row"><td colspan="8"><div class="empty-state">
        <div class="es-icon">${UI.ICONS.receipt}</div>
        <h4>No orders found</h4>
        <p>${filtered
          ? "Nothing matches the current filters. Adjust them or place a new order."
          : 'Take the first order — click "+ New order".'}</p>
      </div></td></tr>`;
  }

  function render() {
    if (orders.length === 0) {
      const filtered =
        Boolean(searchInput.value.trim()) ||
        statusFilter.value !== "" ||
        typeFilter.value !== "" ||
        paymentFilter.value !== "";
      tableBody.innerHTML = emptyRow(filtered);
      return;
    }

    tableBody.innerHTML = orders
      .map((order) => {
        const place = order.order_type === "Dine-in"
          ? `Dine-in <span class="table-no">T${order.table_number}</span>`
          : "Takeaway";
        const payment = order.payment_status === "Paid"
          ? `<span class="badge badge-pay-paid">Paid · ${order.payment_method}</span>`
          : '<span class="badge badge-pay-unpaid">Unpaid</span>';
        const cancellable = !["Completed", "Cancelled"].includes(order.status);
        const actions = [
          '<button type="button" class="btn btn-ghost btn-row" data-action="view">View</button>',
          cancellable
            ? '<button type="button" class="btn btn-ghost btn-row" data-action="cancel">Cancel</button>'
            : "",
          order.status === "Cancelled"
            ? '<button type="button" class="btn btn-ghost btn-row" data-action="delete">Delete</button>'
            : ""
        ].join("");

        return `
        <tr data-id="${order.id}">
          <td><strong>${UI.escapeHtml(order.order_number)}</strong></td>
          <td><span class="type-chip">${place}</span></td>
          <td class="num">${order.item_count}</td>
          <td class="num"><strong>${money(order.total)}</strong></td>
          <td><span class="badge ${STATUS_BADGE[order.status] || ""}">${order.status}</span></td>
          <td>${payment}</td>
          <td>${fmtDateTime(order.created_at)}</td>
          <td><div class="row-actions">${actions}</div></td>
        </tr>`;
      })
      .join("");
  }

  async function loadOrders() {
    skeletonRows();
    try {
      const params = new URLSearchParams();
      const term = searchInput.value.trim();
      if (term) params.set("search", term);
      if (statusFilter.value) params.set("order_status", statusFilter.value);
      if (typeFilter.value) params.set("order_type", typeFilter.value);
      if (paymentFilter.value) params.set("payment_status", paymentFilter.value);
      const query = params.toString();
      const response = await API.get(query ? `${API_URL}?${query}` : API_URL);
      orders = response.data.items;
      render();
    } catch (error) {
      tableBody.innerHTML = `
        <tr class="empty-row"><td colspan="8"><div class="empty-state">
          <div class="es-icon">${UI.ICONS.receipt}</div>
          <h4>Could not load orders</h4><p>${UI.escapeHtml(error.message)}</p>
        </div></td></tr>`;
    }
  }

  async function loadMenuItems() {
    try {
      const response = await API.get("/api/menu/items?available_only=true");
      menuItems = response.data.items;
    } catch (error) {
      menuItems = [];
    }
    itemSelect.innerHTML = '<option value="">Choose a dish…</option>';
    menuItems.forEach((item) => {
      const option = document.createElement("option");
      option.value = String(item.id);
      option.textContent = `${item.name} — ${money(item.price)}`;
      itemSelect.appendChild(option);
    });
  }

  async function loadSettings() {
    try {
      const response = await API.get("/api/settings");
      settings = response.data;
    } catch (error) {
      settings = { tax_percent: 0, currency: "₹" };
    }
    document.getElementById("tTaxPercent").textContent = Number(settings.tax_percent).toString();
  }

  // ------------------------------------------------------------------
  // New-order modal
  // ------------------------------------------------------------------

  function openModal() {
    if (menuItems.length === 0) {
      UI.toast("No available dishes. Add or restock menu items first.", "warning");
      return;
    }
    cart = [];
    form.reset();
    byName("order_type").value = "Dine-in";
    itemQty.value = "1";
    syncTypeToggle();
    renderCart();
    Validator.clearFieldError(tableNumberInput);
    Validator.clearFieldError(discountInput);
    modal.hidden = false;
    itemSelect.focus();
  }

  function closeModal() {
    modal.hidden = true;
  }

  function syncTypeToggle() {
    const isDineIn = byName("order_type").value === "Dine-in";
    tableField.style.display = isDineIn ? "" : "none";
    if (!isDineIn) {
      tableNumberInput.value = "";
      Validator.clearFieldError(tableNumberInput);
    } else {
      tableNumberInput.focus();
    }
  }

  function addToCart() {
    const id = Number(itemSelect.value);
    if (!id) {
      UI.toast("Choose a dish first.", "warning");
      return;
    }
    let quantity = parseInt(itemQty.value, 10);
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 999) {
      UI.toast("Quantity must be a whole number between 1 and 999.", "error");
      return;
    }
    const item = menuItems.find((m) => m.id === id);
    const line = cart.find((l) => l.menu_item_id === id);
    if (line) {
      line.quantity += quantity; // same dish twice → one line with more units
      if (line.quantity > 999) line.quantity = 999;
    } else {
      cart.push({ menu_item_id: id, name: item.name, unit_price: item.price, quantity });
    }
    itemQty.value = "1";
    renderCart();
  }

  function renderCart() {
    cartEmpty.hidden = cart.length > 0;
    cartBody.innerHTML = cart
      .map(
        (line) => `
        <tr data-id="${line.menu_item_id}">
          <td>${UI.escapeHtml(line.name)}</td>
          <td class="num">${money(line.unit_price)}</td>
          <td style="text-align:center">
            <span class="qty-stepper">
              <button type="button" data-step="-1" aria-label="Decrease quantity">−</button>
              <span class="qty-value">${line.quantity}</span>
              <button type="button" data-step="1" aria-label="Increase quantity">+</button>
            </span>
          </td>
          <td class="num"><strong>${money(line.unit_price * line.quantity)}</strong></td>
          <td class="num"><button type="button" class="cart-remove" data-remove>Remove</button></td>
        </tr>`
      )
      .join("");
    updateTotals();
  }

  function cartSubtotal() {
    return round2(cart.reduce((sum, l) => sum + l.unit_price * l.quantity, 0));
  }

  function round2(value) {
    return Math.round(value * 100) / 100;
  }

  function updateTotals() {
    const subtotal = cartSubtotal();
    let discount = parseFloat(discountInput.value);
    if (!Number.isFinite(discount) || discount < 0) discount = 0;
    if (discount > subtotal) discount = subtotal; // live preview only; server re-checks
    const taxable = subtotal - discount;
    const tax = round2(taxable * (Number(settings.tax_percent) || 0) / 100);

    document.getElementById("tSubtotal").textContent = money(subtotal);
    document.getElementById("tDiscount").textContent = `− ${money(discount)}`;
    document.getElementById("tTax").textContent = money(tax);
    document.getElementById("tGrand").textContent = money(taxable + tax);
  }

  async function submitOrder(event) {
    event.preventDefault();

    const errors = [];
    if (byName("order_type").value === "Dine-in") {
      const error = Validator.required(tableNumberInput.value) || Validator.positiveNumber(tableNumberInput.value) || Validator.maxValue(tableNumberInput.value, 999);
      if (error) {
        Validator.showFieldError(tableNumberInput, error);
        errors.push(tableNumberInput);
      }
    }
    const discountError = Validator.nonNegative(discountInput.value);
    if (discountError) {
      Validator.showFieldError(discountInput, discountError);
      errors.push(discountInput);
    }
    if (cart.length === 0) {
      UI.toast("Add at least one item to the order.", "error");
      return;
    }
    if (errors.length > 0) {
      errors[0].focus();
      UI.toast("Please correct the highlighted fields.", "error");
      return;
    }

    const payload = {
      order_type: byName("order_type").value,
      table_number:
        byName("order_type").value === "Dine-in" ? Number(tableNumberInput.value) : null,
      items: cart.map((line) => ({ menu_item_id: line.menu_item_id, quantity: line.quantity })),
      discount_amount: discountInput.value === "" ? 0 : Number(discountInput.value)
    };

    saveBtn.classList.add("is-loading");
    saveBtn.disabled = true;
    try {
      const response = await API.post(API_URL, payload);
      UI.toast(`Order ${response.data.order_number} placed.`, "success");
      closeModal();
      await loadOrders();
    } catch (error) {
      (error.errors || []).forEach((fieldError) => {
        const input = fieldError.field === "table_number"
          ? tableNumberInput
          : fieldError.field === "discount_amount"
            ? discountInput
            : null;
        if (input) Validator.showFieldError(input, fieldError.message);
      });
      UI.toast(error.message, "error");
    } finally {
      saveBtn.classList.remove("is-loading");
      saveBtn.disabled = false;
    }
  }

  // ------------------------------------------------------------------
  // Detail modal + row actions
  // ------------------------------------------------------------------

  async function showDetail(orderId) {
    try {
      const response = await API.get(`${API_URL}/${orderId}`);
      detailId = orderId;
      renderDetail(response.data);
      document.getElementById("detailModal").hidden = false;
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  function renderDetail(order) {
    document.getElementById("detailTitle").textContent = `Order ${order.order_number}`;
    const rows = order.items
      .map(
        (line) => `
        <tr>
          <td>${UI.escapeHtml(line.item_name)}<br /><span style="font-size:11px;color:var(--muted)">× ${line.quantity}</span></td>
          <td class="num">${money(line.unit_price)}</td>
          <td class="num"><strong>${money(line.line_total)}</strong></td>
        </tr>`
      )
      .join("");

    const statusSelect = document.getElementById("detailStatusSelect");
    statusSelect.value = order.status;
    statusSelect.disabled = order.status === "Cancelled";

    document.getElementById("detailBody").innerHTML = `
      <div class="meta-list" style="margin-bottom:14px">
        <div class="row"><span>Status</span><span class="badge ${STATUS_BADGE[order.status]}">${order.status}</span></div>
        <div class="row"><span>Type</span><span>${order.order_type}${order.table_number ? ` · Table ${order.table_number}` : ""}</span></div>
        <div class="row"><span>Placed</span><span>${fmtDateTime(order.created_at)}</span></div>
        <div class="row"><span>Payment</span><span>${
          order.payment_status === "Paid"
            ? `Paid via ${order.payment_method}`
            : "<strong style='color:var(--clay)'>Unpaid</strong>"
        }</span></div>
      </div>
      <div class="detail-grid">
        <div class="cart-wrap">
          <table class="mini-table">
            <thead><tr><th>Item</th><th class="num">Price</th><th class="num">Amount</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
        <div class="totals-box">
          <div class="totals-row"><span>Subtotal</span><strong>${money(order.subtotal)}</strong></div>
          <div class="totals-row"><span>Discount</span><strong>− ${money(order.discount_amount)}</strong></div>
          <div class="totals-row"><span>Tax (${order.tax_percent}%)</span><strong>${money(order.tax_amount)}</strong></div>
          <div class="totals-row grand"><span>Total</span><strong>${money(order.total)}</strong></div>
        </div>
      </div>`;
  }

  async function saveDetailStatus() {
    const nextStatus = document.getElementById("detailStatusSelect").value;
    try {
      await API.put(`${API_URL}/${detailId}/status`, { status: nextStatus });
      UI.toast(`Order marked as ${nextStatus}.`, "success");
      document.getElementById("detailModal").hidden = true;
      await loadOrders();
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  async function cancelOrder(row) {
    const order = orders.find((o) => o.id === Number(row.dataset.id));
    if (!order) return;
    const confirmed = await UI.confirmDialog({
      title: `Cancel ${order.order_number}?`,
      message: "The kitchen stops working on it. Cancelled orders stay in history until deleted.",
      confirmText: "Cancel order"
    });
    if (!confirmed) return;
    try {
      await API.put(`${API_URL}/${order.id}/status`, { status: "Cancelled" });
      UI.toast(`${order.order_number} cancelled.`, "success");
      await loadOrders();
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  async function deleteOrder(row) {
    const order = orders.find((o) => o.id === Number(row.dataset.id));
    if (!order) return;
    const confirmed = await UI.confirmDialog({
      title: `Delete ${order.order_number}?`,
      message: "This removes the cancelled order and its lines permanently.",
      confirmText: "Delete"
    });
    if (!confirmed) return;
    try {
      await API.delete(`${API_URL}/${order.id}`);
      UI.toast("Order deleted.", "success");
      await loadOrders();
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadOrders, 300);
  }

  document.addEventListener("DOMContentLoaded", () => {
    tableBody = document.getElementById("orderTableBody");
    searchInput = document.getElementById("orderSearch");
    statusFilter = document.getElementById("orderStatusFilter");
    typeFilter = document.getElementById("orderTypeFilter");
    paymentFilter = document.getElementById("orderPaymentFilter");
    modal = document.getElementById("orderModal");
    form = document.getElementById("orderForm");
    saveBtn = document.getElementById("orderSaveBtn");
    itemSelect = document.getElementById("orderItemSelect");
    itemQty = document.getElementById("orderItemQty");
    discountInput = document.getElementById("orderDiscount");
    tableNumberInput = document.getElementById("orderTableNumber");
    tableField = document.getElementById("tableNumberField");
    cartBody = document.getElementById("cartBody");
    cartEmpty = document.getElementById("cartEmpty");

    Promise.all([loadSettings(), loadMenuItems()]).then(loadOrders);

    document.getElementById("newOrderBtn").addEventListener("click", openModal);
    searchInput.addEventListener("input", debounceSearch);
    statusFilter.addEventListener("change", loadOrders);
    typeFilter.addEventListener("change", loadOrders);
    paymentFilter.addEventListener("change", loadOrders);

    document.querySelectorAll('input[name="order_type"]').forEach((radio) => {
      radio.addEventListener("change", syncTypeToggle);
    });
    document.getElementById("addLineBtn").addEventListener("click", addToCart);
    itemQty.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        addToCart();
      }
    });

    cartBody.addEventListener("click", (event) => {
      const stepButton = event.target.closest("button[data-step]");
      const removeButton = event.target.closest("button[data-remove]");
      const row = event.target.closest("tr[data-id]");
      if (!row) return;
      const line = cart.find((l) => l.menu_item_id === Number(row.dataset.id));
      if (!line) return;
      if (stepButton) {
        line.quantity = Math.min(999, Math.max(1, line.quantity + Number(stepButton.dataset.step)));
        renderCart();
      } else if (removeButton) {
        cart = cart.filter((l) => l !== line);
        renderCart();
      }
    });

    [discountInput].forEach((input) => {
      input.addEventListener("input", () => {
        updateTotals();
        Validator.clearFieldError(input);
      });
    });

    form.addEventListener("submit", submitOrder);
    modal.querySelector("[data-close-modal]").addEventListener("click", closeModal);
    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeModal();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !modal.hidden) closeModal();
    });

    tableBody.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const row = button.closest("tr[data-id]");
      if (button.dataset.action === "view") showDetail(Number(row.dataset.id));
      else if (button.dataset.action === "cancel") cancelOrder(row);
      else if (button.dataset.action === "delete") deleteOrder(row);
    });

    document.getElementById("detailModal").addEventListener("click", (event) => {
      if (event.target === event.currentTarget) event.currentTarget.hidden = true;
    });
    document.querySelector("#detailModal [data-close-modal]").addEventListener("click", () => {
      document.getElementById("detailModal").hidden = true;
    });
    document.getElementById("detailStatusSave").addEventListener("click", saveDetailStatus);
    document.addEventListener("keydown", (event) => {
      const detailModal = document.getElementById("detailModal");
      if (event.key === "Escape" && !detailModal.hidden) detailModal.hidden = true;
    });
  });
})();
