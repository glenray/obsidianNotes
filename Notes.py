import json
import os
from pathlib import Path
import re
import frontmatter


class Notes():
	def __init__(self, paths, excludePaths=None, recursive=True):
		self.recursive = recursive
		self.paths = self._processPaths(paths)
		self.excludePaths = self._processPaths(excludePaths)
		self.notes = []
		self.propTypes = Note.getPropTypes(self.paths)
		self.add_notes(self.paths, self.recursive)


	def __len__(self):
		return len(self.notes)


	def _processPaths(self, paths):
		if isinstance(paths, list) or paths == None:
			return paths
		elif isinstance(paths, Path):
			return [paths]
		else:
			raise ValueError(f"Parameter must be a Path object, a list of Path objects, or None. {paths} ({type(paths)}) given.")


	def _isExcluded(self, path: str) -> bool:
		"""Test whether path should be skipped as excluded

		Args:
			path:
				string of path to test for exclusion
		Returns bool:
			True: the path should be excluded

		"""
		if self.excludePaths == None:
			return False
		for excludedPath in self.excludePaths:
			if path.startswith(str(excludedPath)):
				return True
		return False


	def add_notes(self, paths, recursive = True):
		if isinstance(paths, Path):
			paths = [paths]
		for path in paths:
			assert path.exists(), f"file or folder does not exist: '{path}'"
			if path.is_dir():
				for root, _, files in os.walk(path):
					for f_name in files:
						pth_f = Path(root) / f_name
						if Note._is_md_file(pth_f) and not self._isExcluded(root):
							n = Note(pth_f, self.propTypes)
							# do not allow duplicate notes
							if n not in self.notes:
								self.notes.append(n)
					if not recursive:
						break
			elif Note._is_md_file(path):
				self.notes.append(Note(path=path))


class Note():
	''' A markdown note object
		Args:
			path: str | Path
				path to markdown file
			propTypes: dict | None
				dict: property types from obsidian types.json file
				None: indicates the note needs to generate its own
				propTypes dict, i.e. the note was not created by Notes
				class. The Notes class would have provided the propTypes
				dict.
	'''
	def __init__(self, path, propTypes=None):
		self.path = path
		if type(path) == str:
			self.path = Path(path)
		assert self._is_md_file(self.path), f"Path {self.path} \ndoes not exist or is not a markdown file."
		# load the file
		try:
			self.post = frontmatter.load(self.path)
		except:
			print(f"There was a problem parsing: {self.path.name}.\nSkipping: {self.path}")

		self.propTypes = Note.getPropTypes(self.path) if propTypes == None else propTypes


	def __eq__(self, other):
		return self.path == other.path


	@staticmethod
	def getPropTypes(path):
		if isinstance(path, Path):
			path = [path]
		typesFile = '.obsidian/types.json'
		attempt = None
		root = Path(path[0].root)
		cwd = path[0].parent if path[0].is_file() else path[0]
		while cwd != root:
			attempt = cwd/typesFile
			if attempt.exists():
				break
			cwd=cwd.parent
		if attempt != None:
			with open(attempt) as file:
				js = json.load(file)
			return js['types']
		else:
			return None

	@staticmethod
	def _is_md_file(path: Path | str) -> bool:
		''' is the file at path a markdown file?

			Args:
				path: str | Path

			Return:
				bool: True if the file is an markdown file

		'''
		if isinstance(path, str):
			path = Path(path)
		exist = path.exists()
		is_md = path.suffix == ".md"
		return exist and is_md


	def to_string(self) -> str:
		''' return the metadata and content as a string

			return: str
		'''
		content = frontmatter.dumps(self.post, encoding='utf-8', sort_keys=False, width=0, allow_unicode=True)
		return content


	def meta_to_string(self) -> str:
		''' Return meta data as a string

				return: str
					the metadata as a string
		'''
		# if there is no metadata, return false.
		if not self.post.metadata:
			return False
		boundry = "---"
		content = self.to_string()
		start_index = content.find(boundry+"\n") + len(boundry)+1
		end_index = content.find("\n"+boundry, start_index)
		meta_text = content[start_index:end_index]
		return meta_text


	def write(self, fileName: str | Path | None = None):
		'''write note to a file

			Args:
				filename: str | Path | None
					the file path to dump the note. None overwrites the originating
					file.
		'''
		# convert string to path
		if isinstance(fileName, str):
			fileName = Path(fileName)
		fn = self.path if fileName==None else fileName
		# if metadata exists
		if self.post.metadata:
			frontmatter.dump(self.post, fn, encoding='utf-8', sort_keys=False, allow_unicode=True)
		# If a document has no metadata, frontmatter.dump writes an empty 
		# metadata dict to the top of the document.
		# This prevents Obsidian from recognizing '---' typed by the user 
		# to trigger insertion of new properties. 
		# So, if the metadata is empty, write only the content without the empty dict.
		else:
			with open(fn, 'w', encoding='utf-8') as f:
				f.write("\n"+self.post.content)


	def has_meta(self, key: str, value: None | str = None):
		''' Return whether metadata key or key:value pair exists
			Args:
				key: str
					The metadata property key
				value: str | None
					The metadata value to match or None to match only the key
			Return:
				bool

		'''
		pm = self.post.metadata
		# does the property key exist
		if value == None:
			return key in pm
		
		# does the property key match a value
		if type(pm[key]) is list:
			return value in pm[key]
		else:
			return pm[key] == value


	def add(self, k, v=None, overwrite=False):
		''' Add metadata 

		Args:
			k string
				a new or existing property key
			v string, [], None. 
				if string, the value to assign to a key
				if [], initialize value with an empty list
				if None, create a new property without assigning a value.
			overwrite bool
				if True, overwrite the existing value
				if False, append the new value to the existing value,
				creating a list if necessary
		'''
		pm = self.post.metadata
		# adding a new property
		if not self.has_meta(k):
			pm[k] = v
		# modify existing list property
		else:
			# modify lists
			if type(pm[k]) is list:
				if v not in pm[k]:
					if overwrite:
						pm[k] = [v]
					else:
						pm[k].append(v)
			# modify scalar values
			else:
				# no duplicate values allowed.
				if pm[k] != v:
					if overwrite:
						pm[k] = v
					else:
						if pm[k]:
							pm[k] = [pm[k]]
							pm[k].append(v)
						else:
							pm[k] = v


	def remove(self, k, v=None, remove_key=False):
		''' Remove metadata
		Args:
			k string
				an existing metadata key. 
			v string | None
				the value to remove. If None, the enire key will be
				removed.
			remove_key bool
				if True, the entire key will be removed.

		If the key value is a list, the value will be removed from that list. All other property types will be set to None
		Empty lists will be set to None.
		'''
		pm = self.post.metadata
		# remove key completely
		if remove_key:
			if self.has_meta(k):
				del self.post.metadata[k]
		else:
			if self.has_meta(k):
				if type(pm[k]) is list:
					# remove value from list of
					if self.has_meta(k, v) and v != None:
						pm[k].remove(v)
						if len(pm[k]) == 0:
							pm[k] = None
				else:
					pm[k] = None
