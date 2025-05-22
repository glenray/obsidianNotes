''' Why import wsPatch
By default, frontmatter changes the white space in an
Obsidian note as follows:
- leading white space is removed and replaced by a single
new line after the metadata
- trailing white spce is removed.

This default behavior has some appeal. But, if you don't
want frontmatter to mess with you whitespace, importing this
file changes frontmatter's default behavior so that 
leading and trail whitespace are not altered.
'''

import codecs
import io
import re

from typing import TYPE_CHECKING, Any, Type, Iterable
import frontmatter
from frontmatter.util import u
from frontmatter.default_handlers import YAMLHandler, JSONHandler, TOMLHandler, BaseHandler

from frontmatter import parse, load, loads, dump, dumps, Post

# global handlers
handlers = [
	Handler()
	for Handler in [YAMLHandler, JSONHandler, TOMLHandler]
	if Handler is not None
]

DEFAULT_POST_TEMPLATE = """\
{start_delimiter}
{metadata}
{end_delimiter}{content}"""


# from Basehandler
def formatter(self, post: Post, **kwargs: object) -> str:
	"""
	Turn a post into a string, used in ``frontmatter.dumps``
	"""
	start_delimiter = kwargs.pop("start_delimiter", self.START_DELIMITER)
	end_delimiter = kwargs.pop("end_delimiter", self.END_DELIMITER)

	metadata = self.export(post.metadata, **kwargs)
	return DEFAULT_POST_TEMPLATE.format(
		metadata=metadata,
		content=post.content,
		start_delimiter=start_delimiter,
		end_delimiter=end_delimiter,
	# **GRP** ).strip()
	)


# from frontmatter
def parser(
	text: str,
	encoding: str = "utf-8",
	handler: BaseHandler | None = None,
	**defaults: object,
) -> tuple[dict[str, object], str]:
	"""
	Parse text with frontmatter, return metadata and content.
	Pass in optional metadata defaults as keyword args.

	If frontmatter is not found, returns an empty metadata dictionary
	(or defaults) and original text content.

	.. testsetup:: *

		>>> import frontmatter

	.. doctest::

		>>> with open('tests/yaml/hello-world.txt') as f:
		...     metadata, content = frontmatter.parse(f.read())
		>>> print(metadata['title'])
		Hello, world!

	"""
	# ensure unicode first
	# ** GRP ** text = u(text, encoding).strip()
	text = u(text, encoding)

	# metadata starts with defaults
	metadata = defaults.copy()

	# this will only run if a handler hasn't been set higher up
	handler = handler or detect_format(text, handlers)
	if handler is None:
		return metadata, text

	# split on the delimiters
	try:
		fm, content = handler.split(text)
	except ValueError:
		# if we can't split, bail
		return metadata, text

	# parse, now that we have frontmatter
	fm_data = handler.load(fm)
	if isinstance(fm_data, dict):
		metadata.update(fm_data)

	# ** GRP ** return metadata, content.strip()
	return metadata, content
	

# from BaseHandler
def split(self, text: str) -> tuple[str, str]:
	"""
	Split text into frontmatter and content
	"""
	self.FM_BOUNDARY = re.compile(r"^-{3,}$", re.MULTILINE)
	assert self.FM_BOUNDARY is not None
	_, fm, content = self.FM_BOUNDARY.split(text, 2)
	return fm, content


# YAMLHandler.FM_BOUNDARY = re.compile(r"^-{3,}$", re.MULTILINE)
BaseHandler.format = formatter
BaseHandler.split = split
frontmatter.parse = parser

