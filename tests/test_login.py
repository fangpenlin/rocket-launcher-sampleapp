# -*- coding: utf-8 -*-
from flask import url_for

from .factories import UserFactory


class TestLoggingIn:
    """Login."""

    def test_can_log_in_returns_200(self, testapp, user_factory):
        """Login successful."""
        user = user_factory(init_password="myprecious")
        # Goes to homepage
        res = testapp.get(url_for("public.login"))
        # Fills out login form in navbar
        form = res.form
        form["email"] = user.email
        form["password"] = "myprecious"
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200

    def test_can_log_with_different_email_case_in_returns_200(
        self, db, testapp, user_factory
    ):
        user = user_factory(email="myemail@gmail.com", init_password="myprecious")

        # Goes to homepage
        res = testapp.get(url_for("public.login"))
        # Fills out login form in navbar
        form = res.form
        form["email"] = "MyEmail@Gmail.com"
        form["password"] = "myprecious"
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200

    def test_sees_alert_on_log_out(self, testapp, user_factory):
        """Show alert on logout."""
        user = user_factory(init_password="myprecious")
        res = testapp.get(url_for("public.login"))
        # Fills out login form in navbar
        form = res.form
        form["email"] = user.email
        form["password"] = "myprecious"
        # Submits
        res = form.submit().follow()
        res = testapp.get(url_for("public.logout")).follow()
        # sees alert
        assert "You are logged out." in res

    def test_sees_error_message_if_password_is_incorrect(self, testapp, user_factory):
        """Show error if password is incorrect."""
        user = user_factory(init_password="myprecious")
        # Goes to homepage
        res = testapp.get(url_for("public.login"))
        # Fills out login form, password incorrect
        form = res.form
        form["email"] = user.email
        form["password"] = "wrong"
        # Submits
        res = form.submit()
        # sees error
        assert "Invalid password" in res

    def test_sees_error_message_if_username_doesnt_exist(self, testapp, user):
        """Show error if username doesn't exist."""
        # Goes to homepage
        res = testapp.get(url_for("public.login"))
        # Fills out login form, password incorrect
        form = res.forms["login-form"]
        form["email"] = "unknown@gmail.com"
        form["password"] = "myprecious"
        # Submits
        res = form.submit()
        # sees error
        assert "Unknown email" in res
