(function () {
  "use strict";

  const API_URL = "/api/employees";
  let employees = [];
  let editingId = null;
  let searchTimer = null;

  let tableBody;
  let searchInput;
  let roleFilter;
  let includeInactive;
  let modal;
  let form;
  let saveBtn;
  let modalTitle;
  let baseSalaryHint;

  const byName = (name) => form.elements.namedItem(name);

  function skeletonRows() {
    const rows = [];
    for (let i = 0; i < 3; i += 1) {
      rows.push(
        `<tr class="skeleton-row">${["40%", "35%", "30%", "50%", "25%", "20%", "25%", "30%"]
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
            <div class="es-icon" data-icon="employees"></div>
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

  function formatJoined(value) {
    const date = new Date(`${value}T00:00:00`);
    return date.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  }

  function updateBaseSalaryHint() {
    const type = byName("salary_type").value;
    if (!type) {
      baseSalaryHint.textContent = "Amount as per salary type";
      return;
    }
    const unit = { Monthly: "per month", Daily: "per day", Hourly: "per hour" }[type];
    baseSalaryHint.textContent = `Amount ${unit}`;
  }

  function render() {
    document.querySelectorAll("#employeeTableBody [data-icon]").forEach((node) => {
      node.innerHTML = UI.ICONS[node.dataset.icon] || "";
    });

    if (employees.length === 0) {
      const filtered = Boolean(searchInput.value.trim()) || Boolean(roleFilter.value) || !includeInactive.checked;
      tableBody.innerHTML = emptyRow(
        "No employees found",
        filtered
          ? "Nothing matches the current filters. Adjust them or add a new employee."
          : 'Add your first team member with "+ Add employee" — chefs, waiters, helpers…',
        8
      );
      return;
    }

    tableBody.innerHTML = employees
      .map((e) => `
        <tr data-id="${e.id}">
          <td>
            <strong>${UI.escapeHtml(e.name)}</strong>
            ${e.email ? `<div class="item-sub">${UI.escapeHtml(e.email)}</div>` : ""}
          </td>
          <td>${UI.escapeHtml(e.mobile)}</td>
          <td><span class="badge badge-clay">${UI.escapeHtml(e.role)}</span></td>
          <td>${formatJoined(e.joining_date)}</td>
          <td>${UI.escapeHtml(e.salary_type)}</td>
          <td class="num">${UI.formatMoney(e.base_salary)}</td>
          <td>${statusBadge(e.is_active)}</td>
          <td>
            <div class="row-actions">
              <button type="button" class="btn btn-ghost btn-row" data-action="edit">Edit</button>
              <button type="button" class="btn btn-ghost btn-row" data-action="delete">Delete</button>
            </div>
          </td>
        </tr>`)
      .join("");
  }

  async function loadEmployees() {
    skeletonRows();
    try {
      const params = new URLSearchParams({ include_inactive: String(includeInactive.checked) });
      const term = searchInput.value.trim();
      if (term) params.set("search", term);
      if (roleFilter.value) params.set("role", roleFilter.value);
      const response = await API.get(`${API_URL}?${params.toString()}`);
      employees = response.data.items;
      render();
    } catch (error) {
      tableBody.innerHTML = emptyRow("Could not load employees", error.message, 8);
    }
  }

  function openModal(employee) {
    editingId = employee ? employee.id : null;
    modalTitle.textContent = employee ? `Edit employee · ${employee.name}` : "New employee";
    byName("name").value = employee ? employee.name : "";
    byName("mobile").value = employee ? employee.mobile : "";
    byName("email").value = employee && employee.email ? employee.email : "";
    byName("address").value = employee && employee.address ? employee.address : "";
    byName("role").value = employee ? employee.role : "";
    byName("joining_date").value = employee ? employee.joining_date : "";
    byName("salary_type").value = employee ? employee.salary_type : "";
    byName("base_salary").value = employee ? employee.base_salary : "";
    byName("is_active").checked = employee ? employee.is_active : true;
    updateBaseSalaryHint();
    clearErrors();
    modal.hidden = false;
    byName("name").focus();
  }

  function closeModal() {
    modal.hidden = true;
    editingId = null;
  }

  const FIELD_NAMES = ["name", "mobile", "email", "address", "role", "joining_date", "salary_type", "base_salary"];

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

  function validateJoiningDate() {
    const input = byName("joining_date");
    if (!input.value) return;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (new Date(`${input.value}T00:00:00`) > today) {
      Validator.showFieldError(input, "Joining date cannot be in the future.");
      return false;
    }
    return true;
  }

  async function saveEmployee(event) {
    event.preventDefault();
    clearErrors();

    if (!Validator.validateForm(form)) {
      UI.toast("Please correct the highlighted fields.", "error");
      return;
    }
    if (!validateJoiningDate()) {
      UI.toast("Please correct the highlighted fields.", "error");
      return;
    }

    const payload = {
      name: byName("name").value.trim(),
      mobile: byName("mobile").value.trim(),
      email: (byName("email").value || "").trim() || null,
      address: (byName("address").value || "").trim() || null,
      role: byName("role").value,
      joining_date: byName("joining_date").value,
      salary_type: byName("salary_type").value,
      base_salary: Number(byName("base_salary").value),
      is_active: byName("is_active").checked
    };

    saveBtn.classList.add("is-loading");
    saveBtn.disabled = true;
    try {
      if (editingId === null) {
        await API.post(API_URL, payload);
        UI.toast("Employee created.", "success");
      } else {
        await API.put(`${API_URL}/${editingId}`, payload);
        UI.toast("Employee updated.", "success");
      }
      closeModal();
      await loadEmployees();
    } catch (error) {
      applyServerErrors(error.errors);
      UI.toast(error.message, "error");
    } finally {
      saveBtn.classList.remove("is-loading");
      saveBtn.disabled = false;
    }
  }

  async function deleteEmployee(row) {
    const employee = employees.find((e) => e.id === Number(row.dataset.id));
    if (!employee) return;

    const confirmed = await UI.confirmDialog({
      title: "Delete employee?",
      message: `"${UI.escapeHtml(employee.name)}" will be removed permanently. Employees with recorded salary payments cannot be deleted until their salary history is removed.`,
      confirmText: "Delete"
    });
    if (!confirmed) return;

    try {
      await API.delete(`${API_URL}/${employee.id}`);
      UI.toast("Employee deleted.", "success");
      await loadEmployees();
    } catch (error) {
      UI.toast(error.status === 409 ? `${employee.name} has salary records. Remove them on the Salaries page first.` : error.message, "error");
    }
  }

  function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadEmployees, 300);
  }

  document.addEventListener("DOMContentLoaded", () => {
    tableBody = document.getElementById("employeeTableBody");
    searchInput = document.getElementById("employeeSearch");
    roleFilter = document.getElementById("roleFilter");
    includeInactive = document.getElementById("includeInactiveEmployees");
    modal = document.getElementById("employeeModal");
    form = document.getElementById("employeeForm");
    saveBtn = document.getElementById("employeeSaveBtn");
    modalTitle = document.getElementById("employeeModalTitle");
    baseSalaryHint = document.getElementById("baseSalaryHint");

    loadEmployees();

    document.getElementById("addEmployeeBtn").addEventListener("click", () => openModal(null));
    searchInput.addEventListener("input", debounceSearch);
    roleFilter.addEventListener("change", loadEmployees);
    includeInactive.addEventListener("change", loadEmployees);

    tableBody.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const row = button.closest("tr[data-id]");
      if (button.dataset.action === "edit") {
        const employee = employees.find((e) => e.id === Number(row.dataset.id));
        if (employee) openModal(employee);
      } else if (button.dataset.action === "delete") {
        deleteEmployee(row);
      }
    });

    form.addEventListener("submit", saveEmployee);
    byName("salary_type").addEventListener("change", updateBaseSalaryHint);
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
