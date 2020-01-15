from flask import Blueprint, render_template

def create_bp(bkapp_server_address):

    bp = Blueprint('monthly', __name__)

    @bp.route('/monthly')
    def monthly():
        return render_template('/viz/monthly.html', address = bkapp_server_address)

    return bp