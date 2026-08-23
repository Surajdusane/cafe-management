(function () {
  "use strict";

  const PATTERNS = {
    email: /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/,
    phone: /^[6-9]\d{9}$/,
    digits: /^\d+$/
  };

  function required(value) {
    if (value === null || value === undefined) return "This field is required.";
    if (typeof value === "string" && value.trim() === "") return "This field is required.";
    return null;
  }

  function number(value) {
    if (value === "" || value === null || value === undefined) return null;
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return "Enter a valid number.";
    return null;
  }

  function positiveNumber(value) {
    const asNumber = Number(value);
    if (!Number.isFinite(asNumber)) return "Enter a valid number.";
    if (asNumber <= 0) return "Value must be greater than zero.";
    return null;
  }

  function nonNegative(value) {
    const asNumber = Number(value);
    if (!Number.isFinite(asNumber)) return "Enter a valid number.";
    if (asNumber < 0) return "Value cannot be negative.";
    return null;
  }

  function maxValue(value, max) {
    if (value === "" || value === null || value === undefined) return null;
    const asNumber = Number(value);
    if (!Number.isFinite(asNumber)) return "Enter a valid number.";
    if (asNumber > Number(max)) return `Value cannot be greater than ${max}.`;
    return null;
  }

  function maxLength(value, max) {
    if (value && String(value).length > Number(max)) {
      return `Must be ${max} characters or fewer.`;
    }
    return null;
  }

  const PATTERN_MESSAGES = {
    email: "Enter a valid email address.",
    phone: "Enter a valid 10-digit mobile number.",
    digits: "Only digits are allowed."
  };

  function pattern(value, name, message) {
    if (!value) return null;
    if (!PATTERNS[name] || !PATTERNS[name].test(String(value).trim())) {
      return message || PATTERN_MESSAGES[name] || "Invalid format.";
    }
    return null;
  }

  function showFieldError(input, message) {
    clearFieldError(input);
    input.classList.add("is-invalid");
    input.setAttribute("aria-invalid", "true");
    const note = document.createElement("div");
    note.className = "field-error";
    note.textContent = message;
    input.insertAdjacentElement("afterend", note);
  }

  function clearFieldError(input) {
    input.classList.remove("is-invalid");
    input.removeAttribute("aria-invalid");
    const next = input.nextElementSibling;
    if (next && next.classList.contains("field-error")) next.remove();
  }

  function validateForm(form) {
    let isValid = true;
    const fields = form.querySelectorAll("[data-validate]");
    fields.forEach((input) => {
      const rules = input.dataset.validate.split("|").filter(Boolean);
      for (const rule of rules) {
        const [name, arg] = rule.split(":");
        const checker = VALIDATORS[name];
        const error = checker ? checker(input.value, arg) : null;
        if (error) {
          showFieldError(input, error);
          isValid = false;
          break;
        }
      }
      if (isValid !== false) clearFieldError(input);
    });
    return isValid;
  }

  const VALIDATORS = { required, number, positiveNumber, nonNegative, maxValue, maxLength, pattern };

  window.Validator = { ...VALIDATORS, showFieldError, clearFieldError, validateForm };
})();
