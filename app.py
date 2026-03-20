# Flask application - Vehicle Platform
# Optimized by Lovable

import os
from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Use a fixed secret key from env, fallback for dev only
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ── Models ──────────────────────────────────────────────

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    nickname = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Relationships for cleaner queries & cascade deletes
    fuel_logs = db.relationship('FuelLog', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    maintenance_logs = db.relationship('Maintenance', backref='vehicle', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Vehicle {self.make} {self.model} ({self.year})>'


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

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'date': self.date.isoformat() if self.date else None,
            'odometer': self.odometer,
            'service_type': self.service_type,
            'cost': self.cost,
            'notes': self.notes
        }


# ── Routes ──────────────────────────────────────────────

@app.route('/')
def index():
    vehicles = Vehicle.query.all()
    return render_template('index.html', vehicles=vehicles)


# ── Vehicle Management ──────────────────────────────────

@app.route('/vehicles')
def vehicles():
    all_vehicles = Vehicle.query.all()
    return render_template('vehicles.html', vehicles=all_vehicles)


@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if request.method == 'POST':
        make = request.form.get('make', '').strip()
        model = request.form.get('model', '').strip()
        year = request.form.get('year', '').strip()
        nickname = request.form.get('nickname', '').strip()
        notes = request.form.get('notes', '').strip()

        # Basic validation
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
        flash(f'{make} {model} added successfully!', 'success')
        return redirect(url_for('vehicles'))

    return render_template('add_vehicle.html')


@app.route('/vehicles/<int:vehicle_id>/delete', methods=['POST'])
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    flash(f'{vehicle.make} {vehicle.model} deleted.', 'success')
    return redirect(url_for('vehicles'))


# ── Maintenance Management ──────────────────────────────

@app.route('/vehicles/<int:vehicle_id>/maintenance_logs')
def maintenance_logs(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    logs = Maintenance.query.filter_by(vehicle_id=vehicle_id).order_by(Maintenance.date.desc()).all()
    all_vehicles = Vehicle.query.all()
    logs_dict = [log.to_dict() for log in logs]
    return render_template(
        'maintenance_logs.html',
        vehicle=vehicle,
        logs=logs_dict,
        all_vehicles=all_vehicles
    )


@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    all_vehicles = Vehicle.query.all()
    if request.method == 'POST':
        vehicle_id = request.form.get('vehicle_id')
        date_str = request.form.get('date')
        odometer = request.form.get('odometer')
        service_type = request.form.get('service_type', '').strip()
        cost = request.form.get('cost')
        notes = request.form.get('notes', '').strip()

        # Validation
        if not all([vehicle_id, date_str, odometer, service_type, cost]):
            flash('All fields except notes are required.', 'danger')
            return render_template('add_service.html', vehicles=all_vehicles)

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            new_service = Maintenance(
                vehicle_id=int(vehicle_id),
                date=date_obj,
                odometer=int(odometer),
                service_type=service_type,
                cost=float(cost),
                notes=notes or None
            )
            db.session.add(new_service)
            db.session.commit()
            flash('Service record added!', 'success')
            return redirect(url_for('maintenance_logs', vehicle_id=int(vehicle_id)))
        except (ValueError, TypeError) as e:
            flash(f'Invalid input: {e}', 'danger')
            return render_template('add_service.html', vehicles=all_vehicles)

    return render_template('add_service.html', vehicles=all_vehicles)


@app.route('/maintenance/<int:log_id>/delete', methods=['POST'])
def delete_maintenance(log_id):
    log = Maintenance.query.get_or_404(log_id)
    vehicle_id = log.vehicle_id
    db.session.delete(log)
    db.session.commit()
    flash('Maintenance entry deleted.', 'success')
    return redirect(url_for('maintenance_logs', vehicle_id=vehicle_id))


# ── Fuel Management ─────────────────────────────────────

@app.route('/vehicles/<int:vehicle_id>/fuel')
def fuel_logs(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    logs = FuelLog.query.filter_by(vehicle_id=vehicle_id).order_by(FuelLog.date.asc()).all()
    all_vehicles = Vehicle.query.all()
    return render_template('fuel_logs.html', vehicle=vehicle, logs=logs, all_vehicles=all_vehicles)


@app.route('/vehicles/<int:vehicle_id>/fuel/add', methods=['GET', 'POST'])
def add_fuel_log(vehicle_id):
    all_vehicles = Vehicle.query.all()
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if request.method == 'POST':
        date_str = request.form.get('date')
        odometer = request.form.get('odometer')
        liter = request.form.get('liter')
        price_per_liter = request.form.get('price_per_liter')
        total_cost = request.form.get('total_cost')
        full_tank = 'full_tank' in request.form
        notes = request.form.get('notes', '').strip()

        if not all([date_str, odometer, liter, price_per_liter, total_cost]):
            flash('All fields except notes are required.', 'danger')
            return render_template('add_fuel_log.html', vehicles=all_vehicles, vehicle=vehicle)

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            new_log = FuelLog(
                vehicle_id=vehicle.id,
                date=date_obj,
                odometer=int(odometer),
                liter=float(liter),
                price_per_liter=float(price_per_liter),
                total_cost=float(total_cost),
                full_tank=full_tank,
                notes=notes or None
            )
            db.session.add(new_log)
            db.session.commit()
            flash('Fuel log added!', 'success')
            return redirect(url_for('fuel_logs', vehicle_id=vehicle.id))
        except (ValueError, TypeError) as e:
            flash(f'Invalid input: {e}', 'danger')
            return render_template('add_fuel_log.html', vehicles=all_vehicles, vehicle=vehicle)

    return render_template('add_fuel_log.html', vehicles=all_vehicles, vehicle=vehicle)


@app.route('/vehicles/<int:vehicle_id>/fuel/<int:log_id>/delete', methods=['POST'])
def delete_fuel_log(vehicle_id, log_id):
    log = FuelLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    flash('Fuel entry deleted.', 'success')
    return redirect(url_for('fuel_logs', vehicle_id=vehicle_id))


# ── Error Handlers ──────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# ── App Entry ───────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
