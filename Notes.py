import json
from pathlib import Path
import frontmatter
# from .Vaulttype import VaultType


class Note():
	def __init__(self, path, vaultTypes=None):
		self.path = path
		self.post = frontmatter.load(self.path)
		self.vaultTypes = Note.getVaultTypes(self.path)
		

	@classmethod
	def getVaultTypes(cls, path):
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


	def to_string(self):
		content = frontmatter.dumps(self.post, encoding='utf-8', sort_keys=False, width=0, allow_unicode=True)
		return content


	def write(self, fileName=None):
		fn = self.path if fileName==None else fileName
		frontmatter.dump(self.post, fn, encoding='utf-8', sort_keys=False, allow_unicode=True)


	def has_key(self, key):
		return key in self.post.metadata


	def add(self, k, v=None, overwrite=False):
		pm = self.post.metadata
		# adding a new property
		if not self.has_key(k):
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
		if self.has_key(k):
			del self.post.metadata[k]


	def removeValue(self, k, v=None):
		''' Remove a key's value
		If the key value is a list, the value will be removed from that list. All other property types will be set to None
		'''
		pm = self.post.metadata
		if self.has_key(k):
			if type(pm[k]) is list:
				# remove value from list of
				if v in pm[k]:
					pm[k].remove(v)
			else:
				pm[k] = None


if __name__ == "__main__":
	secondNotePath='/home/glen/Documents/obsidian/obNoteTest/subdir/Second Note.md'
	n = obNote(secondNotePath)
	breakpoint()
