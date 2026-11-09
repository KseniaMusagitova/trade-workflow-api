from fastapi.testclient import TestClient
from app.main import app, Base, engine

client = TestClient(app)

def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_create_list_report_delete():
    payload = {'symbol': 'aapl', 'side': 'BUY', 'quantity': 3, 'price': '12.50'}
    created = client.post('/trades', json=payload)
    assert created.status_code == 201, created.text
    trade_id = created.json()['id']
    assert created.json()['symbol'] == 'AAPL'
    assert len(client.get('/trades?symbol=AAPL').json()) == 1
    report = client.get('/reports/notional-by-symbol').json()
    assert report[0]['trade_count'] == 1
    assert float(report[0]['total_notional']) == 37.5
    assert client.delete(f'/trades/{trade_id}').status_code == 204
    assert client.get(f'/trades/{trade_id}').status_code == 404

def test_reject_invalid_trade():
    assert client.post('/trades', json={'symbol':'AAPL','side':'BUY','quantity':0,'price':'10'}).status_code == 422

def test_count_trades():
    response = client.get("trades/count")
    assert response.status_code == 200
    assert response.json() == {"count": 0}
