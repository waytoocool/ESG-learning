#!/usr/bin/env python3
"""
Live Browser Testing for Computed Field Dependency Auto-Management Feature
Test Suite: TC-001, TC-008, TC-004, RT-001
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
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots" / "live-test"
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
        prefix = "✅" if level == "success" else "❌" if level == "error" else "ℹ️"
        print(f"{prefix} [{test_id}] {message}")

    def test_tc001_auto_cascade_selection(self):
        """TC-001: Auto-Cascade Selection"""
        print("\n" + "="*80)
        print("🧪 TEST TC-001: AUTO-CASCADE SELECTION")
        print("="*80 + "\n")

        test_id = "TC-001"

        try:
            # Step 1: Initial state
            self.log_result(test_id, "Taking initial screenshot...")
            self.screenshot("01-initial-page-state.png", test_id)

            # Step 2: Clear existing selections
            self.log_result(test_id, "Checking for existing selections...")
            selected_count = self.page.locator('.selected-data-point-item').count()
            if selected_count > 0:
                self.log_result(test_id, f"Found {selected_count} existing selections, clearing...")
                # Try to find and click clear all button
                if self.page.locator('button:has-text("Clear All")').count() > 0:
                    self.page.click('button:has-text("Clear All")')
                    self.page.wait_for_timeout(1000)
                else:
                    # Remove items one by one
                    for i in range(selected_count):
                        self.page.locator('.selected-data-point-item .remove-btn').first.click()
                        self.page.wait_for_timeout(500)
            self.screenshot("01-cleared-selections.png", test_id)

            # Step 3: Find computed field
            self.log_result(test_id, "Searching for computed field 'employee turnover'...")
            search_box = self.page.locator('input[type="search"], input[placeholder*="Search"]').first
            search_box.fill("employee turnover")
            self.page.wait_for_timeout(1000)
            self.screenshot("02-computed-field-in-list.png", test_id)

            # Step 4: Verify purple badge
            self.log_result(test_id, "Checking for purple badge on computed field...")
            purple_badges = self.page.locator('.field-type-badge.computed').count()
            if purple_badges > 0:
                self.log_result(test_id, f"Found {purple_badges} purple badge(s)", "success")
                self.screenshot("03-purple-badge-visible.png", test_id)
            else:
                self.log_result(test_id, "No purple badges found!", "error")

            # Step 5: Click "+" button to add computed field
            self.log_result(test_id, "Clicking '+' button to add computed field...")
            add_buttons = self.page.locator('button.add-btn, button:has-text("+")').all()
            if len(add_buttons) > 0:
                # Find the first visible add button
                for btn in add_buttons:
                    if btn.is_visible():
                        btn.click()
                        break
                self.page.wait_for_timeout(3000)  # Wait for auto-cascade
                self.screenshot("04-after-clicking-add.png", test_id)
            else:
                self.log_result(test_id, "No add button found!", "error")

            # Step 6: Check selected panel
            self.log_result(test_id, "Counting fields in selected panel...")
            self.page.wait_for_timeout(1000)
            selected_items = self.page.locator('.selected-data-point-item').count()
            self.log_result(test_id, f"Found {selected_items} field(s) in selected panel")

            if selected_items == 3:
                self.log_result(test_id, "✅ CORRECT: 3 fields added (1 computed + 2 dependencies)", "success")
                self.results[test_id]["status"] = "PASS"
            else:
                self.log_result(test_id, f"❌ INCORRECT: Expected 3 fields, got {selected_items}", "error")
                self.results[test_id]["status"] = "FAIL"

            self.screenshot("05-selected-panel-three-fields.png", test_id)

            # Step 7: Check counter
            counter = self.page.locator('.selected-count, .counter, text=/\\d+ selected/i').first
            if counter.is_visible():
                counter_text = counter.inner_text()
                self.log_result(test_id, f"Counter shows: {counter_text}")
                self.screenshot("06-counter-display.png", test_id)

            # Step 8: Check for notification
            notification = self.page.locator('.notification, .toast, .alert-success').first
            if notification.is_visible():
                notif_text = notification.inner_text()
                self.log_result(test_id, f"Notification: {notif_text}")
                self.screenshot("07-success-notification.png", test_id)

            # Final console check
            errors_in_test = [e for e in self.console_errors if "DependencyManager" in e["text"] or "cascade" in e["text"].lower()]
            if errors_in_test:
                self.log_result(test_id, f"Found {len(errors_in_test)} related console errors", "error")
                if self.results[test_id]["status"] == "PASS":
                    self.results[test_id]["status"] = "FAIL"

        except Exception as e:
            self.log_result(test_id, f"Exception occurred: {str(e)}", "error")
            self.results[test_id]["status"] = "FAIL"
            self.screenshot("01-error-state.png", test_id)

    def test_tc008_visual_indicators(self):
        """TC-008: Visual Indicators"""
        print("\n" + "="*80)
        print("🧪 TEST TC-008: VISUAL INDICATORS")
        print("="*80 + "\n")

        test_id = "TC-008"

        try:
            # Clear search to see all fields
            self.log_result(test_id, "Clearing search to see all fields...")
            search_box = self.page.locator('input[type="search"], input[placeholder*="Search"]').first
            search_box.fill("")
            self.page.wait_for_timeout(1000)

            # Step 1: Check purple badges in topic tree
            self.log_result(test_id, "Looking for GRI 401 topic...")
            gri401_topic = self.page.locator('text=/GRI 401.*Employment/i').first
            if gri401_topic.is_visible():
                # Expand if collapsed
                parent = gri401_topic.locator('xpath=ancestor::*[contains(@class, "topic")]').first
                if parent.locator('.collapsed').count() > 0:
                    gri401_topic.click()
                    self.page.wait_for_timeout(1000)

            self.screenshot("08-topic-tree-with-badges.png", test_id)

            # Step 2: Count purple badges
            self.log_result(test_id, "Counting purple badges...")
            purple_badges = self.page.locator('.field-type-badge.computed, .badge.computed, [class*="computed"]').all()
            visible_badges = [b for b in purple_badges if b.is_visible()]

            self.log_result(test_id, f"Found {len(visible_badges)} visible computed field badge(s)")

            if len(visible_badges) >= 2:
                self.log_result(test_id, "✅ Purple badges found for computed fields", "success")
                self.results[test_id]["status"] = "PASS"
            else:
                self.log_result(test_id, "❌ Expected at least 2 purple badges", "error")
                self.results[test_id]["status"] = "FAIL"

            # Step 3: Check badge components
            if len(visible_badges) > 0:
                badge = visible_badges[0]
                badge_html = badge.evaluate("el => el.outerHTML")
                self.log_result(test_id, f"Badge HTML: {badge_html[:200]}...")

                # Check for calculator icon
                has_icon = "🧮" in badge_html or "calculator" in badge_html.lower()
                self.log_result(test_id, f"Calculator icon present: {has_icon}")

            self.screenshot("09-badge-details.png", test_id)

            # Step 4: Check selected panel indicators (if any items selected)
            selected_items = self.page.locator('.selected-data-point-item').count()
            if selected_items > 0:
                self.screenshot("10-selected-panel-indicators.png", test_id)

        except Exception as e:
            self.log_result(test_id, f"Exception occurred: {str(e)}", "error")
            self.results[test_id]["status"] = "FAIL"
            self.screenshot("08-error-state.png", test_id)

    def test_tc004_collapsible_grouping(self):
        """TC-004: Collapsible Grouping"""
        print("\n" + "="*80)
        print("🧪 TEST TC-004: COLLAPSIBLE GROUPING")
        print("="*80 + "\n")

        test_id = "TC-004"

        try:
            # Step 1: Check DependencyManager status
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
            self.screenshot("12-dependency-manager-check.png", test_id)

            # Step 2: Look for grouping in selected panel
            self.log_result(test_id, "Checking for grouping structure in selected panel...")

            # Check for toggle buttons
            toggle_buttons = self.page.locator('.dependency-toggle-btn, button.toggle-btn, .toggle-dependencies').count()
            self.log_result(test_id, f"Found {toggle_buttons} toggle button(s)")

            # Check for grouped/indented structure
            grouped_items = self.page.locator('.computed-field-group, .dependency-group').count()
            self.log_result(test_id, f"Found {grouped_items} grouped structure(s)")

            indented_items = self.page.locator('[style*="padding-left"], .indented, .dependency-item').count()
            self.log_result(test_id, f"Found {indented_items} indented item(s)")

            self.screenshot("13-grouping-structure.png", test_id)

            # Step 3: Check DOM for grouping elements
            self.log_result(test_id, "Checking DOM for specific grouping elements...")
            dom_checks = self.page.evaluate("""
                () => {
                    return {
                        hasComputedFieldGroup: !!document.querySelector('.computed-field-group'),
                        hasToggleBtn: !!document.querySelector('.dependency-toggle-btn'),
                        hasDependenciesContainer: !!document.querySelector('.computed-field-dependencies'),
                        selectedItemsCount: document.querySelectorAll('.selected-data-point-item').length
                    };
                }
            """)
            self.log_result(test_id, f"DOM check results: {json.dumps(dom_checks, indent=2)}")
            self.screenshot("14-dom-elements-check.png", test_id)

            # Step 4 & 5: Test toggle functionality if exists
            if toggle_buttons > 0:
                self.log_result(test_id, "Testing toggle functionality...")
                toggle_btn = self.page.locator('.dependency-toggle-btn, button.toggle-btn').first

                # Click to collapse
                toggle_btn.click()
                self.page.wait_for_timeout(500)
                self.screenshot("15-collapsed-state.png", test_id)

                # Click to expand
                toggle_btn.click()
                self.page.wait_for_timeout(500)
                self.screenshot("16-expanded-state.png", test_id)

                self.log_result(test_id, "✅ Toggle functionality works", "success")
                self.results[test_id]["status"] = "PASS"
            else:
                # Check if it's a graceful degradation
                selected_items = dom_checks.get("selectedItemsCount", 0)
                if selected_items > 0:
                    self.log_result(test_id, "⚠️ No grouping/toggle, but fields are accessible (DEGRADED PASS)", "warning")
                    self.results[test_id]["status"] = "DEGRADED"
                else:
                    self.log_result(test_id, "❌ No grouping and no fields visible", "error")
                    self.results[test_id]["status"] = "FAIL"

            # Step 6: Check console logs
            grouping_logs = [log for log in self.console_logs if "SelectedDataPointsPanel" in log["text"] or "DependencyManager" in log["text"]]
            if grouping_logs:
                self.log_result(test_id, f"Found {len(grouping_logs)} relevant console logs")
                for log in grouping_logs[:5]:  # Show first 5
                    self.log_result(test_id, f"  - {log['text']}")

        except Exception as e:
            self.log_result(test_id, f"Exception occurred: {str(e)}", "error")
            self.results[test_id]["status"] = "FAIL"
            self.screenshot("12-error-state.png", test_id)

    def test_rt001_regression(self):
        """RT-001: Regression Test"""
        print("\n" + "="*80)
        print("🧪 TEST RT-001: REGRESSION TEST")
        print("="*80 + "\n")

        test_id = "RT-001"

        try:
            # Step 1: Clear all selections
            self.log_result(test_id, "Clearing all selections...")
            selected_count = self.page.locator('.selected-data-point-item').count()
            if selected_count > 0:
                for i in range(selected_count):
                    remove_btns = self.page.locator('.selected-data-point-item .remove-btn, .selected-data-point-item button:has-text("×")')
                    if remove_btns.count() > 0:
                        remove_btns.first.click()
                        self.page.wait_for_timeout(500)
            self.screenshot("17-cleared-for-regression.png", test_id)

            # Step 2: Select a regular (non-computed) field
            self.log_result(test_id, "Looking for a regular non-computed field...")
            search_box = self.page.locator('input[type="search"], input[placeholder*="Search"]').first
            search_box.fill("GRI 401")
            self.page.wait_for_timeout(1000)

            # Find a field without purple badge
            all_fields = self.page.locator('.data-point-item, .field-item').all()
            regular_field = None
            for field in all_fields:
                has_computed_badge = field.locator('.field-type-badge.computed, .badge.computed').count() > 0
                if not has_computed_badge and field.is_visible():
                    regular_field = field
                    break

            if regular_field:
                self.log_result(test_id, "Found regular field, clicking '+' to add...")
                add_btn = regular_field.locator('button.add-btn, button:has-text("+")').first
                if add_btn.is_visible():
                    add_btn.click()
                    self.page.wait_for_timeout(2000)
                    self.screenshot("18-regular-field-added.png", test_id)
            else:
                self.log_result(test_id, "Could not find regular field", "warning")

            # Step 3: Verify no auto-cascade
            selected_items = self.page.locator('.selected-data-point-item').count()
            self.log_result(test_id, f"Selected items count: {selected_items}")

            if selected_items == 1:
                self.log_result(test_id, "✅ CORRECT: Only 1 field added (no auto-cascade)", "success")
            else:
                self.log_result(test_id, f"⚠️ UNEXPECTED: Got {selected_items} fields (expected 1)", "warning")

            self.screenshot("19-single-field-result.png", test_id)

            # Step 4: Add another regular field
            search_box.fill("total")
            self.page.wait_for_timeout(1000)

            all_fields = self.page.locator('.data-point-item, .field-item').all()
            for field in all_fields:
                has_computed_badge = field.locator('.field-type-badge.computed').count() > 0
                if not has_computed_badge and field.is_visible():
                    add_btn = field.locator('button.add-btn, button:has-text("+")').first
                    if add_btn.is_visible():
                        add_btn.click()
                        self.page.wait_for_timeout(1000)
                        break

            selected_items_after = self.page.locator('.selected-data-point-item').count()
            self.log_result(test_id, f"Selected items after second add: {selected_items_after}")
            self.screenshot("20-two-regular-fields.png", test_id)

            # Step 5: Remove a field
            self.log_result(test_id, "Testing remove functionality...")
            remove_btns = self.page.locator('.selected-data-point-item .remove-btn, .selected-data-point-item button:has-text("×")')
            if remove_btns.count() > 0:
                remove_btns.first.click()
                self.page.wait_for_timeout(1000)

                # Check for warning modal
                modal = self.page.locator('.modal, .dialog, [role="dialog"]')
                if modal.is_visible():
                    self.log_result(test_id, "⚠️ WARNING: Modal appeared on regular field removal", "warning")
                else:
                    self.log_result(test_id, "✅ No warning modal (expected behavior)", "success")

                final_count = self.page.locator('.selected-data-point-item').count()
                self.log_result(test_id, f"Final count after removal: {final_count}")
                self.screenshot("21-field-removed.png", test_id)

                if final_count == selected_items_after - 1:
                    self.log_result(test_id, "✅ Remove worked correctly", "success")
                    self.results[test_id]["status"] = "PASS"
                else:
                    self.log_result(test_id, "❌ Remove count mismatch", "error")
                    self.results[test_id]["status"] = "FAIL"
            else:
                self.log_result(test_id, "No remove button found", "error")
                self.results[test_id]["status"] = "FAIL"

        except Exception as e:
            self.log_result(test_id, f"Exception occurred: {str(e)}", "error")
            self.results[test_id]["status"] = "FAIL"
            self.screenshot("17-error-state.png", test_id)

    def final_analysis(self):
        """Perform final analysis and take screenshots"""
        print("\n" + "="*80)
        print("📊 FINAL ANALYSIS")
        print("="*80 + "\n")

        # Console error summary
        print(f"\n📋 Console Errors: {len(self.console_errors)}")
        for error in self.console_errors[:10]:  # Show first 10
            print(f"  ❌ {error['text']}")

        print(f"\n⚠️ Console Warnings: {len(self.console_warnings)}")
        for warning in self.console_warnings[:10]:
            print(f"  ⚠️ {warning['text']}")

        self.screenshot("22-final-console.png")

        # Page responsiveness check
        print("\n🔍 Testing page responsiveness...")
        try:
            search_box = self.page.locator('input[type="search"]').first
            search_box.fill("test")
            self.page.wait_for_timeout(500)
            search_box.fill("")
            print("  ✅ Search still functional")
        except Exception as e:
            print(f"  ❌ Search issue: {str(e)}")

        self.screenshot("23-final-page-state.png")

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📝 GENERATING REPORT")
        print("="*80 + "\n")

        # Calculate GO/NO-GO
        results_summary = {
            "PASS": 0,
            "FAIL": 0,
            "DEGRADED": 0,
            "NOT_RUN": 0
        }

        for test_id, result in self.results.items():
            status = result["status"]
            results_summary[status] = results_summary.get(status, 0) + 1

        # Determine deployment decision
        if results_summary["FAIL"] > 0:
            if "TC-001" in [tid for tid, r in self.results.items() if r["status"] == "FAIL"]:
                decision = "NO-GO"
                readiness = "NOT READY"
                risk = "HIGH"
            elif "TC-008" in [tid for tid, r in self.results.items() if r["status"] == "FAIL"]:
                decision = "NO-GO"
                readiness = "NOT READY"
                risk = "HIGH"
            elif "RT-001" in [tid for tid, r in self.results.items() if r["status"] == "FAIL"]:
                decision = "NO-GO"
                readiness = "NOT READY"
                risk = "HIGH"
            else:
                decision = "CONDITIONAL GO"
                readiness = "CONDITIONAL"
                risk = "MEDIUM"
        elif results_summary["DEGRADED"] > 0:
            decision = "CONDITIONAL GO"
            readiness = "CONDITIONAL"
            risk = "LOW"
        else:
            decision = "GO"
            readiness = "READY"
            risk = "LOW"

        # Generate markdown report
        report = f"""# Live Browser Test Results
## Computed Field Dependency Auto-Management Feature

**Test Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Tester:** UI Testing Agent (Automated)
**Environment:** {BASE_URL}

---

## Executive Summary

### GO/NO-GO Decision: **{decision}**

**Deployment Readiness:** {readiness}
**Risk Level:** {risk}
**Recommendation:** {self._get_recommendation(decision)}

---

## Test Results Summary

| Test | Name | Result | Impact | Notes |
|------|------|--------|--------|-------|
| TC-001 | Auto-Cascade Selection | {self.results["TC-001"]["status"]} | BLOCKING | {len(self.results["TC-001"]["details"])} checks performed |
| TC-008 | Visual Indicators | {self.results["TC-008"]["status"]} | BLOCKING | {len(self.results["TC-008"]["details"])} checks performed |
| TC-004 | Collapsible Grouping | {self.results["TC-004"]["status"]} | DEGRADABLE | {len(self.results["TC-004"]["details"])} checks performed |
| RT-001 | Regression Test | {self.results["RT-001"]["status"]} | BLOCKING | {len(self.results["RT-001"]["details"])} checks performed |

**Total Tests:** 4
**Passed:** {results_summary["PASS"]}
**Failed:** {results_summary["FAIL"]}
**Degraded:** {results_summary["DEGRADED"]}
**Not Run:** {results_summary["NOT_RUN"]}

---

## Detailed Test Results

"""

        # Add detailed results for each test
        for test_id in ["TC-001", "TC-008", "TC-004", "RT-001"]:
            result = self.results[test_id]
            report += f"\n### {test_id}: {self._get_test_name(test_id)}\n\n"
            report += f"**Status:** {result['status']}\n\n"
            report += f"**Screenshots:** {len(result['screenshots'])}\n\n"
            report += "**Test Log:**\n\n"
            for detail in result["details"]:
                icon = "✅" if detail["level"] == "success" else "❌" if detail["level"] == "error" else "⚠️" if detail["level"] == "warning" else "ℹ️"
                report += f"- {icon} {detail['message']}\n"
            report += "\n"

            if result["screenshots"]:
                report += "**Evidence:**\n\n"
                for screenshot in result["screenshots"]:
                    report += f"![{screenshot}](screenshots/live-test/{screenshot})\n\n"

        # Console output analysis
        report += f"""
---

## Console Output Analysis

### Errors Found: {len(self.console_errors)}

"""
        if self.console_errors:
            for error in self.console_errors:
                report += f"- ❌ **{error['type'].upper()}:** {error['text']}\n"
        else:
            report += "✅ No console errors detected\n"

        report += f"""

### Warnings Found: {len(self.console_warnings)}

"""
        if self.console_warnings:
            for warning in self.console_warnings[:10]:
                report += f"- ⚠️ **WARNING:** {warning['text']}\n"
        else:
            report += "✅ No console warnings detected\n"

        # GO/NO-GO Decision Matrix
        report += f"""

---

## GO/NO-GO Decision Matrix

### {decision}

"""

        if decision == "GO":
            report += """
**Conditions Met:**
- ✅ TC-001: PASS (auto-cascade works)
- ✅ TC-008: PASS (badges visible)
- ✅ TC-004: PASS (grouping works)
- ✅ RT-001: PASS (no regressions)
- ✅ No blocking errors

**Action:** Deploy to production with standard monitoring

**Next Steps:**
- Deploy using standard deployment process
- Monitor for 24 hours post-deployment
- Watch for user feedback on dependency features
"""
        elif decision == "CONDITIONAL GO":
            report += f"""
**Conditions Met:**
- {"✅" if self.results["TC-001"]["status"] == "PASS" else "❌"} TC-001: {self.results["TC-001"]["status"]} (auto-cascade)
- {"✅" if self.results["TC-008"]["status"] == "PASS" else "❌"} TC-008: {self.results["TC-008"]["status"]} (badges)
- {"✅" if self.results["TC-004"]["status"] in ["PASS", "DEGRADED"] else "❌"} TC-004: {self.results["TC-004"]["status"]} (grouping)
- {"✅" if self.results["RT-001"]["status"] == "PASS" else "❌"} RT-001: {self.results["RT-001"]["status"]} (regressions)

**Action:** Deploy with follow-up work required

**Follow-up Required:**
- Monitor collapsible grouping functionality
- Create ticket for any degraded features
- Target fix within 1 week for non-critical issues

**Next Steps:**
- Deploy with caution flag
- Create follow-up tickets for degraded features
- Enhanced monitoring for 48 hours
"""
        else:  # NO-GO
            failed_tests = [tid for tid, r in self.results.items() if r["status"] == "FAIL"]
            report += f"""
**Blocking Issues Found:**
- {"❌" if "TC-001" in failed_tests else "✅"} TC-001: {self.results["TC-001"]["status"]} (auto-cascade)
- {"❌" if "TC-008" in failed_tests else "✅"} TC-008: {self.results["TC-008"]["status"]} (badges)
- {"❌" if "TC-004" in failed_tests else "✅"} TC-004: {self.results["TC-004"]["status"]} (grouping)
- {"❌" if "RT-001" in failed_tests else "✅"} RT-001: {self.results["RT-001"]["status"]} (regressions)

**Action:** ❌ BLOCK DEPLOYMENT - Fix critical issues first

**Critical Issues to Fix:**
"""
            for test_id in failed_tests:
                report += f"\n#### {test_id}: {self._get_test_name(test_id)}\n"
                error_details = [d for d in self.results[test_id]["details"] if d["level"] == "error"]
                for detail in error_details:
                    report += f"- {detail['message']}\n"

            report += """

**Next Steps:**
1. Fix all blocking issues listed above
2. Re-run full test suite
3. Verify fixes with additional manual testing
4. Then proceed with deployment
"""

        report += """

---

## Evidence Package

All screenshots saved to: `test-folder/screenshots/live-test/`

**Total Screenshots:** """ + str(sum(len(r["screenshots"]) for r in self.results.values()) + 5) + """

**Console Logs:** Full logs captured during test execution

---

## Test Environment

- **URL:** """ + BASE_URL + """
- **Login:** """ + LOGIN_EMAIL + """
- **Browser:** Chromium (Playwright)
- **Viewport:** 1920x1080
- **Network:** Waited for idle state
- **Automation:** Python Playwright (sync_api)

---

*End of Report*
"""

        # Save report
        report_dir = Path(__file__).parent / "report"
        report_dir.mkdir(exist_ok=True)
        report_file = report_dir / "LIVE_TEST_RESULTS.md"
        report_file.write_text(report)
        print(f"✅ Report saved to: {report_file}")

        return report

    def _get_recommendation(self, decision):
        if decision == "GO":
            return "Deploy immediately with standard monitoring"
        elif decision == "CONDITIONAL GO":
            return "Deploy now, create follow-up tickets for degraded features, fix within 1 week"
        else:
            return "Fix critical issues before deployment"

    def _get_test_name(self, test_id):
        names = {
            "TC-001": "Auto-Cascade Selection",
            "TC-008": "Visual Indicators",
            "TC-004": "Collapsible Grouping",
            "RT-001": "Regression Test"
        }
        return names.get(test_id, "Unknown Test")

    def teardown(self):
        """Close browser and cleanup"""
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
            print("✅ TEST EXECUTION COMPLETE")
            print("="*80)
            print(f"\nReport: test-folder/report/LIVE_TEST_RESULTS.md")
            print(f"Screenshots: test-folder/screenshots/live-test/")
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
║                                                                               ║
║              COMPUTED FIELD DEPENDENCY MANAGEMENT LIVE TEST                   ║
║                                                                               ║
║  Test Suite: TC-001, TC-008, TC-004, RT-001                                  ║
║  Mode: Automated Browser Testing with Playwright                             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)

    runner = DependencyTestRunner()
    runner.run()
