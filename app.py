#Flask application

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
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
    full_tank = db.Column(db.Boolean, default=True)
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
    return "Flask is working!"
    #return render_template('index.html')

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
        
        new_vehicle = Vehicle(make=make, model=model, year=year, nickname=nickname, notes=notes)
        db.session.add(new_vehicle)
        db.session.commit()
        
        return redirect(url_for('vehicles'))
    return render_template('add_vehicle.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

