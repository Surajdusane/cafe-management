(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", async () => {
    const statusChip = document.getElementById("dbStatus");
    if (!statusChip) return;

    try {
      const response = await API.get("/api/health");
      const data = response.data || {};
      statusChip.textContent =
        data.status === "ok" ? `API online · Database ${data.database}` : "System degraded";
    } catch (error) {
      statusChip.textContent = "Cannot reach API";
    }
  });
})();
