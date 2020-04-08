import os
from flask import Flask, render_template
from bokeh.embed import server_document
from datetime import datetime

def create_app(test_config=None):
    # app factory
    app = Flask(__name__, instance_relative_config=None)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # bkapp section

    from .bkapp.bkapp_server import BokehServer

    # test file and names, later on it will be provided by the user
    bk_file_path_db = os.path.join(app.root_path, 'gnucash', 'gnucash_examples', 'example_gnucash.gnucash')
    # bk_file_path_db = os.path.join(app.root_path, 'gnucash', 'gnucash_files', 'finanse_sql.gnucash')
    bk_port = 9090
    bkapp_server_address = 'http://127.0.0.1:9090/'

    # col_mapping can be later provided from the file
    col_mapping = {
        "date": "Date",
        "price": "Price",
        "currency": "Currency",
        "product": "Product",
        "shop": "Shop",
        "all": "ALL_CATEGORIES",
        "type": "Type",
        "category": "Category",
        "monthyear": "MonthYear"
    }

    server_date = datetime.now()

    bkapp_server = BokehServer(bk_file_path_db, bk_port, col_mapping, server_date)

    from threading import Thread
    Thread(target=bkapp_server.bkworker).start()

    # Blueprints section

    from . import trends, overview, category, settings

    bp_trends = trends.create_bp(bkapp_server_address)
    bp_overview = overview.create_bp(bkapp_server_address)
    bp_category = category.create_bp(bkapp_server_address)
    bp_settings = settings.create_bp(bkapp_server_address)

    app.register_blueprint(bp_trends)
    app.register_blueprint(bp_overview)
    app.register_blueprint(bp_category)
    app.register_blueprint(bp_settings)

    app.add_url_rule('/', endpoint='overview')


    #@app.route('/')
    #def index():
    #    script = server_document('http://127.0.0.1:9090/trends')
    #    return render_template('overview.html', script=script)

    return app
