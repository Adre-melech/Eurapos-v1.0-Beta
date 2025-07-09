  document.addEventListener("DOMContentLoaded", function () {
    // === Cookie Consent + Time Zone ===
    const banner = document.getElementById("cookie-consent");
    if (!localStorage.getItem("consentGiven") && banner) {
      banner.style.display = "block";
    }

    window.acceptConsent = function () {
          const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

          fetch("{% url 'home:accept_consent' %}", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": "{{ csrf_token }}"
            },
            body: JSON.stringify({ timezone: timezone })
          })
          .then(response => {
            if (response.ok) {
              localStorage.setItem("consentGiven", "yes");
              if (banner) banner.style.display = "none";
        }
      });
    };

    // === Job Search & Filtering ===
    const searchInput = document.getElementById("searchInput");
    const countryFilter = document.getElementById("countryFilter");
    const categoryFilter = document.getElementById("categoryFilter");
    const jobTableBody = document.getElementById("jobTableBody");

    function fetchFilteredJobs() {
      const searchText = searchInput.value;
      const selectedCountry = countryFilter.value;
      const selectedCategory = categoryFilter.value;

      fetch(`/jobs/?search=${searchText}&country=${selectedCountry}&category=${selectedCategory}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
      .then(response => response.json())
      .then(data => {
        jobTableBody.innerHTML = "";
        data.jobs.forEach(job => {
          jobTableBody.innerHTML += `
            <tr>
              <td><a href="/jobs/${job.id}/">${job.title}</a></td>
              <td>${job.company}</td>
              <td>${job.salary}</td>
              <td>${job.deadline}</td>
              <td>${job.country}</td>
            </tr>`;
        });
      })
      .catch(error => console.error("Error fetching jobs:", error));
    }

    if (searchInput && countryFilter && categoryFilter && jobTableBody) {
      searchInput.addEventListener("input", fetchFilteredJobs);
      countryFilter.addEventListener("change", fetchFilteredJobs);
      categoryFilter.addEventListener("change", fetchFilteredJobs);
    }

    // === Job Application + Rating Modal ===
    const applyForm = document.getElementById("applyForm");
    const ratingModalElement = document.getElementById("ratingModal");

    if (applyForm && ratingModalElement) {
      const ratingModal = new bootstrap.Modal(ratingModalElement);

      applyForm.addEventListener("submit", function (event) {
        event.preventDefault();
        fetch(applyForm.action, {
          method: "POST",
          body: new FormData(applyForm)
        })
        .then(response => {
          if (response.ok) {
            ratingModal.show();
          }
        })
        .catch(error => console.error("Application error:", error));
      });
    }

    // === Admin Panel: Send Alert ===
    const alertForm = document.getElementById("alertForm");
    const seekerSelect = document.getElementById("seekerSelect");

    if (alertForm && seekerSelect) {
      alertForm.addEventListener("submit", function (event) {
        event.preventDefault();
        const selectedSeeker = seekerSelect.value;
        const messageInput = document.querySelector("input[name='message']").value;

        if (!selectedSeeker || !messageInput) {
          alert("Please select a user and enter a message.");
          return;
        }

        fetch(`/notifications/send-alert/${selectedSeeker}/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
          },
          body: new URLSearchParams({ message: messageInput })
        })
        .then(response => response.json())
        .then(data => {
          alert(data.success ? "Alert sent successfully!" : "Error sending alert: " + data.error);
        })
        .catch(error => console.error("Error sending alert:", error));
      });
    }
  });
