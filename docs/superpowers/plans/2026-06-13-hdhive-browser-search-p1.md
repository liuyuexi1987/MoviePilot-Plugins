# 影巢网页方式搜索/解锁 P1 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 ARO 通过浏览器自动化（MP cloakbrowser）用现有影巢 cookie 完成影巢资源搜索 + 解锁，不依赖 OpenAPI，docker headless 可跑。

**Architecture:** 新增 `services/hdhive_browser.py`，对外 `HDHiveBrowserService`，内部调用 MoviePilot 官方 `app.helper.browser.PlaywrightHelper.action(url, callback, cookies)`（自动开 cloakbrowser context、注入 cookie、FlareSolverr 绕 CF、回调里给真实 playwright page）。`__init__.py` 按新配置 `hdhive_resource_mode` 在搜索/解锁处路由到 browser 或 openapi。前端「影巢资源」卡片加方式下拉。

**Tech Stack:** Python 3.12, MoviePilot PlaywrightHelper/cloakbrowser, Vue3 + Vuetify (federation), pytest 仅用于纯函数, 浏览器链路用容器实测。

**许可:** 复刻自 DDSRem-Dev/MoviePilot-Plugins (p115strmhelper, GPL v3)，本仓库同为 GPL v3，文件头注明来源。

**P1 范围:** cookie 注入（用现有 `hdhive_checkin_cookie`）+ 搜索 + 解锁 + 配置项 + 接入 + 前端。账号密码自动登录与 cookie 持久化属于 P2，不在本计划。

---

## File Structure

- Create: `AgentResourceOfficer/services/hdhive_browser.py` — 影巢网页方式服务（登录态=cookie 注入、search、unlock、结果归一）
- Create: `AgentResourceOfficer/tests/test_hdhive_browser.py` — 纯函数单元测试（cookie 解析、URL 构造、卡片归一）
- Modify: `AgentResourceOfficer/__init__.py` — 新增 `hdhive_resource_mode` 配置读取（约 line 152-196 字段区、line 1179-1196 读取区）、新增 `_ensure_hdhive_browser()` 与搜索/解锁路由（`_ensure_hdhive_service` 调用点附近 line 1867-1882, 3466/3499/3544）
- Modify: `AgentResourceOfficer/src/components/Config.vue` — 「影巢资源」卡片加 `hdhive_resource_mode` 下拉
- Sync: `plugins/agentresourceofficer/`, `plugins.v2/agentresourceofficer/`（实现完成后整体同步）

---

## Task 1: HDHiveBrowserService 骨架 + 纯函数（TDD）

**Files:**
- Create: `AgentResourceOfficer/services/hdhive_browser.py`
- Test: `AgentResourceOfficer/tests/test_hdhive_browser.py`

- [ ] **Step 1: 写失败测试**

```python
# AgentResourceOfficer/tests/test_hdhive_browser.py
import sys, types

# 桩掉 MoviePilot 运行时依赖，使纯函数可在无 MP 环境下测试
for name in ("app", "app.helper", "app.helper.browser", "app.log"):
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["app.helper.browser"].PlaywrightHelper = object  # type: ignore
sys.modules["app.log"].logger = types.SimpleNamespace(
    info=lambda *a, **k: None, warning=lambda *a, **k: None,
    error=lambda *a, **k: None, debug=lambda *a, **k: None,
)

from AgentResourceOfficer.services.hdhive_browser import HDHiveBrowserService


def test_detail_url_movie_and_tv():
    svc = HDHiveBrowserService(base_url="https://hdhive.com/", cookie="token=abc")
    assert svc._detail_url("movie", 123) == "https://hdhive.com/tmdb/movie/123"
    assert svc._detail_url("电影", 123) == "https://hdhive.com/tmdb/movie/123"
    assert svc._detail_url("tv", 9) == "https://hdhive.com/tmdb/tv/9"
    assert svc._detail_url("电视剧", 9) == "https://hdhive.com/tmdb/tv/9"


def test_is_ready_requires_cookie():
    assert HDHiveBrowserService(cookie="token=abc").is_ready() is True
    assert HDHiveBrowserService(cookie="").is_ready() is False


def test_normalize_extracts_slug_from_href():
    svc = HDHiveBrowserService(cookie="token=abc")
    raw = {
        "href": "/resource/115/abc-uuid-123/",
        "title": "电影标题",
        "resolution": "1080P",
        "size": "10 GB",
        "is_free": False,
        "unlock_points": 20,
        "user": "u",
        "posted_at": "2026/01/01",
        "tags": ["官组"],
    }
    out = svc._normalize(raw)
    assert out["slug"] == "abc-uuid-123"
    assert out["unlock_points"] == 20
    assert out["title"] == "电影标题"
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd /Users/jans/workspace/MoviePilot-Plugins && python3 -m pytest AgentResourceOfficer/tests/test_hdhive_browser.py -v`
Expected: FAIL（ModuleNotFoundError: hdhive_browser）

- [ ] **Step 3: 写最小实现**

```python
# AgentResourceOfficer/services/hdhive_browser.py
"""
影巢（HDHive）网页方式资源搜索/解锁服务。

通过 MoviePilot 官方 app.helper.browser.PlaywrightHelper（cloakbrowser 后端，
内置反检测与 FlareSolverr），用账号 cookie 在影巢网页上搜索资源、解锁拿 115 链接，
不依赖影巢 OpenAPI。仅在 MoviePilot docker 容器内 headless 运行。

本模块的页面抓取/解锁 JavaScript 与流程改编自 GPL v3 项目
DDSRem-Dev/MoviePilot-Plugins (plugins.v2/p115strmhelper/helper/hdhive/browser.py)。
原仓库: https://github.com/DDSRem-Dev/MoviePilot-Plugins
本仓库同为 GPL v3。
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from app.helper.browser import PlaywrightHelper
from app.log import logger


class HDHiveBrowserService:
    def __init__(
        self,
        base_url: str = "https://hdhive.com",
        cookie: str = "",
        timeout: int = 30,
    ) -> None:
        self.base_url = (base_url or "https://hdhive.com").rstrip("/")
        self.cookie = (cookie or "").strip()
        self.timeout = int(timeout or 30)

    def is_ready(self) -> bool:
        return bool(self.cookie)

    def _detail_url(self, media_type: Any, tmdb_id: Any) -> str:
        mt = "movie" if str(media_type).lower() in ("movie", "电影") else "tv"
        return f"{self.base_url}/tmdb/{mt}/{tmdb_id}"

    @staticmethod
    def _normalize(card: Dict[str, Any]) -> Dict[str, Any]:
        href = (card.get("href") or "").strip()
        slug = href.rstrip("/").split("/")[-1] if href else ""
        return {
            "slug": slug,
            "href": href,
            "title": card.get("title", ""),
            "resolution": card.get("resolution", ""),
            "size": card.get("size", ""),
            "is_free": bool(card.get("is_free")),
            "unlock_points": card.get("unlock_points"),
            "user": card.get("user", ""),
            "posted_at": card.get("posted_at", ""),
            "tags": card.get("tags", []),
        }
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd /Users/jans/workspace/MoviePilot-Plugins && python3 -m pytest AgentResourceOfficer/tests/test_hdhive_browser.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 提交**

```bash
cd /Users/jans/workspace/MoviePilot-Plugins
git add AgentResourceOfficer/services/hdhive_browser.py AgentResourceOfficer/tests/test_hdhive_browser.py
git commit -m "feat(aro): HDHiveBrowserService 骨架与纯函数(影巢网页方式 P1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: search() —— 浏览器抓资源卡片

**Files:**
- Modify: `AgentResourceOfficer/services/hdhive_browser.py`

- [ ] **Step 1: 在模块顶部（import 之后、class 之前）加入抓卡片 JS 常量**

```python
# 改编自 DDSRem-Dev p115strmhelper browser.py::_scrape_resource_cards_js (GPL v3)
_SCRAPE_CARDS_JS = r"""
() => {
    const sizeRe = /(\d+\.?\d*)\s*(TB|GB|MB|G(?!B)|M(?!B))\b/i;
    const dateRe = /发布于\s*([\d/\-]+)/;
    const resRe = /\b(4K|8K|2K|1080[piP]?|720[piP]?|480[piP]?)\b/;
    const pointsRe = /(\d+)\s*积分/;
    const candidates = [];
    for (const el of document.querySelectorAll('a,div,article,li,section')) {
        const t = el.innerText || '';
        if (!t.includes('发布于') || !sizeRe.test(t)) continue;
        if ((t.match(/发布于/g) || []).length !== 1) continue;
        if (t.length < 30 || t.length > 5000) continue;
        candidates.push(el);
    }
    const minimal = candidates.filter(
        el => !candidates.some(other => other !== el && el.contains(other))
    );
    const metaTerms = new Set([
        '4K','8K','2K','免费','官组','管理员','WEB-DL','WEBRip','BDRip','REMUX','HDTV',
        '简中','繁中','简英','繁英','内封','外挂','内嵌','简日','繁日','简韩','繁韩',
        '1080P','1080p','720P','720p','480P','480p','蓝光原盘','ISO'
    ]);
    return minimal.map(card => {
        const text = card.innerText || '';
        const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
        const dateMatch = text.match(dateRe);
        const sizeMatch = text.match(sizeRe);
        const resMatch = text.match(resRe);
        const pointsMatch = text.match(pointsRe);
        const isFree = text.includes('免费');
        const tags = [];
        if (text.includes('官组') || text.includes('管理员')) tags.push('官组');
        if (isFree) tags.push('免费');
        if (pointsMatch) tags.push(pointsMatch[0].trim());
        const dateLineIdx = lines.findIndex(l => /发布于/.test(l));
        const user = dateLineIdx > 0 ? lines[dateLineIdx - 1] : (lines[0] || '');
        const titleLines = lines.filter(l => {
            if (l.length < 3) return false;
            if (metaTerms.has(l)) return false;
            if (/^发布于/.test(l)) return false;
            if (/^\d+\s*积分$/.test(l)) return false;
            if (/^\d+\.?\d*\s*(T?B|G[Bi]?|M[Bi]?)$/i.test(l)) return false;
            if (l === user) return false;
            return true;
        });
        let title = titleLines
            .map(l => l.replace(/^\d+\s*积分\s*/, '').trim())
            .filter(Boolean).join(' ').trim();
        let hrefEl = card;
        while (hrefEl && hrefEl.tagName !== 'A') { hrefEl = hrefEl.parentElement; }
        const href = hrefEl ? (hrefEl.getAttribute('href') || '') : '';
        return {
            user, posted_at: dateMatch ? dateMatch[1] : '', tags, title,
            resolution: resMatch ? resMatch[1] : '',
            size: sizeMatch ? (sizeMatch[1] + ' ' + sizeMatch[2].toUpperCase()) : '',
            is_free: isFree,
            unlock_points: isFree ? 0 : (pointsMatch ? parseInt(pointsMatch[1]) : null),
            href,
        };
    });
}
"""
```

- [ ] **Step 2: 在 class 内加 `search()` 方法**

```python
    def search(self, media_type: Any, tmdb_id: Any) -> List[Dict[str, Any]]:
        """打开影巢详情页抓资源卡片。失败返回 []。"""
        url = self._detail_url(media_type, tmdb_id)

        def _callback(page: Any) -> List[Dict[str, Any]]:
            cards: List[Dict[str, Any]] = []
            deadline = time.time() + 10
            while time.time() < deadline:
                try:
                    if "/login" in (page.url or ""):
                        raise RuntimeError("cookie 失效，被重定向到登录页")
                    cards = page.evaluate(_SCRAPE_CARDS_JS) or []
                except RuntimeError:
                    raise
                except Exception:
                    cards = []
                if cards:
                    break
                page.wait_for_timeout(500)
            return cards

        try:
            cards = PlaywrightHelper().action(
                url, callback=_callback, cookies=self.cookie, timeout=self.timeout
            )
        except Exception as exc:
            logger.warning(f"[HDHiveBrowser] 搜索失败({url}): {exc}")
            return []
        return [self._normalize(c) for c in (cards or []) if c.get("href")]
```

- [ ] **Step 3: 语法检查**

Run: `cd /Users/jans/workspace/MoviePilot-Plugins && python3 -m py_compile AgentResourceOfficer/services/hdhive_browser.py && echo OK`
Expected: OK

- [ ] **Step 4: 单元测试仍通过（纯函数未受影响）**

Run: `cd /Users/jans/workspace/MoviePilot-Plugins && python3 -m pytest AgentResourceOfficer/tests/test_hdhive_browser.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd /Users/jans/workspace/MoviePilot-Plugins
git add AgentResourceOfficer/services/hdhive_browser.py
git commit -m "feat(aro): 影巢网页搜索 search() 抓卡片

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: unlock() —— 浏览器解锁拿 115 链接

**Files:**
- Modify: `AgentResourceOfficer/services/hdhive_browser.py`

- [ ] **Step 1: 顶部加提取链接 JS 常量**

```python
# 改编自 DDSRem-Dev p115strmhelper browser.py::unlock_resource 内 _EXTRACT_URL_JS (GPL v3)
_EXTRACT_115_URL_JS = r"""
() => {
    const urlPrefixRe = /^https?:\/\/(115cdn|115)\.com\//;
    for (const el of document.querySelectorAll('input')) {
        const v = (el.value || '').trim();
        if (urlPrefixRe.test(v)) return v;
    }
    for (const el of document.querySelectorAll('div, span, p, a, code')) {
        if (el.children.length > 0) continue;
        const t = (el.textContent || '').trim();
        if (urlPrefixRe.test(t)) return t;
    }
    const m = (document.body?.innerText || '').match(/https?:\/\/(115cdn|115)\.com\/\S+/);
    return m ? m[0].replace(/\s+$/, '') : null;
}
"""
```

- [ ] **Step 2: 在 class 内加 `unlock()` 方法**

```python
    def unlock(self, slug: str) -> Dict[str, Any]:
        """解锁资源，返回 {'url','already_owned'}。失败抛 RuntimeError。"""
        if not slug:
            raise RuntimeError("缺少资源 slug")
        url = f"{self.base_url}/resource/115/{slug}"

        def _callback(page: Any) -> Dict[str, Any]:
            captured: Dict[str, Optional[str]] = {"url": None}

            def _on_response(response: Any) -> None:
                try:
                    if response.status != 200:
                        return
                    if "json" not in response.headers.get("content-type", ""):
                        return
                    body = response.json()
                    if not isinstance(body, dict):
                        return
                    data = body.get("data") or {}
                    if not isinstance(data, dict):
                        return
                    for key in ("full_url", "url", "link", "resource_url"):
                        val = data.get(key)
                        if val and re.search(r"(115cdn|115)\.com", str(val)):
                            captured["url"] = str(val).strip()
                            break
                except Exception:
                    pass

            page.on("response", _on_response)

            if "/login" in (page.url or ""):
                raise RuntimeError("cookie 失效，被重定向到登录页")

            confirm = page.get_by_text("确定解锁", exact=True)
            existing: Optional[str] = None
            has_confirm = False
            deadline = time.time() + 15
            while time.time() < deadline:
                try:
                    existing = page.evaluate(_EXTRACT_115_URL_JS)
                except Exception:
                    existing = None
                if existing:
                    break
                try:
                    if confirm.first.is_visible():
                        has_confirm = True
                        break
                except Exception:
                    pass
                page.wait_for_timeout(500)

            if existing:
                return {"url": existing, "already_owned": True}
            if not has_confirm:
                raise RuntimeError(f"未找到「确定解锁」按钮或链接（URL: {page.url}）")

            confirm.first.click()
            deadline = time.time() + 20
            while time.time() < deadline:
                if captured["url"]:
                    return {"url": captured["url"], "already_owned": False}
                if re.search(r"(115cdn|115)\.com", page.url or ""):
                    return {"url": page.url, "already_owned": False}
                try:
                    extracted = page.evaluate(_EXTRACT_115_URL_JS)
                except Exception:
                    extracted = None
                if extracted:
                    return {"url": extracted, "already_owned": False}
                page.wait_for_timeout(500)
            raise RuntimeError(f"解锁后未获取 115 链接（URL: {page.url}）")

        return PlaywrightHelper().action(
            url, callback=_callback, cookies=self.cookie, timeout=self.timeout
        )
```

- [ ] **Step 3: 语法检查**

Run: `cd /Users/jans/workspace/MoviePilot-Plugins && python3 -m py_compile AgentResourceOfficer/services/hdhive_browser.py && echo OK`
Expected: OK

- [ ] **Step 4: 提交**

```bash
cd /Users/jans/workspace/MoviePilot-Plugins
git add AgentResourceOfficer/services/hdhive_browser.py
git commit -m "feat(aro): 影巢网页解锁 unlock() 拿 115 链接

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: 新增 `hdhive_resource_mode` 配置读取

**Files:**
- Modify: `AgentResourceOfficer/__init__.py`

- [ ] **Step 1: 在影巢字段默认值区（`_hdhive_base_url` 附近，约 line 152）加类属性**

定位现有行 `    _hdhive_base_url = "https://hdhive.com"`，在其后新增一行：

```python
    _hdhive_resource_mode = "browser"  # browser | openapi | auto
```

- [ ] **Step 2: 在配置读取区（`self._hdhive_base_url = ...` 附近，约 line 1179）加读取**

定位现有行 `        self._hdhive_base_url = self._clean_text(config.get("hdhive_base_url") or "https://hdhive.com").rstrip("/")`，在其后新增：

```python
        self._hdhive_resource_mode = (self._clean_text(config.get("hdhive_resource_mode")) or "browser").lower()
        if self._hdhive_resource_mode not in ("browser", "openapi", "auto"):
            self._hdhive_resource_mode = "browser"
```

- [ ] **Step 3: 在配置回写处加上该字段**

定位 `get_config` / 配置导出的 dict（搜索 `"hdhive_base_url": self._hdhive_base_url`，约 line 1714 区域），在其后新增一行：

```python
            "hdhive_resource_mode": self._hdhive_resource_mode,
```

- [ ] **Step 4: 语法检查**

Run: `cd /Users/jans/workspace/MoviePilot-Plugins && python3 -m py_compile AgentResourceOfficer/__init__.py && echo OK`
Expected: OK

- [ ] **Step 5: 提交**

```bash
cd /Users/jans/workspace/MoviePilot-Plugins
git add AgentResourceOfficer/__init__.py
git commit -m "feat(aro): 新增 hdhive_resource_mode 配置(browser/openapi/auto)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: 接入搜索/解锁路由

**Files:**
- Modify: `AgentResourceOfficer/__init__.py`

> 说明：保持下游数据结构不变。browser 结果字段（slug/title/resolution/size/unlock_points/...）需映射成 OpenAPI 搜索结果同名字段；解锁返回的 `url` 映射为现有解锁结果中的 115 链接字段。实现时先用 `rg "search_resources_by_keyword\|unlock_resource" AgentResourceOfficer/__init__.py` 找到全部调用点，逐个按 mode 包装。

- [ ] **Step 1: 加入 import 与惰性构造器**

在文件顶部 import 区，`from .services.hdhive_openapi import HDHiveOpenApiService` 之后新增：

```python
from .services.hdhive_browser import HDHiveBrowserService
```

在 `_ensure_hdhive_service` 方法（约 line 1867）之后，新增构造器（复用现有影巢 cookie 与 base_url、timeout）：

```python
    def _ensure_hdhive_browser(self) -> HDHiveBrowserService:
        cookie = self._clean_text(self._hdhive_checkin_cookie)
        return HDHiveBrowserService(
            base_url=self._hdhive_base_url,
            cookie=cookie,
            timeout=self._hdhive_timeout,
        )
```

- [ ] **Step 2: 加一个统一的"按 mode 搜索"辅助方法**

在 `_ensure_hdhive_browser` 之后新增。它把 browser 搜索结果映射到与现有展示兼容的结构（与 OpenAPI 路径对齐：`title/slug/unlock_points/size/resolution`）：

```python
    def _hdhive_browser_search(self, media_type: str, tmdb_id: str) -> List[Dict[str, Any]]:
        svc = self._ensure_hdhive_browser()
        if not svc.is_ready():
            logger.warning("[AgentResourceOfficer] 影巢网页方式未就绪：缺少影巢 Cookie")
            return []
        items = svc.search(media_type, tmdb_id)
        results: List[Dict[str, Any]] = []
        for it in items:
            results.append({
                "slug": it.get("slug", ""),
                "title": it.get("title", ""),
                "unlock_points": it.get("unlock_points"),
                "share_size": it.get("size", ""),
                "video_resolution": [it["resolution"]] if it.get("resolution") else [],
                "is_free": it.get("is_free", False),
                "user": it.get("user", ""),
                "posted_at": it.get("posted_at", ""),
                "pw_tags": it.get("tags", []),
                "source": "hdhive_browser",
            })
        return results
```

> 注意：上面的输出字段需与现有 OpenAPI 搜索结果字段名核对一致（实现时打开 `services/hdhive_openapi.py` 的 `search_resources` 返回结构，对齐键名；若有差异以 OpenAPI 结构为准修改这里）。

- [ ] **Step 3: 在搜索调用点按 mode 路由**

定位影巢按关键词搜索的调用处（`rg "search_resources_by_keyword" AgentResourceOfficer/__init__.py`）。在调用前按 mode 分流，例如把原来的：

```python
        service = self._ensure_hdhive_service()
        ok, payload, message = await service.search_resources_by_keyword(...)
```

改为：

```python
        if self._hdhive_resource_mode == "browser":
            # 由网页方式直接拿候选；需要 media_type 与 tmdb_id（沿用现有候选解析）
            browser_items = self._hdhive_browser_search(media_type, tmdb_id)
            ok, payload, message = bool(browser_items), {"resources": browser_items}, (
                "success" if browser_items else "影巢网页方式未找到资源")
        else:
            service = self._ensure_hdhive_service()
            ok, payload, message = await service.search_resources_by_keyword(...)
            if not ok and self._hdhive_resource_mode == "auto":
                browser_items = self._hdhive_browser_search(media_type, tmdb_id)
                if browser_items:
                    ok, payload, message = True, {"resources": browser_items}, "success"
```

> 实现时按调用点实际拥有的变量（media_type / tmdb_id / payload 结构）调整。逐个调用点对齐 payload 的资源列表键名（如 `resources`/`candidates`）。

- [ ] **Step 4: 在解锁调用点按 mode 路由**

定位解锁调用（`rg "\.unlock_resource\(" AgentResourceOfficer/__init__.py`）。改为：

```python
        if self._hdhive_resource_mode in ("browser", "auto"):
            try:
                browser = self._ensure_hdhive_browser()
                result = browser.unlock(slug)
                link = result.get("url", "")
                ok, payload, message = bool(link), {"url": link, "link": link}, (
                    "success" if link else "影巢网页方式解锁失败")
            except Exception as exc:
                ok, payload, message = False, {}, f"影巢网页方式解锁失败: {exc}"
                if self._hdhive_resource_mode == "auto":
                    service = self._ensure_hdhive_service()
                    ok, payload, message = service.unlock_resource(slug)
        else:
            service = self._ensure_hdhive_service()
            ok, payload, message = service.unlock_resource(slug)
```

> 解锁产出 `url` 后接现有转存流程的字段名需与 OpenAPI 解锁返回对齐（打开 `unlock_resource` 看返回的链接键名，统一）。

- [ ] **Step 5: 语法检查**

Run: `cd /Users/jans/workspace/MoviePilot-Plugins && python3 -m py_compile AgentResourceOfficer/__init__.py && echo OK`
Expected: OK

- [ ] **Step 6: 提交**

```bash
cd /Users/jans/workspace/MoviePilot-Plugins
git add AgentResourceOfficer/__init__.py
git commit -m "feat(aro): 影巢搜索/解锁按 hdhive_resource_mode 路由(网页/OpenAPI/auto)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: 前端「影巢资源」卡片加方式下拉

**Files:**
- Modify: `AgentResourceOfficer/src/components/Config.vue`

- [ ] **Step 1: 在「影巢资源」卡片 VRow 内、`hdhive_resource_enabled` 开关那一列之后插入下拉**

定位 `<VSwitch v-model="config.hdhive_resource_enabled" label="启用搜索/解锁"`，在其所在 `</VCol>` 之后新增：

```vue
            <VCol cols="12" sm="6" md="3">
              <VSelect
                v-model="config.hdhive_resource_mode"
                :items="[
                  { title: '网页方式', value: 'browser' },
                  { title: 'OpenAPI', value: 'openapi' },
                  { title: '自动(网页优先)', value: 'auto' },
                ]"
                item-title="title"
                item-value="value"
                label="影巢资源方式"
                variant="outlined"
                density="compact"
                hide-details="auto"
              />
            </VCol>
```

- [ ] **Step 2: 构建**

Run: `cd /Users/jans/workspace/MoviePilot-Plugins/AgentResourceOfficer && npm run build 2>&1 | grep -E 'Config-|built'`
Expected: 构建成功，输出新的 `Config-xxxx.js`

- [ ] **Step 3: 提交**

```bash
cd /Users/jans/workspace/MoviePilot-Plugins
git add AgentResourceOfficer/src/components/Config.vue AgentResourceOfficer/dist
git commit -m "feat(aro): 影巢资源卡片新增方式下拉(网页/OpenAPI/auto)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: 同步镜像 + 部署容器 + 端到端实测

**Files:**
- Sync: `plugins/agentresourceofficer/`, `plugins.v2/agentresourceofficer/`

- [ ] **Step 1: 同步到两个镜像目录**

```bash
cd /Users/jans/workspace/MoviePilot-Plugins
for dest in plugins/agentresourceofficer plugins.v2/agentresourceofficer; do
  cp AgentResourceOfficer/__init__.py "$dest/__init__.py"
  cp AgentResourceOfficer/services/hdhive_browser.py "$dest/services/hdhive_browser.py"
  cp AgentResourceOfficer/src/components/Config.vue "$dest/src/components/Config.vue"
  rm -rf "$dest/dist" && cp -R AgentResourceOfficer/dist "$dest/dist"
done
echo synced
```

- [ ] **Step 2: 部署到本机容器内置 + /config 两处**

```bash
cd /Users/jans/workspace/MoviePilot-Plugins
docker cp AgentResourceOfficer/services/hdhive_browser.py moviepilot-v2:/app/app/plugins/agentresourceofficer/services/hdhive_browser.py
docker cp AgentResourceOfficer/__init__.py moviepilot-v2:/app/app/plugins/agentresourceofficer/__init__.py
docker cp AgentResourceOfficer/src/components/Config.vue moviepilot-v2:/app/app/plugins/agentresourceofficer/src/components/Config.vue
docker exec moviepilot-v2 sh -c 'rm -rf /app/app/plugins/agentresourceofficer/dist && mkdir -p /app/app/plugins/agentresourceofficer/dist'
tar -C AgentResourceOfficer/dist -cf - . | docker exec -i moviepilot-v2 tar -C /app/app/plugins/agentresourceofficer/dist -xf -
DST="/Applications/Dockge/moviepilotv2/config/plugins/AgentResourceOfficer"
cp AgentResourceOfficer/services/hdhive_browser.py "$DST/services/hdhive_browser.py"
cp AgentResourceOfficer/__init__.py "$DST/__init__.py"
cp AgentResourceOfficer/src/components/Config.vue "$DST/src/components/Config.vue"
rm -rf "$DST/dist" && cp -R AgentResourceOfficer/dist "$DST/dist"
echo deployed
```

- [ ] **Step 3: 容器内直测 service（需用户提供有效影巢 cookie）**

> 前提：用户已在设置页「影巢签到」填入有效影巢网页 Cookie（含 `token=`），或用下面命令临时传入 COOKIE 实测。TMDB_ID 用一个确定有资源的作品。

```bash
docker exec -e HDHIVE_COOKIE="token=xxxx; csrf_access_token=yyyy" moviepilot-v2 python3 -c "
import sys; sys.path.insert(0,'/app')
from app.plugins.agentresourceofficer.services.hdhive_browser import HDHiveBrowserService
import os
svc = HDHiveBrowserService(cookie=os.environ['HDHIVE_COOKIE'])
rows = svc.search('movie', 27205)  # Inception
print('搜索结果数:', len(rows))
for r in rows[:3]:
    print(r['title'], r['size'], r['unlock_points'], r['slug'])
"
```
Expected: 打印若干资源行（标题/大小/积分/slug）。若为 0，检查 cookie 是否有效、是否被 CF 拦（看日志）。

- [ ] **Step 4: 重启容器加载后端改动并确认无异常**

```bash
docker restart moviepilot-v2
# 等待后端就绪后查加载日志
docker logs --since 1m moviepilot-v2 2>&1 | grep -E '加载插件：AgentResourceOfficer|成功加载.*工具|Traceback' | tail -5
```
Expected: `加载插件：AgentResourceOfficer 版本：0.2.92`、`成功加载 ... 工具`，无与本模块相关 Traceback。

- [ ] **Step 5: 前端验证**

硬刷新浏览器，打开「影巢资源」卡片，确认出现「影巢资源方式」下拉，默认「网页方式」。在 MoviePilot 里走一次影巢搜索（智能体或命令），确认能返回资源；对某资源解锁，确认拿到 115 链接并进入转存流程。

- [ ] **Step 6: 最终提交（如有同步文件改动）**

```bash
cd /Users/jans/workspace/MoviePilot-Plugins
git add plugins/agentresourceofficer plugins.v2/agentresourceofficer
git commit -m "chore(aro): 同步影巢网页方式 P1 到 plugins/ 与 plugins.v2/

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 实测依赖说明

- **必须**：用户有有效影巢账号，并在设置页「影巢签到」填入有效网页 Cookie（含 `token=`）。P1 不做账密自动登录，cookie 失效需手动更新（P2 解决）。
- **可能的失败点（实测时重点观察）**：
  1. cookie 通过 `set_extra_http_headers` 注入，影巢 SPA 的 XHR 若不认 header cookie，需改为 context.add_cookies 方式（届时在 service 内改用顶层 `cloakbrowser.launch_context` 自管 context + add_cookies，参考 DDSRem `_page_with_cookies`）。
  2. 搜索详情页为 SPA 异步渲染，卡片需轮询等待（已在 search 内做 10s 轮询）。
  3. 解锁链接可能在点击后的 XHR response 里（已监听）或页面 DOM（已轮询提取）。
  4. CF 拦截：确认 MoviePilot 是否配置 FlareSolverr；未配置且被拦时需在 MP 设置里启用。
