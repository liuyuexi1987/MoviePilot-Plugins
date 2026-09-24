#!/usr/bin/env python3
import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "AgentResourceOfficer" / "feishu_channel.py"
CORE_PATH = ROOT / "AgentResourceOfficer" / "__init__.py"
FORM_PATHS = [
    ROOT / "AgentResourceOfficer" / "__init__.py",
    ROOT / "plugins" / "agentresourceofficer" / "__init__.py",
    ROOT / "plugins.v2" / "agentresourceofficer" / "__init__.py",
]


class FakePlugin:
    def get_config(self):
        return {}

    def get_state(self):
        return True

    @staticmethod
    def _extract_first_url(text):
        match = re.search(r"https?://\S+", str(text or ""))
        return match.group(0) if match else ""

    @staticmethod
    def _is_115_url(url):
        return "115cdn.com" in str(url or "")

    @staticmethod
    def _is_quark_url(url):
        return "pan.quark.cn" in str(url or "")


def load_channel_module():
    spec = importlib.util.spec_from_file_location("agent_resource_officer_feishu_channel", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(name, condition):
    if not condition:
        raise AssertionError(name)


def check_quark_settings_health_auth():
    core = CORE_PATH.read_text(encoding="utf-8")
    config = (ROOT / "AgentResourceOfficer" / "src" / "components" / "Config.vue").read_text(encoding="utf-8")
    check(
        "quark settings health uses bearer route",
        '"path": "/quark/ui/health"' in core
        and '"endpoint": self.api_quark_ui_health' in core
        and '"auth": "bear"' in core
        and 'pluginBase.value}/quark/ui/health' in config,
    )
    check(
        "quark external health keeps api key guard",
        "async def api_quark_health" in core
        and "ok, message = self._check_api_access(request)" in core
        and "async def api_quark_ui_health" in core,
    )
    mounted_block = config.split("onMounted(", 1)[1].split("onBeforeUnmount", 1)[0]
    check(
        "settings mount only loads persisted config",
        "await loadLatestConfig()" in mounted_block
        and "loadStorageHealth()" not in mounted_block,
    )


def check_transfer_history_mp_v3_adapter(module, channel):
    class Record:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    calls = {"hash": 0, "title": 0, "page": 0}
    transfer_record = Record(
        id=7,
        title="测试媒体",
        year="2026",
        type="movie",
        category="电影",
        seasons="",
        episodes="",
        mode="copy",
        status=True,
        date="2026-09-20 12:00:00",
        downloader="qb",
        download_hash="hash-123",
        src="/downloads/测试媒体.mkv",
        dest="/media/电影/测试媒体 (2026)/测试媒体.mkv",
        errmsg="",
        tmdbid=1,
        doubanid="",
    )
    download_record = Record(
        id=1,
        title="测试媒体",
        year="2026",
        type="movie",
        seasons="",
        episodes="",
        date="2026-09-20 11:00:00",
        downloader="qb",
        download_hash="hash-123",
        torrent_name="测试媒体.2026.1080p",
        torrent_site="测试站",
        username="tester",
        channel="manual",
        path="/downloads/测试媒体.mkv",
        tmdbid=1,
        doubanid="",
    )

    class FakeTransferHistoryOper:
        def __init__(self):
            self._db = None

        def list_by_hash(self, download_hash):
            calls["hash"] += 1
            check("transfer hash value", download_hash == "hash-123")
            return [transfer_record]

        def get_by_title(self, title):
            calls["title"] += 1
            check("transfer title value", title)
            return [transfer_record]

        def list_by_date(self, date):
            calls["page"] += 1
            check("transfer earliest date", date == "1970-01-01 00:00:00")
            return [transfer_record]

    class FakeTransferHistory:
        @staticmethod
        def list_by_title(db, title, page=1, count=30, status=None):
            raise AssertionError("should use TransferHistoryOper.get_by_title")

        @staticmethod
        def list_by_page(db, page=1, count=30, status=None):
            raise AssertionError("should use TransferHistoryOper.list_by_date")

    class FakeDownloadHistoryOper:
        _db = None

        @staticmethod
        def list_by_page(page=1, count=30):
            return [download_record]

    original_values = {
        "TransferHistory": module.TransferHistory,
        "TransferHistoryOper": module.TransferHistoryOper,
        "DownloadHistory": module.DownloadHistory,
        "DownloadHistoryOper": module.DownloadHistoryOper,
    }
    try:
        module.TransferHistory = FakeTransferHistory
        module.TransferHistoryOper = FakeTransferHistoryOper
        module.DownloadHistory = object
        module.DownloadHistoryOper = FakeDownloadHistoryOper
        download_result = channel._query_download_history(title="测试媒体")
        check("mpv3 download history success", download_result["success"] is True)
        check("mpv3 download history transfer", download_result["items"][0]["transfer_status"] == "success")
        title_result = channel._query_transfer_history(title="测试媒体")
        check("mpv3 transfer history title success", title_result["success"] is True)
        page_result = channel._query_transfer_history(status="all")
        check("mpv3 transfer history page success", page_result["success"] is True)
        check("mpv3 transfer hash adapter", calls["hash"] == 1)
        check("mpv3 transfer title adapter", calls["title"] == 1)
        check("mpv3 transfer page adapter", calls["page"] == 1)
    finally:
        for name, value in original_values.items():
            setattr(module, name, value)


def main():
    check_quark_settings_health_auth()
    channel_module = load_channel_module()
    channel_cls = channel_module.FeishuChannel
    channel = channel_cls(FakePlugin())
    channel.configure({})
    default_whitelist = set(channel_cls.default_command_whitelist())
    default_alias_targets = set(channel_cls.parse_alias_text(channel_cls.default_command_aliases()).values())
    missing_alias_targets = sorted(default_alias_targets - default_whitelist)
    check("all default alias targets are whitelisted", not missing_alias_targets)

    cases = {
        "yc蜘蛛侠": "/smart_entry 蜘蛛侠",
        "2蜘蛛侠": "/smart_entry 蜘蛛侠",
        "ps大君夫人": "/pansou_search 大君夫人",
        "1大君夫人": "/pansou_search 大君夫人",
        "选择 1 path=/飞书": "/smart_pick 1 path=/飞书",
        "详情": "/smart_pick 详情",
        "审查": "/smart_pick 审查",
        "n 下一页": "/smart_pick n 下一页",
        "https://pan.quark.cn/s/xxxx": "/smart_entry https://pan.quark.cn/s/xxxx",
        "链接 https://115cdn.com/s/xxxx path=/待整理": "/smart_entry 链接 https://115cdn.com/s/xxxx path=/待整理",
    }
    for raw, expected in cases.items():
        check(f"map {raw}", channel._map_text_to_command(raw) == expected)

    health = channel.health()
    check("health has legacy_bridge_running", "legacy_bridge_running" in health)
    check("health has conflict_warning", "conflict_warning" in health)
    check("health has safe_to_enable", "safe_to_enable" in health)
    check("health has recommended_action", "recommended_action" in health)
    check("health has migration_hint", "migration_hint" in health)
    check("default conflict false", health["conflict_warning"] is False)
    check_transfer_history_mp_v3_adapter(channel_module, channel)

    channel.configure({"feishu_enabled": True})
    channel.is_legacy_bridge_running = lambda: True
    health = channel.health()
    check("conflict true when both enabled", health["legacy_bridge_running"] is True and health["conflict_warning"] is True)
    check("conflict recommends disabling legacy", health["recommended_action"] == "disable_legacy_bridge_or_use_different_app")

    required_form_models = [
        '"model": "feishu_reply_receive_id_type"',
        '"model": "feishu_command_whitelist"',
        '"model": "feishu_command_aliases"',
    ]
    for path in FORM_PATHS:
        text = path.read_text(encoding="utf-8")
        for needle in required_form_models:
            check(f"{path.relative_to(ROOT)} has {needle}", needle in text)

    core_text = CORE_PATH.read_text(encoding="utf-8")
    for needle in [
        '("MP搜索", "mp")',
        '("原生搜索", "mp")',
        'if mode == "mp":',
        '"action": "media_search"',
    ]:
        check(f"core assistant route supports {needle}", needle in core_text)

    print("agent_resource_officer_feishu_channel_check_ok")


if __name__ == "__main__":
    main()
