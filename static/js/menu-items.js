(function () {
  "use strict";

  const API_URL = "/api/menu/items";
  let items = [];
  let categories = [];
  let editingId = null;
  let searchTimer = null;

  let tableBody;
  let searchInput;
  let categoryFilter;
  let availabilityFilter;
  let modal;
  let form;
  let saveBtn;
  let modalTitle;
  let categorySelect;
  let imagePreview;
  let imageFallback;

  const byName = (name) => form.elements.namedItem(name);

  function skeletonRows() {
    const widths = ["46px", "55%", "30%", "20%", "25%", "35%"];
    const rows = [];
    for (let i = 0; i < 3; i += 1) {
      rows.push(
        `<tr class="skeleton-row">${widths
          .map((width) => `<td><div class="skeleton-line" style="width:${width}"></div></td>`)
          .join("")}</tr>`
      );
    }
    tableBody.innerHTML = rows.join("");
  }

  function emptyRow() {
    const filtered =
      Boolean(searchInput.value.trim()) ||
      categoryFilter.value !== "" ||
      availabilityFilter.value !== "";
    return `
      <tr class="empty-row">
        <td colspan="6">
          <div class="empty-state">
            <div class="es-icon" data-icon="menu"></div>
            <h4>No menu items found</h4>
            <p>${
              filtered
                ? "Nothing matches the current filters. Adjust them or add a new item."
                : 'Add your first dish — click "+ Add item". Create a category first if the list is empty.'
            }</p>
          </div>
        </td>
      </tr>`;
  }

  function thumbCell(item) {
    if (item.image_url) {
      return `<img class="thumb" src="${UI.escapeHtml(item.image_url)}" alt="" loading="lazy" />`;
    }
    return '<div class="thumb-fallback" data-icon="cup"></div>';
  }

  function badges(item) {
    const parts = [];
    parts.push(item.is_vegetarian ? '<span class="badge badge-ok">Veg</span>' : '<span class="badge badge-clay">Non-veg</span>');
    if (item.is_popular) parts.push('<span class="badge badge-popular">Popular ★</span>');
    return `<span class="item-badges">${parts.join("")}</span>`;
  }

  function render() {
    if (items.length === 0) {
      tableBody.innerHTML = emptyRow();
      document.querySelectorAll("#itemTableBody [data-icon]").forEach((node) => {
        node.innerHTML = UI.ICONS[node.dataset.icon] || "";
      });
      return;
    }

    tableBody.innerHTML = items
      .map((item) => {
        const categoryName = item.category ? item.category.name : "—";
        const statusBadge = item.is_available
          ? '<span class="badge badge-ok">Available</span>'
          : '<span class="badge badge-muted">Sold out</span>';
        return `
        <tr data-id="${item.id}">
          <td>${thumbCell(item)}</td>
          <td>
            <div class="item-cell">
              <strong>${UI.escapeHtml(item.name)}</strong>
              ${badges(item)}
            </div>
          </td>
          <td>${categoryName === "—" ? "—" : UI.escapeHtml(categoryName)}</td>
          <td class="num">${UI.formatMoney(item.price)}</td>
          <td>${statusBadge}</td>
          <td>
            <div class="row-actions">
              <button type="button" class="btn btn-ghost btn-row" data-action="edit">Edit</button>
              <button type="button" class="btn btn-ghost btn-row" data-action="delete">Delete</button>
            </div>
          </td>
        </tr>`;
      })
      .join("");

    tableBody.querySelectorAll("img.thumb").forEach((img) => {
      img.addEventListener("error", () => {
        const fallback = document.createElement("div");
        fallback.className = "thumb-fallback";
        fallback.innerHTML = UI.ICONS.cup;
        img.replaceWith(fallback);
      });
    });
  }

  async function loadItems() {
    skeletonRows();
    try {
      const params = new URLSearchParams();
      const term = searchInput.value.trim();
      if (term) params.set("search", term);
      if (categoryFilter.value !== "") params.set("category_id", categoryFilter.value);
      if (availabilityFilter.value === "available") params.set("available_only", "true");
      const query = params.toString();
      const response = await API.get(query ? `${API_URL}?${query}` : API_URL);
      items = response.data.items;
      render();
    } catch (error) {
      tableBody.innerHTML = `
        <tr class="empty-row"><td colspan="6"><div class="empty-state">
          <div class="es-icon" data-icon="menu"></div>
          <h4>Could not load menu items</h4><p>${UI.escapeHtml(error.message)}</p>
        </div></td></tr>`;
    }
  }

  async function loadCategories() {
    try {
      const response = await API.get("/api/categories?include_inactive=true");
      categories = response.data.items;
    } catch (error) {
      categories = [];
    }
    populateCategoryOptions(categoryFilter, "All categories");
    populateCategoryOptions(categorySelect, "Select a category…");
  }

  function populateCategoryOptions(select, allLabel) {
    const previous = select.value;
    select.innerHTML = `<option value="">${allLabel}</option>`;
    categories.forEach((category) => {
      const suffix = category.is_active ? "" : " (inactive)";
      const option = document.createElement("option");
      option.value = String(category.id);
      option.textContent = `${category.name}${suffix}`;
      select.appendChild(option);
    });
    if ([...select.options].some((option) => option.value === previous)) {
      select.value = previous;
    }
  }

  function updateImagePreview() {
    const url = (byName("image_url").value || "").trim();
    if (!url) {
      imagePreview.hidden = true;
      imagePreview.removeAttribute("src");
      imageFallback.hidden = false;
      imageFallback.textContent = "No image set";
      return;
    }
    imagePreview.onerror = () => {
      imagePreview.hidden = true;
      imagePreview.removeAttribute("src");
      imageFallback.hidden = false;
      imageFallback.textContent = "Image could not be loaded";
    };
    imagePreview.onload = () => {
      imageFallback.hidden = true;
      imageFallback.textContent = "No image set";
    };
    imagePreview.src = url;
    imagePreview.hidden = false;
  }

  function openModal(item) {
    if (categories.length === 0) {
      UI.toast("Create at least one category before adding items.", "warning");
      document.getElementById("categoriesCard").scrollIntoView({ behavior: "smooth" });
      return;
    }
    editingId = item ? item.id : null;
    modalTitle.textContent = item ? `Edit item · ${item.name}` : "New menu item";
    byName("category_id").value = item ? String(item.category_id) : "";
    byName("name").value = item ? item.name : "";
    byName("price").value = item ? String(item.price) : "";
    byName("description").value = item && item.description ? item.description : "";
    byName("image_url").value = item && item.image_url ? item.image_url : "";
    byName("is_vegetarian").checked = item ? item.is_vegetarian : true;
    byName("is_popular").checked = item ? item.is_popular : false;
    byName("is_available").checked = item ? item.is_available : true;
    clearErrors();
    updateImagePreview();
    modal.hidden = false;
    byName("category_id").focus();
  }

  function closeModal() {
    modal.hidden = true;
    editingId = null;
  }

  function clearErrors() {
    ["category_id", "name", "price", "description", "image_url"].forEach((name) => {
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

  function localDuplicateCheck(categoryId, name) {
    const lower = name.toLowerCase();
    return items.find(
      (item) =>
        item.category_id === categoryId &&
        item.name.toLowerCase() === lower &&
        item.id !== editingId
    );
  }

  async function saveItem(event) {
    event.preventDefault();
    clearErrors();

    if (!Validator.validateForm(form)) return;

    const categoryId = Number(byName("category_id").value);
    const name = byName("name").value.trim();
    const duplicate = localDuplicateCheck(categoryId, name);
    if (duplicate) {
      Validator.showFieldError(byName("name"), `"${duplicate.name}" already exists in this category.`);
      UI.toast("Please correct the highlighted fields.", "error");
      return;
    }

    const valueOrNone = (fieldName) => (byName(fieldName).value || "").trim() || null;
    const payload = {
      category_id: categoryId,
      name,
      price: Number(byName("price").value),
      description: valueOrNone("description"),
      image_url: valueOrNone("image_url"),
      is_vegetarian: byName("is_vegetarian").checked,
      is_popular: byName("is_popular").checked,
      is_available: byName("is_available").checked
    };

    saveBtn.classList.add("is-loading");
    saveBtn.disabled = true;
    try {
      if (editingId === null) {
        await API.post(API_URL, payload);
        UI.toast("Menu item created.", "success");
      } else {
        await API.put(`${API_URL}/${editingId}`, payload);
        UI.toast("Menu item updated.", "success");
      }
      closeModal();
      await Promise.all([loadItems(), loadCategories()]);
    } catch (error) {
      applyServerErrors(error.errors);
      UI.toast(error.message, "error");
    } finally {
      saveBtn.classList.remove("is-loading");
      saveBtn.disabled = false;
    }
  }

  async function deleteItem(row) {
    const item = items.find((i) => i.id === Number(row.dataset.id));
    if (!item) return;

    const confirmed = await UI.confirmDialog({
      title: "Delete menu item?",
      message: `"${UI.escapeHtml(item.name)}" will be removed from the menu permanently.`,
      confirmText: "Delete"
    });
    if (!confirmed) return;

    try {
      await API.delete(`${API_URL}/${item.id}`);
      UI.toast("Menu item deleted.", "success");
      await Promise.all([loadItems(), loadCategories()]);
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadItems, 300);
  }

  document.addEventListener("DOMContentLoaded", () => {
    tableBody = document.getElementById("itemTableBody");
    searchInput = document.getElementById("itemSearch");
    categoryFilter = document.getElementById("itemCategoryFilter");
    availabilityFilter = document.getElementById("itemAvailabilityFilter");
    modal = document.getElementById("itemModal");
    form = document.getElementById("itemForm");
    saveBtn = document.getElementById("itemSaveBtn");
    modalTitle = document.getElementById("itemModalTitle");
    categorySelect = byName("category_id");
    imagePreview = document.getElementById("itemImagePreview");
    imageFallback = document.getElementById("itemImageFallback");

    loadCategories().then(loadItems);

    document.getElementById("addItemBtn").addEventListener("click", () => openModal(null));
    searchInput.addEventListener("input", debounceSearch);
    categoryFilter.addEventListener("change", loadItems);
    availabilityFilter.addEventListener("change", loadItems);

    tableBody.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const row = button.closest("tr[data-id]");
      if (button.dataset.action === "edit") {
        const item = items.find((i) => i.id === Number(row.dataset.id));
        if (item) openModal(item);
      } else if (button.dataset.action === "delete") {
        deleteItem(row);
      }
    });

    form.addEventListener("submit", saveItem);
    modal.querySelector("[data-close-modal]").addEventListener("click", closeModal);
    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeModal();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !modal.hidden) closeModal();
    });

    byName("image_url").addEventListener("input", updateImagePreview);
    ["category_id", "name", "price", "description", "image_url"].forEach((name) => {
      const input = byName(name);
      input.addEventListener("input", () => Validator.clearFieldError(input));
      input.addEventListener("change", () => Validator.clearFieldError(input));
    });

    document.addEventListener("categories:changed", () => {
      // Category names/counts shown in the items table may be stale after edits.
      if (document.getElementById("itemsCard")) loadCategories().then(loadItems);
    });
  });
})();
