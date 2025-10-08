#Flask application

import os
from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Models
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    nickname = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
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
    
# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Vehicle Management
@app.route('/vehicles')
def vehicles():
    all_vehicles = Vehicle.query.all()
    return render_template('vehicles.html', vehicles=all_vehicles)

@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if request.method == 'POST':
        make = request.form['make']
        model = request.form['model']
        year = request.form['year']
        nickname = request.form.get('nickname')
        notes = request.form.get('notes')
        
        new_vehicle = Vehicle(
            make=make, 
            model=model,
            year=year, 
            nickname=nickname, 
            notes=notes)
        db.session.add(new_vehicle)
        db.session.commit()
        
        return redirect(url_for('vehicles'))
    return render_template('add_vehicle.html')

# Maintenance Management
@app.route('/vehicles/<int:vehicle_id>/maintenance_logs')
def maintenance_logs(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    logs = Maintenance.query.filter_by(vehicle_id=vehicle_id).all()
    all_vehicles = Vehicle.query.all()
    return render_template(
        'maintenance_logs.html', 
        vehicle=vehicle, 
        logs=logs,
        all_vehicles=all_vehicles
        )
    
@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    all_vehicles = Vehicle.query.all()
    if request.method == 'POST':
        vehicle_id = request.form['vehicle_id']
        date_str = request.form.get('date')  # e.g., '2024-10-06'
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        odometer = request.form['odometer']
        service_type = request.form['service_type']
        cost = request.form['cost']
        notes = request.form.get('notes')
        
        new_service = Maintenance(
            vehicle_id=int(request.form.get('vehicle_id')), 
            date=date_obj, 
            odometer=int(request.form.get('odometer')),
            service_type=request.form.get('service_type'),
            cost=float(request.form.get('cost')),
            notes=request.form.get('notes')
            )
        db.session.add(new_service)
        db.session.commit()
        
        return redirect(url_for('maintenance_logs', vehicle_id=vehicle_id))
    return render_template('add_service.html', vehicles=all_vehicles)

@app.route('/maintenance/<int:log_id>/delete', methods=['POST'])
def delete_maintenance(log_id):
    log = Maintenance.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    flash('Maintenance entry deleted successfully!', 'success')
    return redirect(url_for('maintenance_logs', vehicle_id=log.vehicle_id))

# Fueling Management
@app.route('/vehicles/<int:vehicle_id>/fuel')
def fuel_logs(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    logs = FuelLog.query.filter_by(vehicle_id=vehicle_id).all()
    all_vehicles = Vehicle.query.all()
    return render_template('fuel_logs.html', vehicle=vehicle, logs=logs, all_vehicles=all_vehicles)

@app.route('/vehicles/<int:vehicle_id>/fuel/add', methods=['GET', 'POST'])
def add_fuel_log(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if request.method == 'POST':
        date_str = request.form.get('date')  # e.g., '2024-10-06'
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        odometer = request.form['odometer']
        liter = request.form['liter']
        price_per_liter = request.form['price_per_liter']
        total_cost = request.form['total_cost']
        full_tank = 'full_tank' in request.form
        notes = request.form.get('notes')
        
        new_log = FuelLog(
            vehicle_id=vehicle.id,
            date = date_obj,
            odometer=odometer,
            liter=liter,
            price_per_liter=price_per_liter,
            total_cost=total_cost,
            full_tank=full_tank,
            notes = notes
            )
        db.session.add(new_log)
        db.session.commit()
        return redirect(url_for('fuel_logs', vehicle_id=vehicle.id))
    
    return render_template('add_fuel_log.html', vehicle=vehicle)
        


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

