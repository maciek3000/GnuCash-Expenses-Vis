from flask import Blueprint, render_template

def create_bp(bkapp_server_address):

    bp = Blueprint('category', __name__)

    @bp.route('/category')
    def category():
        return render_template('category.html', address = bkapp_server_address)

    return bp