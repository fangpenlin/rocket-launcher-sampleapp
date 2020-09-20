import pytest
from flask import url_for

ADMIN_ENDPOINTS = [
    "admin.index",
    "admin.user.index_view",
]


@pytest.fixture(params=ADMIN_ENDPOINTS)
def endpoint(request):
    return request.param


def test_endpoints_without_user(endpoint, testapp, user):
    testapp.get(url_for(endpoint), status=302)


def test_endpoints_with_not_admin_user(endpoint, testapp, user):
    with testapp.session_transaction() as session:
        session["user_id"] = user.id
    testapp.get(url_for(endpoint), status=302)


def test_endpoints_with_admin_user(endpoint, testapp, admin_user):
    assert admin_user.is_admin
    with testapp.session_transaction() as session:
        session["user_id"] = admin_user.id
    testapp.get(url_for(endpoint), status=200)
