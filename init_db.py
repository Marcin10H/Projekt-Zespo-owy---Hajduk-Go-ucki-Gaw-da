from app import app, db, Room

with app.app_context():
    room1 = Room(name="Sala Konferencyjna 1", capacity=12, has_projector=True)
    room2 = Room(name="Sala 3.21DH", capacity=4, has_projector=False)
    room3 = Room(name="Aula 1", capacity=50, has_projector=True)

    db.session.add_all([room1, room2, room3])
    db.session.commit()
    print("Pomyślnie dodano sale do bazy danych!")