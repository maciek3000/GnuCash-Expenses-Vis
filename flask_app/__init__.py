import os
from flask import Flask
from datetime import datetime
from multiprocessing import Process
import webbrowser

from . import trends, overview, category, settings
from .bkapp.bkapp_server import BokehServer
from .gnucash.gnucash_db_parser import GnuCashDBParser

def create_app(test_config=None):

    # app factory
    app = Flask(__name__, instance_relative_config=None)

    app.config.from_mapping(
        SECRET_KEY='dev',
        ENV="development"
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
    category_sep = ":"
    monthyear_format = "%Y-%m"

    bk_file_path_db = None

    # checking if there is any file provided in .cfg file and if it is SQLite file
    with open(os.path.join(app.root_path, "gnucash_file_path.cfg"), "r") as g_cfg:
        lines = g_cfg.readlines()
        for line in lines:
            if "GNUCASH_FILE_PATH" in line:
                address = line.split("=")[1]
                if os.path.isfile(address) and os.path.splitext(address)[1] == ".gnucash":
                        if GnuCashDBParser.check_file(address):
                            bk_file_path_db = address

    if bk_file_path_db is None:
        print("Not a correct .gnucash file - perhaps it was saved as XML and not as SQL?\n"
              "Using Test file instead.\n")
        bk_file_path_db = os.path.join(app.root_path, 'gnucash', 'gnucash_examples', 'example_gnucash.gnucash')

    gnucash_parser = GnuCashDBParser(bk_file_path_db, category_sep=category_sep, monthyear_format=monthyear_format)

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

    # bkapp server
    bk_port = 9090
    bkapp_server_address = 'http://127.0.0.1:9090/'

    bkapp_server = BokehServer(
        bk_port,
        col_mapping,
        gnucash_parser.get_expenses_df(),
        gnucash_parser.get_income_df(),
        server_date,
        monthyear_format,
        category_sep
    )

    bkserver_process = Process(target=bkapp_server.bkworker)
    bkserver_process.start()

    # Blueprints
    bp_trends = trends.create_bp(bkapp_server_address)
    bp_overview = overview.create_bp(bkapp_server_address)
    bp_category = category.create_bp(bkapp_server_address)
    bp_settings = settings.create_bp(bk_file_path_db, bkapp_server_address)

    app.register_blueprint(bp_trends)
    app.register_blueprint(bp_overview)
    app.register_blueprint(bp_category)
    app.register_blueprint(bp_settings)

    app.add_url_rule('/', endpoint='overview')

    # Opening new browser window on load
    webbrowser.open_new("http://127.0.0.1:5000/")

    return app
