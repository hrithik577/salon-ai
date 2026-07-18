from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Service, Booking, Queue, Revenue, AIFeedback
from ai import AIPredictor
from datetime import datetime, date, timedelta
import json
import hashlib
import re
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# PostgreSQL Connection
# Use environment variable for security
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    # Fallback for local development
    database_url = 'sqlite:///database.db'

# Handle Render's PostgreSQL URL format
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# For Render PostgreSQL
if 'postgresql' in database_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'sslmode': 'require'
        }
    }

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please login to access admin panel.'

# Initialize AI Predictor
ai_predictor = AIPredictor()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables and seed data
def create_tables_and_seed():
    with app.app_context():
        db.create_all()
        seed_data()

def seed_data():
    # Check if owner exists
    if not User.query.filter_by(role='owner').first():
        owner = User(
            name='Admin Owner',
            email='admin@manjunathsalon.com',
            phone='9876543210',
            role='owner'
        )
        owner.set_password('admin123')
        db.session.add(owner)
        db.session.commit()
        print("✅ Owner created")

    # Seed services if none exist
    if Service.query.count() == 0:
        services = [
            Service(name='Classic Haircut', description='Professional haircut with styling', price=250, duration=30, category='Hair'),
            Service(name='Premium Haircut', description='Premium haircut with beard trim', price=400, duration=45, category='Hair'),
            Service(name='Hair Coloring', description='Full hair coloring service', price=800, duration=90, category='Hair'),
            Service(name='Beard Grooming', description='Precision beard trimming and shaping', price=150, duration=20, category='Grooming'),
            Service(name='Royal Shave', description='Traditional hot towel shave', price=200, duration=25, category='Grooming'),
            Service(name='Facial Treatment', description='Deep cleansing facial with massage', price=500, duration=45, category='Skincare'),
            Service(name='Hair Spa', description='Nourishing hair spa treatment', price=600, duration=60, category='Hair'),
            Service(name='Complete Grooming', description='Full grooming package', price=1000, duration=90, category='Grooming')
        ]
        for service in services:
            db.session.add(service)
        db.session.commit()
        print("✅ Services created")

create_tables_and_seed()

@app.route('/')
def index():
    services = Service.query.filter_by(is_active=True).all()
    queue_count = Queue.query.filter_by(status='waiting').count()
    return render_template('index.html', services=services, queue_count=queue_count)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    all_services = Service.query.filter_by(is_active=True).all()
    return render_template('services.html', services=all_services)

@app.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        booking_date = request.form.get('booking_date')
        booking_time = request.form.get('booking_time')
        
        print(f"📝 Booking Attempt: Name={name}, Phone={phone}, Date={booking_date}, Time={booking_time}")
        
        if not name or not phone or not booking_date or not booking_time:
            flash('Please fill in all fields', 'danger')
            return redirect(url_for('book'))
        
        # Check if customer exists
        customer = User.query.filter_by(phone=phone, role='customer').first()
        if not customer:
            customer = User(
                name=name,
                email=f"{phone}@temp.com",
                phone=phone,
                role='customer'
            )
            customer.set_password(hashlib.md5(phone.encode()).hexdigest()[:20])
            db.session.add(customer)
            db.session.commit()
            print(f"✅ New customer created: {customer.id} - {customer.name}")
        else:
            print(f"✅ Existing customer: {customer.id} - {customer.name}")
        
        # Create booking with a default service (first service)
        default_service = Service.query.first()
        if not default_service:
            flash('No services available. Please contact admin.', 'danger')
            return redirect(url_for('book'))
        
        booking = Booking(
            user_id=customer.id,
            service_id=default_service.id,
            booking_date=datetime.strptime(booking_date, '%Y-%m-%d').date(),
            booking_time=booking_time,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        
        print(f"✅ Booking created: {booking.id} for {customer.name} at {booking_time} on {booking_date}")
        print(f"📊 Total bookings: {Booking.query.count()}")
        
        flash('✅ Booking confirmed! We will contact you shortly.', 'success')
        return redirect(url_for('book_success'))
    
    return render_template('book.html', datetime=datetime)

@app.route('/book/success')
def book_success():
    return render_template('book_success.html')

@app.route('/queue', methods=['GET', 'POST'])
def queue():
    if request.method == 'POST':
        name = request.form.get('customer_name', '').strip()
        phone = request.form.get('phone', '').strip()
        service_id = request.form.get('service_id', '').strip()
        
        if not name:
            flash('Please enter your name', 'danger')
            return redirect(url_for('queue'))
        
        if not phone:
            flash('Please enter your phone number', 'danger')
            return redirect(url_for('queue'))
        
        if len(phone) < 10:
            flash('Please enter a valid 10-digit phone number', 'danger')
            return redirect(url_for('queue'))
        
        if not service_id:
            flash('Please select a service', 'danger')
            return redirect(url_for('queue'))
        
        customer = User.query.filter_by(phone=phone, role='customer').first()
        if not customer:
            customer = User(
                name=name,
                email=f"{phone}@temp.com",
                phone=phone,
                role='customer'
            )
            customer.set_password(hashlib.md5(phone.encode()).hexdigest()[:20])
            db.session.add(customer)
            db.session.commit()
        else:
            if customer.name != name:
                customer.name = name
                db.session.commit()
        
        existing = Queue.query.filter(
            Queue.user_id == customer.id,
            Queue.status.in_(['waiting', 'in_progress'])
        ).first()
        
        if existing:
            flash(f'⚠️ You are already in the queue at position #{existing.position}!', 'warning')
            return redirect(url_for('queue'))
        
        service = Service.query.get(service_id)
        if not service:
            flash('Invalid service selected!', 'danger')
            return redirect(url_for('queue'))
        
        position = Queue.query.filter_by(status='waiting').count() + 1
        
        hour = datetime.now().hour
        day = datetime.now().weekday()
        duration = service.duration
        
        predicted_wait = ai_predictor.predict_wait_time(position, hour, day, duration)
        
        queue_entry = Queue(
            user_id=customer.id,
            service_id=service_id,
            position=position,
            estimated_wait_time=predicted_wait,
            status='waiting'
        )
        db.session.add(queue_entry)
        db.session.commit()
        
        flash(f'✅ Successfully joined queue! Position: #{position} | Estimated wait: {predicted_wait} minutes', 'success')
        return redirect(url_for('queue'))
    
    services = Service.query.filter_by(is_active=True).all()
    queue_entries = Queue.query.filter_by(status='waiting').order_by(Queue.position).all()
    
    for entry in queue_entries:
        if entry.estimated_wait_time:
            hour = datetime.now().hour
            day = datetime.now().weekday()
            duration = entry.service.duration if entry.service else 30
            entry.estimated_wait_time = ai_predictor.predict_wait_time(
                entry.position, hour, day, duration
            )
    
    db.session.commit()
    
    return render_template('queue.html', services=services, queue_entries=queue_entries)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.role == 'owner':
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email, role='owner').first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'owner':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    
    # Get all data
    total_customers = User.query.filter_by(role='customer').count()
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    queue_count = Queue.query.filter_by(status='waiting').count()
    services = Service.query.all()
    
    # Get queue entries
    queue_entries = Queue.query.filter_by(status='waiting').order_by(Queue.position).all()
    in_progress_entries = Queue.query.filter_by(status='in_progress').all()
    
    # Get all bookings - ordered by newest first
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    
    # Calculate revenue
    total_revenue = 0
    revenue_entries = Revenue.query.all()
    for rev in revenue_entries:
        if rev.total_amount:
            total_revenue += rev.total_amount
    
    completed_bookings = Booking.query.filter_by(status='completed').all()
    for booking in completed_bookings:
        if booking.service:
            total_revenue += booking.service.price
    
    print(f"📊 Admin Dashboard - Bookings: {len(bookings)} total, {pending_bookings} pending")
    for b in bookings:
        print(f"   Booking: {b.id} - {b.user.name if b.user else 'Unknown'} - {b.booking_date} - {b.booking_time} - {b.status}")
    
    return render_template('admin_dashboard.html', 
                         total_customers=total_customers,
                         total_bookings=total_bookings,
                         pending_bookings=pending_bookings,
                         queue_count=queue_count,
                         services=services,
                         queue_entries=queue_entries,
                         in_progress_entries=in_progress_entries,
                         bookings=bookings,
                         total_revenue=total_revenue)

@app.route('/admin/clear_all')
@login_required
def clear_all_data():
    if current_user.role != 'owner':
        flash('Unauthorized!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        Queue.query.delete()
        Revenue.query.delete()
        Booking.query.delete()
        User.query.filter_by(role='customer').delete()
        db.session.commit()
        flash('✅ All data cleared successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error clearing data: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/service/add', methods=['POST'])
@login_required
def add_service():
    if current_user.role != 'owner':
        flash('Unauthorized!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    name = request.form.get('name')
    description = request.form.get('description')
    price = float(request.form.get('price'))
    duration = int(request.form.get('duration'))
    category = request.form.get('category')
    
    service = Service(
        name=name,
        description=description,
        price=price,
        duration=duration,
        category=category
    )
    db.session.add(service)
    db.session.commit()
    
    flash('✅ Service added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/service/edit/<int:service_id>', methods=['POST'])
@login_required
def edit_service(service_id):
    if current_user.role != 'owner':
        flash('Unauthorized!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    service = Service.query.get(service_id)
    if not service:
        flash('Service not found!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    service.name = request.form.get('name')
    service.description = request.form.get('description')
    service.price = float(request.form.get('price'))
    service.duration = int(request.form.get('duration'))
    service.category = request.form.get('category')
    
    db.session.commit()
    flash('✅ Service updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/service/delete/<int:service_id>')
@login_required
def delete_service(service_id):
    if current_user.role != 'owner':
        flash('Unauthorized!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    service = Service.query.get(service_id)
    if service:
        db.session.delete(service)
        db.session.commit()
        flash('✅ Service deleted!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/queue/complete/<int:queue_id>')
@login_required
def complete_queue_service(queue_id):
    if current_user.role != 'owner':
        flash('Unauthorized!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    queue_entry = Queue.query.get(queue_id)
    if not queue_entry:
        flash('Queue entry not found!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    service_price = queue_entry.service.price if queue_entry.service else 0
    
    queue_entry.status = 'completed'
    queue_entry.completed_at = datetime.now()
    
    if service_price > 0:
        revenue = Revenue(
            date=date.today(),
            total_amount=service_price,
            booking_count=1
        )
        db.session.add(revenue)
    
    db.session.commit()
    update_queue_positions()
    
    flash(f'✅ Service completed! ₹{service_price} added to revenue.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/booking/complete/<int:booking_id>')
@login_required
def complete_booking(booking_id):
    if current_user.role != 'owner':
        flash('Unauthorized!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    booking = Booking.query.get(booking_id)
    if booking:
        booking.status = 'completed'
        
        if booking.service:
            revenue = Revenue(
                date=date.today(),
                total_amount=booking.service.price,
                booking_count=1
            )
            db.session.add(revenue)
        
        db.session.commit()
        flash('✅ Booking marked as completed! Revenue added.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/booking/delete/<int:booking_id>')
@login_required
def delete_booking(booking_id):
    if current_user.role != 'owner':
        flash('Unauthorized!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    booking = Booking.query.get(booking_id)
    if booking:
        db.session.delete(booking)
        db.session.commit()
        flash('✅ Booking deleted!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/api/queue/status')
def api_queue_status():
    queue_entries = Queue.query.filter_by(status='waiting').order_by(Queue.position).all()
    queue_data = []
    for entry in queue_entries:
        hour = datetime.now().hour
        day = datetime.now().weekday()
        duration = entry.service.duration if entry.service else 30
        predicted_wait = ai_predictor.predict_wait_time(entry.position, hour, day, duration)
        
        queue_data.append({
            'id': entry.id,
            'position': entry.position,
            'user_name': entry.user.name if entry.user else 'Unknown',
            'service_name': entry.service.name if entry.service else 'Unknown',
            'estimated_wait': predicted_wait
        })
    return jsonify({
        'queue_length': len(queue_data),
        'entries': queue_data,
        'busy_hours': ai_predictor.get_busy_hours()
    })

@app.route('/api/queue/call/<int:queue_id>')
@login_required
def api_call_customer(queue_id):
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    queue_entry = Queue.query.get(queue_id)
    if not queue_entry:
        return jsonify({'success': False, 'message': 'Queue entry not found'})
    
    if queue_entry.status != 'waiting':
        return jsonify({'success': False, 'message': 'Customer is not waiting'})
    
    queue_entry.status = 'in_progress'
    db.session.commit()
    
    customer_name = queue_entry.user.name if queue_entry.user else 'Guest'
    service_name = queue_entry.service.name if queue_entry.service else 'Service'
    
    return jsonify({
        'success': True, 
        'message': f'Called {customer_name} for {service_name}',
        'customer_name': customer_name,
        'service_name': service_name,
        'phone': queue_entry.user.phone if queue_entry.user else 'N/A'
    })

@app.route('/api/queue/next')
@login_required
def api_next_customer():
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    next_queue = Queue.query.filter_by(status='waiting').order_by(Queue.position).first()
    if not next_queue:
        return jsonify({'success': False, 'message': 'Queue is empty'})
    
    next_queue.status = 'in_progress'
    db.session.commit()
    update_queue_positions()
    
    return jsonify({'success': True, 'message': f'Called {next_queue.user.name}'})

@app.route('/api/queue/remove/<int:queue_id>')
@login_required
def api_remove_queue(queue_id):
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    queue_entry = Queue.query.get(queue_id)
    if not queue_entry:
        return jsonify({'success': False, 'message': 'Queue entry not found'})
    
    queue_entry.status = 'cancelled'
    db.session.commit()
    update_queue_positions()
    
    return jsonify({'success': True, 'message': 'Removed from queue'})

def update_queue_positions():
    entries = Queue.query.filter_by(status='waiting').order_by(Queue.id).all()
    for idx, entry in enumerate(entries, 1):
        entry.position = idx
    db.session.commit()

def cleanup_duplicate_queue_entries():
    with app.app_context():
        users = db.session.query(Queue.user_id).filter_by(status='waiting').group_by(Queue.user_id).having(db.func.count(Queue.id) > 1).all()
        
        for user_id in users:
            entries = Queue.query.filter_by(user_id=user_id[0], status='waiting').order_by(Queue.id).all()
            for entry in entries[1:]:
                db.session.delete(entry)
        db.session.commit()
        update_queue_positions()

cleanup_duplicate_queue_entries()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
