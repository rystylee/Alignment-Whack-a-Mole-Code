#!/usr/bin/env python3
"""
Base class for formatting rules

This module provides the base class used by both Japanese and English formatters.
"""

from typing import List


class FormattingRule:
    """
    Base class for formatting rules
    """

    def __init__(self, name: str, priority: int):
        """
        Initialize formatting rule

        Args:
            name: Rule identifier
            priority: Execution priority (lower = earlier)
        """
        self.name = name
        self.priority = priority
        self.changes = []  # Track changes made by this rule

    def apply(self, text: str) -> str:
        """
        Apply the rule to text

        Args:
            text: Input text

        Returns:
            Transformed text
        """
        raise NotImplementedError(f"Rule {self.name} must implement apply()")

    def log_change(self, line_num: int, before: str, after: str):
        """
        Record a change made by this rule

        Args:
            line_num: Line number where change occurred (1-indexed)
            before: Text before transformation
            after: Text after transformation
        """
        self.changes.append({"line": line_num, "before": before, "after": after})

    def get_change_summary(self) -> str:
        """
        Get a summary of changes made by this rule

        Returns:
            Summary string describing the changes
        """
        if not self.changes:
            return f"✓ {self.name}: No changes"
        return f"✓ {self.name}: {len(self.changes)} change(s)"

    def get_detailed_changes(self, max_display: int = 10) -> List[str]:
        """
        Get detailed list of changes

        Args:
            max_display: Maximum number of changes to display

        Returns:
            List of formatted change descriptions
        """
        details = []
        for change in self.changes[:max_display]:
            details.append(f"  - Line {change['line']}: \"{change['before']}\" → \"{change['after']}\"")

        if len(self.changes) > max_display:
            details.append(f"  ... and {len(self.changes) - max_display} more change(s)")

        return details

    def reset_changes(self):
        """Reset the change log"""
        self.changes = []
