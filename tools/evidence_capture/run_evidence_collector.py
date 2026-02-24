from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright


def slugify_path(route: str) -> str:
    cleaned = route.strip("/") or "home"
    cleaned = cleaned.replace("/", "_")
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", cleaned)


def run_bench_execute(method: str) -> dict:
    cmd = [
        "docker",
        "compose",
        "-f",
        "infra/docker/docker-compose.yml",
        "exec",
        "backend",
        "bash",
        "-lc",
        f"bench --site localhost execute {method}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    payload = None
    if stdout:
        try:
            payload = json.loads(stdout)
        except Exception:
            payload = stdout

    return {
        "method": method,
        "exit_code": proc.returncode,
        "stdout": payload,
        "stderr": stderr,
    }


def open_and_capture(page, base_url: str, route: str, screenshots_dir: Path) -> dict:
    target = f"{base_url.rstrip('/')}{route}"
    page.goto(target, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1500)

    shot_path = screenshots_dir / f"{slugify_path(route)}.png"
    page.screenshot(path=str(shot_path), full_page=True)

    content = page.content().lower()
    has_not_found = "not found" in content or "page not found" in content
    return {
        "route": route,
        "url": page.url,
        "title": page.title(),
        "not_found_detected": has_not_found,
        "screenshot": str(shot_path).replace("\\", "/"),
    }


def collect_records(request_ctx, base_url: str, doctype: str, limit: int) -> dict:
    endpoint = (
        f"{base_url.rstrip('/')}/api/resource/{quote(doctype)}"
        f"?fields=[\"name\",\"modified\"]&limit_page_length={limit}"
    )
    resp = request_ctx.get(endpoint, timeout=45000)

    result = {
        "doctype": doctype,
        "status": resp.status,
        "ok": resp.ok,
        "records": [],
        "error": None,
    }

    if not resp.ok:
        result["error"] = resp.text()
        return result

    try:
        body = resp.json()
        records = body.get("data") or []
        result["records"] = records
    except Exception as exc:
        result["error"] = str(exc)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect end-to-end evidence for AT runs")
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON")
    args = parser.parse_args()

    scenario_path = Path(args.scenario).resolve()
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))

    output_dir = Path(scenario["output_dir"]).resolve()
    screenshots_dir = output_dir / "screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    base_url = scenario["base_url"]
    username = scenario["login"]["username"]
    password = scenario["login"]["password"]

    evidence: dict = {
        "scenario": scenario.get("name"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "login_user": username,
        "pages": [],
        "record_queries": [],
        "bench_execute": [],
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        page.goto(f"{base_url.rstrip('/')}/login", wait_until="domcontentloaded", timeout=45000)

        user_selector = None
        pass_selector = None

        if page.locator("input[name='usr']").count() > 0:
            user_selector = "input[name='usr']"
        elif page.locator("#login_email").count() > 0:
            user_selector = "#login_email"

        if page.locator("input[name='pwd']").count() > 0:
            pass_selector = "input[name='pwd']"
        elif page.locator("#login_password").count() > 0:
            pass_selector = "#login_password"

        if not user_selector or not pass_selector:
            page.screenshot(path=str(screenshots_dir / "login_form_missing.png"), full_page=True)
            raise RuntimeError("Login form not found at /login with known selectors")

        page.fill(user_selector, username)
        page.fill(pass_selector, password)

        if page.locator("button.btn-login").count() > 0:
            page.click("button.btn-login")
        elif page.locator("button:has-text('Login')").count() > 0:
            page.click("button:has-text('Login')")
        else:
            page.keyboard.press("Enter")

        page.wait_for_timeout(3000)

        still_on_login = (
            page.locator("#login_password").count() > 0
            and page.locator("#login_password").is_visible()
        ) or (
            page.locator("input[name='pwd']").count() > 0
            and page.locator("input[name='pwd']").is_visible()
        )

        if still_on_login:
            page.screenshot(path=str(screenshots_dir / "login_failed.png"), full_page=True)
            raise RuntimeError(f"Login appears to have failed; current URL: {page.url}")

        page.screenshot(path=str(screenshots_dir / "post_login.png"), full_page=True)

        for route in scenario.get("pages", []):
            evidence["pages"].append(open_and_capture(page, base_url, route, screenshots_dir))

        request_ctx = context.request
        for query in scenario.get("record_queries", []):
            doctype = query["doctype"]
            limit = int(query.get("limit", 10))
            evidence["record_queries"].append(collect_records(request_ctx, base_url, doctype, limit))

        browser.close()

    for method in scenario.get("bench_execute", []):
        evidence["bench_execute"].append(run_bench_execute(method))

    report_path = output_dir / "evidence_report.json"
    report_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    print(str(report_path).replace("\\", "/"))


if __name__ == "__main__":
    main()
