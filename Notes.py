import json
import os
from pathlib import Path
import frontmatter


class Notes():
	def __init__(self, paths, recursive=True):
		self.recursive = recursive
		self.paths = paths
		self.notes = []
		self.propTypes = Note.getVaultTypes(self.paths)
		self.add_notes(self.paths, self.recursive)


	def add_notes(self, paths, recursive = True):
		if isinstance(paths, Path):
			paths = [paths]
		for path in paths:
			assert path.exists(), f"file or folder does not exist: '{path}'"
			if path.is_dir():
				for root, _, files in os.walk(path):
					for f_name in files:
						pth_f = Path(root) / f_name
						if Note._is_md_file(pth_f):
							self.notes.append(Note(path=pth_f))
					if not recursive:
						break
			elif Note._is_md_file(path):
				self.notes.append(Note(path=path))


class Note():
	def __init__(self, path, vaultTypes=None):
		self.path = path
		self.post = frontmatter.load(self.path)
		self.vaultTypes = Note.getVaultTypes(self.path)
		

	@staticmethod
	def getVaultTypes(path):
		typesFile = '.obsidian/types.json'
		attempt = None
		root = Path(path.root)
		cwd = path.parent if path.is_file() else path
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
	def _is_md_file(path: Path):
		exist = path.exists()
		is_md = path.suffix == ".md"
		return exist and is_md


	def to_string(self):
		content = frontmatter.dumps(self.post, encoding='utf-8', sort_keys=False, width=0, allow_unicode=True)
		return content


	def write(self, fileName=None):
		fn = self.path if fileName==None else fileName
		frontmatter.dump(self.post, fn, encoding='utf-8', sort_keys=False, allow_unicode=True)


	def has_meta(self, key, value=None):
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
				pm[k] = v


	def removeKey(self, k):
		'''
		Remove a property completely
		'''
		if self.has_meta(k):
			del self.post.metadata[k]


	def removeValue(self, k, v=None):
		''' Remove a key's value
		If the key value is a list, the value will be removed from that list. All other property types will be set to None
		'''
		pm = self.post.metadata
		if self.has_meta(k):
			if type(pm[k]) is list:
				# remove value from list of
				if v in pm[k]:
					pm[k].remove(v)
			else:
				pm[k] = None
