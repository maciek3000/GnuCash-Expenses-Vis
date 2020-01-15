from flask import Blueprint, render_template

def create_bp(bkapp_server_address):

    bp = Blueprint('trends', __name__)

    @bp.route('/trends')
    def trends():
        return render_template('trends.html', address = bkapp_server_address)

    return bp
