from flask import Blueprint, render_template
from bokeh.embed import server_document


def create_bp(bkapp_server_address):

    bp = Blueprint('settings', __name__)

    @bp.route('/settings')
    def settings():
        script = server_document(bkapp_server_address + 'settings')
        return render_template('settings.html', script=script)

    return bp
