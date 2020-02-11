from flask import Blueprint, render_template
from bokeh.embed import server_document

def create_bp(bkapp_server_address):

    bp = Blueprint('category', __name__)

    @bp.route('/category')
    def category():
        script = server_document(bkapp_server_address + 'category')
        table = server_document(bkapp_server_address + 'describing_table')
        return render_template('category.html', script=script, table=table)

    return bp