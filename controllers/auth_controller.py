from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.user import User
from models.wallet import Wallet

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login-page', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/register-page', methods=['GET'])
def register_page():
    return render_template('register.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    role = request.form.get('role')
    vehicle_details = request.form.get('vehicle_details')
    
    if User.query.filter_by(email=email).first():
        flash('Email already registered', 'danger')
        return redirect(url_for('auth.register_page'))
    
    user = User(name=name, email=email, phone=phone, role=role, vehicle_details=vehicle_details)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    starter = 50.0 if role == 'passenger' else 0.0
    wallet = Wallet(user_id=user.user_id, balance=starter)
    db.session.add(wallet)
    db.session.commit()
    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        flash('Logged in successfully.', 'success')
        return redirect(url_for('home'))
    flash('Invalid email or password', 'danger')
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@auth_bp.route('/profile')
@login_required
def get_profile():
    return render_template('profile.html', user=current_user)  # optional template