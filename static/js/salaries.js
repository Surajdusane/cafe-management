(function () {
  "use strict";

  const API_URL = "/api/salaries";
  const EMPLOYEES_URL = "/api/employees";

  let salaries = [];
  let employees = [];
  let editingId = null;

  let tableBody;
  let employeeFilter;
  let monthFilter;
  let statusFilter;
  let clearFiltersBtn;
  let statRecords;
  let statPaid;
  let statUnpaid;
  let modal;
  let form;
  let saveBtn;
  let modalTitle;
  let netPreview;
  let employeeSalaryHint;

  const byName = (name) => form.elements.namedItem(name);

  function skeletonRows() {
    const rows = [];
    for (let i = 0; i < 3; i += 1) {
      rows.push(
        `<tr class="skeleton-row">${["45%", "20%", "20%", "20%", "25%", "30%", "20%", "25%", "30%"]
          .map((width) => `<td><div class="skeleton-line" style="width:${width}"></div></td>`)
          .join("")}</tr>`
      );
    }
    tableBody.innerHTML = rows.join("");
  }

  function emptyRow(message, hint) {
    return `
      <tr class="empty-row">
        <td colspan="9">
          <div class="empty-state">
            <div class="es-icon" data-icon="salaries"></div>
            <h4>${message}</h4>
            <p>${hint}</p>
          </div>
        </td>
      </tr>`;
  }

  function monthLabel(yyyyMm) {
    const date = new Date(`${yyyyMm}-01T00:00:00`);
    return date.toLocaleDateString("en-IN", { month: "short", year: "numeric" });
  }

  function dayLabel(isoDate) {
    if (!isoDate) return "—";
    return new Date(`${isoDate}T00:00:00`).toLocaleDateString("en-IN",
      { day: "numeric", month: "short", year: "numeric" });
  }

  function statusBadge(status) {
    return status === "Paid"
      ? '<span class="badge badge-ok">Paid</span>'
      : '<span class="badge badge-clay">Unpaid</span>';
  }

  function renderStats() {
    statRecords.textContent = String(salaries.length);
    const paid = salaries.filter((s) => s.payment_status === "Paid")
      .reduce((sum, s) => sum + Number(s.net_salary), 0);
    const unpaid = salaries.filter((s) => s.payment_status === "Unpaid")
      .reduce((sum, s) => sum + Number(s.net_salary), 0);
    statPaid.textContent = UI.formatMoney(paid);
    statUnpaid.textContent = UI.formatMoney(unpaid);
  }

  function render() {
    document.querySelectorAll("#salaryTableBody [data-icon]").forEach((node) => {
      node.innerHTML = UI.ICONS[node.dataset.icon] || "";
    });

    renderStats();

    if (salaries.length === 0) {
      const filtered =
        Boolean(employeeFilter.value) || Boolean(monthFilter.value) || Boolean(statusFilter.value);
      tableBody.innerHTML = emptyRow(
        "No salary records found",
        filtered
          ? "Nothing matches the current filters. Adjust them or record a new salary."
          : 'Record the first salary with "+ New salary record".',
        9
      );
      return;
    }

    tableBody.innerHTML = salaries
      .map((s) => `
        <tr data-id="${s.id}">
          <td><strong>${UI.escapeHtml(s.employee.name)}</strong>
              <div class="item-sub">${UI.escapeHtml(s.employee.role)}</div></td>
          <td>${monthLabel(s.salary_month)}</td>
          <td class="num">${UI.formatMoney(s.base_salary)}</td>
          <td class="num">${UI.formatMoney(s.bonus)}</td>
          <td class="num">−${UI.formatMoney(s.deduction)}</td>
          <td class="num"><strong>${UI.formatMoney(s.net_salary)}</strong></td>
          <td>${statusBadge(s.payment_status)}</td>
          <td>${dayLabel(s.payment_date)}</td>
          <td>
            <div class="row-actions">
              ${s.payment_status === "Unpaid"
                ? '<button type="button" class="btn btn-ghost btn-row" data-action="mark-paid">Mark paid</button>'
                : ""}
              <button type="button" class="btn btn-ghost btn-row" data-action="edit">Edit</button>
              <button type="button" class="btn btn-ghost btn-row" data-action="delete">Delete</button>
            </div>
          </td>
        </tr>`)
      .join("");
  }

  async function loadSalaries() {
    skeletonRows();
    try {
      const params = new URLSearchParams();
      if (employeeFilter.value) params.set("employee_id", employeeFilter.value);
      if (monthFilter.value) params.set("month", monthFilter.value);
      if (statusFilter.value) params.set("payment_status", statusFilter.value);
      const query = params.toString();
      const response = await API.get(`${API_URL}${query ? `?${query}` : ""}`);
      salaries = response.data.items;
      render();
    } catch (error) {
      tableBody.innerHTML = emptyRow("Could not load salaries", error.message);
    }
  }

  async function loadEmployees() {
    try {
      const response = await API.get(`${EMPLOYEES_URL}?include_inactive=true`);
      employees = response.data.items;

      const options = employees
        .map((e) => `<option value="${e.id}">${UI.escapeHtml(e.name)} · ${UI.escapeHtml(e.role)}${e.is_active ? "" : " (inactive)"}</option>`)
        .join("");

      employeeFilter.innerHTML = '<option value="">All employees</option>' + options;
      byName("employee_id").innerHTML = '<option value="">Select employee…</option>' + options;
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  function selectedEmployee() {
    return employees.find((e) => e.id === Number(byName("employee_id").value)) || null;
  }

  function updateEmployeeHint() {
    const employee = selectedEmployee();
    employeeSalaryHint.textContent = employee
      ? `Current base salary: ${UI.formatMoney(employee.base_salary)} (${employee.salary_type.toLowerCase()})`
      : "";
  }

  function effectiveBase() {
    const raw = byName("base_salary").value.trim();
    if (raw !== "") return Number(raw);
    const employee = selectedEmployee();
    return employee ? Number(employee.base_salary) : 0;
  }

  function updateNetPreview() {
    const base = effectiveBase();
    const bonus = Number(byName("bonus").value) || 0;
    const deduction = Number(byName("deduction").value) || 0;
    const net = Math.round((base + bonus - deduction) * 100) / 100;
    netPreview.textContent = UI.formatMoney(net);
    netPreview.style.color = net < 0 ? "var(--danger, #b3402a)" : "";
  }

  function openModal(salary) {
    editingId = salary ? salary.id : null;
    modalTitle.textContent = salary ? `Edit salary · ${monthLabel(salary.salary_month)}` : "New salary record";
    byName("employee_id").value = salary ? salary.employee_id : "";
    byName("salary_month").value = salary ? salary.salary_month : "";
    byName("base_salary").value = salary ? salary.base_salary : "";
    byName("bonus").value = salary ? salary.bonus : 0;
    byName("deduction").value = salary ? salary.deduction : 0;
    byName("payment_status").value = salary ? salary.payment_status : "Unpaid";
    byName("payment_date").value = salary && salary.payment_date ? salary.payment_date : "";
    byName("notes").value = salary && salary.notes ? salary.notes : "";
    updateEmployeeHint();
    updateNetPreview();
    clearErrors();
    modal.hidden = false;
    byName("employee_id").focus();
  }

  function closeModal() {
    modal.hidden = true;
    editingId = null;
  }

  const FIELD_NAMES = ["employee_id", "salary_month", "base_salary", "bonus", "deduction", "notes"];

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

  function validateNetNotNegative() {
    const net = effectiveBase() + (Number(byName("bonus").value) || 0);
    const deductionInput = byName("deduction");
    if ((Number(deductionInput.value) || 0) > net) {
      Validator.showFieldError(deductionInput, "Deduction is larger than base plus bonus.");
      return false;
    }
    return true;
  }

  function localDuplicateMonthCheck(employeeId, month) {
    return salaries.find(
      (s) => s.employee_id === Number(employeeId) && s.salary_month === month && s.id !== editingId
    );
  }

  function buildPayload() {
    return {
      employee_id: Number(byName("employee_id").value),
      salary_month: byName("salary_month").value,
      base_salary: byName("base_salary").value.trim() === ""
        ? null
        : Number(byName("base_salary").value),
      bonus: Number(byName("bonus").value) || 0,
      deduction: Number(byName("deduction").value) || 0,
      payment_status: byName("payment_status").value,
      payment_date: byName("payment_date").value || null,
      notes: (byName("notes").value || "").trim() || null
    };
  }

  async function saveSalary(event) {
    event.preventDefault();
    clearErrors();

    if (!Validator.validateForm(form)) {
      UI.toast("Please correct the highlighted fields.", "error");
      return;
    }
    if (!validateNetNotNegative()) {
      UI.toast("Please correct the highlighted fields.", "error");
      return;
    }

    const payload = buildPayload();

    saveBtn.classList.add("is-loading");
    saveBtn.disabled = true;
    try {
      if (editingId === null) {
        await API.post(API_URL, payload);
        UI.toast("Salary record created.", "success");
      } else {
        await API.put(`${API_URL}/${editingId}`, payload);
        UI.toast("Salary record updated.", "success");
      }
      closeModal();
      await loadSalaries();
    } catch (error) {
      applyServerErrors(error.errors);
      UI.toast(error.message, "error");
    } finally {
      saveBtn.classList.remove("is-loading");
      saveBtn.disabled = false;
    }
  }

  async function markPaid(row) {
    const salary = salaries.find((s) => s.id === Number(row.dataset.id));
    if (!salary) return;

    try {
      await API.put(`${API_URL}/${salary.id}`, {
        employee_id: salary.employee_id,
        salary_month: salary.salary_month,
        base_salary: salary.base_salary,
        bonus: salary.bonus,
        deduction: salary.deduction,
        payment_status: "Paid",
        payment_date: new Date().toISOString().slice(0, 10),
        notes: salary.notes
      });
      UI.toast(`Marked ${monthLabel(salary.salary_month)} as paid.`, "success");
      await loadSalaries();
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  async function deleteSalary(row) {
    const salary = salaries.find((s) => s.id === Number(row.dataset.id));
    if (!salary) return;

    const confirmed = await UI.confirmDialog({
      title: "Delete salary record?",
      message: `${UI.escapeHtml(salary.employee.name)}'s ${monthLabel(salary.salary_month)} salary record will be removed permanently.`,
      confirmText: "Delete"
    });
    if (!confirmed) return;

    try {
      await API.delete(`${API_URL}/${salary.id}`);
      UI.toast("Salary record deleted.", "success");
      await loadSalaries();
    } catch (error) {
      UI.toast(error.message, "error");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    tableBody = document.getElementById("salaryTableBody");
    employeeFilter = document.getElementById("employeeFilter");
    monthFilter = document.getElementById("monthFilter");
    statusFilter = document.getElementById("statusFilter");
    clearFiltersBtn = document.getElementById("clearFiltersBtn");
    statRecords = document.getElementById("statRecords");
    statPaid = document.getElementById("statPaid");
    statUnpaid = document.getElementById("statUnpaid");
    modal = document.getElementById("salaryModal");
    form = document.getElementById("salaryForm");
    saveBtn = document.getElementById("salarySaveBtn");
    modalTitle = document.getElementById("salaryModalTitle");
    netPreview = document.getElementById("netPreview");
    employeeSalaryHint = document.getElementById("employeeSalaryHint");

    loadEmployees();
    loadSalaries();

    document.getElementById("addSalaryBtn").addEventListener("click", () => openModal(null));
    employeeFilter.addEventListener("change", loadSalaries);
    monthFilter.addEventListener("change", loadSalaries);
    statusFilter.addEventListener("change", loadSalaries);
    clearFiltersBtn.addEventListener("click", () => {
      employeeFilter.value = "";
      monthFilter.value = "";
      statusFilter.value = "";
      loadSalaries();
    });

    tableBody.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const row = button.closest("tr[data-id]");
      const action = button.dataset.action;
      if (action === "edit") {
        const salary = salaries.find((s) => s.id === Number(row.dataset.id));
        if (salary) openModal(salary);
      } else if (action === "mark-paid") {
        markPaid(row);
      } else if (action === "delete") {
        deleteSalary(row);
      }
    });

    byName("employee_id").addEventListener("change", () => {
      updateEmployeeHint();
      updateNetPreview();
    });
    ["base_salary", "bonus", "deduction"].forEach((name) => {
      byName(name).addEventListener("input", updateNetPreview);
    });

    form.addEventListener("submit", saveSalary);
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
