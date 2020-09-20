from flask import url_for


def test_can_log_in_returns_200(testapp, user):
    """Login successful."""
    res = testapp.get(url_for("public.login"))
    form = res.form
    form["email"] = user.email
    form["password"] = "myprecious"
    res = form.submit().follow()
    assert res.status_code == 200


def test_can_log_with_different_email_case_in_returns_200(db, testapp, user_factory):
    user_factory(email="myemail@gmail.com")
    res = testapp.get(url_for("public.login"))
    form = res.form
    form["email"] = "MyEmail@Gmail.com"
    form["password"] = "myprecious"
    res = form.submit().follow()
    assert res.status_code == 200


def test_sees_alert_on_log_out(testapp, user):
    """Show alert on logout."""
    res = testapp.get(url_for("public.login"))
    form = res.form
    form["email"] = user.email
    form["password"] = "myprecious"
    res = form.submit().follow()
    res = testapp.get(url_for("public.logout")).follow()
    assert "You are logged out." in res


def test_sees_error_message_if_password_is_incorrect(testapp, user):
    """Show error if password is incorrect."""
    res = testapp.get(url_for("public.login"))
    form = res.form
    form["email"] = user.email
    form["password"] = "wrong"
    res = form.submit()
    assert "Invalid email or password" in res


def test_sees_error_message_if_username_doesnt_exist(testapp, user):
    """Show error if username doesn't exist."""
    res = testapp.get(url_for("public.login"))
    form = res.form
    form["email"] = "unknown@gmail.com"
    form["password"] = "myprecious"
    res = form.submit()
    assert "Invalid email or password" in res
