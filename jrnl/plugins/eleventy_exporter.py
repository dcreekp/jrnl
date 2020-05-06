#!/usr/bin/env python
# encoding: utf-8

from .text_exporter import TextExporter
import os
import re
import sys
from ..util import slugify
from ..util import WARNING_COLOR, ERROR_COLOR, RESET_COLOR


class EleventyExporter(TextExporter):
    """This Exporter can convert entries and journals into Markdown formatted
    text with YAML front matter specifically for 11ty."""

    names = ["11ty"]
    extension = "md"

    @classmethod
    def make_filename(cls, entry):
        return f'{ slugify(str(entry.title)) }.{ cls.extension }'

    @classmethod
    def export_entry(cls, entry, to_multifile=True):
        """Returns a markdown representation of a single entry, with YAML front matter."""
        if to_multifile is False:
            print(
                f"{ERROR_COLOR}ERROR{RESET_COLOR}: YAML export must be to individual files. Please \
                specify a directory to export to.",
                file=sys.stderr,
            )
            return

        date_str = entry.date.strftime(entry.journal.config["timeformat"])
        body_wrapper = "\n" if entry.body else ""
        body = body_wrapper + entry.body

        tagsymbols = entry.journal.config["tagsymbols"]
        # see also Entry.Entry.rag_regex
        multi_tag_regex = re.compile(fr"(?u)^\s*([{tagsymbols}][-+*#/\w]+\s*)+$")

        """Increase heading levels in body text"""
        newbody = ""
        heading = "#"
        previous_line = ""
        warn_on_heading_level = False
        for line in body.splitlines(True):
            if re.match(r"^#+ ", line):
                """ATX style headings"""
                newbody = newbody + previous_line + heading + line
                if re.match(r"^#######+ ", heading + line):
                    warn_on_heading_level = True
                line = ""
            elif re.match(r"^=+$", line.rstrip()) and not re.match(
                r"^$", previous_line.strip()
            ):
                """Setext style H1"""
                newbody = newbody + heading + "# " + previous_line
                line = ""
            elif re.match(r"^-+$", line.rstrip()) and not re.match(
                r"^$", previous_line.strip()
            ):
                """Setext style H2"""
                newbody = newbody + heading + "## " + previous_line
                line = ""
            elif multi_tag_regex.match(line):
                """Tag only lines"""
                line = ""
            else:
                newbody = newbody + previous_line
            previous_line = line
        newbody = newbody + previous_line  # add very last line

        # make sure the export ends with a blank line
        if previous_line not in ["\r", "\n", "\r\n", "\n\r"]:
            newbody = newbody + os.linesep

        if warn_on_heading_level is True:
            print(
                "{}WARNING{}: Headings increased past H6 on export - {} {}".format(
                    WARNING_COLOR, RESET_COLOR, date_str, entry.title
                ),
                file=sys.stderr,
            )

        title = entry.title.replace('@', '').replace(':', '')
        tags = list(
            set([entry.journal.name] + [tag[1:] for tag in entry.tags])
        )
        permalink = f'{ entry.journal.name }/{ slugify(str(entry.title)) }/'

        return '---\ntitle: {title}\ndate: {date}\nstarred: {starred}\nlayout: "entries"\ntags: {tags}\npermalink: "{permalink}"\n\n---\n## {title}\n{body} {space}'.format(
            date=date_str,
            title=title,
            starred=entry.starred,
            tags=tags,
            permalink=permalink,
            body=newbody,
            space="",
        )

    @classmethod
    def export_journal(cls, journal):
        """Returns an error, as YAML export requires a directory as a target."""
        print(
            "{}ERROR{}: YAML export must be to individual files. Please specify a directory to export to.".format(
                ERROR_COLOR, RESET_COLOR
            ),
            file=sys.stderr,
        )
        return
