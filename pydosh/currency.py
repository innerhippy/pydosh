import locale
import platform


class _Locales(object):
	_locales=(
		'en_AU', 'en_BW', 'en_CA', 'en_DK', 'en_GB', 'en_HK', 'en_IE', 
		'en_IN', 'en_NG', 'en_PH', 'en_US', 'en_ZA', 'en_ZW', 'ja_JP')

	def __init__(self):
		super(_Locales, self).__init__()
		self.currencyMap = {}
		for loc in self._locales:
			if platform.system() == 'Darwin':
				loc += '.utf-8'
			else:
				loc += '.utf8'
				
			try:
				locale.setlocale(locale.LC_ALL, loc)
				conv=locale.localeconv()
				self.currencyMap[conv['int_curr_symbol'].strip()] = loc
			except locale.Error:
				pass

def formatCurrency(value):
	locale.setlocale(locale.LC_ALL, '')
	return locale.currency(value, symbol=False, grouping=True)

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
