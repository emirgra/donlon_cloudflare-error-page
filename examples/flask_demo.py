#!/usr/bin/env python3

import os
import re
import sys

from flask import (
    Flask,
    request,
    send_from_directory
)

# Append this directory to sys.path is not required if the package is already installed
examples_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(examples_dir))

from cloudflare_error_page import render as render_cf_error_page

app = Flask(__name__)


@app.route('/')
def index():
    params = {
        "title": "Internal server error",
        "error_code": 500,
        "browser_status": {
            "status": "ok"
        },
        "cloudflare_status": {
            "status": "error",
            "status_text": "Error"
        },
        "host_status": {
            "status": "ok",
            "location": "example.com"
        },
        "error_source": "cloudflare",
        "what_happened": "<p>There is an internal server error on Cloudflare\"s network.</p>",
        "what_can_i_do": "<p>Please try again in a few minutes.</p>"
    }

    # Get the real Ray ID from Cloudflare header
    ray_id = request.headers.get('Cf-Ray', '')[:16]

    # Get the real client ip from Cloudflare header or request.remote_addr
    client_ip = request.headers.get('X-Forwarded-For')
    if not client_ip:
        client_ip = request.remote_addr

    params.update({
        'ray_id': ray_id,
        'client_ip': client_ip,
    })

    # Render the error page
    return render_cf_error_page(params), 500


if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else None
    port = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    app.run(debug=True, host=host, port=port)
