document.getElementById('addRoomForm').addEventListener('submit', async function(event) {
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
        if (response.ok) { window.location.reload(); } else { alert('Błąd: ' + data.error); }
    } catch (error) { alert('Wystąpił błąd podczas komunikacji z serwerem.'); }
});

async function deleteRoom(roomId) {
    if (!confirm('Czy na pewno chcesz usunąć tę salę?')) return; 
    try {
        const response = await fetch(`/api/rooms/${roomId}`, { method: 'DELETE' });
        const data = await response.json();
        if (response.ok) { window.location.reload(); } else { alert('Błąd: ' + data.error); }
    } catch (error) { alert('Wystąpił błąd podczas komunikacji z serwerem.'); }
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

document.getElementById('editRoomForm').addEventListener('submit', async function(event) {
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