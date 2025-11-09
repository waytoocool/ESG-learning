"""
GitHub Integration Service for Issue Reporting System.

This module provides GitHub API integration for automatically creating GitHub issues
from user-reported bugs and feature requests. It handles issue creation, formatting,
and synchronization status tracking.

Key Features:
- Automatic GitHub issue creation from IssueReport records
- Rich formatting of issue details, browser info, and debug data
- Error handling and graceful degradation
- Sync status tracking in database

Environment Variables Required:
- GITHUB_ENABLED: Enable/disable GitHub integration (default: False)
- GITHUB_TOKEN: GitHub personal access token with repo access
- GITHUB_REPO: Repository in format 'owner/repo-name'
- GITHUB_LABELS: Comma-separated list of labels to apply (default: 'bug,user-reported')
"""

import os
from datetime import datetime, UTC
from flask import current_app

try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    # Note: PyGithub not installed - GitHub integration will be disabled


class GitHubService:
    """
    Service for creating and managing GitHub issues from user reports.

    This service handles the complete lifecycle of syncing IssueReport records
    to GitHub issues, including formatting, error handling, and status tracking.
    """

    def __init__(self):
        """Initialize GitHub service with configuration from environment variables."""
        self.enabled = os.getenv('GITHUB_ENABLED', 'false').lower() == 'true'
        self.token = os.getenv('GITHUB_TOKEN', '')
        self.repo_name = os.getenv('GITHUB_REPO', '')
        self.labels = os.getenv('GITHUB_LABELS', 'bug,user-reported').split(',')

        self.github_client = None
        self.repo = None

        # Only initialize if enabled and dependencies available
        if self.enabled and GITHUB_AVAILABLE:
            if not self.token or not self.repo_name:
                current_app.logger.error(
                    "GitHub integration enabled but GITHUB_TOKEN or GITHUB_REPO not configured"
                )
                self.enabled = False
            else:
                try:
                    self.github_client = Github(self.token)
                    self.repo = self.github_client.get_repo(self.repo_name)
                    current_app.logger.info(f"GitHub service initialized for repo: {self.repo_name}")
                except Exception as e:
                    current_app.logger.error(f"Failed to initialize GitHub client: {str(e)}")
                    self.enabled = False
        elif self.enabled and not GITHUB_AVAILABLE:
            current_app.logger.warning(
                "GitHub integration enabled but PyGithub not installed. "
                "Run: pip install PyGithub"
            )
            self.enabled = False

    def create_issue(self, issue_report):
        """
        Create a GitHub issue from an IssueReport record.

        Args:
            issue_report (IssueReport): The issue report to sync to GitHub

        Returns:
            dict: Result dictionary with the following structure:
                {
                    'success': bool,
                    'issue_number': int (if successful),
                    'issue_url': str (if successful),
                    'error': str (if failed)
                }

        Side Effects:
            - Updates issue_report with GitHub details on success
            - Updates github_sync_status to 'synced' or 'failed'
            - Commits changes to database
        """
        from ..extensions import db

        if not self.enabled:
            current_app.logger.debug("GitHub integration disabled, skipping issue creation")
            issue_report.github_sync_status = 'failed'
            issue_report.github_sync_error = 'GitHub integration is disabled'
            db.session.commit()
            return {
                'success': False,
                'error': 'GitHub integration is disabled'
            }

        try:
            # Format issue title with ticket number
            title = f"[{issue_report.ticket_number}] {issue_report.title}"

            # Format comprehensive issue body
            body = self._format_issue_body(issue_report)

            # Determine labels based on category and severity
            issue_labels = self._determine_labels(issue_report)

            # Create GitHub issue
            current_app.logger.info(f"Creating GitHub issue for ticket {issue_report.ticket_number}")
            github_issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=issue_labels
            )

            # Update issue report with GitHub details
            issue_report.github_issue_id = github_issue.id
            issue_report.github_issue_number = github_issue.number
            issue_report.github_issue_url = github_issue.html_url
            issue_report.github_sync_status = 'synced'
            issue_report.github_sync_error = None
            issue_report.github_synced_at = datetime.now(UTC)

            db.session.commit()

            current_app.logger.info(
                f"Successfully created GitHub issue #{github_issue.number} "
                f"for ticket {issue_report.ticket_number}"
            )

            return {
                'success': True,
                'issue_number': github_issue.number,
                'issue_url': github_issue.html_url
            }

        except GithubException as e:
            error_message = f"GitHub API error: {str(e)}"
            current_app.logger.error(
                f"Failed to create GitHub issue for ticket {issue_report.ticket_number}: {error_message}"
            )

            issue_report.github_sync_status = 'failed'
            issue_report.github_sync_error = error_message
            db.session.commit()

            return {
                'success': False,
                'error': error_message
            }

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            current_app.logger.error(
                f"Unexpected error creating GitHub issue for ticket {issue_report.ticket_number}: "
                f"{error_message}"
            )

            issue_report.github_sync_status = 'failed'
            issue_report.github_sync_error = error_message
            db.session.commit()

            return {
                'success': False,
                'error': error_message
            }

    def _format_issue_body(self, issue_report):
        """
        Format comprehensive issue body for GitHub issue creation.

        Args:
            issue_report (IssueReport): The issue report to format

        Returns:
            str: Markdown-formatted issue body
        """
        body_parts = [
            f"## Issue Report: {issue_report.ticket_number}",
            "",
            "### Metadata",
            f"- **Category:** {issue_report.category.replace('_', ' ').title()}",
            f"- **Severity:** {issue_report.severity.title()}",
            f"- **Reported by:** {issue_report.user.name if issue_report.user else 'Unknown'} "
            f"({issue_report.user.email if issue_report.user else 'N/A'})",
            f"- **Company:** {issue_report.company.name if issue_report.company else 'N/A'}",
            f"- **Date:** {issue_report.created_at.strftime('%Y-%m-%d %H:%M UTC') if issue_report.created_at else 'N/A'}",
            "",
            "### Description",
            issue_report.description or "No description provided",
            ""
        ]

        # Add steps to reproduce if provided
        if issue_report.steps_to_reproduce:
            body_parts.extend([
                "### Steps to Reproduce",
                issue_report.steps_to_reproduce,
                ""
            ])

        # Add expected behavior if provided
        if issue_report.expected_behavior:
            body_parts.extend([
                "### Expected Behavior",
                issue_report.expected_behavior,
                ""
            ])

        # Add actual behavior if provided
        if issue_report.actual_behavior:
            body_parts.extend([
                "### Actual Behavior",
                issue_report.actual_behavior,
                ""
            ])

        # Add environment details
        body_parts.extend([
            "### Environment Details",
            f"- **Page URL:** {issue_report.page_url or 'N/A'}",
            f"- **Page Title:** {issue_report.page_title or 'N/A'}",
        ])

        # Add browser information
        if issue_report.browser_info:
            browser_info = self._format_browser_info(issue_report.browser_info)
            body_parts.extend(browser_info)

        body_parts.extend([
            f"- **Screen Resolution:** {issue_report.screen_resolution or 'N/A'}",
            f"- **Viewport Size:** {issue_report.viewport_size or 'N/A'}",
            ""
        ])

        # Add console errors if available
        if issue_report.console_errors:
            console_errors_str = self._format_console_errors(issue_report.console_errors)
            body_parts.extend([
                "### Console Errors",
                "```",
                console_errors_str,
                "```",
                ""
            ])

        # Add API history if available
        if issue_report.api_history:
            api_history_str = self._format_api_history(issue_report.api_history)
            body_parts.extend([
                "### Recent API Calls",
                "```",
                api_history_str,
                "```",
                ""
            ])

        # Add user actions if available
        if issue_report.user_actions:
            user_actions_str = self._format_user_actions(issue_report.user_actions)
            body_parts.extend([
                "### Recent User Actions",
                "```",
                user_actions_str,
                "```",
                ""
            ])

        # Add screenshot information if available
        if issue_report.screenshot_path:
            body_parts.extend([
                "### Screenshot",
                f"Screenshot saved at: `{issue_report.screenshot_path}`",
                ""
            ])

        # Add internal tracking information
        body_parts.extend([
            "---",
            "### Internal Tracking",
            f"- **Ticket Number:** {issue_report.ticket_number}",
            f"- **Internal ID:** {issue_report.id}",
            f"- **Status:** {issue_report.status}",
        ])

        return "\n".join(body_parts)

    def _format_browser_info(self, browser_info):
        """
        Format browser information for display.

        Args:
            browser_info (dict): Browser information dictionary

        Returns:
            list: List of formatted strings
        """
        lines = []
        if browser_info.get('name'):
            version = browser_info.get('version', '')
            lines.append(f"- **Browser:** {browser_info['name']} {version}")
        if browser_info.get('platform'):
            lines.append(f"- **Platform:** {browser_info['platform']}")
        if browser_info.get('language'):
            lines.append(f"- **Language:** {browser_info['language']}")
        if browser_info.get('user_agent'):
            lines.append(f"- **User Agent:** {browser_info['user_agent'][:100]}...")

        return lines

    def _format_console_errors(self, errors):
        """
        Format console errors for display (limit to 10 most recent).

        Args:
            errors (list): List of error objects

        Returns:
            str: Formatted error string
        """
        if not errors:
            return "No console errors captured"

        formatted_errors = []
        for error in errors[:10]:  # Limit to 10 most recent
            timestamp = error.get('timestamp', 'N/A')
            level = error.get('level', 'ERROR')
            message = error.get('message', '')
            formatted_errors.append(f"[{timestamp}] {level}: {message}")

        if len(errors) > 10:
            formatted_errors.append(f"\n... and {len(errors) - 10} more errors")

        return "\n".join(formatted_errors)

    def _format_api_history(self, history):
        """
        Format API call history for display (limit to 10 most recent).

        Args:
            history (list): List of API call objects

        Returns:
            str: Formatted API history string
        """
        if not history:
            return "No API history captured"

        formatted_calls = []
        for call in history[:10]:  # Limit to 10 most recent
            status = call.get('status', 'N/A')
            method = call.get('method', 'GET')
            url = call.get('url', 'N/A')
            timestamp = call.get('timestamp', 'N/A')
            formatted_calls.append(f"[{timestamp}] {method} {url} - Status: {status}")

        if len(history) > 10:
            formatted_calls.append(f"\n... and {len(history) - 10} more API calls")

        return "\n".join(formatted_calls)

    def _format_user_actions(self, actions):
        """
        Format user action history for display (limit to 10 most recent).

        Args:
            actions (list): List of user action objects

        Returns:
            str: Formatted user actions string
        """
        if not actions:
            return "No user actions captured"

        formatted_actions = []
        for action in actions[:10]:  # Limit to 10 most recent
            timestamp = action.get('timestamp', 'N/A')
            action_type = action.get('type', 'unknown')

            # Extract target information from element field if present
            target = 'N/A'
            if action.get('element'):
                element = action['element']
                target_parts = []
                if element.get('tagName'):
                    target_parts.append(element['tagName'])
                if element.get('id'):
                    target_parts.append(f"#{element['id']}")
                if element.get('className'):
                    # Get first class name if multiple
                    class_name = element['className'].split()[0] if element['className'] else ''
                    if class_name:
                        target_parts.append(f".{class_name}")
                if element.get('text'):
                    target_parts.append(f'"{element["text"][:30]}..."' if len(element['text']) > 30 else f'"{element["text"]}"')
                target = ' '.join(target_parts) if target_parts else 'N/A'
            elif action.get('target'):
                # Fallback to 'target' field if present (for backward compatibility)
                target = action['target']
            elif action.get('url'):
                # For navigation actions
                target = action.get('url', 'N/A')

            formatted_actions.append(f"[{timestamp}] {action_type}: {target}")

        if len(actions) > 10:
            formatted_actions.append(f"\n... and {len(actions) - 10} more actions")

        return "\n".join(formatted_actions)

    def _determine_labels(self, issue_report):
        """
        Determine GitHub labels based on issue category and severity.

        Args:
            issue_report (IssueReport): The issue report

        Returns:
            list: List of label strings
        """
        labels = list(self.labels)  # Start with default labels

        # Add category-based labels
        category_label_map = {
            'bug': 'bug',
            'feature_request': 'enhancement',
            'help': 'question',
            'other': 'needs-triage'
        }
        category_label = category_label_map.get(issue_report.category)
        if category_label and category_label not in labels:
            labels.append(category_label)

        # Add severity-based labels
        severity_label_map = {
            'critical': 'priority:critical',
            'high': 'priority:high',
            'medium': 'priority:medium',
            'low': 'priority:low'
        }
        severity_label = severity_label_map.get(issue_report.severity)
        if severity_label:
            labels.append(severity_label)

        return labels


# Create singleton instance
_github_service = None


def get_github_service():
    """
    Get or create the GitHub service singleton instance.

    Returns:
        GitHubService: The GitHub service instance
    """
    global _github_service
    if _github_service is None:
        _github_service = GitHubService()
    return _github_service
