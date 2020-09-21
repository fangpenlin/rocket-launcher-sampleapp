import datetime
import re

import jwt
from flask import url_for
from freezegun import freeze_time

from sampleapp.extensions import mail


def test_can_log_in_returns_200(testapp, user, default_password):
    res = testapp.get(url_for("public.login"))
    form = res.form
    form["email"] = user.email
    form["password"] = default_password
    res = form.submit().follow()
    assert res.status_code == 200


def test_can_login_with_different_email_case_in_returns_200(
    db, testapp, user_factory, default_password
):
    user_factory(email="myemail@gmail.com")
    res = testapp.get(url_for("public.login"))
    form = res.form
    form["email"] = "MyEmail@Gmail.com"
    form["password"] = default_password
    res = form.submit().follow()
    assert res.status_code == 200


def test_sees_alert_on_logout(testapp, user, default_password):
    res = testapp.get(url_for("public.login"))
    form = res.form
    form["email"] = user.email
    form["password"] = default_password
    res = form.submit().follow()
    res = testapp.get(url_for("public.logout")).follow()
    assert "You are logged out." in res


def test_sees_error_message_if_password_is_incorrect(testapp, user, default_password):
    res = testapp.get(url_for("public.login"))
    form = res.form
    form["email"] = user.email
    form["password"] = default_password + "1"
    res = form.submit()
    assert "Invalid email or password" in res


def test_sees_error_message_if_username_doesnt_exist(testapp, user, default_password):
    res = testapp.get(url_for("public.login"))
    form = res.form
    form["email"] = "unknown@gmail.com"
    form["password"] = default_password
    res = form.submit()
    assert "Invalid email or password" in res


def test_forgot_password(testapp, user):
    testapp.app.config["FORGOT_PASSWORD_COOLDOWN_TIME_SECONDS"] = 60 * 10
    testapp.app.config["RESET_PASSWORD_LINK_VALID_SECONDS"] = 123

    res = testapp.get(url_for("public.forgot_password"))
    form = res.form
    form["email"] = user.email
    with mail.record_messages() as outbox:
        res = form.submit()
        assert len(outbox) == 1
        match = re.search("reset-password\?token=([0-9a-zA-Z.\-_]+)", outbox[0].body)
        raw_token = match.group(1)
        token = jwt.decode(
            raw_token, key=testapp.app.config["SECRET_KEY"], algorithms=["HS256"],
        )
        user_id = token["user_id"]
        expires_at = datetime.datetime.utcfromtimestamp(token["expires_at"])
        assert user_id == str(user.id)
        assert user.sent_reset_password_at is not None
        assert expires_at == user.sent_reset_password_at + datetime.timedelta(
            seconds=testapp.app.config["RESET_PASSWORD_LINK_VALID_SECONDS"]
        )
    assert "Please check your mailbox for reset password email" in res


def test_forgot_password_cooldown_period(testapp, db, user):
    testapp.app.config["FORGOT_PASSWORD_COOLDOWN_TIME_SECONDS"] = 60 * 10
    testapp.app.config["RESET_PASSWORD_LINK_VALID_SECONDS"] = 123

    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    with freeze_time(now):
        user.sent_reset_password_at = now
        db.session.add(user)
        db.session.commit()

    res = testapp.get(url_for("public.forgot_password"))
    form = res.form
    form["email"] = user.email
    with freeze_time(now + datetime.timedelta(seconds=(60 * 10) - 1)):
        res = form.submit().follow()
    assert "We just sent a reset password email to you, please try again later" in res

    with freeze_time(
        now + datetime.timedelta(seconds=60 * 10)
    ), mail.record_messages() as outbox:
        form.submit()
        assert len(outbox) == 1
