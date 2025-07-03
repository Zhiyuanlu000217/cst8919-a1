"""Python Flask WebApp Auth0 integration example with enhanced logging
"""

import json
import logging
from datetime import datetime
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

# Configure basic logging
logging.basicConfig(level=logging.INFO)

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


def get_user_info_from_session():
    """Extract user information from session"""
    user = session.get("user", {})
    userinfo = user.get("userinfo", {})
    return {
        "user_id": userinfo.get("sub"),
        "email": userinfo.get("email"),
        "name": userinfo.get("name")
    }


# Controllers API
@app.route("/")
def home():
    app.logger.info('Home page accessed')
    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    try:
        token = oauth.auth0.authorize_access_token()
        # Fetch user info from Auth0 userinfo endpoint
        userinfo = oauth.auth0.userinfo()
        session["user"] = {"userinfo": {
            "sub": userinfo.get("sub"),
            "email": userinfo.get("email"),
            "name": userinfo.get("name")
        }}
        
        # Extract user information for logging
        user_info = get_user_info_from_session()
        timestamp = datetime.now().isoformat()
        
        # Log successful login with required information
        app.logger.info(f'Successful login for user: {user_info["email"]} - user_id: {user_info["user_id"]}, timestamp: {timestamp}')
        
        return redirect("/")
    except Exception as e:
        app.logger.warning(f'Failed login attempt: {str(e)}')
        return redirect("/")


@app.route("/login")
def login():
    app.logger.info('Login page accessed')
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/logout")
def logout():
    # Log logout if user was logged in
    if session.get("user"):
        user_info = get_user_info_from_session()
        timestamp = datetime.now().isoformat()
        app.logger.info(f'User logout: {user_info["email"]} - user_id: {user_info["user_id"]}, timestamp: {timestamp}')
    
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@app.route("/protected")
def protected():
    if not session.get("user"):
        # Log unauthorized access attempt
        timestamp = datetime.now().isoformat()
        app.logger.warning(f'Unauthorized access attempt to /protected - timestamp: {timestamp}')
        return redirect("/login")
    
    # Log successful access to protected route
    user_info = get_user_info_from_session()
    timestamp = datetime.now().isoformat()
    app.logger.info(f'Protected route accessed by user: {user_info["email"]} - user_id: {user_info["user_id"]}, timestamp: {timestamp}')
    
    return render_template(
        "protected.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000)) 