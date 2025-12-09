import html
import os
import secrets
from datetime import datetime, timezone

from jinja2 import Environment, PackageLoader, Template, select_autoescape

env = Environment(
    loader=PackageLoader("cloudflare_error_page"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)

default_template = env.get_template("error.html")


def fill_params(params: dict):
    if not params.get('time'):
        utc_now = datetime.now(timezone.utc)
        params['time'] = utc_now.strftime("%Y-%m-%d %H:%M:%S UTC")
    if not params.get('ray_id'):
        params['ray_id'] = secrets.token_hex(8)


def render(params: dict, allow_html: bool=True) -> str:
    """
    Render a customized Cloudflare error page.
    """
    params = {**params}
    fill_params(params)
    if not allow_html:
        params['what_happened'] = html.escape(params.get('what_happened', ''))
        params['what_can_i_do'] = html.escape(params.get('what_can_i_do', ''))

    return default_template.render(params=params)
