from cli.tmpl import Store

def test_basic_list():
    s = Store()
    rows = s.list(limit=5)
    assert isinstance(rows, list)
