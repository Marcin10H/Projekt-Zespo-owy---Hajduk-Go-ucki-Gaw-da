from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'projekt-zespolowy-secret-key'
db = SQLAlchemy(app)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer)
    has_projector = db.Column(db.Boolean, default=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    login = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    must_change_password = db.Column(db.Boolean, default=False)


with app.app_context():
    db.create_all()
    admin_user = User.query.filter_by(login='admin').first()
    if not admin_user:
        admin_user = User(
            username='Administrator',
            login='admin',
            password='admin',
            role='admin',
            must_change_password=False
        )
        db.session.add(admin_user)
        db.session.commit()


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return view_func(*args, **kwargs)

    return wrapper


def admin_required_api(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            return jsonify({'error': 'Brak uprawnień. Tylko administrator ma dostęp.'}), 403
        return view_func(*args, **kwargs)

    return wrapper


@app.route('/')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('panel'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    login_value = request.form.get('login', '').strip()
    password = request.form.get('password', '')
    selected_role = request.form.get('role', '')

    user = User.query.filter_by(login=login_value).first()
    if not user or user.password != password:
        return render_template('login.html', error='Niepoprawny login lub hasło.')

    if user.role != selected_role:
        return render_template('login.html', error='Wybrano niepoprawną rolę dla tego konta.')

    session['user_id'] = user.id
    session['username'] = user.username
    session['login'] = user.login
    session['role'] = user.role
    session['must_change_password'] = user.must_change_password
    return redirect(url_for('panel'))


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/panel')
@login_required
def panel():
    rooms = Room.query.all()
    success = session.pop('success', None)
    return render_template('index.html', rooms=rooms, success=success)


@app.route('/users', methods=['POST'])
@login_required
def add_user():
    if session.get('role') != 'admin':
        return render_template('index.html', rooms=Room.query.all(), error='Tylko administrator może dodawać użytkowników.')

    username = request.form.get('username', '').strip()
    login_value = request.form.get('login', '').strip()
    password = request.form.get('password', '')

    if not username or not login_value or not password:
        return render_template('index.html', rooms=Room.query.all(), error='Uzupełnij wszystkie pola użytkownika.')

    existing_user = User.query.filter_by(login=login_value).first()
    if existing_user:
        return render_template('index.html', rooms=Room.query.all(), error='Użytkownik o takim loginie już istnieje.')

    new_user = User(
        username=username,
        login=login_value,
        password=password,
        role='pracownik',
        must_change_password=True
    )
    db.session.add(new_user)
    db.session.commit()
    session['success'] = f'Użytkownik {username} został dodany.'
    return redirect(url_for('panel'))


@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    if session.get('role') != 'pracownik':
        return redirect(url_for('panel'))

    new_password = request.form.get('new_password', '').strip()
    if not new_password:
        return render_template('index.html', rooms=Room.query.all(), error='Nowe hasło nie może być puste.')

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login_page'))

    user.password = new_password
    user.must_change_password = False
    db.session.commit()
    session['must_change_password'] = False
    return render_template('index.html', rooms=Room.query.all(), success='Hasło zostało zmienione.')


@app.route('/api/rooms', methods=['POST'])
@login_required
@admin_required_api
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
@login_required
@admin_required_api
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
@login_required
@admin_required_api
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


if __name__ == '__main__':
    app.run(debug=True)
