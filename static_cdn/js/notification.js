const bell = document.getElementById("notification-bell");
const chatbox = document.getElementById("notification-chatbox");

if (bell && chatbox) {
  bell.addEventListener("click", () => {
    const isVisible = chatbox.style.display === "flex";
    chatbox.style.display = isVisible ? "none" : "flex";
    bell.setAttribute("aria-expanded", isVisible ? "false" : "true");
  });

  document.addEventListener("click", (e) => {
    if (!chatbox.contains(e.target) && !bell.contains(e.target)) {
      chatbox.style.display = "none";
      bell.setAttribute("aria-expanded", "false");
    }
  });

  bell.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      bell.click();
    }
  });
}

function markAsRead(element, source = "mobile") {
  const noteId = element.getAttribute("data-note-id");
  fetch("/seeker/notifications/ajax-mark-read/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": getCSRFToken()
    },
    body: `id=${noteId}`
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      element.classList.remove("fw-bold");
      const btn = element.querySelector("button");
      if (btn) btn.remove();
      updateNotificationBadges();
    }
  });
}

function updateNotificationBadges() {
  ["notification-count", "notification-count-desktop", "notification-count-mobile"].forEach(id => {
    const badge = document.getElementById(id);
    if (badge) {
      let rawText = badge.textContent.trim().replace("+", "");
      let count = parseInt(rawText);
      if (!isNaN(count)) {
        count = Math.max(0, count - 1);
        if (count > 0) {
          badge.textContent = count > 99 ? "99+" : count;
        } else {
          badge.remove();
        }
      }
    }
  });
}

function getCSRFToken() {
  return document.cookie
    .split("; ")
    .find(row => row.startsWith("csrftoken="))
    ?.split("=")[1];
}
