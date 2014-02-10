import locale
import warnings
import os

class _Locales(object):
	_locales=(
		'af_ZA.utf-8', 'am_ET.utf-8', 'be_BY.utf-8', 'bg_BG.utf-8', 'ca_ES.utf-8',
		'cs_CZ.utf-8', 'da_DK.utf-8', 'de_AT.utf-8', 'de_CH.utf-8', 'de_DE.utf-8',
		'el_GR.utf-8', 'en_AU.utf-8', 'en_CA.utf-8', 'en_GB.utf-8', 'en_IE.utf-8',
		'en_NZ.utf-8', 'en_US.utf-8', 'es_ES.utf-8', 'et_EE.utf-8', 'eu_ES.utf-8',
		'fi_FI.utf-8', 'fr_BE.utf-8', 'fr_CA.utf-8', 'fr_CH.utf-8', 'fr_FR.utf-8',
		'he_IL.utf-8', 'hr_HR.utf-8', 'hu_HU.utf-8', 'hy_AM.utf-8', 'is_IS.utf-8',
		'it_CH.utf-8', 'it_IT.utf-8', 'ja_JP.utf-8', 'kk_KZ.utf-8', 'ko_KR.utf-8',
		'lt_LT.utf-8', 'nl_BE.utf-8', 'nl_NL.utf-8', 'no_NO.utf-8', 'pl_PL.utf-8',
		'pt_BR.utf-8', 'pt_PT.utf-8', 'ro_RO.utf-8', 'ru_RU.utf-8', 'sk_SK.utf-8',
		'sl_SI.utf-8', 'sv_SE.utf-8', 'tr_TR.utf-8', 'uk_UA.utf-8', 'zh_CN.utf-8',
		'zh_HK.utf-8', 'zh_TW.utf-8')

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

def formatCurrency(value):
	""" Returns the currency string with commans for a float value
		without currency symbol.
		23000.10 -> 23,000.10
	"""
	return '{:,.2f}'.format(value)

def currencyCodes():
	""" Returns a list of known all currency codes
	"""
	return _locales.currencyMap.keys()

def defaultCurrencyCode():
	""" Returns the local currency code (3 chars)
		eg:
			$LANG=en_GB.utf-8 -> 'GBP'
			$LANG=en_US.utf-8 -> 'USD'
	"""

	locale.setlocale(locale.LC_ALL, '')
	conv=locale.localeconv()
	return conv['int_curr_symbol'].strip()

def toCurrencyStr(value, currencyCode=None):
	try:
		locale.setlocale(locale.LC_ALL, _locales.currencyMap[currencyCode or defaultCurrencyCode()])
		return locale.currency(value, symbol=True, grouping=True).decode('utf-8')
	except (locale.Error, KeyError):
		warnings.warn('Failed to convert currency: current $LANG=%r' % os.getenv('LANG', ''))
		return formatCurrency(value)


_locales = _Locales()
