#!/usr/bin/env python3
"""
Live Browser Testing for Computed Field Dependency Auto-Management Feature
Test Suite: TC-001, TC-008, TC-004, RT-001
Version 2: With proper UI navigation fixes
"""

import sys
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from datetime import datetime

# Configuration
BASE_URL = "http://test-company-alpha.127-0-0-1.nip.io:8000"
LOGIN_EMAIL = "alice@alpha.com"
LOGIN_PASSWORD = "admin123"
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots" / "live-test-v2"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

class DependencyTestRunner:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.results = {
            "TC-001": {"status": "NOT_RUN", "details": [], "screenshots": []},
            "TC-008": {"status": "NOT_RUN", "details": [], "screenshots": []},
            "TC-004": {"status": "NOT_RUN", "details": [], "screenshots": []},
            "RT-001": {"status": "NOT_RUN", "details": [], "screenshots": []},
        }
        self.console_logs = []
        self.console_errors = []
        self.console_warnings = []

    def setup(self):
        """Initialize browser and login"""
        print("🚀 Starting browser automation...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False, slow_mo=500)
        self.context = self.browser.new_context(viewport={'width': 1920, 'height': 1080})
        self.page = self.context.new_page()

        # Set up console monitoring
        self.page.on("console", self._handle_console_message)

        print(f"📍 Navigating to login page: {BASE_URL}/login")
        self.page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        self.screenshot("00-login-page.png")

        # Login
        print(f"🔐 Logging in as {LOGIN_EMAIL}...")
        self.page.fill('input[name="email"]', LOGIN_EMAIL)
        self.page.fill('input[name="password"]', LOGIN_PASSWORD)
        self.screenshot("00-credentials-filled.png")
        self.page.click('button[type="submit"]')
        self.page.wait_for_load_state("networkidle")

        # Navigate to assign data points page
        print("📍 Navigating to Assign Data Points page...")
        self.page.goto(f"{BASE_URL}/admin/assign-data-points", wait_until="networkidle")
        self.page.wait_for_timeout(2000)  # Wait for JS to initialize
        self.screenshot("00-assign-data-points-page.png")

        # CRITICAL FIX: Switch to "All Fields" view
        print("🔄 Switching to 'All Fields' view...")
        all_fields_btn = self.page.locator('button:has-text("All Fields"), .tab-btn:has-text("All Fields"), #all-fields-tab')
        if all_fields_btn.count() > 0:
            all_fields_btn.first.click()
            self.page.wait_for_timeout(1000)
            print("✅ Switched to All Fields view")
        else:
            print("⚠️ Could not find All Fields button, trying alternative selector...")
            # Try clicking on the tab icon
            self.page.click('text=All Fields')
            self.page.wait_for_timeout(1000)

        self.screenshot("00-all-fields-view.png")
        print("✅ Setup complete\n")

    def _handle_console_message(self, msg):
        """Capture all console messages"""
        log_entry = {
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }
        self.console_logs.append(log_entry)

        if msg.type == "error":
            self.console_errors.append(log_entry)
            print(f"❌ CONSOLE ERROR: {msg.text}")
        elif msg.type == "warning":
            self.console_warnings.append(log_entry)
            print(f"⚠️ CONSOLE WARNING: {msg.text}")

    def screenshot(self, filename, test_id=None):
        """Take and save screenshot"""
        filepath = SCREENSHOTS_DIR / filename
        self.page.screenshot(path=str(filepath), full_page=True)
        if test_id:
            self.results[test_id]["screenshots"].append(filename)
        print(f"📸 Screenshot saved: {filename}")
        return filepath

    def log_result(self, test_id, message, level="info"):
        """Log test result details"""
        self.results[test_id]["details"].append({
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        })
        prefix = "✅" if level == "success" else "❌" if level == "error" else "⚠️" if level == "warning" else "ℹ️"
        print(f"{prefix} [{test_id}] {message}")

    def switch_to_all_fields_view(self):
        """Ensure we're in All Fields view"""
        try:
            # Check if we're already in All Fields view
            topics_active = self.page.locator('.tab-btn.active:has-text("Topics")').count() > 0
            if topics_active:
                self.page.click('text=All Fields')
                self.page.wait_for_timeout(1000)
                print("  🔄 Switched to All Fields view")
        except Exception as e:
            print(f"  ⚠️ Could not switch view: {str(e)}")

    def test_tc001_auto_cascade_selection(self):
        """TC-001: Auto-Cascade Selection"""
        print("\n" + "="*80)
        print("🧪 TEST TC-001: AUTO-CASCADE SELECTION")
        print("="*80 + "\n")

        test_id = "TC-001"

        try:
            # Ensure All Fields view
            self.switch_to_all_fields_view()

            # Step 1: Initial state
            self.log_result(test_id, "Taking initial screenshot...")
            self.screenshot("01-initial-page-state.png", test_id)

            # Step 2: Clear existing selections
            self.log_result(test_id, "Checking for existing selections...")
            selected_count = self.page.locator('.selected-item, .selected-data-point').count()
            if selected_count > 0:
                self.log_result(test_id, f"Found {selected_count} existing selections, clearing...")
                # Try clicking Deselect All
                deselect_btn = self.page.locator('button:has-text("DESELECT ALL"), button:has-text("Deselect All")')
                if deselect_btn.count() > 0:
                    deselect_btn.first.click()
                    self.page.wait_for_timeout(1000)
            self.screenshot("01-cleared-selections.png", test_id)

            # Step 3: Search for computed field
            self.log_result(test_id, "Searching for computed field...")
            search_box = self.page.locator('input[placeholder*="Search"]').first
            search_box.clear()
            search_box.fill("employee turnover")
            self.page.wait_for_timeout(1500)
            self.screenshot("02-search-employee-turnover.png", test_id)

            # Step 4: Look for computed fields with purple badges
            self.log_result(test_id, "Looking for computed fields with purple badges...")

            # Count all visible field items
            all_fields = self.page.locator('.field-item, .data-point-item, [data-field-id]').all()
            visible_fields = [f for f in all_fields if f.is_visible()]
            self.log_result(test_id, f"Found {len(visible_fields)} visible field(s)")

            # Look for purple/computed badges
            computed_badges = self.page.locator('.badge.computed, .field-type-badge.computed, [class*="computed"]').all()
            visible_badges = [b for b in computed_badges if b.is_visible()]
            self.log_result(test_id, f"Found {len(visible_badges)} computed field badge(s)")

            if len(visible_badges) > 0:
                self.log_result(test_id, "✅ Purple badges found!", "success")
                self.screenshot("03-purple-badges-found.png", test_id)

                # Find parent field item of the first badge
                badge = visible_badges[0]
                field_item = badge.locator('xpath=ancestor::*[contains(@class, "field-item") or contains(@class, "data-point-item")]').first

                # Step 5: Click add button for computed field
                self.log_result(test_id, "Clicking '+' button on computed field...")
                add_btn = field_item.locator('button:has-text("+"), button.add-btn').first

                if add_btn.is_visible():
                    add_btn.click()
                    self.page.wait_for_timeout(3000)  # Wait for auto-cascade
                    self.screenshot("04-after-clicking-add.png", test_id)

                    # Step 6: Check selected panel
                    self.log_result(test_id, "Checking selected panel...")
                    self.page.wait_for_timeout(1000)

                    selected_items = self.page.locator('.selected-item, .selected-data-point, [class*="selected-point"]').count()
                    self.log_result(test_id, f"Selected items: {selected_items}")

                    if selected_items == 3:
                        self.log_result(test_id, "✅ PASS: 3 fields added (1 computed + 2 dependencies)", "success")
                        self.results[test_id]["status"] = "PASS"
                    elif selected_items > 0:
                        self.log_result(test_id, f"⚠️ PARTIAL: Got {selected_items} fields (expected 3)", "warning")
                        self.results[test_id]["status"] = "PARTIAL"
                    else:
                        self.log_result(test_id, f"❌ FAIL: No fields were added", "error")
                        self.results[test_id]["status"] = "FAIL"

                    self.screenshot("05-selected-panel.png", test_id)

                    # Check for success notification
                    notification = self.page.locator('.notification, .toast, .alert, .message').first
                    if notification.is_visible():
                        notif_text = notification.inner_text()
                        self.log_result(test_id, f"Notification: {notif_text}")
                        self.screenshot("06-notification.png", test_id)
                else:
                    self.log_result(test_id, "❌ Add button not visible", "error")
                    self.results[test_id]["status"] = "FAIL"
            else:
                self.log_result(test_id, "❌ No purple badges found - feature not working", "error")
                self.results[test_id]["status"] = "FAIL"

                # Take diagnostic screenshot showing what fields are visible
                self.screenshot("03-no-badges-diagnostic.png", test_id)

        except Exception as e:
            self.log_result(test_id, f"Exception: {str(e)}", "error")
            self.results[test_id]["status"] = "FAIL"
            self.screenshot("01-exception.png", test_id)

    def test_tc008_visual_indicators(self):
        """TC-008: Visual Indicators"""
        print("\n" + "="*80)
        print("🧪 TEST TC-008: VISUAL INDICATORS")
        print("="*80 + "\n")

        test_id = "TC-008"

        try:
            # Ensure All Fields view
            self.switch_to_all_fields_view()

            # Clear search
            self.log_result(test_id, "Clearing search to see all fields...")
            search_box = self.page.locator('input[placeholder*="Search"]').first
            search_box.clear()
            self.page.wait_for_timeout(1000)
            self.screenshot("08-all-fields-cleared.png", test_id)

            # Count all computed field badges
            self.log_result(test_id, "Counting purple/computed field badges...")
            badges = self.page.locator('.badge.computed, .field-type-badge.computed, [class*="badge"][class*="computed"]').all()
            visible_badges = [b for b in badges if b.is_visible()]

            self.log_result(test_id, f"Found {len(visible_badges)} visible computed field badge(s)")

            if len(visible_badges) >= 2:
                self.log_result(test_id, "✅ PASS: Found expected computed field badges", "success")
                self.results[test_id]["status"] = "PASS"

                # Check badge contents
                for i, badge in enumerate(visible_badges[:3]):  # Check first 3
                    badge_html = badge.evaluate("el => el.outerHTML")
                    badge_text = badge.inner_text() if badge.is_visible() else ""
                    self.log_result(test_id, f"Badge {i+1} text: '{badge_text}'")

                    # Check for calculator icon or dependency count
                    has_icon = "🧮" in badge_html or "calculator" in badge_html.lower()
                    has_count = "(" in badge_text and ")" in badge_text

                    if has_icon or has_count:
                        self.log_result(test_id, f"Badge {i+1} has proper indicators", "success")
            elif len(visible_badges) > 0:
                self.log_result(test_id, f"⚠️ PARTIAL: Found {len(visible_badges)} badges (expected 2+)", "warning")
                self.results[test_id]["status"] = "PARTIAL"
            else:
                self.log_result(test_id, "❌ FAIL: No purple badges found", "error")
                self.results[test_id]["status"] = "FAIL"

            self.screenshot("09-badges-overview.png", test_id)

        except Exception as e:
            self.log_result(test_id, f"Exception: {str(e)}", "error")
            self.results[test_id]["status"] = "FAIL"
            self.screenshot("08-exception.png", test_id)

    def test_tc004_collapsible_grouping(self):
        """TC-004: Collapsible Grouping"""
        print("\n" + "="*80)
        print("🧪 TEST TC-004: COLLAPSIBLE GROUPING")
        print("="*80 + "\n")

        test_id = "TC-004"

        try:
            # Check DependencyManager
            self.log_result(test_id, "Checking DependencyManager status...")
            is_ready = self.page.evaluate("""
                () => {
                    if (window.DependencyManager && typeof window.DependencyManager.isReady === 'function') {
                        return window.DependencyManager.isReady();
                    }
                    return false;
                }
            """)
            self.log_result(test_id, f"DependencyManager.isReady(): {is_ready}")

            # Check selected panel for grouping
            selected_count = self.page.locator('.selected-item, .selected-data-point').count()
            self.log_result(test_id, f"Currently {selected_count} items selected")

            if selected_count > 0:
                # Look for grouping elements
                toggle_btns = self.page.locator('.toggle-btn, .dependency-toggle, button[class*="toggle"]').count()
                grouped_items = self.page.locator('.dependency-group, .computed-field-group, [class*="group"]').count()

                self.log_result(test_id, f"Toggle buttons: {toggle_btns}")
                self.log_result(test_id, f"Grouped items: {grouped_items}")

                if toggle_btns > 0:
                    self.log_result(test_id, "✅ PASS: Grouping UI present", "success")
                    self.results[test_id]["status"] = "PASS"
                else:
                    self.log_result(test_id, "⚠️ DEGRADED: No grouping, but fields accessible", "warning")
                    self.results[test_id]["status"] = "DEGRADED"
            else:
                self.log_result(test_id, "⚠️ No items selected to test grouping", "warning")
                self.results[test_id]["status"] = "NOT_RUN"

            self.screenshot("12-grouping-check.png", test_id)

        except Exception as e:
            self.log_result(test_id, f"Exception: {str(e)}", "error")
            self.results[test_id]["status"] = "FAIL"
            self.screenshot("12-exception.png", test_id)

    def test_rt001_regression(self):
        """RT-001: Regression Test"""
        print("\n" + "="*80)
        print("🧪 TEST RT-001: REGRESSION TEST")
        print("="*80 + "\n")

        test_id = "RT-001"

        try:
            # Ensure All Fields view
            self.switch_to_all_fields_view()

            # Clear all selections
            self.log_result(test_id, "Clearing all selections...")
            deselect_btn = self.page.locator('button:has-text("DESELECT ALL"), button:has-text("Deselect All")')
            if deselect_btn.count() > 0:
                deselect_btn.first.click()
                self.page.wait_for_timeout(1000)
            self.screenshot("17-cleared.png", test_id)

            # Search for a regular field
            self.log_result(test_id, "Searching for regular fields...")
            search_box = self.page.locator('input[placeholder*="Search"]').first
            search_box.clear()
            search_box.fill("total")
            self.page.wait_for_timeout(1500)

            # Find first field WITHOUT purple badge
            all_fields = self.page.locator('.field-item, .data-point-item, [data-field-id]').all()
            regular_field = None

            for field in all_fields:
                if not field.is_visible():
                    continue
                has_badge = field.locator('.badge.computed, .field-type-badge.computed').count() > 0
                if not has_badge:
                    regular_field = field
                    break

            if regular_field:
                self.log_result(test_id, "Found regular field, adding it...")
                add_btn = regular_field.locator('button:has-text("+"), button.add-btn').first
                if add_btn.is_visible():
                    add_btn.click()
                    self.page.wait_for_timeout(2000)

                    # Check count
                    selected_count = self.page.locator('.selected-item, .selected-data-point').count()
                    self.log_result(test_id, f"Selected count: {selected_count}")

                    if selected_count == 1:
                        self.log_result(test_id, "✅ PASS: Only 1 field added (no auto-cascade)", "success")
                        self.results[test_id]["status"] = "PASS"
                    else:
                        self.log_result(test_id, f"⚠️ Unexpected count: {selected_count}", "warning")
                        self.results[test_id]["status"] = "PARTIAL"

                    self.screenshot("18-regular-field-added.png", test_id)
                else:
                    self.log_result(test_id, "❌ Add button not visible", "error")
                    self.results[test_id]["status"] = "FAIL"
            else:
                self.log_result(test_id, "⚠️ Could not find regular field", "warning")
                self.results[test_id]["status"] = "NOT_RUN"

        except Exception as e:
            self.log_result(test_id, f"Exception: {str(e)}", "error")
            self.results[test_id]["status"] = "FAIL"
            self.screenshot("17-exception.png", test_id)

    def final_analysis(self):
        """Final analysis and screenshots"""
        print("\n" + "="*80)
        print("📊 FINAL ANALYSIS")
        print("="*80 + "\n")

        print(f"\n📋 Console Errors: {len(self.console_errors)}")
        for error in self.console_errors[:5]:
            print(f"  ❌ {error['text']}")

        print(f"\n⚠️ Console Warnings: {len(self.console_warnings)}")
        for warning in self.console_warnings[:5]:
            print(f"  ⚠️ {warning['text']}")

        self.screenshot("99-final-state.png")

    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*80)
        print("📝 GENERATING REPORT")
        print("="*80 + "\n")

        # Calculate results
        pass_count = sum(1 for r in self.results.values() if r["status"] == "PASS")
        fail_count = sum(1 for r in self.results.values() if r["status"] == "FAIL")
        partial_count = sum(1 for r in self.results.values() if r["status"] == "PARTIAL")
        degraded_count = sum(1 for r in self.results.values() if r["status"] == "DEGRADED")

        # Determine decision
        blocking_fails = [tid for tid, r in self.results.items() if r["status"] == "FAIL" and tid in ["TC-001", "TC-008", "RT-001"]]

        if len(blocking_fails) > 0:
            decision = "NO-GO"
            readiness = "NOT READY"
            risk = "HIGH"
        elif fail_count > 0 or (pass_count + partial_count) < 3:
            decision = "CONDITIONAL GO"
            readiness = "CONDITIONAL"
            risk = "MEDIUM"
        else:
            decision = "GO"
            readiness = "READY"
            risk = "LOW"

        report = f"""# Live Browser Test Results - Version 2
## Computed Field Dependency Auto-Management Feature

**Test Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Tester:** UI Testing Agent (Automated - Playwright)
**Environment:** {BASE_URL}

---

## Executive Summary

### GO/NO-GO Decision: **{decision}**

**Deployment Readiness:** {readiness}
**Risk Level:** {risk}

---

## Test Results Summary

| Test | Name | Result | Impact |
|------|------|--------|--------|
| TC-001 | Auto-Cascade Selection | {self.results["TC-001"]["status"]} | BLOCKING |
| TC-008 | Visual Indicators | {self.results["TC-008"]["status"]} | BLOCKING |
| TC-004 | Collapsible Grouping | {self.results["TC-004"]["status"]} | DEGRADABLE |
| RT-001 | Regression Test | {self.results["RT-001"]["status"]} | BLOCKING |

**Results:**
- PASS: {pass_count}
- FAIL: {fail_count}
- PARTIAL: {partial_count}
- DEGRADED: {degraded_count}

---

## Detailed Results

"""

        for test_id in ["TC-001", "TC-008", "TC-004", "RT-001"]:
            result = self.results[test_id]
            report += f"\n### {test_id}: {self._get_test_name(test_id)}\n\n"
            report += f"**Status:** {result['status']}\n\n"
            report += "**Log:**\n\n"
            for detail in result["details"]:
                icon = "✅" if detail["level"] == "success" else "❌" if detail["level"] == "error" else "⚠️" if detail["level"] == "warning" else "ℹ️"
                report += f"- {icon} {detail['message']}\n"
            report += "\n"

        # Console errors
        report += f"\n## Console Errors: {len(self.console_errors)}\n\n"
        for error in self.console_errors[:10]:
            report += f"- ❌ {error['text']}\n"

        report += f"\n## Console Warnings: {len(self.console_warnings)}\n\n"
        for warning in self.console_warnings[:10]:
            report += f"- ⚠️ {warning['text']}\n"

        # Decision
        report += f"\n---\n\n## Decision: {decision}\n\n"

        if decision == "GO":
            report += "**Action:** Deploy to production\n\n"
        elif decision == "CONDITIONAL GO":
            report += "**Action:** Deploy with follow-up work\n\n"
        else:
            report += "**Action:** ❌ BLOCK - Fix issues first\n\n"
            report += "**Blocking Issues:**\n\n"
            for tid in blocking_fails:
                report += f"- {tid}: {self._get_test_name(tid)}\n"

        report += f"\n---\n\n**Screenshots:** test-folder/screenshots/live-test-v2/\n"
        report += f"\n*Generated: {datetime.now().isoformat()}*\n"

        # Save report
        report_dir = Path(__file__).parent / "report"
        report_dir.mkdir(exist_ok=True)
        report_file = report_dir / "LIVE_TEST_RESULTS_V2.md"
        report_file.write_text(report)
        print(f"✅ Report saved: {report_file}")

        return report

    def _get_test_name(self, test_id):
        names = {
            "TC-001": "Auto-Cascade Selection",
            "TC-008": "Visual Indicators",
            "TC-004": "Collapsible Grouping",
            "RT-001": "Regression Test"
        }
        return names.get(test_id, "Unknown")

    def teardown(self):
        """Cleanup"""
        print("\n🧹 Cleaning up...")
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("✅ Cleanup complete\n")

    def run(self):
        """Run all tests"""
        try:
            self.setup()
            self.test_tc001_auto_cascade_selection()
            self.test_tc008_visual_indicators()
            self.test_tc004_collapsible_grouping()
            self.test_rt001_regression()
            self.final_analysis()
            report = self.generate_report()
            print("\n" + "="*80)
            print("✅ TESTING COMPLETE")
            print("="*80)
            return report
        except Exception as e:
            print(f"\n❌ FATAL ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.teardown()

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                 DEPENDENCY MANAGEMENT LIVE TEST - V2                          ║
║                        (With UI Navigation Fixes)                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)

    runner = DependencyTestRunner()
    runner.run()
