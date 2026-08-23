(function () {
  "use strict";

  const API_URL = "/api/suppliers";
  let suppliers = [];
  let editingId = null;
  let searchTimer = null;

  let tableBody;
  let searchInput;
  let includeInactive;
  let modal;
  let form;
  let saveBtn;
  let modalTitle;

  const byName = (name) => form.elements.namedItem(name);

  function skeletonRows() {
    const rows = [];
    for (let i = 0; i < 3; i += 1) {
      rows.push(
        `<tr class="skeleton-row">${["40%", "35%", "30%", "50%", "20%", "25%", "30%"]
          .map((width) => `<td><div class="skeleton-line" style="width:${width}"></div></td>`)
          .join("")}</tr>`
      );
    }
    tableBody.innerHTML = rows.join("");
  }

  function emptyRow(message, hint, colspan) {
    return `
      <tr class="empty-row">
        <td colspan="${colspan}">
          <div class="empty-state">
            <div class="es-icon" data-icon="suppliers"></div>
            <h4>${message}</h4>
            <p>${hint}</p>
          </div>
        </td>
      </tr>`;
  }

  function statusBadge(isActive) {
    return isActive
      ? '<span class="badge badge-ok">Active</span>'
      : '<span class="badge badge-muted">Inactive</span>';
  }

  function render() {
    document.querySelectorAll("#supplierTableBody [data-icon]").forEach((node) => {
      node.innerHTML = UI.ICONS[node.dataset.icon] || "";
    });

    if (suppliers.length === 0) {
      const filtered = Boolean(searchInput.value.trim()) || !includeInactive.checked;
      tableBody.innerHTML = emptyRow(
        "No suppliers found",
        filtered
          ? "Nothing matches the current filters. Adjust them or add a new supplier."
          : 'Add your first supplier with "+ Add supplier" — milk, beans, vegetables…',
        7
      );
      return;
    }

    tableBody.innerHTML = suppliers
      .map((s) => {
        const contact = [s.contact_person, s.phone].filter(Boolean).join(" · ");
        return `
        <tr data-id="${s.id}">
          <td><strong>${UI.escapeHtml(s.name)}</strong></td>
          <td>${UI.escapeHtml(contact || "—")}</td>
          <td>${UI.escapeHtml(s.phone || "—")}</td>
          <td>${UI.escapeHtml(s.materials_supplied || "—")}</td>
          <td class="num">${s.inventory_item_count}</td>
          <td>${statusBadge(s.is_active)}</td>
          <td>
            <div class="row-actions">
              <button type="button" class="btn btn-ghost btn-row" data-action="edit">Edit</button>
              <button type="button" class="btn btn-ghost btn-row" data-action="delete">Delete</button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  }

  async function loadSuppliers() {
    skeletonRows();
    try {
      const params = new URLSearchParams({ include_inactive: String(includeInactive.checked) });
      const term = searchInput.value.trim();
      if (term) params.set("search", term);
      const response = await API.get(`${API_URL}?${params.toString()}`);
      suppliers = response.data.items;
      render();
    } catch (error) {
      tableBody.innerHTML = emptyRow("Could not load suppliers", error.message, 7);
    }
  }

  function openModal(supplier) {
    editingId = supplier ? supplier.id : null;
    modalTitle.textContent = supplier ? `Edit supplier · ${supplier.name}` : "New supplier";
    byName("name").value = supplier ? supplier.name : "";
    byName("contact_person").value = supplier && supplier.contact_person ? supplier.contact_person : "";
    byName("phone").value = supplier && supplier.phone ? supplier.phone : "";
    byName("email").value = supplier && supplier.email ? supplier.email : "";
    byName("address").value = supplier && supplier.address ? supplier.address : "";
    byName("materials_supplied").value =
      supplier && supplier.materials_supplied ? supplier.materials_supplied : "";
    byName("is_active").checked = supplier ? supplier.is_active : true;
    clearErrors();
    modal.hidden = false;
    byName("name").focus();
  }

  function closeModal() {
    modal.hidden = true;
    editingId = null;
  }

  const FIELD_NAMES = ["name", "contact_person", "phone", "email", "address", "materials_supplied"];

  function clearErrors() {
    FIELD_NAMES.forEach((name) => {
      const input = byName(name);
      if (input) Validator.clearFieldError(input);
    });
  }

  function applyServerErrors(errors) {
    let firstField = null;
    (errors || []).forEach((error) => {
      const input = error.field ? form.elements.namedItem(error.field) : null;
      if (input) {
        Validator.showFieldError(input, error.message);
        if (!firstField) firstField = input;
      }
    });
    if (firstField) firstField.focus();
  }

  function localDuplicateCheck(name) {
    const lower = name.toLowerCase();
    return suppliers.find((s) => s.name.toLowerCase() === lower && s.id !== editingId);
  }

  async function saveSupplier(event) {
    event.preventDefault();
    clearErrors();

    if (!Validator.validateForm(form)) return;

    const name = byName("name").value.trim();
    const duplicate = localDuplicateCheck(name);
    if (duplicate) {
      Validator.showFieldError(byName("name"), `A supplier named "${duplicate.name}" already exists.`);
      UI.toast("Please correct the highlighted fields.", "error");
      return;
    }

    const payload = {
      name,
      contact_person: (byName("contact_person").value || "").trim() || null,
      phone: (byName("phone").value || "").trim() || null,
      email: (byName("email").value || "").trim() || null,
      address: (byName("address").value || "").trim() || null,
      materials_supplied: (byName("materials_supplied").value || "").trim() || null,
      is_active: byName("is_active").checked
    };

    saveBtn.classList.add("is-loading");
    saveBtn.disabled = true;
    try {
      if (editingId === null) {
        await API.post(API_URL, payload);
        UI.toast("Supplier created.", "success");
      } else {
        await API.put(`${API_URL}/${editingId}`, payload);
        UI.toast("Supplier updated.", "success");
      }
      closeModal();
      await loadSuppliers();
    } catch (error) {
      applyServerErrors(error.errors);
      UI.toast(error.message, "error");
    } finally {
      saveBtn.classList.remove("is-loading");
      saveBtn.disabled = false;
    }
  }

  async function deleteSupplier(row) {
    const supplier = suppliers.find((s) => s.id === Number(row.dataset.id));
    if (!supplier) return;

    const confirmed = await UI.confirmDialog({
      title: "Delete supplier?",
      message: `"${UI.escapeHtml(supplier.name)}" will be removed permanently. Raw materials linked to this supplier simply lose the link — their stock and history stay intact.`,
      confirmText: "Delete"
    });
    if (!confirmed) return;

    try {
      await API.delete(`${API_URL}/${supplier.id}`);
      UI.toast("Supplier deleted.", "success");
      await loadSuppliers();
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadSuppliers, 300);
  }

  document.addEventListener("DOMContentLoaded", () => {
    tableBody = document.getElementById("supplierTableBody");
    searchInput = document.getElementById("supplierSearch");
    includeInactive = document.getElementById("includeInactiveSuppliers");
    modal = document.getElementById("supplierModal");
    form = document.getElementById("supplierForm");
    saveBtn = document.getElementById("supplierSaveBtn");
    modalTitle = document.getElementById("supplierModalTitle");

    loadSuppliers();

    document.getElementById("addSupplierBtn").addEventListener("click", () => openModal(null));
    searchInput.addEventListener("input", debounceSearch);
    includeInactive.addEventListener("change", loadSuppliers);

    tableBody.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const row = button.closest("tr[data-id]");
      if (button.dataset.action === "edit") {
        const supplier = suppliers.find((s) => s.id === Number(row.dataset.id));
        if (supplier) openModal(supplier);
      } else if (button.dataset.action === "delete") {
        deleteSupplier(row);
      }
    });

    form.addEventListener("submit", saveSupplier);
    modal.querySelector("[data-close-modal]").addEventListener("click", closeModal);
    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeModal();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !modal.hidden) closeModal();
    });

    FIELD_NAMES.forEach((name) => {
      const input = byName(name);
      if (input) input.addEventListener("input", () => Validator.clearFieldError(input));
    });
  });
})();
