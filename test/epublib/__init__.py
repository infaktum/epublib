
"""Test-package shim: when pytest imports the test package named `epublib`
it would shadow the real `epublib` package in `src/`. To make the tests
work without renaming directories, load the real modules from `src/epublib`
and inject them into sys.modules under the names `epublib.*`.

This keeps the test package present but delegates module imports to the
implementation in `src/epublib`.
"""
import sys
import os
import importlib.util

# Determine project root and src/epublib path relative to this file
HERE = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC_PKG_DIR = os.path.join(PROJECT_ROOT, 'src', 'epublib')

_modules = ['book', 'epub', 'markdown', '__init__']
for mod in _modules:
	path = os.path.join(SRC_PKG_DIR, f"{mod}.py")
	if not os.path.isfile(path):
		continue
	fullname = f"epublib.{mod}" if mod != '__init__' else 'epublib'
	if fullname in sys.modules:
		# already loaded
		continue
	spec = importlib.util.spec_from_file_location(fullname, path)
	module = importlib.util.module_from_spec(spec)
	sys.modules[fullname] = module
	try:
		spec.loader.exec_module(module)
	except Exception:
		# if loading fails, remove partial module to avoid confusing state
		sys.modules.pop(fullname, None)
		raise
	# Also make the submodule available as attribute of this package
	if fullname != 'epublib':
		setattr(sys.modules.setdefault('epublib', sys.modules.get(fullname)), mod, module)

