(function () {
  "use strict";

  const API_URL = "/api/categories";
  let categories = [];
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

  function skeletonRows(placeholderCells) {
    const rows = [];
    for (let i = 0; i < 3; i += 1) {
      rows.push(
        `<tr class="skeleton-row">${placeholderCells
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
            <div class="es-icon" data-icon="menu"></div>
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
    if (categories.length === 0) {
      const filtered = Boolean(searchInput.value.trim()) || !includeInactive.checked;
      tableBody.innerHTML = emptyRow(
        "No categories found",
        filtered
          ? "Nothing matches the current filters. Adjust them or add a new category."
          : 'Start building your menu — click "+ Add category" to create the first one.',
        5
      );
      document.querySelectorAll("#categoryTableBody [data-icon]").forEach((node) => {
        node.innerHTML = UI.ICONS[node.dataset.icon] || "";
      });
      return;
    }

    tableBody.innerHTML = categories
      .map(
        (category) => `
        <tr data-id="${category.id}">
          <td><strong>${UI.escapeHtml(category.name)}</strong></td>
          <td>${UI.escapeHtml(category.description || "—")}</td>
          <td class="num">${category.item_count}</td>
          <td>${statusBadge(category.is_active)}</td>
          <td>
            <div class="row-actions">
              <button type="button" class="btn btn-ghost btn-row" data-action="edit">Edit</button>
              <button type="button" class="btn btn-ghost btn-row" data-action="delete">Delete</button>
            </div>
          </td>
        </tr>`
      )
      .join("");
  }

  async function loadCategories() {
    skeletonRows(["40%", "60%", "20%", "30%", "35%"]);
    try {
      const params = new URLSearchParams({ include_inactive: String(includeInactive.checked) });
      const term = searchInput.value.trim();
      if (term) params.set("search", term);
      const response = await API.get(`${API_URL}?${params.toString()}`);
      categories = response.data.items;
      render();
    } catch (error) {
      tableBody.innerHTML = emptyRow("Could not load categories", error.message, 5);
    }
  }

  function openModal(category) {
    editingId = category ? category.id : null;
    modalTitle.textContent = category ? `Edit category · ${category.name}` : "New category";
    byName("name").value = category ? category.name : "";
    byName("description").value = category && category.description ? category.description : "";
    byName("is_active").checked = category ? category.is_active : true;
    clearErrors();
    modal.hidden = false;
    byName("name").focus();
  }

  function closeModal() {
    modal.hidden = true;
    editingId = null;
  }

  function clearErrors() {
    ["name", "description"].forEach((name) => {
      const input = byName(name);
      if (input) Validator.clearFieldError(input);
    });
  }

  function applyServerErrors(errors) {
    let firstField = null;
    (errors || []).forEach((error) => {
      const input = error.field ? form.elements.namedItem(error.field === "is_active" ? "is_active" : error.field) : null;
      if (input) {
        Validator.showFieldError(input, error.message);
        if (!firstField) firstField = input;
      }
    });
    if (firstField) firstField.focus();
  }

  function localDuplicateCheck(name) {
    const lower = name.toLowerCase();
    return categories.find((c) => c.name.toLowerCase() === lower && c.id !== editingId);
  }

  async function saveCategory(event) {
    event.preventDefault();
    clearErrors();

    if (!Validator.validateForm(form)) return;

    const name = byName("name").value.trim();
    const duplicate = localDuplicateCheck(name);
    if (duplicate) {
      Validator.showFieldError(byName("name"), `A category named "${duplicate.name}" already exists.`);
      UI.toast("Please correct the highlighted fields.", "error");
      return;
    }

    const payload = {
      name,
      description: (byName("description").value || "").trim() || null,
      is_active: byName("is_active").checked
    };

    saveBtn.classList.add("is-loading");
    saveBtn.disabled = true;
    try {
      if (editingId === null) {
        await API.post(API_URL, payload);
        UI.toast("Category created.", "success");
      } else {
        await API.put(`${API_URL}/${editingId}`, payload);
        UI.toast("Category updated.", "success");
      }
      closeModal();
      await loadCategories();
      notifyCategoriesChanged();
    } catch (error) {
      applyServerErrors(error.errors);
      UI.toast(error.message, "error");
    } finally {
      saveBtn.classList.remove("is-loading");
      saveBtn.disabled = false;
    }
  }

  function notifyCategoriesChanged() {
    document.dispatchEvent(new CustomEvent("categories:changed"));
  }

  async function deleteCategory(row) {
    const category = categories.find((c) => c.id === Number(row.dataset.id));
    if (!category) return;

    const confirmed = await UI.confirmDialog({
      title: "Delete category?",
      message: `"${UI.escapeHtml(category.name)}" will be removed permanently. Categories with menu items cannot be deleted.`,
      confirmText: "Delete"
    });
    if (!confirmed) return;

    try {
      await API.delete(`${API_URL}/${category.id}`);
      UI.toast("Category deleted.", "success");
      await loadCategories();
      notifyCategoriesChanged();
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadCategories, 300);
  }

  document.addEventListener("DOMContentLoaded", () => {
    tableBody = document.getElementById("categoryTableBody");
    searchInput = document.getElementById("categorySearch");
    includeInactive = document.getElementById("includeInactiveCategories");
    modal = document.getElementById("categoryModal");
    form = document.getElementById("categoryForm");
    saveBtn = document.getElementById("categorySaveBtn");
    modalTitle = document.getElementById("categoryModalTitle");

    loadCategories();

    document.getElementById("addCategoryBtn").addEventListener("click", () => openModal(null));
    searchInput.addEventListener("input", debounceSearch);
    includeInactive.addEventListener("change", loadCategories);

    tableBody.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const row = button.closest("tr[data-id]");
      if (button.dataset.action === "edit") {
        const category = categories.find((c) => c.id === Number(row.dataset.id));
        if (category) openModal(category);
      } else if (button.dataset.action === "delete") {
        deleteCategory(row);
      }
    });

    form.addEventListener("submit", saveCategory);
    modal.querySelector("[data-close-modal]").addEventListener("click", closeModal);
    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeModal();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !modal.hidden) closeModal();
    });

    [byName("name"), byName("description")].forEach((input) => {
      input.addEventListener("input", () => Validator.clearFieldError(input));
    });
  });
})();
