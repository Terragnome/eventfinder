def get_from(container, keys, default=None):
	try:
		result = container
		for key in keys:
			result = result[key]
		return result
	except Exception as e:
		pass
	return default