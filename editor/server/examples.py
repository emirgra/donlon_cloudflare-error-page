# SPDX-License-Identifier: MIT

import os
import re

from flask import (
    Blueprint,
    json,
    abort,
    redirect,
)

from . import get_common_cf_template_params
from cloudflare_error_page import render as render_cf_error_page

root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../')
examples_dir = os.path.join(root_dir, 'examples')

bp = Blueprint('examples', __name__, url_prefix='/')


param_cache: dict[str, dict] = {}

def get_page_params(name: str) -> dict:
    name = re.sub(r'[^\w]', '', name)
    params = param_cache.get(name)
    if params is not None:
        return params
    try:
        with open(os.path.join(examples_dir, f'{name}.json')) as f:
            params = json.load(f)
        param_cache[name] = params
        return params
    except Exception as _:
        return None


@bp.route('/', defaults={'name': 'default'})
@bp.route('/<path:name>')
def index(name: str):
    name = os.path.basename(name)  # keep only the base name
    lower_name = name.lower()
    print(lower_name, name)
    if name != lower_name:
        return redirect(lower_name)
    else:
        name = lower_name

    params = get_page_params(name)
    if params is None:
        abort(404)

    params = {
        **params,
        **get_common_cf_template_params(),
    }

    # Render the error page
    return render_cf_error_page(params, use_cdn=True), 500
