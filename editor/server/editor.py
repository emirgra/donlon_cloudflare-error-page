# SPDX-License-Identifier: MIT

import os

from flask import (
    Blueprint,
    send_from_directory,
)

root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../')
res_folder = os.path.join(root_dir, 'editor/resources')

bp = Blueprint('editor', __name__, url_prefix='/')


@bp.route('/', defaults={'path': 'index.html'})
@bp.route('/<path:path>')
def index(path: str):
    return send_from_directory(res_folder, path)
