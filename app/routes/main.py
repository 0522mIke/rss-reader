from flask import Blueprint, render_template
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # if current_user.is_authenticated:
        return render_template('index.html')  
    # else:
     #   return render_template('login.html')