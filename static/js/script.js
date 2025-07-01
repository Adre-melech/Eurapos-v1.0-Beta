document.addEventListener("DOMContentLoaded", function () {
    // Job Search & Filtering
    const searchInput = document.getElementById("searchInput");
    const countryFilter = document.getElementById("countryFilter");
    const categoryFilter = document.getElementById("categoryFilter");
    const jobTableBody = document.getElementById("jobTableBody");

    function fetchFilteredJobs() {
        let searchText = searchInput.value;
        let selectedCountry = countryFilter.value;
        let selectedCategory = categoryFilter.value;

        fetch(`/jobs/?search=${searchText}&country=${selectedCountry}&category=${selectedCategory}`, {
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        })
        .then(response => response.json())
        .then(data => {
            jobTableBody.innerHTML = ""; // Clear previous results

            data.jobs.forEach(job => {
                let row = `<tr>
                    <td><a href="/jobs/${job.id}/">${job.title}</a></td>
                    <td>${job.company}</td>
                    <td>${job.salary}</td>
                    <td>${job.deadline}</td>
                    <td>${job.country}</td>
                </tr>`;
                jobTableBody.innerHTML += row;
            });
        })
        .catch(error => console.error("Error fetching jobs:", error));
    }

    // Attach search & filter event listeners
    searchInput.addEventListener("input", fetchFilteredJobs);
    countryFilter.addEventListener("change", fetchFilteredJobs);
    categoryFilter.addEventListener("change", fetchFilteredJobs);

    // Job Application & Rating Modal Handling
    const applyForm = document.getElementById("applyForm");
    const ratingModalElement = document.getElementById("ratingModal");

    if (applyForm && ratingModalElement) {
        const ratingModal = new bootstrap.Modal(ratingModalElement);

        applyForm.addEventListener("submit", function (event) {
            event.preventDefault(); // Prevent page reload
            fetch(applyForm.action, {
                method: "POST",
                body: new FormData(applyForm)
            }).then(response => {
                if (response.ok) {
                    ratingModal.show(); // Show rating modal after successful application
                }
            }).catch(error => console.error("Application error:", error));
        });
    }

    // Admin Panel Send Alert Handling
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
                if (data.success) {
                    alert("Alert sent successfully!");
                } else {
                    alert("Error sending alert: " + data.error);
                }
            })
            .catch(error => console.error("Error sending alert:", error));
        });
    }
});
