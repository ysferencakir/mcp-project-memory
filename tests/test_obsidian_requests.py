from datetime import date
from itertools import islice
from unittest.mock import MagicMock, patch

import pytest
import requests

from mcp_obsidian.obsidian import (
    Obsidian,
    ObsidianApiError,
    _periodic_candidate_dates,
)


def _make_obsidian():
    return Obsidian(api_key="test-key", protocol="http", host="localhost", port=27123)


def _json_response(payload):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    return resp


def _text_response(text):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.text = text
    return resp


def _http_error_response(content=b'{"errorCode": 40149, "message": "bad key"}'):
    resp = requests.Response()
    resp.status_code = 401
    resp._content = content
    return resp


def test_constructor_defaults_to_https_for_unknown_protocol():
    api = Obsidian(api_key="key", protocol="ftp", host="host", port=1)
    assert api.get_base_url() == "https://host:1"


def test_constructor_allows_http_protocol():
    api = _make_obsidian()
    assert api.get_base_url() == "http://localhost:27123"


def test_get_headers_uses_bearer_token():
    assert _make_obsidian()._get_headers() == {"Authorization": "Bearer test-key"}


def test_safe_call_formats_http_error_json_body():
    api = _make_obsidian()
    error = requests.HTTPError(response=_http_error_response())

    with pytest.raises(Exception, match="Error 40149: bad key"):
        api._safe_call(MagicMock(side_effect=error))


def test_safe_call_preserves_http_status_and_plugin_error_code():
    api = _make_obsidian()
    error = requests.HTTPError(response=_http_error_response())

    with pytest.raises(ObsidianApiError) as excinfo:
        api._safe_call(MagicMock(side_effect=error))

    assert excinfo.value.status_code == 401
    assert excinfo.value.error_code == 40149
    assert excinfo.value.message == "bad key"


def test_safe_call_handles_http_error_empty_body():
    api = _make_obsidian()
    error = requests.HTTPError(response=_http_error_response(b""))

    with pytest.raises(Exception, match="Error -1: <unknown>"):
        api._safe_call(MagicMock(side_effect=error))


def test_safe_call_handles_http_error_non_json_body():
    api = _make_obsidian()
    error = requests.HTTPError(response=_http_error_response(b"not json"))

    with pytest.raises(Exception, match="Error -1: <unknown>"):
        api._safe_call(MagicMock(side_effect=error))


def test_safe_call_handles_http_error_without_response():
    api = _make_obsidian()
    error = requests.HTTPError("no response")

    with pytest.raises(Exception, match="Error -1: <unknown>"):
        api._safe_call(MagicMock(side_effect=error))


def test_safe_call_wraps_request_exception():
    api = _make_obsidian()

    with pytest.raises(Exception, match="Request failed: boom"):
        api._safe_call(MagicMock(side_effect=requests.exceptions.Timeout("boom")))


def test_list_files_in_vault_hits_root_vault_endpoint():
    api = _make_obsidian()
    with patch("mcp_obsidian.obsidian.requests.get", return_value=_json_response({"files": ["a.md"]})) as mock_get:
        assert api.list_files_in_vault() == ["a.md"]

    mock_get.assert_called_once()
    assert mock_get.call_args.args[0] == "http://localhost:27123/vault/"
    assert mock_get.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert mock_get.call_args.kwargs["verify"] is False
    assert mock_get.call_args.kwargs["timeout"] == (3, 6)


def test_list_files_in_dir_hits_directory_endpoint():
    api = _make_obsidian()
    with patch("mcp_obsidian.obsidian.requests.get", return_value=_json_response({"files": ["b.md"]})) as mock_get:
        assert api.list_files_in_dir("notes") == ["b.md"]

    assert mock_get.call_args.args[0] == "http://localhost:27123/vault/notes/"


def test_get_file_contents_returns_text():
    api = _make_obsidian()
    with patch("mcp_obsidian.obsidian.requests.get", return_value=_text_response("# Title")) as mock_get:
        assert api.get_file_contents("notes/a.md") == "# Title"

    assert mock_get.call_args.args[0] == "http://localhost:27123/vault/notes/a.md"


def test_search_posts_simple_query_params():
    api = _make_obsidian()
    payload = [{"filename": "a.md"}]
    with patch("mcp_obsidian.obsidian.requests.post", return_value=_json_response(payload)) as mock_post:
        assert api.search("needle", context_length=42) == payload

    assert mock_post.call_args.args[0] == "http://localhost:27123/search/simple/"
    assert mock_post.call_args.kwargs["params"] == {"query": "needle", "contextLength": 42}


def test_delete_file_uses_delete_method():
    api = _make_obsidian()
    with patch("mcp_obsidian.obsidian.requests.delete", return_value=_json_response({})) as mock_delete:
        assert api.delete_file("notes/a.md") is None

    assert mock_delete.call_args.args[0] == "http://localhost:27123/vault/notes/a.md"


def test_search_json_posts_jsonlogic_payload():
    api = _make_obsidian()
    query = {"glob": ["*.md", {"var": "path"}]}
    payload = [{"filename": "a.md", "result": True}]
    with patch("mcp_obsidian.obsidian.requests.post", return_value=_json_response(payload)) as mock_post:
        assert api.search_json(query) == payload

    kwargs = mock_post.call_args.kwargs
    assert mock_post.call_args.args[0] == "http://localhost:27123/search/"
    assert kwargs["json"] == query
    assert kwargs["headers"]["Content-Type"] == "application/vnd.olrapi.jsonlogic+json"


def test_get_periodic_note_content_uses_plain_accept_headers():
    api = _make_obsidian()
    with patch("mcp_obsidian.obsidian.requests.get", return_value=_text_response("daily text")) as mock_get:
        assert api.get_periodic_note("daily") == "daily text"

    assert mock_get.call_args.args[0] == "http://localhost:27123/periodic/daily/"
    assert "Accept" not in mock_get.call_args.kwargs["headers"]


def test_get_periodic_note_metadata_sets_note_json_accept_header():
    api = _make_obsidian()
    with patch("mcp_obsidian.obsidian.requests.get", return_value=_text_response('{"path":"daily.md"}')) as mock_get:
        assert api.get_periodic_note("daily", type="metadata") == '{"path":"daily.md"}'

    assert mock_get.call_args.kwargs["headers"]["Accept"] == "application/vnd.olrapi.note+json"


def test_get_recent_periodic_notes_sends_query_params():
    api = _make_obsidian()
    payload = {
        "path": "daily.md",
        "content": "daily text",
        "tags": [],
        "frontmatter": {},
    }
    with patch("mcp_obsidian.obsidian.requests.get", return_value=_json_response(payload)) as mock_get:
        assert api.get_recent_periodic_notes("daily", limit=1) == [
            {"path": "daily.md", "tags": [], "frontmatter": {}}
        ]

    today = date.today()
    assert mock_get.call_args.args[0] == (
        f"http://localhost:27123/periodic/daily/"
        f"{today.year}/{today.month}/{today.day}/"
    )
    assert mock_get.call_args.kwargs["headers"]["Accept"] == (
        "application/vnd.olrapi.note+json"
    )


def test_get_recent_periodic_notes_skips_missing_and_invalid_notes():
    api = _make_obsidian()
    missing = _http_error_response(
        b'{"errorCode": 40461, "message": "periodic note missing"}'
    )
    missing.status_code = 404
    responses = [
        missing,
        _json_response({"content": "no path"}),
        _json_response({"path": "daily.md", "content": "found"}),
    ]

    with patch("mcp_obsidian.obsidian.requests.get", side_effect=responses):
        assert api.get_recent_periodic_notes(
            "daily", limit=1, include_content=True
        ) == [{"path": "daily.md", "content": "found"}]


@pytest.mark.parametrize(
    ("period", "expected"),
    [
        ("daily", [date(2026, 2, 10), date(2026, 2, 9)]),
        ("weekly", [date(2026, 2, 10), date(2026, 2, 3)]),
        ("monthly", [date(2026, 2, 1), date(2026, 1, 1)]),
        ("quarterly", [date(2026, 2, 1), date(2025, 11, 1)]),
        ("yearly", [date(2026, 1, 1), date(2025, 1, 1)]),
    ],
)
def test_periodic_candidate_dates_step_by_period(period, expected):
    candidates = _periodic_candidate_dates(period, date(2026, 2, 10))
    assert list(islice(candidates, 2)) == expected


def test_periodic_candidate_dates_stop_at_date_floor_and_reject_unknown_period():
    assert list(_periodic_candidate_dates("monthly", date(1, 1, 1))) == [
        date(1, 1, 1)
    ]
    assert list(_periodic_candidate_dates("yearly", date(1, 1, 1))) == [
        date(1, 1, 1)
    ]
    with pytest.raises(ValueError, match="unsupported period"):
        next(_periodic_candidate_dates("invalid", date(2026, 1, 1)))


def test_get_recent_changes_uses_jsonlogic_mtime_and_filters_and_sorts():
    api = _make_obsidian()
    now_seconds = 1_800_000_000
    now_ms = now_seconds * 1000
    payload = [
        {"filename": "older.md", "result": now_ms - (10 * 86_400_000)},
        {"filename": "newer.md", "result": now_ms - 1000},
        {"filename": "too-old.md", "result": now_ms - (15 * 86_400_000)},
        {"filename": "invalid.md", "result": True},
    ]
    with (
        patch.object(api, "search_json", return_value=payload) as search_json,
        patch("mcp_obsidian.obsidian.time.time", return_value=now_seconds),
    ):
        assert api.get_recent_changes(limit=2, days=14) == [
            {"filename": "newer.md", "mtime": now_ms - 1000},
            {"filename": "older.md", "mtime": now_ms - (10 * 86_400_000)},
        ]

    search_json.assert_called_once_with({"var": "stat.mtime"})


def test_get_batch_file_contents_includes_successes_and_errors():
    api = _make_obsidian()
    with patch.object(api, "get_file_contents", side_effect=["alpha", Exception("missing"), "gamma"]):
        result = api.get_batch_file_contents(["a.md", "b.md", "c.md"])

    assert "# a.md\n\nalpha\n\n---\n\n" in result
    assert "# b.md\n\nError reading file: missing\n\n---\n\n" in result
    assert "# c.md\n\ngamma\n\n---\n\n" in result
