#views.py - Maps URLs to backend functions, then returns the results to the appropriate view

import json, datetime
from functools import wraps
from flask import (render_template, Blueprint, Response, request)
from web.extensions import cache
from .api.user.utilities import get_gallery_images
from .settings import ANNOUNCEMENT, Config

main = Blueprint('main', __name__)

DEFAULT_CANVAS = {'x':26, 'y':26}

#Home page
@main.route('/', methods=('GET', ))
@main.route('/index', methods=('GET', ))
@cache.cached(timeout=60)
def index():
    return render_template('main.html', canvas_size=DEFAULT_CANVAS, announcement=ANNOUNCEMENT, home_tag=' active', about_tag='')

@main.route('/gallery',methods=('GET',))
@cache.cached(timeout=60)
def about():
    img_list = get_gallery_images()
    return render_template('gallery.html', img_list=img_list, home_tag='', gallery_tag=' active')

@main.route('/print', methods=('GET', ))
def print_view():
    return render_template('print.html')

@main.route('/art_confirmation', methods=('GET', ))
def art_confirmation():
    args = request.args
    token = args.get('token')
    artpiece_id = args.get('id')

    return render_template(
            'art_confirmation.html', confirmation_token=token, artpiece_id=artpiece_id
            )

@main.route(Config.LOGGING_URI, methods=('POST', ))
def report_info():
    msg = request.get_data()
    try:
        msg = json.loads(msg)
    except:
        return Response(status = 400)
    print(f'{request.remote_addr} - - [{datetime.datetime.now().strftime("%d/%b/%Y %H:%M:%S")}] REPORT {str(msg)}')
    return Response(status = 200)