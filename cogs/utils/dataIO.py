import json
import os
from random import randint


def save_json(filename, data):
	"""Atomically saves json file"""
	rnd = randint(1000, 9999)
	path, ext = os.path.splitext(filename)
	tmp_file = "{}-{}.tmp".format(path, rnd)
	_save_json(tmp_file, data)
	try:
		_read_json(tmp_file)
	except json.decoder.JSONDecodeError:
		return False
	os.replace(tmp_file, filename)
	return True


def load_json(filename):
	"""Loads json file"""
	return _read_json(filename)


def is_valid_json(filename):
	"""Verifies if json file exists / is readable"""
	try:
		_read_json(filename)
		return True
	except FileNotFoundError:
		return False
	except json.decoder.JSONDecodeError:
		return False


def _read_json(filename):
	with open(filename, encoding='utf-8', mode="r") as f:
		data = json.load(f)
	return data


def _save_json(filename, data):
	with open(filename, encoding='utf-8', mode="w") as f:
		json.dump(data, f, indent=4, sort_keys=True,
		          separators=(',', ' : '))
	return data
