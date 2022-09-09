def test_register_app(test_client):
    response = test_client.post("/service/app")
    assert response.status_code == 200