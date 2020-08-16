"""
Extract release notes for the given tag
"""

from __future__ import absolute_import, unicode_literals

import argparse
import io
import logging
import os
import re
import sys

from packaging import version as versiontool

logger = logging.getLogger(__name__)

GENERIC_MESSAGE = """
This release was automatically generated by the release pipeline.
""".strip()


def iterate_until_version(infile, version):
  """Read lines from `infile` until we have parsed a version heading in the
  form of::

    ---------
    v##.##.##
    ---------

  at which point the next line from `infile` will be the first line after the
  heading."""

  history = []
  ruler = re.compile("^-+$")

  for line in infile:
    line = line.rstrip()
    history.append(line)

    if len(history) < 3:
      continue

    try:
      line_version = versiontool.parse(history[-2].strip().rstrip("v"))
    except versiontool.InvalidVersion:
      continue

    if (ruler.match(history[-3]) and
        ruler.match(history[-1]) and
        (version is None or
         line_version.base_version == version.base_version)):
      break

    if len(history) > 3:
      for buffered_line in history[:-3]:
        yield buffered_line
      history = history[-3:]

  for buffered_line in history:
    yield buffered_line


def get_note_text(infile_path, versionstr):
  try:
    version = versiontool.parse(versionstr)
  except versiontool.InvalidVersion:
    return GENERIC_MESSAGE

  with io.open(infile_path, "r", encoding="utf-8") as infile:
    for _ in iterate_until_version(infile, version):
      pass

    lines = list(iterate_until_version(infile, None))
    content = "\n".join(lines[:-3])
    return re.sub(r"(\S)\n(\S)", r"\1\2", content).strip()


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("infile_path")
  parser.add_argument("version")
  parser.add_argument("-o", "--outfile-path", default="-")

  args = parser.parse_args()

  if args.outfile_path == "-":
    args.outfile_path = os.dup(sys.stdout.fileno())
  with io.open(args.outfile_path, "w", encoding="utf-8") as outfile:
    outfile.write(get_note_text(args.infile_path, args.version))
    outfile.write("\n")


if __name__ == "__main__":
  main()