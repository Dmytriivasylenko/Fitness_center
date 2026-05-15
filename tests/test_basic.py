

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert b"ok" in res.data


def test_login_page_loads(client):
    res = client.get("/login")
    assert res.status_code == 200


def test_register_page_loads(client):
    res = client.get("/register")
    assert res.status_code == 200