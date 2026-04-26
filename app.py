import os
from flask import Flask, render_template, session, jsonify, request
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import CSRFError
from flask_talisman import Talisman
from config import config
from models import db, login_manager
from datetime import timedelta

csrf = CSRFProtect()
talisman = Talisman()
socketio = SocketIO(cors_allowed_origins="*")

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.permanent_session_lifetime = timedelta(days=7)

    csrf.init_app(app)
    talisman.init_app(app,
        content_security_policy={
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com",
                           "https://cdnjs.cloudflare.com", "https://unpkg.com",
                           "https://cdn.socket.io",
                           "https://maps.googleapis.com", "https://maps.gstatic.com"],
            'style-src': ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com",
                          "https://unpkg.com", "https://fonts.googleapis.com"],
            'font-src': ["'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com"],
            'img-src': ["'self'", "data:", "https:", "blob:"],
            'connect-src': ["'self'", "ws:", "wss:", "https://maps.googleapis.com"],
            # Allow embedding Google Maps route iframe in prototype.
            'frame-src': ["'self'", "https://www.google.com", "https://maps.google.com"],
            'worker-src': ["'self'", "blob:"],
        },
        force_https=False
    )

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_page'

    from models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

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
    from controllers.message_controller import message_bp
    from controllers.notification_controller import notification_bp
    from controllers.chat_controller import chat_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(ride_bp, url_prefix='/api/rides')
    app.register_blueprint(booking_bp, url_prefix='/api/bookings')
    app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
    app.register_blueprint(rating_bp, url_prefix='/api/ratings')
    app.register_blueprint(sos_bp, url_prefix='/api/sos')
    app.register_blueprint(admin_bp)
    app.register_blueprint(lang_bp)
    app.register_blueprint(message_bp, url_prefix='/api/messages')
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    # Exempt CSRF for API JSON endpoints
    # Prototype: CSRF causes booking/posting to fail if the token/session mismatch.
    # Disable global CSRF checks and rely on authentication/roles for API endpoints.
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False

    # SocketIO event handlers
    from sockets.tracking_socket import register_tracking_handlers
    from sockets.chat_socket import register_chat_handlers
    from sockets.sos_socket import register_sos_handlers
    register_tracking_handlers(socketio)
    register_chat_handlers(socketio)
    register_sos_handlers(socketio)

    # Translation helper
    @app.context_processor
    def inject_maps_config():
        key = app.config.get('GOOGLE_MAPS_API_KEY') or ''
        return dict(
            google_maps_api_key=key,
            google_maps_enabled=bool(key.strip()),
        )

    @app.context_processor
    def utility_processor():
        def _(text):
            if session.get('lang') != 'ar':
                return text
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
                'Driver Dashboard': 'لوحة السائق',
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
                'Any origin': 'أي نقطة انطلاق',
                'Any destination': 'أي وجهة',
                'View Bookings': 'عرض الحجوزات',
                'Welcome back,': 'مرحباً بعودتك،',
                'Guest': 'زائر',
                'Safe, affordable, and eco-friendly ridesharing for university students.': 'مشاركة رحلات آمنة وبأسعار معقولة وصديقة للبيئة لطلاب الجامعات.',
                'Your Upcoming Rides': 'رحلاتك القادمة',
                'Quick Actions': 'إجراءات سريعة',
                'Loading...': 'جاري التحميل...',
                'No upcoming rides': 'لا توجد رحلات قادمة',
                'Manage wallet': 'إدارة المحفظة',
                'Safe & Smart Carpooling': 'مشاركة رحلات ذكية وآمنة',
                'Origin': 'نقطة الانطلاق',
                'Destination': 'الوجهة',
                'Date': 'التاريخ',
                'Search': 'بحث',
                'Seats': 'المقاعد',
                'Book Now': 'احجز الآن',
                'How many seats?': 'كم مقعداً؟',
                'Booking confirmed!': 'تم تأكيد الحجز!',
                'No active rides found.': 'لا توجد رحلات نشطة.',
                'Driver Dashboard': 'لوحة السائق',
                'Your Active Rides': 'رحلاتك النشطة',
                'Passengers & Chat': 'الركاب والدردشة',
                'Select a ride to view passengers': 'اختر رحلة لعرض الركاب',
                'No passengers booked for this ride.': 'لا يوجد ركاب محجوزون لهذه الرحلة.',
                'Chat with Passenger': 'الدردشة مع الراكب',
                'Chat with Driver': 'الدردشة مع السائق',
                'Chat with': 'الدردشة مع',
                'Driver': 'السائق',
                'Type a message...': 'اكتب رسالة...',
                'Failed to send message': 'فشل في إرسال الرسالة',
                'Offer a Ride': 'اعرض رحلة',
                'Post Ride': 'نشر الرحلة',
                'e.g. King Saud University': 'مثال: جامعة الملك سعود',
                'e.g. Riyadh Park Mall': 'مثال: الرياض بارك',
                'Departure Date & Time': 'تاريخ ووقت المغادرة',
                'Available Seats': 'المقاعد المتاحة',
                'Price per Seat ($)': 'السعر لكل مقعد ($)',
                'Recurring Days (optional)': 'أيام التكرار (اختياري)',
                'Create Account': 'إنشاء حساب',
                'Full Name': 'الاسم الكامل',
                'Email': 'البريد الإلكتروني',
                'Phone': 'الهاتف',
                'Password': 'كلمة المرور',
                'Role': 'الدور',
                'Passenger': 'راكب',
                'Driver': 'سائق',
                'Vehicle Details': 'تفاصيل المركبة',
                'Register': 'تسجيل',
                'You have no bookings.': 'ليس لديك حجوزات.',
                'Are you sure you want to cancel this booking?': 'هل أنت متأكد من إلغاء هذا الحجز؟',
                'Booking cancelled successfully.': 'تم إلغاء الحجز بنجاح.',
                'Book seats': 'احجز مقاعد',
                'Close': 'إغلاق',
                'Wallet': 'المحفظة',
                'Add funds to your wallet to book.': 'أضف رصيداً إلى محفظتك للحجز.',
                'Map unavailable': 'الخريطة غير متاحة',
                'Login to UniRide': 'تسجيل الدخول إلى UniRide',
                "Don't have an account?": 'ليس لديك حساب؟',
                'Demo sign-in (local)': 'تسجيل تجريبي (محلي)',
                'After running init_db.py, use these accounts:': 'بعد تشغيل init_db.py، استخدم هذه الحسابات:',
                'Admin is not available on Sign Up. After running init_db.py, use:': 'حساب المشرف غير متاح في التسجيل العام. بعد تشغيل init_db.py استخدم:',
                'Fill admin': 'تعبئة حساب المشرف',
                'Main menu': 'القائمة الرئيسية',
                'Back': 'رجوع',
                'Page navigation': 'تنقل الصفحة',
                'Add a Google Maps API key': 'أضف مفتاح Google Maps API',
                'to your environment as GOOGLE_MAPS_API_KEY.': 'إلى البيئة كـ GOOGLE_MAPS_API_KEY.',
                'View on map': 'عرض على الخريطة',
                'No available rides right now.': 'لا توجد رحلات متاحة حالياً.',
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

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        # JSON clients should never receive HTML error pages.
        if request.path.startswith('/api/'):
            return jsonify({'error': 'CSRF token missing or invalid'}), 400
        return render_template('base.html', title='400'), 400

    # Home route
    @app.route('/')
    def home():
        return render_template('index.html')

    # Create tables
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app(os.environ.get('FLASK_ENV', 'default'))
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
