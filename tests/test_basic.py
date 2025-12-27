def test_homepage(client):
    res = client.get("/")
    assert res.status_code == 200
