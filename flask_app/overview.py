from flask import Blueprint, render_template
from bokeh.embed import server_document

def create_bp(value):

    bp = Blueprint('overview', __name__)

    @bp.route('/')
    def overview():
        val= value
        return render_template('overview.html', val = val)

    return bp
