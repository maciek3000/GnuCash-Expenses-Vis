from flask import Blueprint, render_template
from bokeh.embed import server_document


def create_bp(bkapp_server_address):

    bp = Blueprint('settings', __name__)

    @bp.route('/settings')
    def settings():
        categories = server_document(bkapp_server_address + 'settings')
        month_range = server_document(bkapp_server_address + 'slider')
        return render_template('settings.html', categories=categories, month_range=month_range)

    return bp
