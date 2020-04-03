from flask import Blueprint, render_template
from bokeh.embed import server_document

def create_bp(bkapp_server_address):

    bp = Blueprint('overview', __name__)

    @bp.route('/')
    def overview():
        script = server_document(bkapp_server_address + 'overview')
        return render_template('overview.html', script = script)

    return bp
