def test_admin_protected(client):
    res = client.get("/admin/", follow_redirects=True)
    assert res.status_code in (302, 401, 403)
