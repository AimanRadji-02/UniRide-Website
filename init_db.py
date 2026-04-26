from app import create_app
from models import db
from models.user import User
from models.wallet import Wallet
from pathlib import Path

def init_db():
    app = create_app('default')
    with app.app_context():
        # Ensure the SQLite file directory exists (for default instance/uniride.db).
        try:
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_uri.startswith('sqlite:///'):
                sqlite_path = db_uri.replace('sqlite:///', '', 1)
                Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        db.drop_all()
        db.create_all()

        # Create sample admin
        admin = User(name='Admin', email='admin@uniride.com', phone='0500000000', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        # Create sample driver
        driver = User(name='Ahmed Driver', email='driver@uniride.com', phone='0501111111', role='driver', vehicle_details='Toyota Camry 2023 - White')
        driver.set_password('driver123')
        db.session.add(driver)

        # Create sample passenger
        passenger = User(name='Sara Passenger', email='passenger@uniride.com', phone='0502222222', role='passenger')
        passenger.set_password('passenger123')
        db.session.add(passenger)

        db.session.flush()

        # Create wallets
        for user in [admin, driver, passenger]:
            wallet = Wallet(user_id=user.user_id, balance=100.0)
            db.session.add(wallet)

        db.session.commit()
        print("Database initialized with sample data.")
        print("Admin: admin@uniride.com / admin123")
        print("Driver: driver@uniride.com / driver123")
        print("Passenger: passenger@uniride.com / passenger123")

if __name__ == '__main__':
    init_db()
