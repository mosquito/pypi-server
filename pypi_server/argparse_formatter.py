from __future__ import annotations

import argparse

import rich.console
import rich.markdown
import rich.text
import rich_argparse


class MarkdownDescriptionRichHelpFormatter(rich_argparse.RichHelpFormatter):

    styles = dict(
        **{"argparse.env": "bright_magenta"},
        **rich_argparse.RichHelpFormatter.styles
    )

    highlights = (
        r"(?:^|\s)(?P<args>-{1,2}[\w]+[\w-]*)",
        r"'(?P<syntax>[^`]*)'",
        r"\[(?P<syntax>ENV:).*\]",
        r"ENV: (?P<env>[A-Z_]+)",
        r"\((?P<args>default: \S+)\)",
    )

    def add_text(self, text: str | None) -> None:
        if text is argparse.SUPPRESS or text is None:
            return
        self._current_section.rich_items.append(rich.markdown.Markdown(text))
