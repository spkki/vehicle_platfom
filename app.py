import logging
logging.basicConfig(filename='app.log', level=logging.ERROR)

import os
from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# ── App Setup ─────────────────────────────────────────

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', 'CHANGE-ME-in-production')

db_path = os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.config['PREFERRED_URL_SCHEME'] = 'https'

db = SQLAlchemy(app)

# ── Models ──────────────────────────────────────────────

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    nickname = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    fuel_logs = db.relationship('FuelLog', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    maintenance_logs = db.relationship('Maintenance', backref='vehicle', lazy=True, cascade='all, delete-orphan')


class FuelLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    odometer = db.Column(db.Integer, nullable=False)
    liter = db.Column(db.Float, nullable=False)
    price_per_liter = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    full_tank = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)


class Maintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    odometer = db.Column(db.Integer, nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)


# ── Initialize DB ─────────────────────────────────────

with app.app_context():
    db.create_all()


# ── Routes ──────────────────────────────────────────────

@app.route('/')
def index():
    vehicles = Vehicle.query.all()
    return render_template('index.html', vehicles=vehicles)


@app.route('/vehicles')
def vehicles():
    all_vehicles = Vehicle.query.all()
    return render_template('vehicles.html', vehicles=all_vehicles)


# ── Add Vehicle ─────────────────────────────────────────

@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if request.method == 'POST':
        make = request.form.get('make', '').strip()
        model = request.form.get('model', '').strip()
        year = request.form.get('year', '').strip()
        nickname = request.form.get('nickname', '').strip()
        notes = request.form.get('notes', '').strip()

        if not make or not model or not year:
            flash('Make, Model and Year are required.', 'danger')
            return render_template('add_vehicle.html')

        try:
            year_int = int(year)
        except ValueError:
            flash('Year must be a number.', 'danger')
            return render_template('add_vehicle.html')

        new_vehicle = Vehicle(
            make=make,
            model=model,
            year=year_int,
            nickname=nickname or None,
            notes=notes or None
        )
        db.session.add(new_vehicle)
        db.session.commit()

        return redirect(url_for('vehicles'))

    return render_template('add_vehicle.html')


# ── Maintenance ─────────────────────────────────────────

@app.route('/vehicles/<int:vehicle_id>/maintenance_logs')
def maintenance_logs(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    logs = Maintenance.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(Maintenance.date.asc()).all()
    all_vehicles = Vehicle.query.all()

    # ✅ FIX: JSON-safe logs
    logs_json = []
    for log in logs:
        logs_json.append({
            "date": str(log.date) if log.date else "",
            "odometer": log.odometer or 0,
            "service_type": log.service_type or "Unknown",
            "cost": float(log.cost) if log.cost else 0,
            "notes": log.notes or ""
        })

    return render_template(
        'maintenance_logs.html',
        vehicle=vehicle,
        logs=logs,
        logs_json=logs_json,   # IMPORTANT FIX
        all_vehicles=all_vehicles
    )


@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    vehicles = Vehicle.query.all()

    if request.method == 'POST':
        try:
            new_service = Maintenance(
                vehicle_id=int(request.form.get('vehicle_id')),
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
                odometer=int(request.form.get('odometer')),
                service_type=request.form.get('service_type'),
                cost=float(request.form.get('cost')),
                notes=request.form.get('notes')
            )
            db.session.add(new_service)
            db.session.commit()
            return redirect(url_for('maintenance_logs', vehicle_id=new_service.vehicle_id))

        except Exception as e:
            flash(f'Error: {e}', 'danger')

    return render_template('add_service.html', vehicles=vehicles)


# ── Fuel ────────────────────────────────────────────────

@app.route('/vehicles/<int:vehicle_id>/fuel')
def fuel_logs(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    logs = FuelLog.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(FuelLog.date.asc()).all()
    all_vehicles = Vehicle.query.all()

    # ✅ ALSO FIXED (future-proof)
    logs_json = []
    for log in logs:
        logs_json.append({
            "date": str(log.date) if log.date else "",
            "odometer": log.odometer or 0,
            "liter": log.liter or 0,
            "price_per_liter": log.price_per_liter or 0,
            "total_cost": log.total_cost or 0,
            "full_tank": log.full_tank,
            "notes": log.notes or ""
        })

    return render_template(
        'fuel_logs.html',
        vehicle=vehicle,
        logs=logs,
        logs_json=logs_json,   # optional but recommended
        all_vehicles=all_vehicles
    )


@app.route('/vehicles/<int:vehicle_id>/fuel/add', methods=['GET', 'POST'])
def add_fuel_log(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if request.method == 'POST':
        try:
            new_log = FuelLog(
                vehicle_id=vehicle.id,
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
                odometer=int(request.form.get('odometer')),
                liter=float(request.form.get('liter')),
                price_per_liter=float(request.form.get('price_per_liter')),
                total_cost=float(request.form.get('total_cost')),
                full_tank=('full_tank' in request.form),
                notes=request.form.get('notes')
            )
            db.session.add(new_log)
            db.session.commit()

            return redirect(url_for('fuel_logs', vehicle_id=vehicle.id))

        except Exception as e:
            flash(f'Error: {e}', 'danger')

    return render_template('add_fuel_log.html', vehicle=vehicle)


# ── Delete ─────────────────────────────────────────────

@app.route('/maintenance/<int:log_id>/delete', methods=['POST'])
def delete_maintenance(log_id):
    log = Maintenance.query.get_or_404(log_id)
    vid = log.vehicle_id
    db.session.delete(log)
    db.session.commit()
    return redirect(url_for('maintenance_logs', vehicle_id=vid))


@app.route('/vehicles/<int:vehicle_id>/fuel/<int:log_id>/delete', methods=['POST'])
def delete_fuel_log(vehicle_id, log_id):
    log = FuelLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return redirect(url_for('fuel_logs', vehicle_id=vehicle_id))


# ── Run (dev only) ─────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)