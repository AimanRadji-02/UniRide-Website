from flask import Blueprint, session, redirect, request, url_for

lang_bp = Blueprint('language', __name__)

@lang_bp.route('/set-language/<lang>')
def set_language(lang):
    if lang in ['en', 'ar']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))