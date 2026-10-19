"""Settings: round-trip, corruption recovery, the shared service
URL config name, and the clock high-water guard."""

from __future__ import annotations

import json

from hackproof_app import config


def test_roundtrip(store):
    store.settings.license_key = "KEYDATA"
    store.settings.service_base_url = "https://svc.example/"
    store.settings.order.order_id = "hp_1"
    store.settings.order.email = "a@b.co"
    store.save()
    fresh = config.SettingsStore(store.dir)
    assert fresh.settings.license_key == "KEYDATA"
    assert fresh.settings.service_base_url == "https://svc.example/"
    assert fresh.settings.order.order_id == "hp_1"
    assert fresh.settings.order.email == "a@b.co"


def test_trailing_slash_normalized(store):
    store.settings.service_base_url = "https://svc.example///"
    assert store.settings.effective_service_base_url() == "https://svc.example"


def test_env_var_wins_over_saved(store, monkeypatch):
    store.settings.service_base_url = "https://saved.example"
    monkeypatch.setenv(config.SERVICE_BASE_ENV, "https://env.example/")
    assert store.settings.effective_service_base_url() == "https://env.example"
    monkeypatch.delenv(config.SERVICE_BASE_ENV)
    assert store.settings.effective_service_base_url() == "https://saved.example"


def test_corrupt_settings_recover_empty(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "settings.json").write_text("{ not json", encoding="utf-8")
    store = config.SettingsStore(folder)
    assert store.settings.license_key == ""
    # The corrupt file is left as-is until a save replaces it.
    assert (folder / "settings.json").read_text(
        encoding="utf-8"
    ) == "{ not json"
    store.save()  # saving still works after corruption
    json.loads((folder / "settings.json").read_text(encoding="utf-8"))


def test_types_coerced_not_trusted(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "settings.json").write_text(
        json.dumps({"license_key": 42, "max_clock_ms": "soon",
                    "order": {"order_id": 7, "email": None}}),
        encoding="utf-8",
    )
    store = config.SettingsStore(folder)
    assert store.settings.license_key == "42"  # str-coerced
    assert store.settings.max_clock_ms == 0  # unparseable -> 0, no crash
    assert store.settings.order.order_id == "7"
    assert store.settings.order.email == ""


def test_clock_high_water_never_decreases(store):
    store.record_clock_ms(1000)
    assert store.clock_high_water_ms() == 1000
    store.record_clock_ms(500)
    assert store.clock_high_water_ms() == 1000
    store.record_clock_ms(2000)
    assert store.clock_high_water_ms() == 2000


def test_data_dir_env_redirects(tmp_path, monkeypatch):
    monkeypatch.setenv(config.DATA_DIR_ENV, str(tmp_path / "portable"))
    assert config.data_dir() == tmp_path / "portable"
    assert config.is_portable()
    monkeypatch.delenv(config.DATA_DIR_ENV)
    assert not config.is_portable()


def test_settings_file_is_valid_json_after_save(store):
    store.save()
    payload = json.loads(store.path.read_text(encoding="utf-8"))
    assert payload["license_key"] == ""
    assert "service_base_url" in payload


def test_shared_config_name():
    # THE name shared with the site crew's placeholder and the
    # app: both mean "the payments service base URL".
    assert config.SERVICE_BASE_ENV == "HACKPROOF_SERVICE_BASE_URL"
