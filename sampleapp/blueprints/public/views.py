from flask import abort
from flask import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import session
from flask import url_for
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from flask_principal import AnonymousIdentity
from flask_principal import Identity
from flask_principal import identity_changed

from ...extensions import db
from ...models.accounts import User
from ...utils import is_safe_url
from .forms import ForgotPasswordForm
from .forms import LoginForm
from .forms import RegisterForm
from .forms import ResetPasswordForm

blueprint = Blueprint("public", __name__, static_folder="../../static")


@blueprint.route("/", methods=["GET"])
def home():
    """Home page."""
    return render_template("public/home.html")


@blueprint.route("/terms-of-service")
def terms():
    """TOS page."""
    return render_template("public/terms.html")


@blueprint.route("/logout")
@login_required
def logout():
    """Logout."""
    logout_user()
    # Remove session keys set by Flask-Principal
    for key in ("identity.name", "identity.auth_type"):
        session.pop(key, None)
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    next_url = request.args.get("next")
    if form.validate_on_submit():
        remember = request.form.get("remember", "0") == "1"
        login_user(form.user, remember=remember)
        identity_changed.send(
            current_app._get_current_object(), identity=Identity(form.user.id)
        )
        if not is_safe_url(next_url):
            return abort(400)
        flash("You are logged in.", "success")
        redirect_url = next_url or url_for("public.home")
        return redirect(redirect_url)
    return render_template("public/login.html", form=form, next_url=next_url)


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    next_url = request.args.get("next")
    if form.validate_on_submit():
        user = User(email=form.email.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        if not is_safe_url(next_url):
            return abort(400)
        flash("Thank you for registering.", "success")
        redirect_url = next_url or url_for("public.home")
        return redirect(redirect_url)
    return render_template("public/register.html", form=form, next_url=next_url,)


@blueprint.route("/forgot-password/", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        pass
    return render_template("public/forgot_password.html", form=form)


@blueprint.route("/reset-password/", methods=["GET", "POST"])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        pass
    return render_template("public/reset_password.html", form=form)


@blueprint.route("/__raise_error__/")
def raise_error():
    # for testing bugsnag
    raise RuntimeError("failed")


@blueprint.route("/robots.txt")
def static_from_root():
    return send_from_directory(current_app.static_folder, request.path[1:])
