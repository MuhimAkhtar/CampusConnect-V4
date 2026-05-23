from flask import Blueprint, render_template, redirect, url_for
from helpers import is_logged_in, get_unread_count

calculators_bp = Blueprint('calculators', __name__)

@calculators_bp.route('/gpa-calculator')
def gpa_calculator():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    return render_template('gpa_calculator.html', unread=get_unread_count())

@calculators_bp.route('/merit-calculator')
def merit_calculator():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    return render_template('merit_calculator.html', unread=get_unread_count())
