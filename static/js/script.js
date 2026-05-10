const addRoomForm = document.getElementById('addRoomForm');
if (addRoomForm) {
    addRoomForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const name = document.getElementById('roomName').value;
        const capacity = parseInt(document.getElementById('roomCapacity').value);
        const hasProjector = document.getElementById('roomProjector').checked;

        try {
            const response = await fetch('/api/rooms', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
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
        const response = await fetch(`/api/rooms/${roomId}`, { method: 'DELETE' });
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

let editModal;

function openEditModal(buttonElement) {
    const id = buttonElement.dataset.id;
    const name = buttonElement.dataset.name;
    const capacity = buttonElement.dataset.capacity;
    const hasProjector = buttonElement.dataset.projector === 'true';

    document.getElementById('editRoomId').value = id;
    document.getElementById('editRoomName').value = name;
    document.getElementById('editRoomCapacity').value = capacity;
    document.getElementById('editRoomProjector').checked = hasProjector;

    editModal = new bootstrap.Modal(document.getElementById('editRoomModal'));
    editModal.show();
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
            const response = await fetch(`/api/rooms/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
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

let reserveModal;

function showModalAlert(message, type = 'danger') {
    const alertDiv = document.getElementById('modalAlert');
    alertDiv.innerText = message;
    alertDiv.className = `alert alert-${type}`;
    alertDiv.classList.remove('d-none');
    setTimeout(() => alertDiv.classList.add('d-none'), 5000);
}

// Zaktualizowana funkcja otwierania modala
async function openReserveModal(id, name) {
    document.getElementById('reserveRoomId').value = id;
    document.getElementById('modalRoomName').innerText = name;
    
    // Pobierz aktualne rezerwacje dla tej sali
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

// Obsługa wysyłania (aktualizacja fragmentu z poprzedniej odpowiedzi)
document.getElementById('reservationForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        room_id: parseInt(document.getElementById('reserveRoomId').value),
        start_time: document.getElementById('startTime').value,
        end_time: document.getElementById('endTime').value,
        is_recurring: document.getElementById('isRecurring').checked
    };

    const response = await fetch('/api/reservations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const result = await response.json();
    if (response.ok) {
        showModalAlert("Zarezerwowano!", "success");
        setTimeout(() => location.reload(), 1000);
    } else {
        showModalAlert(result.error, "danger");
    }
});

async function cancelReservation(resId) {
    if (!confirm('Czy na pewno chcesz odwołać tę rezerwację?')) return;
    
    try {
        const response = await fetch(`/api/reservations/${resId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            location.reload();
        } else {
            const data = await response.json();
            alert("Błąd: " + data.error);
        }
    } catch (error) {
        alert("Wystąpił błąd podczas usuwania.");
    }
}

const changePasswordForm = document.getElementById('changePasswordForm');
if (changePasswordForm) {
    changePasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (newPassword !== confirmPassword) {
            alert("Hasła nie są identyczne!");
            return;
        }

        try {
            const response = await fetch('/api/change_password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    new_password: newPassword,
                    confirm_password: confirmPassword 
                })
            });

            const result = await response.json();

            if (response.ok) {
                alert("Hasło zmienione pomyślnie. Zaloguj się ponownie.");
                window.location.href = '/'; // Przekierowanie do logowania
            } else {
                alert("Błąd: " + result.error);
            }
        } catch (error) {
            alert("Wystąpił błąd połączenia.");
        }
    });
}