import locale


class _Locales(object):
	_locales=(
		'en_AU.utf8', 'en_BW.utf8', 'en_CA.utf8', 'en_DK.utf8', 
		'en_GB.utf8', 'en_HK.utf8', 'en_IE.utf8', 'en_IN', 'en_NG',
		'en_PH.utf8', 'en_US.utf8', 'en_ZA.utf8', 'en_ZW.utf8', 
		'ja_JP.utf8')

	def __init__(self):
		super(_Locales, self).__init__()
		self.currencyMap = {}
		for loc in self._locales:
			try:
				locale.setlocale(locale.LC_ALL, loc)
				conv=locale.localeconv()
				self.currencyMap[conv['int_curr_symbol'].strip()] = loc
			except locale.Error:
				pass

def currencyCodes():
	""" Returns a list of known all currency codes
	"""
	return _locales.currencyMap.keys()

def defaultCurrencyCode():
	""" Returns the local currency code (3 chars)
		eg:
			$LANG=en_GB.utf8 -> 'GBP'
			$LANG=en_US.utf8 -> 'USD'
	"""

	locale.setlocale(locale.LC_ALL, '')
	conv=locale.localeconv()
	return conv['int_curr_symbol'].strip()

def toCurrencyStr(value, currencyCode=None):
	try:
		locale.setlocale(locale.LC_ALL, _locales.currencyMap[currencyCode or defaultCurrencyCode()])
		symbol = True
	except (locale.Error, KeyError):
		locale.setlocale(locale.LC_ALL, '')
		symbol = False

	return locale.currency(value, symbol=symbol, grouping=True).decode('utf8')


_locales = _Locales()
