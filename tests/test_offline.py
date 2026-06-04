"""Offline tests — exercise everything that needs no live PAW server:
URL building, OData query construction, path encoding, and config validation.

Run with:  uv run pytest   (or:  python -m pytest)
"""

import pytest

from PAWpy import PAWService, PAWConfigException
from PAWpy.Services.RestService import RestService
from PAWpy.Utils.Utils import odata_query, encode_path_twice, odata_value_list


def make_paw():
    # connect=False skips authentication so no network call is made.
    return PAWService(
        host="paw.test.local",
        auth_mode="session",
        csrf_token="dummy",
        connect=False,
    )


# --------------------------- base url ------------------------------------ #
def test_base_url_https_default():
    rest = RestService(host="paw.test.local", auth_mode="session",
                       csrf_token="x", connect=False)
    assert rest.base_url == "https://paw.test.local"


def test_base_url_with_port_and_tenant_and_http():
    rest = RestService(host="host", port=9510, ssl=False,
                       auth_mode="session", csrf_token="x",
                       tenant_id="tenant-123", connect=False)
    assert rest.base_url == "http://host:9510/tenant-123"


# --------------------------- UI url builders ----------------------------- #
def test_book_url():
    paw = make_paw()
    url = paw.ui.book_url("/shared/myBook", embed=True)
    assert url.startswith("https://paw.test.local/ui?")
    assert "type=book" in url
    assert "embed=true" in url
    # path is URL-encoded
    assert "%2Fshared%2FmyBook" in url


def test_cube_viewer_by_server_cube_view():
    paw = make_paw()
    url = paw.ui.cube_viewer_url("Planning Sample", "plan_BudgetPlan", view="Budget Input")
    assert "type=cube-viewer" in url
    assert "cube=plan_BudgetPlan" in url
    assert "view=Budget%20Input" in url


def test_cube_viewer_requires_path_or_cube():
    paw = make_paw()
    with pytest.raises(ValueError):
        paw.ui.cube_viewer_url(server="Planning Sample")


def test_dimension_editor_omits_none():
    paw = make_paw()
    url = paw.ui.dimension_editor_url("Planning Sample", "plan_business_unit")
    assert "hierarchy=" not in url  # None dropped
    assert "dimension=plan_business_unit" in url


def test_websheet_url():
    paw = make_paw()
    url = paw.ui.websheet_url("App/Report", tm1_server="Planning Sample", admin_host="localhost")
    assert "type=websheet" in url and "Action=Open" in url


# --------------------------- OData helpers ------------------------------- #
def test_odata_query_only_includes_supplied():
    q = odata_query(filter="name eq 'x'", top=10)
    assert q == {"$filter": "name eq 'x'", "$top": 10}


def test_encode_path_twice():
    # space -> %20 -> %2520
    assert encode_path_twice("/a b") == "%252Fa%2520b"


def test_odata_value_list_handles_both_shapes():
    assert odata_value_list({"value": [1, 2]}) == [1, 2]
    assert odata_value_list([1, 2]) == [1, 2]
    assert odata_value_list({"other": 1}) == []


# --------------------------- TM1 proxy paths ----------------------------- #
def test_tm1_proxy_path():
    paw = make_paw()
    tm1 = paw.tm1("Global FPA")
    # exercise the private path builder via build_url for assertion
    full = paw.rest.build_url(tm1._path("Cubes"))
    assert full == "https://paw.test.local/api/v0/tm1/Global FPA/api/v1/Cubes"


def test_tm1_requires_database():
    paw = make_paw()
    with pytest.raises(ValueError):
        paw.tm1()  # no default database set


# --------------------------- config validation --------------------------- #
def test_bad_auth_mode_raises():
    with pytest.raises(PAWConfigException):
        RestService(host="h", auth_mode="banana", connect=False)


def test_oauth_requires_token_url():
    with pytest.raises(PAWConfigException):
        RestService(host="h", auth_mode="oauth", client_id="a",
                   client_secret="b", connect=True)
