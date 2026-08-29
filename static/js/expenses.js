(function () {
  "use strict";

  const API_URL = "/api/expenses";
  const OPTIONS_URL = "/api/expenses/options";

  let expenses = [];
  let categories = [];
  let paymentMethods = ["Cash", "UPI", "Card", "Other"];
  let editingId = null;
  let searchTimer;

  let tableBody;
  let searchInput;
  let categoryFilter;
  let methodFilter;
  let startDateFilter;
  let endDateFilter;
  let clearFiltersBtn;
  let statCount;
  let statTotal;
  let statCategories;
  let modal;
  let form;
  let saveBtn;
  let modalTitle;

  const byName = (name) => form.elements.namedItem(name);

  function skeletonRows() {
    const rows = [];
    for (let i = 0; i < 3; i += 1) {
      rows.push(
        `<tr class="skeleton-row">${["35%", "20%", "20%", "25%", "20%", "35%", "30%"]
          .map((width) => `<td><div class="skeleton-line" style="width:${width}"></div></td>`)
          .join("")}</tr>`
      );
    }
    tableBody.innerHTML = rows.join("");
  }

  function emptyRow(message, hint) {
    return `
      <tr class="empty-row">
        <td colspan="7">
          <div class="empty-state">
            <div class="es-icon" data-icon="expenses"></div>
            <h4>${message}</h4>
            <p>${hint}</p>
          </div>
        </td>
      </tr>`;
  }

  function dayLabel(isoDate) {
    if (!isoDate) return "—";
    return new Date(`${isoDate}T00:00:00`).toLocaleDateString("en-IN",
      { day: "numeric", month: "short", year: "numeric" });
  }

  function categoryBadge(category) {
    return `<span class="badge badge-muted">${UI.escapeHtml(category)}</span>`;
  }

  function renderStats() {
    if (!expenses.length) {
      statCount.textContent = "0";
      statTotal.textContent = UI.formatMoney(0);
      statCategories.textContent = "0";
      return;
    }
    const total = expenses.reduce((sum, e) => sum + Number(e.amount), 0);
    const cats = new Set(expenses.map((e) => e.category));
    statCount.textContent = String(expenses.length);
    statTotal.textContent = UI.formatMoney(total);
    statCategories.textContent = String(cats.size);
  }

  function render() {
    document.querySelectorAll("[data-icon]").forEach((node) => {
      node.innerHTML = UI.ICONS[node.dataset.icon] || "";
    });

    renderStats();

    if (expenses.length === 0) {
      const filtered =
        Boolean(searchInput.value) || Boolean(categoryFilter.value) ||
        Boolean(methodFilter.value) || Boolean(startDateFilter.value) || Boolean(endDateFilter.value);
      tableBody.innerHTML = emptyRow(
        "No expenses found",
        filtered
          ? "Nothing matches the current filters. Adjust them or record a new expense."
          : 'Record the first expense with "+ New expense".',
        7
      );
      return;
    }

    tableBody.innerHTML = expenses
      .map((e) => `
        <tr data-id="${e.id}">
          <td><strong>${UI.escapeHtml(e.title)}</strong></td>
          <td>${categoryBadge(e.category)}</td>
          <td class="num"><strong>${UI.formatMoney(e.amount)}</strong></td>
          <td>${dayLabel(e.expense_date)}</td>
          <td>${UI.escapeHtml(e.payment_method)}</td>
          <td>${e.notes ? UI.escapeHtml(e.notes) : "—"}</td>
          <td>
            <div class="row-actions">
              <button type="button" class="btn btn-ghost btn-row" data-action="edit">Edit</button>
              <button type="button" class="btn btn-ghost btn-row" data-action="delete">Delete</button>
            </div>
          </td>
        </tr>`)
      .join("");
  }

  function queryParams() {
    const params = new URLSearchParams();
    const search = searchInput.value.trim();
    if (search) params.set("search", search);
    if (categoryFilter.value) params.set("category", categoryFilter.value);
    if (methodFilter.value) params.set("payment_method", methodFilter.value);
    if (startDateFilter.value) params.set("start_date", startDateFilter.value);
    if (endDateFilter.value) params.set("end_date", endDateFilter.value);
    return params.toString();
  }

  async function loadExpenses() {
    skeletonRows();
    try {
      const query = queryParams();
      const response = await API.get(`${API_URL}${query ? `?${query}` : ""}`);
      expenses = response.data.items;
      render();
    } catch (error) {
      tableBody.innerHTML = emptyRow("Could not load expenses", error.message);
    }
  }

  function scheduleSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadExpenses, 300);
  }

  async function loadOptions() {
    try {
      const response = await API.get(OPTIONS_URL);
      categories = response.data.categories;
      paymentMethods = response.data.payment_methods;

      const catOptions = categories
        .map((c) => `<option value="${UI.escapeHtml(c)}">${UI.escapeHtml(c)}</option>`)
        .join("");
      categoryFilter.innerHTML = '<option value="">All categories</option>' + catOptions;
      byName("category").innerHTML = '<option value="">Select category…</option>' + catOptions;

      const methodOptions = paymentMethods
        .map((m) => `<option>${UI.escapeHtml(m)}</option>`)
        .join("");
      methodFilter.innerHTML = '<option value="">All methods</option>' + methodOptions;
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  function openModal(expense) {
    editingId = expense ? expense.id : null;
    modalTitle.textContent = expense ? "Edit expense" : "New expense";
    byName("title").value = expense ? expense.title : "";
    byName("category").value = expense ? expense.category : "";
    byName("amount").value = expense ? expense.amount : "";
    byName("expense_date").value = expense && expense.expense_date ? expense.expense_date : "";
    byName("payment_method").value = expense ? expense.payment_method : "Cash";
    byName("notes").value = expense && expense.notes ? expense.notes : "";
    clearErrors();
    modal.hidden = false;
    byName("title").focus();
  }

  function closeModal() {
    modal.hidden = true;
    editingId = null;
  }

  const FIELD_NAMES = ["title", "category", "amount", "notes"];

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

  function buildPayload() {
    return {
      title: byName("title").value.trim(),
      category: byName("category").value,
      amount: Number(byName("amount").value),
      expense_date: byName("expense_date").value || null,
      payment_method: byName("payment_method").value,
      notes: (byName("notes").value || "").trim() || null
    };
  }

  async function saveExpense(event) {
    event.preventDefault();
    clearErrors();

    if (!Validator.validateForm(form)) {
      UI.toast("Please correct the highlighted fields.", "error");
      return;
    }

    const payload = buildPayload();

    saveBtn.classList.add("is-loading");
    saveBtn.disabled = true;
    try {
      if (editingId === null) {
        await API.post(API_URL, payload);
        UI.toast("Expense recorded.", "success");
      } else {
        await API.put(`${API_URL}/${editingId}`, payload);
        UI.toast("Expense updated.", "success");
      }
      closeModal();
      await loadExpenses();
    } catch (error) {
      applyServerErrors(error.errors);
      UI.toast(error.message, "error");
    } finally {
      saveBtn.classList.remove("is-loading");
      saveBtn.disabled = false;
    }
  }

  async function deleteExpense(row) {
    const expense = expenses.find((e) => e.id === Number(row.dataset.id));
    if (!expense) return;

    const confirmed = await UI.confirmDialog({
      title: "Delete expense?",
      message: `"${UI.escapeHtml(expense.title)}" (${UI.formatMoney(expense.amount)}) will be removed permanently.`,
      confirmText: "Delete"
    });
    if (!confirmed) return;

    try {
      await API.delete(`${API_URL}/${expense.id}`);
      UI.toast("Expense deleted.", "success");
      await loadExpenses();
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    tableBody = document.getElementById("expenseTableBody");
    searchInput = document.getElementById("searchInput");
    categoryFilter = document.getElementById("categoryFilter");
    methodFilter = document.getElementById("methodFilter");
    startDateFilter = document.getElementById("startDateFilter");
    endDateFilter = document.getElementById("endDateFilter");
    clearFiltersBtn = document.getElementById("clearFiltersBtn");
    statCount = document.getElementById("statCount");
    statTotal = document.getElementById("statTotal");
    statCategories = document.getElementById("statCategories");
    modal = document.getElementById("expenseModal");
    form = document.getElementById("expenseForm");
    saveBtn = document.getElementById("expenseSaveBtn");
    modalTitle = document.getElementById("expenseModalTitle");

    loadOptions();
    loadExpenses();

    document.getElementById("addExpenseBtn").addEventListener("click", () => openModal(null));
    searchInput.addEventListener("input", scheduleSearch);
    categoryFilter.addEventListener("change", loadExpenses);
    methodFilter.addEventListener("change", loadExpenses);
    startDateFilter.addEventListener("change", loadExpenses);
    endDateFilter.addEventListener("change", loadExpenses);
    clearFiltersBtn.addEventListener("click", () => {
      searchInput.value = "";
      categoryFilter.value = "";
      methodFilter.value = "";
      startDateFilter.value = "";
      endDateFilter.value = "";
      loadExpenses();
    });

    tableBody.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const row = button.closest("tr[data-id]");
      const action = button.dataset.action;
      if (action === "edit") {
        const expense = expenses.find((e) => e.id === Number(row.dataset.id));
        if (expense) openModal(expense);
      } else if (action === "delete") {
        deleteExpense(row);
      }
    });

    form.addEventListener("submit", saveExpense);
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
