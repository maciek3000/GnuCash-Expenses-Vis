from flask import Blueprint, render_template


def create_bp(bkapp_server_address):

    bp = Blueprint('overview', __name__)

    @bp.route('/')
    def overview():
        return render_template('overview.html', address = bkapp_server_address)

    return bp
