// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Theme toggle
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
}

// Load saved theme
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-bs-theme', savedTheme);
updateThemeIcon(savedTheme);

// Delete confirmation
let deleteTaskId = null;

function confirmDelete(taskId, taskTitle) {
    deleteTaskId = taskId;
    document.getElementById('deleteTaskName').textContent = taskTitle;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

document.getElementById('confirmDeleteBtn').addEventListener('click', function () {
    if (deleteTaskId) {
        fetch(`/task/${deleteTaskId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        }).then(response => {
            if (response.ok) {
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
                modal.hide();

                // Trigger board refresh
                document.body.dispatchEvent(new CustomEvent('taskChanged'));
            }
        });
    }
});

// HTMX modal handling
document.body.addEventListener('htmx:afterSwap', (e) => {
    if (e.detail.target.id === "modalContent") {
        const modal = new bootstrap.Modal(document.getElementById("modal"));
        modal.show();
    }
});

document.body.addEventListener('htmx:beforeSwap', (e) => {
    if (e.detail.target.id === "modalContent" && !e.detail.xhr.response) {
        const el = document.getElementById("modal");
        const instance = bootstrap.Modal.getInstance(el);
        if (instance) instance.hide();
    }
});

// Close modal after successful form submission
document.body.addEventListener('htmx:afterRequest', (e) => {
    if (e.detail.successful && e.detail.target.id === "modalContent") {
        const el = document.getElementById("modal");
        const instance = bootstrap.Modal.getInstance(el);
        if (instance) instance.hide();
    }
});
