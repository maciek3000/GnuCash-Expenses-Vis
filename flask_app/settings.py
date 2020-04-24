from flask import Blueprint, render_template, request
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField
from werkzeug import secure_filename

from bokeh.embed import server_document



def create_bp(file_path, bkapp_server_address):

    bp = Blueprint('settings', __name__)

    @bp.route('/settings/', methods=["GET", "POST"])
    def settings():

        if request.method == "POST":
            address = request.form["file_path"]
            print(address)

        # Bokeh Gridplots
        categories = server_document(bkapp_server_address + 'settings_categories')
        month_range = server_document(bkapp_server_address + 'settings_month_range')

        return render_template('settings.html', categories=categories, month_range=month_range, file_path=file_path)

    return bp
