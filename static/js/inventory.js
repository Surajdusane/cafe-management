(function () {
  "use strict";

  const ITEMS_URL = "/api/inventory/items";
  const TX_URL = "/api/inventory/transactions";
  const CATEGORIES_URL = "/api/inventory/categories";
  const SUPPLIERS_URL = "/api/suppliers";

  let items = [];
  let suppliers = [];
  let editingId = null;
  let stockItem = null;
  let movementType = "Stock In";
  let searchTimer = null;

  const el = {
    statTotalItems: document.getElementById("statTotalItems"),
    statLowStock: document.getElementById("statLowStock"),
    statSuppliers: document.getElementById("statSuppliers"),
    itemTableBody: document.getElementById("itemTableBody"),
    historyTableBody: document.getElementById("historyTableBody"),
    search: document.getElementById("itemSearch"),
    categoryFilter: document.getElementById("categoryFilter"),
    supplierFilter: document.getElementById("supplierFilter"),
    lowStockOnly: document.getElementById("lowStockOnly"),
    movementTypeFilter: document.getElementById("movementTypeFilter"),
    refreshHistoryBtn: document.getElementById("refreshHistoryBtn"),
    addItemBtn: document.getElementById("addItemBtn"),
    itemModal: document.getElementById("itemModal"),
    itemForm: document.getElementById("itemForm"),
    itemSaveBtn: document.getElementById("itemSaveBtn"),
    itemModalTitle: document.getElementById("itemModalTitle"),
    openingQuantityField: document.getElementById("openingQuantityField"),
    stockModal: document.getElementById("stockModal"),
    stockForm: document.getElementById("stockForm"),
    stockSaveBtn: document.getElementById("stockSaveBtn"),
    stockModalTitle: document.getElementById("stockModalTitle"),
    stockCurrentLine: document.getElementById("stockCurrentLine"),
    movementTypeGroup: document.getElementById("movementTypeGroup"),
    movementTypeHint: document.getElementById("movementTypeHint"),
    quantityLabel: document.getElementById("quantityLabel"),
    quantityHint: document.getElementById("quantityHint"),
    stockQuantity: document.getElementById("stockQuantity"),
    historyModal: document.getElementById("historyModal"),
    historyModalTitle: document.getElementById("historyModalTitle"),
    historyDetailBody: document.getElementById("historyDetailBody")
  };

  const byName = (name) => el.itemForm.elements.namedItem(name);

  function fmtQty(value) {
    return String(Number(Number(value || 0).toFixed(3)));
  }

  function fmtWhen(value) {
    return new Date(value).toLocaleString("en-IN", {
      day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
    });
  }

  function skeletonRows(tbody, widths) {
    const rows = [];
    for (let i = 0; i < 3; i += 1) {
      rows.push(
        `<tr class="skeleton-row">${widths
          .map((width) => `<td><div class="skeleton-line" style="width:${width}"></div></td>`)
          .join("")}</tr>`
      );
    }
    tbody.innerHTML = rows.join("");
  }

  function emptyRow(message, hint, colspan) {
    return `
      <tr class="empty-row">
        <td colspan="${colspan}">
          <div class="empty-state">
            <div class="es-icon" data-icon="inventory"></div>
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

  function statusCell(item) {
    let badges = "";
    if (item.is_low_stock) {
      badges +=
        item.current_quantity <= 0
          ? '<span class="badge badge-out">Out of stock</span> '
          : '<span class="badge badge-low">Low stock</span> ';
    }
    badges += item.is_active
      ? '<span class="badge badge-ok">Active</span>'
      : '<span class="badge badge-muted">Inactive</span>';
    return badges;
  }

  /* ===================== Materials table ===================== */

  function renderItemTable() {
    hydrateIcons(el.itemTableBody);

    if (items.length === 0) {
      const filtered =
        Boolean(el.search.value.trim()) ||
        el.categoryFilter.value ||
        el.supplierFilter.value ||
        el.lowStockOnly.checked;
      el.itemTableBody.innerHTML = emptyRow(
        "No raw materials found",
        filtered
          ? "Nothing matches the current filters."
          : 'Add your first material with "+ Add material" — milk, coffee beans, sugar…',
        8
      );
      return;
    }

    el.itemTableBody.innerHTML = items
      .map((item) => {
        const supplierName = item.supplier ? item.supplier.name : "—";
        return `
        <tr data-id="${item.id}">
          <td><strong>${UI.escapeHtml(item.name)}</strong></td>
          <td>${UI.escapeHtml(item.category)}</td>
          <td class="num qty-cell ${item.is_low_stock ? "is-low" : ""}">
            ${fmtQty(item.current_quantity)}<span class="qty-unit">${UI.escapeHtml(item.unit)}</span>
          </td>
          <td class="num">${fmtQty(item.minimum_stock)}<span class="qty-unit">${UI.escapeHtml(item.unit)}</span></td>
          <td class="num">${UI.formatMoney(item.purchase_price)}</td>
          <td>${UI.escapeHtml(supplierName)}</td>
          <td>${statusCell(item)}</td>
          <td>
            <div class="row-actions">
              <button type="button" class="btn btn-ghost btn-row" data-action="stock">Stock</button>
              <button type="button" class="btn btn-ghost btn-row" data-action="history">History</button>
              <button type="button" class="btn btn-ghost btn-row" data-action="edit">Edit</button>
              <button type="button" class="btn btn-ghost btn-row" data-action="delete">Delete</button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  }

  async function loadItems() {
    skeletonRows(el.itemTableBody, ["40%", "25%", "30%", "30%", "25%", "30%", "35%", "40%"]);
    try {
      const params = new URLSearchParams({ include_inactive: "true" });
      const term = el.search.value.trim();
      if (term) params.set("search", term);
      if (el.categoryFilter.value) params.set("category", el.categoryFilter.value);
      if (el.supplierFilter.value) params.set("supplier_id", el.supplierFilter.value);
      if (el.lowStockOnly.checked) params.set("low_stock_only", "true");

      const response = await API.get(`${ITEMS_URL}?${params.toString()}`);
      items = response.data.items;
      const summary = response.data.summary;
      el.statTotalItems.textContent = summary.total_items;
      el.statLowStock.textContent = summary.low_stock_items;
      el.statSuppliers.textContent = summary.total_suppliers;
      renderItemTable();
    } catch (error) {
      el.itemTableBody.innerHTML = emptyRow("Could not load materials", error.message, 8);
    }
  }

  async function loadCategories() {
    try {
      const response = await API.get(CATEGORIES_URL);
      const categories = response.data.categories;
      const suggestions = categories.map((c) => `<option value="${UI.escapeHtml(c)}"></option>`).join("");
      document.getElementById("categorySuggestions").innerHTML = suggestions;

      const current = el.categoryFilter.value;
      el.categoryFilter.innerHTML =
        '<option value="">All categories</option>' +
        categories.map((c) => `<option value="${UI.escapeHtml(c)}">${UI.escapeHtml(c)}</option>`).join("");
      if (categories.includes(current)) el.categoryFilter.value = current;
    } catch (_error) {
      /* filter dropdown stays as-is; not critical */
    }
  }

  async function loadSuppliers() {
    try {
      const response = await API.get(`${SUPPLIERS_URL}?include_inactive=true`);
      suppliers = response.data.items;
      const options = suppliers
        .map(
          (s) =>
            `<option value="${s.id}">${UI.escapeHtml(s.name)}${s.is_active ? "" : " (inactive)"}</option>`
        )
        .join("");
      el.supplierFilter.innerHTML = '<option value="">All suppliers</option>' + options;
      byName("supplier_id").innerHTML = '<option value="">No supplier selected</option>' + options;
    } catch (_error) {
      /* selects stay empty; server still validates */
    }
  }

  /* ===================== Movements table ===================== */

  function movementBadge(type) {
    const cls = { "Stock In": "mv-in", "Stock Out": "mv-out", Adjustment: "mv-adj" }[type] || "";
    return `<span class="${cls}">${UI.escapeHtml(type)}</span>`;
  }

  function renderMovementTable(transactions) {
    if (transactions.length === 0) {
      el.historyTableBody.innerHTML = emptyRow(
        "No stock movements yet",
        "Movements appear here when materials are created with opening stock or stock is recorded.",
        6
      );
      return;
    }
    el.historyTableBody.innerHTML = transactions
      .map(
        (t) => `
        <tr>
          <td>${fmtWhen(t.created_at)}</td>
          <td><strong>${UI.escapeHtml(t.item_name)}</strong></td>
          <td>${movementBadge(t.transaction_type)}</td>
          <td class="num ${t.transaction_type === "Stock Out" ? "mv-out" : t.transaction_type === "Stock In" ? "mv-in" : "mv-adj"}">
            ${t.transaction_type === "Adjustment" ? "=" : t.transaction_type === "Stock Out" ? "−" : "+"}${fmtQty(t.quantity)}
          </td>
          <td class="num qty-cell">${fmtQty(t.balance_after)}</td>
          <td>${UI.escapeHtml(t.note || "—")}</td>
        </tr>`
      )
      .join("");
  }

  async function loadMovements() {
    skeletonRows(el.historyTableBody, ["25%", "35%", "20%", "25%", "40%"]);
    try {
      const params = new URLSearchParams({ limit: "25" });
      if (el.movementTypeFilter.value) params.set("transaction_type", el.movementTypeFilter.value);
      const response = await API.get(`${TX_URL}?${params.toString()}`);
      renderMovementTable(response.data.items);
    } catch (error) {
      el.historyTableBody.innerHTML = emptyRow("Could not load movements", error.message, 6);
    }
  }

  /* ===================== Material modal ===================== */

  const ITEM_FIELD_NAMES = [
    "name", "category", "unit", "initial_quantity",
    "minimum_stock", "purchase_price", "supplier_id", "notes"
  ];

  function clearItemErrors() {
    ITEM_FIELD_NAMES.forEach((name) => {
      const input = byName(name);
      if (input) Validator.clearFieldError(input);
    });
  }

  function openItemModal(item) {
    editingId = item ? item.id : null;
    el.itemModalTitle.textContent = item ? `Edit material · ${item.name}` : "New raw material";
    byName("name").value = item ? item.name : "";
    byName("category").value = item ? item.category : "";
    byName("unit").value = item ? item.unit : "";
    byName("initial_quantity").value = "0";
    byName("minimum_stock").value = item ? fmtQty(item.minimum_stock) : "0";
    byName("purchase_price").value = item ? Number(item.purchase_price).toFixed(2) : "0.00";
    byName("supplier_id").value = item && item.supplier_id ? String(item.supplier_id) : "";
    byName("notes").value = item && item.notes ? item.notes : "";
    byName("is_active").checked = item ? item.is_active : true;

    // Opening stock only applies while creating; edits go through movements.
    el.openingQuantityField.hidden = Boolean(item);

    clearItemErrors();
    el.itemModal.hidden = false;
    byName("name").focus();
  }

  function closeItemModal() {
    el.itemModal.hidden = true;
    editingId = null;
  }

  function localDuplicateCheck(name) {
    const lower = name.toLowerCase();
    return items.find((i) => i.name.toLowerCase() === lower && i.id !== editingId);
  }

  async function saveItem(event) {
    event.preventDefault();
    clearItemErrors();

    if (!Validator.validateForm(el.itemForm)) return;

    const name = byName("name").value.trim();
    const duplicate = localDuplicateCheck(name);
    if (duplicate) {
      Validator.showFieldError(byName("name"), `A material named "${duplicate.name}" already exists.`);
      UI.toast("Please correct the highlighted fields.", "error");
      return;
    }

    const payload = {
      name,
      category: byName("category").value.trim(),
      unit: byName("unit").value,
      minimum_stock: Number(byName("minimum_stock").value),
      purchase_price: Number(byName("purchase_price").value),
      supplier_id: byName("supplier_id").value ? Number(byName("supplier_id").value) : null,
      notes: (byName("notes").value || "").trim() || null,
      is_active: byName("is_active").checked
    };

    el.itemSaveBtn.classList.add("is-loading");
    el.itemSaveBtn.disabled = true;
    try {
      if (editingId === null) {
        payload.initial_quantity = Number(byName("initial_quantity").value || 0);
        await API.post(ITEMS_URL, payload);
        UI.toast("Raw material created.", "success");
      } else {
        await API.put(`${ITEMS_URL}/${editingId}`, payload);
        UI.toast("Raw material updated.", "success");
      }
      closeItemModal();
      await Promise.all([loadItems(), loadCategories(), loadMovements()]);
    } catch (error) {
      applyServerErrors(error.errors);
      UI.toast(error.message, "error");
    } finally {
      el.itemSaveBtn.classList.remove("is-loading");
      el.itemSaveBtn.disabled = false;
    }
  }

  function applyServerErrors(errors) {
    let firstField = null;
    (errors || []).forEach((error) => {
      const input = error.field ? el.itemForm.elements.namedItem(error.field) : null;
      if (input) {
        Validator.showFieldError(input, error.message);
        if (!firstField) firstField = input;
      }
    });
    if (firstField) firstField.focus();
  }

  async function deleteItem(row) {
    const item = items.find((i) => i.id === Number(row.dataset.id));
    if (!item) return;

    const confirmed = await UI.confirmDialog({
      title: "Delete raw material?",
      message: `"${UI.escapeHtml(item.name)}" and its entire stock movement history will be removed permanently. This cannot be undone.`,
      confirmText: "Delete"
    });
    if (!confirmed) return;

    try {
      await API.delete(`${ITEMS_URL}/${item.id}`);
      UI.toast(`Raw material '${item.name}' deleted.`, "success");
      await Promise.all([loadItems(), loadCategories(), loadMovements()]);
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  /* ===================== Stock movement modal ===================== */

  const MOVEMENT_HINTS = {
    "Stock In": {
      label: "Quantity to add",
      hint: "Must be greater than zero",
      rule: "required|positiveNumber|maxValue:999999"
    },
    "Stock Out": {
      label: "Quantity to remove",
      hint: "Must be greater than zero and available in stock",
      rule: "required|positiveNumber|maxValue:999999"
    },
    Adjustment: {
      label: "Counted new total",
      hint: "The full quantity counted physically (0 allowed)",
      rule: "required|nonNegative|maxValue:999999"
    }
  };

  function setMovementType(type) {
    movementType = type;
    el.movementTypeGroup.querySelectorAll(".seg").forEach((btn) => {
      btn.classList.toggle("is-selected", btn.dataset.type === type);
    });
    const config = MOVEMENT_HINTS[type];
    el.quantityLabel.textContent = config.label;
    el.quantityHint.textContent = config.hint;
    el.stockQuantity.dataset.validate = config.rule;
    Validator.clearFieldError(el.stockQuantity);
  }

  function openStockModal(item) {
    stockItem = item;
    el.stockModalTitle.textContent = `Record stock movement · ${item.name}`;
    el.stockCurrentLine.innerHTML =
      `Current balance: <strong>${fmtQty(item.current_quantity)} ${UI.escapeHtml(item.unit)}</strong>` +
      ` · Minimum: ${fmtQty(item.minimum_stock)} ${UI.escapeHtml(item.unit)}`;
    el.stockQuantity.value = "";
    el.stockNote.value = "";
    setMovementType("Stock In");
    el.stockModal.hidden = false;
    el.stockQuantity.focus();
  }

  function closeStockModal() {
    el.stockModal.hidden = true;
    stockItem = null;
  }

  async function saveStock(event) {
    event.preventDefault();
    Validator.clearFieldError(el.stockQuantity);
    if (!Validator.validateForm(el.stockForm)) return;

    const payload = {
      transaction_type: movementType,
      quantity: Number(el.stockQuantity.value),
      note: (el.stockNote.value || "").trim() || null
    };

    el.stockSaveBtn.classList.add("is-loading");
    el.stockSaveBtn.disabled = true;
    try {
      const response = await API.post(`${ITEMS_URL}/${stockItem.id}/stock`, payload);
      UI.toast(response.message, "success");
      closeStockModal();
      await Promise.all([loadItems(), loadMovements()]);
    } catch (error) {
      UI.toast(error.message, "error");
    } finally {
      el.stockSaveBtn.classList.remove("is-loading");
      el.stockSaveBtn.disabled = false;
    }
  }

  /* ===================== Per-item history modal ===================== */

  function openHistoryModal(itemId) {
    el.historyDetailBody.innerHTML =
      '<tr><td colspan="5"><div class="skeleton-line" style="width:60%"></div></td></tr>';
    el.historyModalTitle.textContent = "Movement history";
    el.historyModal.hidden = false;

    API.get(`${ITEMS_URL}/${itemId}`)
      .then((response) => {
        const item = response.data;
        el.historyModalTitle.textContent = `Movement history · ${item.name}`;
        if (item.transactions.length === 0) {
          el.historyDetailBody.innerHTML =
            '<tr class="empty-row"><td colspan="5">No movements recorded yet.</td></tr>';
          return;
        }
        el.historyDetailBody.innerHTML = item.transactions
          .map(
            (t) => `
            <tr>
              <td>${fmtWhen(t.created_at)}</td>
              <td>${movementBadge(t.transaction_type)}</td>
              <td class="num">${fmtQty(t.quantity)}</td>
              <td class="num qty-cell">${fmtQty(t.balance_after)}</td>
              <td>${UI.escapeHtml(t.note || "—")}</td>
            </tr>`
          )
          .join("");
      })
      .catch((error) => {
        el.historyDetailBody.innerHTML = `<tr class="empty-row"><td colspan="5">${UI.escapeHtml(error.message)}</td></tr>`;
      });
  }

  function closeHistoryModal() {
    el.historyModal.hidden = true;
  }

  /* ===================== Wiring ===================== */

  function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadItems, 300);
  }

  function wireModal(modalNode, closeFn) {
    modalNode.querySelector("[data-close-modal]").addEventListener("click", closeFn);
    modalNode.addEventListener("click", (event) => {
      if (event.target === modalNode) closeFn();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    loadSuppliers();
    loadCategories();
    loadItems();
    loadMovements();

    el.addItemBtn.addEventListener("click", () => openItemModal(null));
    el.search.addEventListener("input", debounceSearch);
    el.categoryFilter.addEventListener("change", loadItems);
    el.supplierFilter.addEventListener("change", loadItems);
    el.lowStockOnly.addEventListener("change", loadItems);
    el.movementTypeFilter.addEventListener("change", loadMovements);
    el.refreshHistoryBtn.addEventListener("click", loadMovements);

    el.itemTableBody.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const row = button.closest("tr[data-id]");
      const item = items.find((i) => i.id === Number(row.dataset.id));
      if (!item) return;

      if (button.dataset.action === "edit") openItemModal(item);
      else if (button.dataset.action === "delete") deleteItem(row);
      else if (button.dataset.action === "stock") openStockModal(item);
      else if (button.dataset.action === "history") openHistoryModal(item.id);
    });

    el.itemForm.addEventListener("submit", saveItem);
    wireModal(el.itemModal, closeItemModal);

    el.movementTypeGroup.addEventListener("click", (event) => {
      const button = event.target.closest(".seg");
      if (button) setMovementType(button.dataset.type);
    });
    el.stockForm.addEventListener("submit", saveStock);
    wireModal(el.stockModal, closeStockModal);

    wireModal(el.historyModal, closeHistoryModal);

    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      if (!el.itemModal.hidden) closeItemModal();
      if (!el.stockModal.hidden) closeStockModal();
      if (!el.historyModal.hidden) closeHistoryModal();
    });

    ITEM_FIELD_NAMES.forEach((name) => {
      const input = byName(name);
      if (input) input.addEventListener("input", () => Validator.clearFieldError(input));
    });
    [el.stockQuantity, el.stockNote].forEach((input) => {
      input.addEventListener("input", () => Validator.clearFieldError(input));
    });
  });
})();
