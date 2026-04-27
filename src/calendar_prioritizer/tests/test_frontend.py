from __future__ import annotations


def test_frontend_root_serves_dashboard(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Calendar Priority" in response.text
    assert "/static/app.js" in response.text


def test_frontend_static_asset_serves_javascript(client) -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "const API_BASE" in response.text


def test_frontend_styles_hide_collapsed_event_lists(client) -> None:
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert ".event-list[hidden]" in response.text
    assert "display: none" in response.text


def test_frontend_styles_hide_collapsed_event_subsections(client) -> None:
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert ".event-subsection-body[hidden]" in response.text
    assert "display: none" in response.text
