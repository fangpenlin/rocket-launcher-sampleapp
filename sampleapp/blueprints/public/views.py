import datetime

import jwt
from flask import abort
from flask import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import url_for
from flask_login import login_required
from flask_mail import Message

from ...extensions import db
from ...extensions import mail
from ...models.accounts import User
from ...utils import is_safe_url
from ...utils import login_user
from ...utils import logout_user
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
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    next_url = request.args.get("next")
    if form.validate_on_submit():
        remember = request.form.get("remember", "0") == "1"
        login_user(form.user, remember=remember)
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


@blueprint.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).with_for_update().first()
        if user is not None:
            now = datetime.datetime.utcnow()
            cooldown_time = current_app.config["FORGOT_PASSWORD_COOLDOWN_TIME_SECONDS"]
            if cooldown_time > 0 and user.sent_reset_password_at is not None:
                elapsed = now - user.sent_reset_password_at
                if elapsed.total_seconds() < cooldown_time:
                    flash(
                        "We just sent a reset password email to you, please try again later",
                        "danger",
                    )
                    return redirect(url_for("public.forgot_password"))
            valid_period = current_app.config["RESET_PASSWORD_LINK_VALID_SECONDS"]
            token = jwt.encode(
                dict(
                    user_id=str(user.id),
                    expires_at=(
                        now + datetime.timedelta(seconds=valid_period)
                    ).timestamp(),
                ),
                key=current_app.config["SECRET_KEY"],
                algorithm="HS256",
            )
            reset_link = url_for("public.reset_password", token=token, _external=True)
            msg = Message(
                f"{current_app.config['SITE_NAME']} - Reset your password",
                sender=current_app.config["MAIL_DEFAULT_SENDER"],
                recipients=[user.email],
            )
            msg.body = f"To reset your password, please visit {reset_link}"
            # TODO: render email template here
            msg.html = f'To reset your password, please click this <a href="{reset_link}">link</a>'
            mail.send(msg)
            user.sent_reset_password_at = now
            flash("Please check your mailbox for reset password email.", "success")
            db.session.add(user)
            db.session.commit()
    return render_template("public/forgot_password.html", form=form)


@blueprint.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        pass
    return render_template("public/reset_password.html", form=form)


@blueprint.route("/__raise_error__")
def raise_error():
    # for testing bugsnag
    raise RuntimeError("failed")


@blueprint.route("/robots.txt")
def static_from_root():
    return send_from_directory(current_app.static_folder, request.path[1:])
