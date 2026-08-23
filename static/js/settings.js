(function () {
  "use strict";

  const FIELDS = ["cafe_name", "phone", "email", "address", "logo_url", "tax_percent", "currency", "receipt_footer"];

  let form;
  let saveBtn;
  let resetBtn;

  const byName = (name) => form.elements.namedItem(name);

  function setFieldsDisabled(disabled) {
    FIELDS.forEach((name) => {
      const input = byName(name);
      if (input) input.disabled = disabled;
    });
    saveBtn.disabled = disabled;
    resetBtn.disabled = disabled;
  }

  function setSaving(isSaving) {
    saveBtn.classList.toggle("is-loading", isSaving);
    saveBtn.disabled = isSaving;
    resetBtn.disabled = isSaving;
  }

  function updateLogoPreview() {
    const input = byName("logo_url");
    const img = document.getElementById("logoPreview");
    const fallback = document.getElementById("logoFallback");
    const url = (input.value || "").trim();

    if (!url) {
      img.hidden = true;
      img.removeAttribute("src");
      fallback.hidden = false;
      return;
    }
    img.onerror = () => {
      img.hidden = true;
      img.removeAttribute("src");
      fallback.hidden = false;
      fallback.textContent = "Logo could not be loaded";
    };
    img.onload = () => {
      fallback.hidden = true;
      fallback.textContent = "No logo set";
    };
    img.src = url;
    img.hidden = false;
  }

  function fillForm(settings) {
    FIELDS.forEach((name) => {
      const input = byName(name);
      if (!input) return;
      input.value = settings[name] === null || settings[name] === undefined ? "" : String(settings[name]);
    });
    clearAllErrors();
    updateLogoPreview();
    showUpdatedNote(settings.updated_at);
  }

  function collectPayload() {
    const valueOrNone = (name) => {
      const value = (byName(name).value || "").trim();
      return value === "" ? null : value;
    };
    return {
      cafe_name: valueOrNone("cafe_name"),
      address: valueOrNone("address"),
      phone: valueOrNone("phone"),
      email: valueOrNone("email"),
      logo_url: valueOrNone("logo_url"),
      tax_percent: Number(byName("tax_percent").value),
      currency: valueOrNone("currency"),
      receipt_footer: valueOrNone("receipt_footer")
    };
  }

  function clearAllErrors() {
    FIELDS.forEach((name) => {
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

  function showUpdatedNote(updatedAt) {
    const note = document.getElementById("updatedAtNote");
    note.textContent = updatedAt ? `Last saved ${UI.formatDate(updatedAt)}` : "";
  }

  function showLoadedForm() {
    document.getElementById("formSkeleton").hidden = true;
    document.getElementById("billingSkeleton").hidden = true;
    document.getElementById("formFields").hidden = false;
    document.getElementById("billingFields").hidden = false;
  }

  async function loadSettings() {
    try {
      const response = await API.get("/api/settings");
      fillForm(response.data);
      setFieldsDisabled(false);
      showLoadedForm();
    } catch (error) {
      UI.toast(error.message, "error");
      document.getElementById("formSkeleton").hidden = false;
      document.getElementById("formSkeleton").innerHTML =
        '<p class="hint">Could not load settings. Refresh the page to try again.</p>';
      document.getElementById("billingSkeleton").hidden = true;
    }
  }

  async function saveSettings(event) {
    event.preventDefault();
    clearAllErrors();

    if (!Validator.validateForm(form)) {
      UI.toast("Please correct the highlighted fields.", "error");
      const invalid = form.querySelector(".is-invalid");
      if (invalid) invalid.focus();
      return;
    }
    if (byName("tax_percent").value !== "" && Number(byName("tax_percent").value) > 100) {
      UI.toast("Tax percentage cannot be greater than 100.", "error");
      return;
    }

    setSaving(true);
    try {
      const response = await API.put("/api/settings", collectPayload());
      fillForm(response.data);
      UI.toast("Settings saved successfully.", "success");
    } catch (error) {
      applyServerErrors(error.errors);
      UI.toast(error.message, "error");
    } finally {
      setSaving(false);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    form = document.getElementById("settingsForm");
    saveBtn = document.getElementById("saveBtn");
    resetBtn = document.getElementById("resetBtn");

    setFieldsDisabled(true);
    loadSettings();

    form.addEventListener("submit", saveSettings);

    resetBtn.addEventListener("click", async () => {
      await loadSettings();
      UI.toast("Changes discarded.", "info");
    });

    byName("logo_url").addEventListener("input", updateLogoPreview);

    FIELDS.forEach((name) => {
      const input = byName(name);
      input.addEventListener("input", () => Validator.clearFieldError(input));
    });
  });
})();
