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

const csrftoken = getCookie('csrftoken');

function initSortable() {
    document.querySelectorAll('.tasks-container').forEach(container => {
        if (container._sortable) {
            container._sortable.destroy();
        }

        container._sortable = new Sortable(container, {
            group: 'tasks',
            animation: 200,
            easing: 'cubic-bezier(0.25, 1, 0.5, 1)',
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            chosenClass: 'sortable-chosen',
            forceFallback: true,

            onStart: function (evt) {
                document.body.style.cursor = 'grabbing';
                document.querySelectorAll('.empty-column').forEach(el => {
                    el.style.display = 'none';
                });
            },

            onEnd: function (evt) {
                document.body.style.cursor = '';
                const taskId = evt.item.dataset.taskId;
                const columnId = evt.to.dataset.columnId;
                const newIndex = evt.newIndex;

                updateEmptyStates();
                updateColumnCounts();

                fetch(`/task/${taskId}/move/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrftoken
                    },
                    body: `column_id=${columnId}&order=${newIndex}`
                });
            },

            onMove: function (evt) {
                evt.to.classList.add('drag-over');
                if (evt.from !== evt.to) {
                    evt.from.classList.remove('drag-over');
                }
            },

            onUnchoose: function () {
                document.querySelectorAll('.tasks-container').forEach(col => {
                    col.classList.remove('drag-over');
                });
            }
        });
    });
}

function updateEmptyStates() {
    document.querySelectorAll('.column-body').forEach(column => {
        const container = column.querySelector('.tasks-container');
        const taskCount = container ? container.querySelectorAll('.task-card').length : 0;
        const emptyState = column.querySelector('.empty-column');

        if (emptyState) {
            emptyState.style.display = taskCount === 0 ? 'block' : 'none';
        }
    });
}

function updateColumnCounts() {
    document.querySelectorAll('.column-body').forEach(column => {
        const container = column.querySelector('.tasks-container');
        const count = container ? container.querySelectorAll('.task-card').length : 0;
        const header = column.closest('.board-column').querySelector('.column-count');
        if (header) {
            header.textContent = count;
        }
    });
}

initSortable();

document.body.addEventListener('htmx:afterSwap', function (evt) {
    if (evt.detail.target.id === 'board-columns') {
        initSortable();
    }
});

document.body.addEventListener('taskChanged', function () {
    const modal = bootstrap.Modal.getInstance(document.getElementById('modal'));
    if (modal) modal.hide();
});

document.body.addEventListener('columnChanged', function () {
    const modal = bootstrap.Modal.getInstance(document.getElementById('modal'));
    if (modal) modal.hide();
});
