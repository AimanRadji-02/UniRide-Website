import os
from flask import Flask, render_template, session
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from config import config
from models import db, login_manager
from datetime import timedelta

# Initialize extensions (without app)
csrf = CSRFProtect()
talisman = Talisman()
socketio = SocketIO(cors_allowed_origins="*")

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.permanent_session_lifetime = timedelta(days=7)

    # Initialize extensions with app
    csrf.init_app(app)
    talisman.init_app(app,
        content_security_policy={
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com",
                           "https://cdnjs.cloudflare.com", "https://unpkg.com",
                           "https://cdn.socket.io"],
            'style-src': ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com",
                          "https://unpkg.com"],
            'img-src': ["'self'", "data:", "https://*.tile.openstreetmap.org"]
        },
        force_https=False
    )

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_page'

    # **IMPORTANT: user_loader callback**
    from models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialize SocketIO with the app
    socketio.init_app(app, cors_allowed_origins="*")

    # Import and register blueprints
    from controllers.auth_controller import auth_bp
    from controllers.ride_controller import ride_bp
    from controllers.booking_controller import booking_bp
    from controllers.wallet_controller import wallet_bp
    from controllers.rating_controller import rating_bp
    from controllers.sos_controller import sos_bp
    from controllers.admin_controller import admin_bp
    from controllers.language_controller import lang_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(ride_bp, url_prefix='/api/rides')
    app.register_blueprint(booking_bp, url_prefix='/api/bookings')
    app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
    app.register_blueprint(rating_bp, url_prefix='/api/ratings')
    app.register_blueprint(sos_bp, url_prefix='/api/sos')
    app.register_blueprint(admin_bp)
    app.register_blueprint(lang_bp)

    # SocketIO event handlers (import after socketio init)
    from sockets.tracking_socket import register_tracking_handlers
    from sockets.chat_socket import register_chat_handlers
    from sockets.sos_socket import register_sos_handlers
    register_tracking_handlers(socketio)
    register_chat_handlers(socketio)
    register_sos_handlers(socketio)

    # Translation helper
    @app.context_processor
    def utility_processor():
        def _(text):
            translations = {
                'Offer Ride': 'اعرض رحلة',
                'Search Rides': 'ابحث عن رحلات',
                'My Bookings': 'حجوزاتي',
                'Wallet': 'المحفظة',
                'Admin': 'لوحة التحكم',
                'Login': 'تسجيل الدخول',
                'Sign Up': 'إنشاء حساب',
                'Logout': 'تسجيل الخروج',
                'Profile': 'الملف الشخصي',
                'Home': 'الرئيسية',
                'Upcoming Rides': 'الرحلات القادمة',
                'Wallet Balance': 'رصيد المحفظة',
                'Cancel': 'إلغاء',
                'Confirm': 'تأكيد',
                'Rate Ride': 'تقييم الرحلة',
                'SOS Alert': 'تنبيه طوارئ',
                'Live Track': 'تتبع مباشر',
                'Post a Ride': 'انشر رحلة',
                'Find a Ride': 'ابحث عن رحلة',
                'View Bookings': 'عرض الحجوزات'
            }
            return translations.get(text, text)
        return dict(_=_)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('base.html', title='404'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('base.html', title='500'), 500

    # Home route
    @app.route('/')
    def home():
        return render_template('index.html')

    # Create tables
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    # Create the app
    app = create_app(os.environ.get('FLASK_ENV', 'default'))
    # Run with socketio
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)