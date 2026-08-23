(function () {
  "use strict";

  const API_URL = "/api/purchases";
  const SUPPLIERS_URL = "/api/suppliers";
  const MATERIALS_URL = "/api/inventory/items";

  let purchases = [];
  let materials = [];
  let cart = []; // { inventory_item_id, name, unit, quantity, unit_cost }
  let searchTimer = null;

  const el = {
    statTotalValue: document.getElementById("statTotalValue"),
    statOutstanding: document.getElementById("statOutstanding"),
    statCount: document.getElementById("statCount"),
    tableBody: document.getElementById("purchaseTableBody"),
    search: document.getElementById("purchaseSearch"),
    supplierFilter: document.getElementById("supplierFilter"),
    paymentFilter: document.getElementById("paymentFilter"),
    dateFrom: document.getElementById("dateFrom"),
    dateTo: document.getElementById("dateTo"),
    newBtn: document.getElementById("newPurchaseBtn"),
    modal: document.getElementById("purchaseModal"),
    form: document.getElementById("purchaseForm"),
    saveBtn: document.getElementById("purchaseSaveBtn"),
    modalTitle: document.getElementById("purchaseModalTitle"),
    itemSelect: document.getElementById("itemSelect"),
    itemQty: document.getElementById("itemQty"),
    itemCost: document.getElementById("itemCost"),
    addLineBtn: document.getElementById("addLineBtn"),
    cartBody: document.getElementById("cartBody"),
    cartEmpty: document.getElementById("cartEmpty"),
    tItems: document.getElementById("tItems"),
    tGrand: document.getElementById("tGrand"),
    detailModal: document.getElementById("detailModal"),
    detailTitle: document.getElementById("detailTitle"),
    detailBody: document.getElementById("detailBody")
  };

  const byName = (name) => el.form.elements.namedItem(name);

  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function fmtQty(value) {
    return String(Number(Number(value || 0).toFixed(3)));
  }

  function fmtDay(isoDate) {
    // purchase_date arrives as "YYYY-MM-DD"; format without timezone surprises
    const parts = String(isoDate).split("-");
    if (parts.length !== 3) return UI.escapeHtml(isoDate);
    return `${Number(parts[2])} ${MONTHS[Number(parts[1]) - 1]} ${parts[0]}`;
  }

  function todayIso() {
    const now = new Date();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    return `${now.getFullYear()}-${month}-${day}`;
  }

  function skeletonRows() {
    const rows = [];
    for (let i = 0; i < 3; i += 1) {
      rows.push(
        `<tr class="skeleton-row">${["35%", "30%", "25%", "20%", "25%", "25%", "40%"]
          .map((width) => `<td><div class="skeleton-line" style="width:${width}"></div></td>`)
          .join("")}</tr>`
      );
    }
    el.tableBody.innerHTML = rows.join("");
  }

  function emptyRow(message, hint) {
    return `
      <tr class="empty-row">
        <td colspan="7">
          <div class="empty-state">
            <div class="es-icon" data-icon="truck"></div>
            <h4>${message}</h4>
            <p>${hint}</p>
          </div>
        </td>
      </tr>`;
  }

  function hydrateIcons(scope) {
    scope.querySelectorAll("[data-icon]").forEach((node) => {
      node.innerHTML = UI.ICONS[node.dataset.icon] || "";
    });
  }

  function payBadge(status) {
    return status === "Paid"
      ? '<span class="badge badge-pay-paid">Paid</span>'
      : '<span class="badge badge-pay-unpaid">Unpaid</span>';
  }

  function render() {
    hydrateIcons(el.tableBody);

    if (purchases.length === 0) {
      const filtered =
        Boolean(el.search.value.trim()) ||
        el.supplierFilter.value ||
        el.paymentFilter.value ||
        el.dateFrom.value ||
        el.dateTo.value;
      el.tableBody.innerHTML = emptyRow(
        "No purchases found",
        filtered
          ? "Nothing matches the current filters."
          : 'Record your first delivery with "+ New purchase" — stock increases automatically.'
      );
      return;
    }

    el.tableBody.innerHTML = purchases
      .map((p) => {
        const flipAction = p.payment_status === "Paid" ? "Mark unpaid" : "Mark paid";
        return `
        <tr data-id="${p.id}">
          <td><strong>${UI.escapeHtml(p.purchase_number)}</strong></td>
          <td>${UI.escapeHtml(p.supplier_name)}</td>
          <td>${fmtDay(p.purchase_date)}</td>
          <td class="num">${p.item_count}</td>
          <td class="num qty-cell">${UI.formatMoney(p.total)}</td>
          <td>${payBadge(p.payment_status)}</td>
          <td>
            <div class="row-actions">
              <button type="button" class="btn btn-ghost btn-row" data-action="view">View</button>
              <button type="button" class="btn btn-ghost btn-row" data-action="flip-payment">${flipAction}</button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  }

  async function loadPurchases() {
    skeletonRows();
    try {
      const params = new URLSearchParams();
      const term = el.search.value.trim();
      if (term) params.set("search", term);
      if (el.supplierFilter.value) params.set("supplier_id", el.supplierFilter.value);
      if (el.paymentFilter.value) params.set("payment_status", el.paymentFilter.value);
      if (el.dateFrom.value) params.set("start_date", el.dateFrom.value);
      if (el.dateTo.value) params.set("end_date", el.dateTo.value);

      const response = await API.get(`${API_URL}?${params.toString()}`);
      purchases = response.data.items;
      const summary = response.data.summary;
      el.statTotalValue.textContent = UI.formatMoney(summary.total_amount);
      el.statOutstanding.textContent = UI.formatMoney(summary.unpaid_amount);
      el.statCount.textContent = summary.count;
      render();
    } catch (error) {
      el.tableBody.innerHTML = emptyRow("Could not load purchases", UI.escapeHtml(error.message));
    }
  }

  async function loadSuppliers() {
    try {
      const response = await API.get(`${SUPPLIERS_URL}?include_inactive=true`);
      const suppliers = response.data.items;
      const options = suppliers
        .map(
          (s) =>
            `<option value="${s.id}">${UI.escapeHtml(s.name)}${s.is_active ? "" : " (inactive)"}</option>`
        )
        .join("");
      el.supplierFilter.innerHTML = '<option value="">All suppliers</option>' + options;
      byName("supplier_id").innerHTML = '<option value="">Select a supplier…</option>' + options;
    } catch (_error) {
      /* selects stay empty; server still validates */
    }
  }

  async function loadMaterials() {
    try {
      const response = await API.get(`${MATERIALS_URL}?include_inactive=false`);
      materials = response.data.items;
      el.itemSelect.innerHTML =
        '<option value="">Select a material…</option>' +
        materials
          .map(
            (m) =>
              `<option value="${m.id}" data-cost="${m.purchase_price}">${UI.escapeHtml(
                m.name
              )} (${UI.escapeHtml(m.unit)})</option>`
          )
          .join("");
    } catch (_error) {
      /* picker stays empty; server still validates */
    }
  }

  /* ===================== Cart ===================== */

  function prefillCost() {
    const option = el.itemSelect.selectedOptions[0];
    if (option && option.dataset.cost !== undefined) {
      el.itemCost.value = Number(option.dataset.cost).toFixed(2);
    }
  }

  function addToCart() {
    Validator.clearFieldError(el.itemQty);
    Validator.clearFieldError(el.itemCost);

    const materialId = Number(el.itemSelect.value);
    const material = materials.find((m) => m.id === materialId);
    if (!material) {
      UI.toast("Choose a material first.", "warning");
      return;
    }
    const quantity = Number(el.itemQty.value);
    const unitCost = Number(el.itemCost.value);

    const qtyError = Validator.positiveNumber(el.itemQty.value) || Validator.maxValue(el.itemQty.value, 999999);
    if (qtyError) {
      Validator.showFieldError(el.itemQty, qtyError);
      return;
    }
    const costError = Validator.nonNegative(el.itemCost.value) || Validator.maxValue(el.itemCost.value, 999999);
    if (costError) {
      Validator.showFieldError(el.itemCost, costError);
      return;
    }
    if (cart.some((line) => line.inventory_item_id === materialId)) {
      UI.toast(`"${UI.escapeHtml(material.name)}" is already in the list — adjust its quantity below.`, "warning");
      return;
    }

    cart.push({
      inventory_item_id: materialId,
      name: material.name,
      unit: material.unit,
      quantity,
      unit_cost: unitCost
    });

    el.itemSelect.selectedIndex = 0;
    el.itemQty.value = "";
    el.itemCost.value = "";
    renderCart();
    el.itemSelect.focus();
  }

  function lineAmount(line) {
    return Math.round(line.quantity * line.unit_cost * 100) / 100;
  }

  function updateTotals() {
    const grand = Math.round(cart.reduce((sum, line) => sum + lineAmount(line), 0) * 100) / 100;
    el.tItems.textContent = String(cart.length);
    el.tGrand.textContent = UI.formatMoney(grand);
    el.cartEmpty.hidden = cart.length > 0;
  }

  function renderCart() {
    if (cart.length === 0) {
      el.cartBody.innerHTML = "";
      updateTotals();
      return;
    }
    el.cartBody.innerHTML = cart
      .map(
        (line) => `
        <tr data-id="${line.inventory_item_id}">
          <td><strong>${UI.escapeHtml(line.name)}</strong> <span style="color:var(--muted)">· ${UI.escapeHtml(line.unit)}</span></td>
          <td style="text-align:center">
            <input class="input cart-input" type="number" min="0" step="0.01" data-field="unit_cost" value="${line.unit_cost}" aria-label="Unit cost" />
          </td>
          <td style="text-align:center">
            <input class="input cart-input" type="number" min="0.001" step="0.001" data-field="quantity" value="${line.quantity}" aria-label="Quantity" />
          </td>
          <td class="num">${UI.formatMoney(lineAmount(line))}</td>
          <td>
            <button type="button" class="cart-remove" data-action="remove">Remove</button>
          </td>
        </tr>`
      )
      .join("");
    updateTotals();
  }

  function onCartInput(event) {
    const input = event.target.closest("input[data-field]");
    if (!input) return;
    const row = input.closest("tr[data-id]");
    const line = cart.find((l) => l.inventory_item_id === Number(row.dataset.id));
    if (!line) return;

    const parsed = Number(input.value);
    line[input.dataset.field] = Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;

    const amountCell = row.querySelector("td.num");
    if (amountCell) amountCell.textContent = UI.formatMoney(lineAmount(line));
    updateTotals();
  }

  function onCartClick(event) {
    const button = event.target.closest("button[data-action='remove']");
    if (!button) return;
    const row = button.closest("tr[data-id]");
    cart = cart.filter((line) => line.inventory_item_id !== Number(row.dataset.id));
    renderCart();
  }

  /* ===================== New purchase modal ===================== */

  const FIELD_NAMES = ["supplier_id", "purchase_date", "notes"];

  function clearErrors() {
    FIELD_NAMES.forEach((name) => {
      const input = byName(name);
      if (input) Validator.clearFieldError(input);
    });
  }

  function applyServerErrors(errors) {
    let firstField = null;
    (errors || []).forEach((error) => {
      const input = error.field ? el.form.elements.namedItem(error.field.split(".")[0]) : null;
      if (input) {
        Validator.showFieldError(input, error.message);
        if (!firstField) firstField = input;
      }
    });
    if (firstField) firstField.focus();
  }

  function openModal() {
    byName("supplier_id").value = "";
    byName("purchase_date").value = todayIso();
    byName("notes").value = "";
    el.itemSelect.selectedIndex = 0;
    el.itemQty.value = "";
    el.itemCost.value = "";
    cart = [];
    renderCart();
    clearErrors();
    el.modal.hidden = false;
    byName("supplier_id").focus();
  }

  function closeModal() {
    el.modal.hidden = true;
    cart = [];
  }

  async function savePurchase(event) {
    event.preventDefault();
    clearErrors();

    if (!Validator.validateForm(el.form)) return;

    if (cart.length === 0) {
      UI.toast("Add at least one material to the purchase.", "warning");
      return;
    }

    const payload = {
      supplier_id: Number(byName("supplier_id").value),
      purchase_date: byName("purchase_date").value || null,
      notes: (byName("notes").value || "").trim() || null,
      items: cart.map((line) => ({
        inventory_item_id: line.inventory_item_id,
        quantity: line.quantity,
        unit_cost: Number(line.unit_cost.toFixed(2))
      }))
    };

    el.saveBtn.classList.add("is-loading");
    el.saveBtn.disabled = true;
    try {
      const response = await API.post(API_URL, payload);
      UI.toast(response.message, "success");
      closeModal();
      await Promise.all([loadPurchases(), loadMaterials()]);
    } catch (error) {
      applyServerErrors(error.errors);
      UI.toast(error.message, "error");
    } finally {
      el.saveBtn.classList.remove("is-loading");
      el.saveBtn.disabled = false;
    }
  }

  /* ===================== Row actions ===================== */

  async function flipPayment(row) {
    const purchase = purchases.find((p) => p.id === Number(row.dataset.id));
    if (!purchase) return;
    const nextStatus = purchase.payment_status === "Paid" ? "Unpaid" : "Paid";
    try {
      const response = await API.put(`${API_URL}/${purchase.id}/payment-status`, {
        payment_status: nextStatus
      });
      UI.toast(response.message, "success");
      await loadPurchases();
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  async function viewPurchase(id) {
    el.detailTitle.textContent = "Purchase";
    el.detailBody.innerHTML = '<div class="skeleton-line" style="width:60%"></div>';
    el.detailModal.hidden = false;

    try {
      const response = await API.get(`${API_URL}/${id}`);
      const p = response.data;
      el.detailTitle.textContent = `Purchase · ${p.purchase_number}`;

      const meta = `
        <div class="meta-list">
          <div class="row"><span>Supplier</span><span><strong>${UI.escapeHtml(p.supplier_name)}</strong></span></div>
          <div class="row"><span>Purchase date</span><span>${fmtDay(p.purchase_date)}</span></div>
          <div class="row"><span>Payment</span><span>${payBadge(p.payment_status)}</span></div>
          <div class="row"><span>Recorded</span><span>${new Date(p.created_at).toLocaleString("en-IN")}</span></div>
          <div class="row"><span>Notes</span><span>${UI.escapeHtml(p.notes || "—")}</span></div>
        </div>`;

      const lines = `
        <table class="mini-table" style="margin-top:12px">
          <thead>
            <tr><th>Material</th><th class="num">Qty</th><th class="num">Unit cost</th><th class="num">Amount</th></tr>
          </thead>
          <tbody>
            ${p.items
              .map(
                (line) => `
              <tr>
                <td>${UI.escapeHtml(line.item_name)}</td>
                <td class="num">${fmtQty(line.quantity)} ${UI.escapeHtml(line.unit)}</td>
                <td class="num">${UI.formatMoney(line.unit_cost)}</td>
                <td class="num">${UI.formatMoney(line.line_total)}</td>
              </tr>`
              )
              .join("")}
          </tbody>
        </table>`;

      const total = `
        <div class="light-total">
          <span>Total added to inventory</span>
          <strong>${UI.formatMoney(p.total)}</strong>
        </div>`;

      el.detailBody.innerHTML = `${meta}${lines}${total}`;
    } catch (error) {
      el.detailBody.innerHTML = `<p>${UI.escapeHtml(error.message)}</p>`;
    }
  }

  function closeDetail() {
    el.detailModal.hidden = true;
  }

  /* ===================== Wiring ===================== */

  function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadPurchases, 300);
  }

  function wireModal(modalNode, closeFn) {
    modalNode.querySelector("[data-close-modal]").addEventListener("click", closeFn);
    modalNode.addEventListener("click", (event) => {
      if (event.target === modalNode) closeFn();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    loadSuppliers();
    loadMaterials();
    loadPurchases();

    el.newBtn.addEventListener("click", openModal);
    el.search.addEventListener("input", debounceSearch);
    [el.supplierFilter, el.paymentFilter, el.dateFrom, el.dateTo].forEach((node) => {
      node.addEventListener("change", loadPurchases);
    });

    el.itemSelect.addEventListener("change", prefillCost);
    el.addLineBtn.addEventListener("click", addToCart);
    el.cartBody.addEventListener("input", onCartInput);
    el.cartBody.addEventListener("click", onCartClick);

    el.form.addEventListener("submit", savePurchase);
    wireModal(el.modal, closeModal);

    el.tableBody.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const row = button.closest("tr[data-id]");
      if (button.dataset.action === "view") viewPurchase(Number(row.dataset.id));
      else if (button.dataset.action === "flip-payment") flipPayment(row);
    });

    wireModal(el.detailModal, closeDetail);

    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      if (!el.modal.hidden) closeModal();
      if (!el.detailModal.hidden) closeDetail();
    });

    FIELD_NAMES.forEach((name) => {
      const input = byName(name);
      if (input) input.addEventListener("input", () => Validator.clearFieldError(input));
    });
    [el.itemQty, el.itemCost].forEach((input) => {
      input.addEventListener("input", () => Validator.clearFieldError(input));
    });
  });
})();
