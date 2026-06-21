const IS_ADMIN = document.body.dataset.isAdmin === 'true';

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

function apiFetch(url, options = {}) {
    const headers = { ...(options.headers || {}) };
    const method = (options.method || 'GET').toUpperCase();

    if (method !== 'GET' && method !== 'HEAD') {
        headers['X-CSRFToken'] = getCsrfToken();
    }
    if (options.body && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    return fetch(url, { ...options, headers });
}

const addRoomForm = document.getElementById('addRoomForm');
if (addRoomForm) {
    addRoomForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const name = document.getElementById('roomName').value;
        const capacity = parseInt(document.getElementById('roomCapacity').value);
        const hasProjector = document.getElementById('roomProjector').checked;

        try {
            const response = await apiFetch('/api/rooms', {
                method: 'POST',
                body: JSON.stringify({ name: name, capacity: capacity, has_projector: hasProjector })
            });
            const data = await response.json();
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Błąd: ' + data.error);
            }
        } catch (error) {
            alert('Wystąpił błąd podczas komunikacji z serwerem.');
        }
    });
}

async function deleteRoom(roomId) {
    if (!confirm('Czy na pewno chcesz usunąć tę salę?')) return;
    try {
        const response = await apiFetch(`/api/rooms/${roomId}`, { method: 'DELETE' });
        const data = await response.json();
        if (response.ok) {
            window.location.reload();
        } else {
            alert('Błąd: ' + data.error);
        }
    } catch (error) {
        alert('Wystąpił błąd podczas komunikacji z serwerem.');
    }
}

function openEditModal(buttonElement) {
    const id = buttonElement.dataset.id;
    const name = buttonElement.dataset.name;
    const capacity = buttonElement.dataset.capacity;
    const hasProjector = buttonElement.dataset.projector === 'true';

    document.getElementById('editRoomId').value = id;
    document.getElementById('editRoomName').value = name;
    document.getElementById('editRoomCapacity').value = capacity;
    document.getElementById('editRoomProjector').checked = hasProjector;

    new bootstrap.Modal(document.getElementById('editRoomModal')).show();
}

const editRoomForm = document.getElementById('editRoomForm');
if (editRoomForm) {
    editRoomForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const id = document.getElementById('editRoomId').value;
        const name = document.getElementById('editRoomName').value;
        const capacity = parseInt(document.getElementById('editRoomCapacity').value);
        const hasProjector = document.getElementById('editRoomProjector').checked;

        try {
            const response = await apiFetch(`/api/rooms/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ name: name, capacity: capacity, has_projector: hasProjector })
            });
            const data = await response.json();

            if (response.ok) {
                window.location.reload();
            } else {
                alert('Błąd: ' + data.error);
            }
        } catch (error) {
            alert('Wystąpił błąd podczas komunikacji z serwerem.');
        }
    });
}

function showModalAlert(message, type = 'danger') {
    const alertDiv = document.getElementById('modalAlert');
    alertDiv.innerText = message;
    alertDiv.className = `alert alert-${type}`;
    alertDiv.classList.remove('d-none');
    setTimeout(() => alertDiv.classList.add('d-none'), 5000);
}

function getFilterValues() {
    return {
        minCapacity: document.getElementById('filterMinCapacity').value,
        startTime: document.getElementById('filterStartTime').value,
        endTime: document.getElementById('filterEndTime').value,
        requiresProjector: document.getElementById('filterProjector').checked
    };
}

function buildRoomCardHtml(room) {
    const projectorLabel = room.has_projector ? 'Tak' : 'Brak';
    const escapedName = room.name.replace(/'/g, "\\'");
    let adminButtons = '';
    if (IS_ADMIN) {
        const projectorAttr = room.has_projector ? 'true' : 'false';
        adminButtons = `
            <button class="btn btn-outline-secondary w-100 mb-2"
                data-id="${room.id}"
                data-name="${room.name}"
                data-capacity="${room.capacity}"
                data-projector="${projectorAttr}"
                onclick="openEditModal(this)">Edytuj</button>
            <button class="btn btn-outline-danger w-100" data-id="${room.id}" onclick="deleteRoom(this.dataset.id)">Usuń salę</button>`;
    }
    return `
        <div class="col-md-6 mb-3">
            <div class="card shadow-sm room-card h-100">
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title text-primary">${room.name}</h5>
                    <p class="card-text mb-4">
                        <strong>Miejsca:</strong> ${room.capacity}<br>
                        <strong>Rzutnik:</strong> ${projectorLabel}
                    </p>
                    <div class="mt-auto room-actions">
                        <button class="btn btn-primary w-100 mb-2" onclick="openReserveModal('${room.id}', '${escapedName}')">Zarezerwuj</button>
                        ${adminButtons}
                    </div>
                </div>
            </div>
        </div>`;
}

function renderRooms(rooms) {
    const container = document.getElementById('roomsContainer');
    const noRoomsMsg = document.getElementById('noRoomsMessage');

    if (!rooms.length) {
        container.innerHTML = '';
        noRoomsMsg.classList.remove('d-none');
        return;
    }

    noRoomsMsg.classList.add('d-none');
    container.innerHTML = rooms.map(buildRoomCardHtml).join('');
}

async function searchRooms() {
    const filters = getFilterValues();
    const params = new URLSearchParams();

    if (filters.minCapacity) {
        params.set('min_capacity', filters.minCapacity);
    }
    if (filters.requiresProjector) {
        params.set('requires_projector', 'true');
    }
    if (filters.startTime) {
        params.set('start_time', filters.startTime);
    }
    if (filters.endTime) {
        params.set('end_time', filters.endTime);
    }

    const hasAnyFilter = params.toString().length > 0;
    const infoEl = document.getElementById('roomsFilterInfo');

    if (!hasAnyFilter) {
        infoEl.classList.add('d-none');
        window.location.reload();
        return;
    }

    if ((filters.startTime && !filters.endTime) || (!filters.startTime && filters.endTime)) {
        alert('Podaj zarówno początek, jak i koniec terminu - albo zostaw oba pola puste.');
        return;
    }

    try {
        const response = await fetch(`/api/rooms/search?${params.toString()}`);
        const data = await response.json();

        if (!response.ok) {
            alert('Błąd: ' + (data.error || 'Nie udało się wyszukać sal.'));
            return;
        }

        renderRooms(data);
        infoEl.innerText = `Znaleziono ${data.length} ${data.length === 1 ? 'salę' : 'sal'} spełniających kryteria.`;
        infoEl.classList.remove('d-none');
    } catch (error) {
        alert('Wystąpił błąd podczas wyszukiwania sal.');
    }
}

const roomFilterForm = document.getElementById('roomFilterForm');
if (roomFilterForm) {
    roomFilterForm.addEventListener('submit', (e) => {
        e.preventDefault();
        searchRooms();
    });
}

const clearFilterBtn = document.getElementById('clearFilterBtn');
if (clearFilterBtn) {
    clearFilterBtn.addEventListener('click', () => {
        window.location.reload();
    });
}

async function openReserveModal(id, name) {
    document.getElementById('reserveRoomId').value = id;
    document.getElementById('modalRoomName').innerText = name;

    const filters = getFilterValues();
    const startInput = document.getElementById('startTime');
    const endInput = document.getElementById('endTime');
    if (filters.startTime && filters.endTime) {
        startInput.value = filters.startTime;
        endInput.value = filters.endTime;
    } else {
        startInput.value = '';
        endInput.value = '';
    }

    const resList = document.getElementById('currentReservations');
    resList.innerHTML = '<small class="text-center d-block">Ładowanie...</small>';

    const response = await fetch(`/api/rooms/${id}/reservations`);
    const reservations = await response.json();

    resList.innerHTML = reservations.length ? '' : '<small class="text-muted p-2">Brak rezerwacji.</small>';
    reservations.forEach(r => {
        resList.innerHTML += `
            <div class="list-group-item d-flex justify-content-between align-items-center small py-1">
                <span>${r.start} - ${r.end.split(' ')[1]}</span>
                <span class="badge bg-secondary rounded-pill">${r.user}</span>
            </div>`;
    });

    const modal = new bootstrap.Modal(document.getElementById('reserveModal'));
    modal.show();
}

const reservationForm = document.getElementById('reservationForm');
if (reservationForm) {
    reservationForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            room_id: parseInt(document.getElementById('reserveRoomId').value),
            start_time: document.getElementById('startTime').value,
            end_time: document.getElementById('endTime').value,
            is_recurring: document.getElementById('isRecurring').checked
        };

        const response = await apiFetch('/api/reservations', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        if (response.ok) {
            showModalAlert('Zarezerwowano!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showModalAlert(result.error, 'danger');
        }
    });
}

async function cancelReservation(resId) {
    if (!confirm('Czy na pewno chcesz odwołać tę rezerwację?')) return;

    try {
        const response = await apiFetch(`/api/reservations/${resId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            location.reload();
        } else {
            const data = await response.json();
            alert('Błąd: ' + data.error);
        }
    } catch (error) {
        alert('Wystąpił błąd podczas usuwania.');
    }
}

function showEditUserAlert(message, type = 'danger') {
    const alertDiv = document.getElementById('editUserAlert');
    alertDiv.innerText = message;
    alertDiv.className = `alert alert-${type}`;
    alertDiv.classList.remove('d-none');
}

function openEditUserModal(buttonElement) {
    document.getElementById('editUserId').value = buttonElement.dataset.id;
    document.getElementById('editUserUsername').value = buttonElement.dataset.username;
    document.getElementById('editUserLogin').value = buttonElement.dataset.login;
    document.getElementById('editUserPassword').value = '';
    document.getElementById('editUserMustChange').checked = true;
    document.getElementById('editUserAlert').classList.add('d-none');

    new bootstrap.Modal(document.getElementById('editUserModal')).show();
}

const editUserForm = document.getElementById('editUserForm');
if (editUserForm) {
    editUserForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('editUserId').value;
        const payload = {
            username: document.getElementById('editUserUsername').value.trim(),
            login: document.getElementById('editUserLogin').value.trim()
        };
        const password = document.getElementById('editUserPassword').value;
        if (password) {
            payload.password = password;
            payload.must_change_password = document.getElementById('editUserMustChange').checked;
        }

        try {
            const response = await apiFetch(`/api/users/${id}`, {
                method: 'PUT',
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (response.ok) {
                location.reload();
            } else {
                showEditUserAlert(result.error || 'Nie udało się zapisać zmian.');
            }
        } catch (error) {
            showEditUserAlert('Wystąpił błąd połączenia.');
        }
    });
}

async function deleteUser(userId, username) {
    if (!confirm(`Czy na pewno chcesz usunąć użytkownika „${username}”? Zostaną usunięte także jego rezerwacje.`)) return;

    try {
        const response = await apiFetch(`/api/users/${userId}`, { method: 'DELETE' });
        const data = await response.json();
        if (response.ok) {
            location.reload();
        } else {
            alert('Błąd: ' + data.error);
        }
    } catch (error) {
        alert('Wystąpił błąd podczas usuwania użytkownika.');
    }
}
