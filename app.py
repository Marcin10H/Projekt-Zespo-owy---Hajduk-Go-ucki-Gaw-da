import os
from functools import wraps
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-change-me-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['WTF_CSRF_TIME_LIMIT'] = None

db = SQLAlchemy(app)
CSRFProtect(app)

PASSWORD_MIN_LENGTH = 8
MUST_CHANGE_PASSWORD_ALLOWED = {'panel', 'change_password', 'logout', 'login_page', 'login', 'static'}


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer)
    has_projector = db.Column(db.Boolean, default=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    login = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    must_change_password = db.Column(db.Boolean, default=False)


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)

    room = db.relationship('Room', backref=db.backref('reservations', lazy=True))
    user = db.relationship('User', backref=db.backref('reservations', lazy=True))


def hash_password(password):
    return generate_password_hash(password)


def verify_password(user, password):
    if check_password_hash(user.password, password):
        return True
    # jak w bazie zostalo jeszcze stare haslo plain text to przy logowaniu je hashujemy
    if user.password == password:
        user.password = hash_password(password)
        db.session.commit()
        return True
    return False


def validate_password(password):
    if not password or len(password) < PASSWORD_MIN_LENGTH:
        return f'Hasło musi mieć co najmniej {PASSWORD_MIN_LENGTH} znaków.'
    return None


def parse_datetime(value, field_name):
    if not value:
        return None, jsonify({'error': f'Pole {field_name} jest wymagane.'}), 400
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M'), None, None
    except (ValueError, TypeError):
        return None, jsonify({'error': 'Nieprawidłowy format daty.'}), 400


# sprawdza czy ktos jest zalogowany
def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return view_func(*args, **kwargs)

    return wrapper


# endpoint tylko dla admina
def admin_required_api(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            return jsonify({'error': 'Brak uprawnień. Tylko administrator ma dostęp.'}), 403
        return view_func(*args, **kwargs)

    return wrapper


# pracownik z haslem startowym moze tylko je zmienic
@app.before_request
def enforce_password_change():
    if 'user_id' not in session or not session.get('must_change_password'):
        return None
    if session.get('role') == 'admin':
        return None
    if request.endpoint in MUST_CHANGE_PASSWORD_ALLOWED:
        return None
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Musisz zmienić hasło startowe przed dalszym korzystaniem z systemu.'}), 403
    return redirect(url_for('panel'))


# jak baza pusta to zakladamy konto admin
with app.app_context():
    db.create_all()
    admin_user = User.query.filter_by(login='admin').first()
    if not admin_user:
        admin_user = User(
            username='Administrator',
            login='admin',
            password=hash_password('admin'),
            role='admin',
            must_change_password=False
        )
        db.session.add(admin_user)
        db.session.commit()


@app.route('/')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('panel'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    login_value = request.form.get('login', '').strip()
    password = request.form.get('password', '')

    user = User.query.filter_by(login=login_value).first()

    if not user or not verify_password(user, password):
        return render_template('login.html', error='Niepoprawny login lub hasło.')

    session.clear()
    session['user_id'] = user.id
    session['username'] = user.username
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
    force_password_change = (
        session.get('must_change_password')
        and session.get('role') != 'admin'
    )

    rooms = Room.query.all()
    user_res = Reservation.query.filter_by(user_id=session['user_id']).order_by(Reservation.start_time.asc()).all()
    all_reservations = None
    users = None
    success = session.pop('success', None)

    if session.get('role') == 'admin':
        all_reservations = (
            Reservation.query
            .order_by(Reservation.start_time.asc())
            .all()
        )
        users = User.query.filter(User.role != 'admin').order_by(User.username.asc()).all()

    return render_template(
        'index.html',
        rooms=rooms,
        user_reservations=user_res,
        all_reservations=all_reservations,
        users=users,
        success=success,
        force_password_change=force_password_change,
    )


@app.route('/api/rooms/search', methods=['GET'])
@login_required
def search_rooms():
    min_capacity = request.args.get('min_capacity', type=int)
    requires_projector = request.args.get('requires_projector', 'false').lower() == 'true'
    start_str = request.args.get('start_time', '').strip()
    end_str = request.args.get('end_time', '').strip()

    query = Room.query

    if min_capacity is not None and min_capacity > 0:
        query = query.filter(Room.capacity >= min_capacity)

    if requires_projector:
        query = query.filter(Room.has_projector.is_(True))

    rooms = query.all()

    if start_str and end_str:
        start_time, error_response, status = parse_datetime(start_str, 'start_time')
        if error_response:
            return error_response, status
        end_time, error_response, status = parse_datetime(end_str, 'end_time')
        if error_response:
            return error_response, status

        if start_time >= end_time:
            return jsonify({'error': 'Czas zakończenia musi być po czasie rozpoczęcia.'}), 400

        # czy sala wolna - sprawdzamy nakladanie terminow
        available = []
        for room in rooms:
            conflict = Reservation.query.filter(
                Reservation.room_id == room.id,
                Reservation.start_time < end_time,
                Reservation.end_time > start_time,
            ).first()
            if not conflict:
                available.append(room)
        rooms = available

    return jsonify([
        {
            'id': r.id,
            'name': r.name,
            'capacity': r.capacity,
            'has_projector': r.has_projector,
        }
        for r in rooms
    ])


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required_api
def edit_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Nie znaleziono użytkownika.'}), 404
    if user.role == 'admin':
        return jsonify({'error': 'Nie można edytować konta administratora.'}), 403

    data = request.get_json() or {}

    if 'username' in data:
        username = (data['username'] or '').strip()
        if not username:
            return jsonify({'error': 'Nazwa użytkownika nie może być pusta.'}), 400
        user.username = username

    if 'login' in data:
        login_value = (data['login'] or '').strip()
        if not login_value:
            return jsonify({'error': 'Login nie może być pusty.'}), 400
        existing = User.query.filter(User.login == login_value, User.id != user.id).first()
        if existing:
            return jsonify({'error': 'Ten login jest już zajęty.'}), 409
        user.login = login_value

    if 'password' in data and data['password']:
        password_error = validate_password(data['password'])
        if password_error:
            return jsonify({'error': password_error}), 400
        user.password = hash_password(data['password'])
        user.must_change_password = data.get('must_change_password', True)

    try:
        db.session.commit()
        return jsonify({'message': 'Dane użytkownika zostały zaktualizowane.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Błąd zapisu: {str(e)}'}), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_user(user_id):
    if user_id == session.get('user_id'):
        return jsonify({'error': 'Nie możesz usunąć własnego konta.'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Nie znaleziono użytkownika.'}), 404
    if user.role == 'admin':
        return jsonify({'error': 'Nie można usunąć konta administratora.'}), 403

    try:
        Reservation.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Użytkownik został usunięty.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Błąd usuwania: {str(e)}'}), 500


@app.route('/api/rooms/<int:room_id>/reservations', methods=['GET'])
@login_required
def get_room_reservations(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({'error': 'Nie znaleziono sali.'}), 404

    reservations = Reservation.query.filter_by(room_id=room_id).filter(Reservation.end_time >= datetime.now()).all()
    res_list = [{
        'user': r.user.username,
        'start': r.start_time.strftime('%Y-%m-%d %H:%M'),
        'end': r.end_time.strftime('%Y-%m-%d %H:%M')
    } for r in reservations]
    return jsonify(res_list)


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

    password_error = validate_password(password)
    if password_error:
        return render_template('index.html', rooms=Room.query.all(), error=password_error)

    existing_user = User.query.filter_by(login=login_value).first()
    if existing_user:
        return render_template('index.html', rooms=Room.query.all(), error='Użytkownik o takim loginie już istnieje.')

    new_user = User(
        username=username,
        login=login_value,
        password=hash_password(password),
        role='pracownik',
        must_change_password=True
    )
    db.session.add(new_user)
    db.session.commit()
    session['success'] = f'Użytkownik {username} został dodany.'
    return redirect(url_for('panel'))


@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    rooms = Room.query.all()
    user_res = Reservation.query.filter_by(user_id=session['user_id']).order_by(Reservation.start_time.asc()).all()
    force_password_change = (
        session.get('must_change_password')
        and session.get('role') != 'admin'
    )

    if not new_password or not confirm_password:
        return render_template(
            'index.html',
            rooms=rooms,
            user_reservations=user_res,
            error="Oba pola są wymagane.",
            force_password_change=force_password_change,
        )

    if new_password != confirm_password:
        return render_template(
            'index.html',
            rooms=rooms,
            user_reservations=user_res,
            error="Hasła nie są identyczne.",
            force_password_change=force_password_change,
        )

    password_error = validate_password(new_password)
    if password_error:
        return render_template(
            'index.html',
            rooms=rooms,
            user_reservations=user_res,
            error=password_error,
            force_password_change=force_password_change,
        )

    user = User.query.get(session['user_id'])
    user.password = hash_password(new_password)
    user.must_change_password = False
    db.session.commit()

    session.clear()
    return render_template('login.html', success="Hasło zostało zmienione. Zaloguj się ponownie nowym hasłem.")


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

    name = (data['name'] or '').strip()
    if not name:
        return jsonify({'error': 'Nazwa sali nie może być pusta.'}), 400

    existing_room = Room.query.filter_by(name=name).first()
    if existing_room:
        return jsonify({'error': 'Sala o podanej nazwie już istnieje w bazie.'}), 409

    new_room = Room(name=name, capacity=capacity, has_projector=data.get('has_projector', False))

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

    if room.reservations:
        return jsonify({'error': 'Nie można usunąć sali, która ma przypisane rezerwacje.'}), 400

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
    if not data:
        return jsonify({'error': 'Brak danych do aktualizacji.'}), 400

    if 'name' in data:
        name = (data['name'] or '').strip()
        if not name:
            return jsonify({'error': 'Nazwa nie może być pusta.'}), 400
        room.name = name

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


@app.route('/api/reservations', methods=['POST'])
@login_required
def make_reservation():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Brak danych rezerwacji.'}), 400

    room_id = data.get('room_id')
    if not room_id:
        return jsonify({'error': 'Nie wybrano sali.'}), 400

    room = Room.query.get(room_id)
    if not room:
        return jsonify({'error': 'Nie znaleziono sali.'}), 404

    start_time, error_response, status = parse_datetime(data.get('start_time'), 'start_time')
    if error_response:
        return error_response, status
    end_time, error_response, status = parse_datetime(data.get('end_time'), 'end_time')
    if error_response:
        return error_response, status

    is_recurring = data.get('is_recurring', False)

    if start_time >= end_time:
        return jsonify({'error': 'Czas zakończenia musi być po czasie rozpoczęcia.'}), 400

    def check_conflict(s, e):
        # terminy sie nie moga nakladac
        return Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.start_time < e,
            Reservation.end_time > s
        ).first()

    occurrences = 5 if is_recurring else 1  # co tydzien przez miesiac
    to_create = []

    for i in range(occurrences):
        current_start = start_time + timedelta(weeks=i)
        current_end = end_time + timedelta(weeks=i)

        conflict = check_conflict(current_start, current_end)
        if conflict:
            return jsonify({'error': f'Sala zajęta w terminie {current_start.strftime("%Y-%m-%d %H:%M")}'}), 400

        new_res = Reservation(
            room_id=room_id,
            user_id=session['user_id'],
            start_time=current_start,
            end_time=current_end,
            is_recurring=is_recurring
        )
        to_create.append(new_res)

    try:
        for res in to_create:
            db.session.add(res)
        db.session.commit()
        return jsonify({'message': 'Zarezerwowano pomyślnie!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Wystąpił błąd podczas zapisu rezerwacji: {str(e)}'}), 500


@app.route('/api/reservations/<int:res_id>', methods=['DELETE'])
@login_required
def cancel_reservation(res_id):
    res = Reservation.query.get(res_id)
    if not res:
        return jsonify({'error': 'Nie znaleziono rezerwacji.'}), 404
    is_owner = res.user_id == session['user_id']
    is_admin = session.get('role') == 'admin'
    if not is_owner and not is_admin:
        return jsonify({'error': 'Nie możesz odwołać tej rezerwacji.'}), 403

    try:
        db.session.delete(res)
        db.session.commit()
        return jsonify({'message': 'Odwołano rezerwację.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Wystąpił błąd podczas usuwania rezerwacji: {str(e)}'}), 500


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug)
