from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import db
from models.notification import Notification

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/my-notifications')
@login_required
def get_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.user_id).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        'id': n.notification_id,
        'title': n.title,
        'message': n.message_body,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat()
    } for n in notifs])

@notification_bp.route('/mark-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'message': 'Marked as read'})
