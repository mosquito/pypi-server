import io
import os
import sys

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

    def _rich_format_text(self, text: str) -> rich.text.Text:
        with io.StringIO() as fp:
            console = rich.console.Console(
                file=fp,
                force_terminal=os.isatty(sys.stdout.fileno()),
                stderr=True,
                width=self._width,
            )
            console.print(rich.markdown.Markdown(text, hyperlinks=True))
            return rich.text.Text(fp.getvalue())
