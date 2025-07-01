document.addEventListener("DOMContentLoaded", function () {
  // 🔍 Dynamic Job Search
  function fetchJobs() {
    const searchQuery = document.getElementById("searchInput").value;
    const categoryId = document.getElementById("categoryFilter").value;
    const countryId = document.getElementById("countryFilter").value;

    fetch(`/jobs/ajax_search/?search=${searchQuery}&category=${categoryId}&country=${countryId}`)
      .then(response => response.text())
      .then(data => {
        const jobResultsDiv = document.getElementById("jobResults");
        if (jobResultsDiv) {
          jobResultsDiv.innerHTML = data;
        } else {
          console.error("Element #jobResults not found in HTML");
        }
      })
      .catch(error => console.error("Error fetching jobs:", error));
  }

  document.getElementById("searchBtn")?.addEventListener("click", fetchJobs);
  document.getElementById("searchInput")?.addEventListener("keyup", fetchJobs);
  document.getElementById("categoryFilter")?.addEventListener("change", fetchJobs);
  document.getElementById("countryFilter")?.addEventListener("change", fetchJobs);

  // 📋 Referral ID Copy Functionality
  const copyBtn = document.querySelector("button[onclick='copyReferralId()']");
  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      const referralText = document.getElementById("referralId").textContent;
      navigator.clipboard.writeText(referralText).then(() => {
        const copyMsg = document.getElementById("copyMsg");
        if (copyMsg) {
          copyMsg.style.display = "block";
          setTimeout(() => {
            copyMsg.style.display = "none";
          }, 2000);
        }
      }).catch(err => {
        console.error("Failed to copy referral ID:", err);
      });
    });
  }

  // 🔔 Mark Notification as Read via AJAX
  window.markAsRead = function (elem) {
    const noteId = elem.getAttribute("data-note-id");

    fetch("/seeker/ajax/notification/read/", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCSRFToken()
      },
      body: `id=${noteId}`
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        elem.classList.remove("fw-bold");
      }
    })
    .catch(error => console.error("Notification read error:", error));
  };

  // 🔐 Helper to get CSRF token from cookie
  function getCSRFToken() {
    const name = "csrftoken=";
    const decodedCookies = decodeURIComponent(document.cookie).split(";");

    for (let cookie of decodedCookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name)) {
        return cookie.substring(name.length);
      }
    }
    console.warn("CSRF token not found in cookies.");
    return "";
  }
});
