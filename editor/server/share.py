# SPDX-License-Identifier: MIT

import random
import string

from flask import (
    Blueprint,
    request,
    abort,
    jsonify,
    url_for,
)

from . import get_common_cf_template_params, render_cf_error_page
from . import db
from . import limiter
from . import models

# root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../')
# examples_dir = os.path.join(root_dir, 'examples')

bp = Blueprint('share', __name__, url_prefix='/')


rand_charset = string.ascii_lowercase + string.digits 

def get_rand_name(digits=8):
    return ''.join(random.choice(rand_charset) for _ in range(digits))


@bp.post('/create')
@limiter.limit("20 per minute")
@limiter.limit("500 per hour")
def create():
    if len(request.data) > 4096:
        abort(413)
    params = request.json['parameters']  # throws KeyError
    # TODO: strip unused params
    try:
        item = models.Item()
        item.name = get_rand_name()
        item.params = params
        db.session.add(item)
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({
            'status': 'failed',
        })
    return jsonify({
        'status': 'ok',
        'name': item.name,
        'url': request.host_url[:-1] + url_for('share.get', name=item.name),
        # TODO: better way to handle this
    })


@bp.get('/<name>')
def get(name: str):
    accept = request.headers.get('Accept', '')
    is_json = 'application/json' in accept

    item = db.session.query(models.Item).filter_by(name=name).first()
    if not item:
        if is_json:
            return jsonify({
                'status': 'not-found'
            })
        else:
            return abort(404)
    params = item.params
    params = {
        **params,
        **get_common_cf_template_params(),
    }
    params.pop('time')
    params.pop('ray_id')
    params.pop('client_ip')
    params['creator_info'] = {
        'hidden': False,
        'text': 'CF Error Page Editor',
        'link': f'https://virt.moe/cloudflare-error-page/editor/?from={name}',
    }
    
    if is_json:
        return jsonify({
            'status': 'ok',
            'parameters': params,
        })
    else:
        return render_cf_error_page(params=params, allow_html=False, use_cdn=True), 200
