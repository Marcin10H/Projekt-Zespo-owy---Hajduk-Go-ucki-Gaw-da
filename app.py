from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer)
    has_projector = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

@app.route('/api/rooms', methods=['POST'])
def add_room():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('capacity'):
        return jsonify({'error': 'Brakujące dane: nazwa sali i pojemność są wymagane.'}), 400

    capacity = data.get('capacity')
    if not isinstance(capacity, int) or capacity <= 0:
        return jsonify({'error': 'Pojemność sali musi być liczbą całkowitą większą niż 0.'}), 400

    existing_room = Room.query.filter_by(name=data['name']).first()
    if existing_room:
        return jsonify({'error': 'Sala o podanej nazwie już istnieje w bazie.'}), 409

    new_room = Room(name=data['name'], capacity=capacity, has_projector=data.get('has_projector', False))
    
    try:
        db.session.add(new_room)
        db.session.commit()
        return jsonify({'message': 'Sala została pomyślnie dodana.'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Wystąpił błąd podczas zapisu: {str(e)}'}), 500

@app.route('/api/rooms/<int:room_id>', methods=['DELETE'])
def delete_room(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({'error': 'Nie znaleziono sali o podanym ID.'}), 404

    try:
        db.session.delete(room)
        db.session.commit()
        return jsonify({'message': 'Sala została pomyślnie usunięta.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Wystąpił błąd podczas usuwania: {str(e)}'}), 500

@app.route('/api/rooms/<int:room_id>', methods=['PUT'])
def edit_room(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({'error': 'Nie znaleziono sali.'}), 404

    data = request.get_json()
    
    if 'name' in data:
        if not data['name']:
            return jsonify({'error': 'Nazwa nie może być pusta.'}), 400
        room.name = data['name']
        
    if 'capacity' in data:
        if not isinstance(data['capacity'], int) or data['capacity'] <= 0:
            return jsonify({'error': 'Pojemność musi być większa niż 0.'}), 400
        room.capacity = data['capacity']
        
    if 'has_projector' in data:
        room.has_projector = data['has_projector']

    try:
        db.session.commit()
        return jsonify({'message': 'Dane sali zostały zaktualizowane.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Błąd zapisu w bazie: {str(e)}'}), 500

@app.route('/')
def index():
    rooms = Room.query.all()
    return render_template('index.html', rooms=rooms)

if __name__ == '__main__':
    app.run(debug=True)

