(function () {
  "use strict";

  class ApiError extends Error {
    constructor(message, status = 0, errors = []) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.errors = errors;
    }
  }

  const FALLBACK_MESSAGES = {
    400: "The request was invalid.",
    401: "You are not authorised to do this.",
    403: "You do not have permission for this action.",
    404: "The requested item was not found.",
    409: "This record already exists or conflicts with another.",
    422: "Please correct the highlighted fields.",
    500: "Something went wrong on the server. Try again."
  };

  async function request(method, url, body) {
    const options = { method, headers: { Accept: "application/json" } };
    if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }

    let response;
    try {
      response = await fetch(url, options);
    } catch (networkError) {
      throw new ApiError("Cannot reach the server. Please check your connection.", 0);
    }

    let payload = null;
    try {
      payload = await response.json();
    } catch (parseError) {
      payload = null;
    }

    if (!response.ok) {
      const message =
        (payload && payload.message) || FALLBACK_MESSAGES[response.status] || "Unexpected error.";
      throw new ApiError(message, response.status, (payload && payload.errors) || []);
    }

    return payload;
  }

  const API = {
    ApiError,
    get: (url) => request("GET", url),
    post: (url, body) => request("POST", url, body),
    put: (url, body) => request("PUT", url, body),
    patch: (url, body) => request("PATCH", url, body),
    delete: (url) => request("DELETE", url)
  };

  window.API = API;
})();
