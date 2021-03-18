from src.event_processor.main import hello


def test_hello():
    assert hello() == "Hello world"
