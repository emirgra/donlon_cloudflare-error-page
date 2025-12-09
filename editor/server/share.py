# SPDX-License-Identifier: MIT

import html
import random
import string

from flask import (
    Blueprint,
    request,
    abort,
    jsonify,
    url_for,
)
from jinja2 import Environment, select_autoescape

from cloudflare_error_page import (
    fill_params as fill_template_params,
    default_template as cf_template
)

from . import (
    db,
    limiter,
    models
)

from .utils import fill_cf_template_params, sanitize_page_param_links

# root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../')
# examples_dir = os.path.join(root_dir, 'examples')
env = Environment(
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)
template = env.from_string('''
{% extends base %}

{% block header %}
<meta property="og:type" content="website" />
<meta property="og:site_name" content="moe::virt" />
<meta property="og:title" content="{{ html_title }}" />
<meta property="og:url" content="{{ url }}" />
<meta property="og:description" content="{{ description }}" />

<meta property="twitter:card" content="summary" />
<meta property="twitter:site" content="moe::virt" />
<meta property="twitter:title" content="{{ html_title }}" />
<meta property="twitter:description" content="{{ description }}" />
{% endblock %}
''')

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
                'status': 'notfound'
            })
        else:
            return abort(404)
    params: dict = item.params
    params.pop('time', None)
    params.pop('ray_id', None)
    params.pop('client_ip', None)
    
    if is_json:
        return jsonify({
            'status': 'ok',
            'parameters': params,
        })
    else:
        params['creator_info'] = {
            'hidden': False,
            'text': 'CF Error Page Editor',
            'link': request.host_url[:-1] + url_for('editor.index') + f'#from={name}',
        }
        # Always escape HTML
        params['what_happened'] = html.escape(params.get('what_happened', '')) # TODO: common render function?
        params['what_can_i_do'] = html.escape(params.get('what_can_i_do', ''))
        fill_cf_template_params(params)
        fill_template_params(params)
        sanitize_page_param_links(params)

        return template.render(base=cf_template,
                               params=params,
                               url=request.url,
                               description='Cloudflare error page')
