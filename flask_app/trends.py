from flask import Blueprint, render_template
from bokeh.embed import server_document

def create_bp(bkapp_server_address):

    bp = Blueprint('trends', __name__)

    @bp.route('/trends')
    def trends():
        t = server_document(bkapp_server_address + 'some_data')
        return render_template('trends.html', val = t)

    return bp
