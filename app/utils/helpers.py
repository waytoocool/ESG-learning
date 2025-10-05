import os
from flask import url_for, request, current_app

def dated_url_for(endpoint, **values):
    """
    Add version number to static files based on modification time.
    
    This helps in cache busting for static files by appending a timestamp
    to the URL when the file changes.
    """
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(current_app.static_folder, filename)
            if os.path.isfile(file_path):
                values['v'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

def init_url_versioning(app):
    """
    Initialize URL versioning for static files.
    
    This function should be called in the app factory to set up 
    the context processor for URL versioning.
    """
    @app.context_processor
    def override_url_for():
        return dict(url_for=dated_url_for)


def init_caching(app):
    """
    Initialize caching headers for the application.
    
    This function sets up caching headers to ensure proper 
    caching behavior for static and dynamic content.
    """
    @app.after_request
    def add_header(response):
        """
        Add caching headers to responses.
        
        - Static files are cached for 1 year
        - Other responses are not cached
        """
        if 'static' in request.path:
            # Cache static files for 1 year
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        else:
            # Don't cache other responses
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '-1'
        return response

def _compute_cookie_domain(hostname: str) -> str | None:
    """Compute a suitable ``SESSION_COOKIE_DOMAIN`` based on the request host.

    The goal is to allow *cross-subdomain* sessions while still keeping
    the domain as specific as possible.  It supports:

    • localhost / bare IP addresses          → ``None`` (no sharing)
    • nip.io development domains             → ``.127-0-0-1.nip.io``
    • ngrok free domains (id.ngrok-free.app) → ``.<id>.ngrok-free.app``
    • generic multi-level domains            → ``.<root-domain>`` (drops only
                                               the most specific label)

    Args:
        hostname: Host portion of the request (without port).
    Returns:
        A domain string suitable for Flask's ``SESSION_COOKIE_DOMAIN`` (leading
        dot for sub-domain sharing) or ``None`` to keep the default host-only
        cookie behaviour.
    """
    import re

    # 1. Plain localhost or raw IP → keep host-only cookies
    if hostname in {"localhost", "127.0.0.1"} or re.match(r"^\d+\.\d+\.\d+\.\d+$", hostname):
        return None

    # 2. nip.io domains (e.g. tenant.127-0-0-1.nip.io or 127-0-0-1.nip.io)
    if hostname.endswith(".nip.io"):
        parts = hostname.split(".")
        # Get last 3 labels: 127-0-0-1.nip.io
        if len(parts) >= 3:
            return "." + ".".join(parts[-3:])
        return None

    # 3. ngrok domains (e.g. <id>.ngrok-free.app or <id>.ngrok.app)
    if ".ngrok" in hostname:
        parts = hostname.split(".")
        if len(parts) >= 3:
            return "." + ".".join(parts[-3:])  # keep the <id>.ngrok-free.app part
        return "." + hostname

    # 4. Generic: drop the most specific label (tenant) and keep the rest
    parts = hostname.split(".")
    if len(parts) >= 3:
        return "." + ".".join(parts[1:])

    # Fallback – keep host-only
    return None


def init_dynamic_session_cookie_domain(app):
    """Dynamically set ``SESSION_COOKIE_DOMAIN`` on each request.

    If ``SESSION_COOKIE_DOMAIN`` is *already* set via config or environment
    variable, this function leaves it untouched.  Otherwise, it derives a
    domain from the current request host using :pyfunc:`_compute_cookie_domain`.
    This lets you run the same codebase locally (localhost / nip.io), via
    ngrok, and in production with a real domain without manual changes.
    """

    @app.before_request
    def _set_cookie_domain():
        # Respect explicit configuration (e.g. in production environment
        # variables or config file).
        if app.config.get("SESSION_COOKIE_DOMAIN") is not None:
            return

        host = request.host.split(":")[0]
        derived_domain = _compute_cookie_domain(host)
        app.config["SESSION_COOKIE_DOMAIN"] = derived_domain