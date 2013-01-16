from PyQt4 import QtCore, QtGui, QtSql
import enum

class Decoder(QtCore.QObject):
	def __init__(self, accountName, files, parent=None):
		super(Decoder, self).__init__(parent=parent)
		self.__accountName = accountName
		self.__files = files

		model = QtSql.QSqlTableModel(self)
		model.setTable('accounttypes')
#		model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
		model.setFilter("accountname='%s'" % accountName)
		model.select()
		if model.rowCount() != 1:
			
#		QSqlQuery query(QString("SELECT "
#				"accounttypeid, "
#				"datefield, "
#				"typefield, "
#				"descriptionfield,"
#				"creditfield, "
#				"debitfield, "
#				"balancefield, "
#				"currencysign, "
#				"dateformat "
#				"FROM accounttypes WHERE accountname='%1'")
#				.arg(accountName));
		query.next()
	"""
		if (!query.isValid()) {
			m_errorMessage = QString("Sorry - dunno how to decode '%1'").arg(accountName);
			return;
		}

	QSqlRecord rec = query.record();

	m_accountId              = rec.value(0).toInt();
	m_fieldMap[DateField]    = rec.isNull(1)? -1: rec.value(1).toInt();
	m_fieldMap[TypeField]    = rec.isNull(2)? -1: rec.value(2).toInt();
	m_fieldMap[DescField]    = rec.isNull(3)? -1: rec.value(3).toInt();
	m_fieldMap[CreditField]  = rec.isNull(4)? -1: rec.value(4).toInt();
	m_fieldMap[DebitField]   = rec.isNull(5)? -1: rec.value(5).toInt();
	m_fieldMap[BalanceField] = rec.isNull(6)? -1: rec.value(6).toInt();
	m_currencySign           = rec.value(7).toInt();
	m_dateFormat             = rec.value(8).toString();


	for (int i=0; i < files.size(); i++) {
		import(files.at(i));
	}
}

void
CSVDecoder::import(const QString& filename)
{
	QFile file(filename);
	
	if (!file.open(QIODevice::ReadOnly)) {
		qWarning() << "Cannot open file "  << file.fileName();
		return;
	}
	
	QTextStream in(&file);
	
	while (!in.atEnd()) {
		CSVParser csv(in.readLine());

		// Skip blank lines
		if (!csv.size()) 
			continue;

		// If the line doesn't being with a valid date field, then skip it
		if (!QDate::fromString(csv.get(m_fieldMap[DateField]), m_dateFormat).isValid()) {
			continue;
		}
		
		m_errorMessage.clear();

		// Initialise the CSV record with the raw data
		ImportRecord record(csv.line());
		
		// decode csv fields
		record.date = getDateField(csv);
	""""
		record.type = getTypeField(csv);
		record.description = getDescriptionField(csv);
		record.txDate = extractTransactionDate(record);
		record.credit = getCreditField(csv);
		record.debit = getDebitField(csv);
		record.balance = getBalanceField(csv);

		if (record.credit == 0.0 && record.debit == 0.0) {
			setError("No credit or debit found");
		}

		record.valid = isValid();
		record.error = m_errorMessage;

		m_errorMessage.clear();
		m_records.append(record);
	}
}

void
CSVDecoder::setError(const QString& message)
{
	if (!m_errorMessage.isEmpty())
		m_errorMessage += ", ";

	m_errorMessage += message;
}

QDate
CSVDecoder::getDateField(const CSVParser& csv)
{
	if (m_fieldMap[DateField] == -1)
		return QDate();

	QString text = csv.get(m_fieldMap[DateField]);

	QDate date(QDate::fromString(text, m_dateFormat));

	if (!date.isValid()) {
		setError("Invalid date:" + text);
		return QDate();
	}

	return date;
}

QString CSVDecoder::getTypeField(const CSVParser& csv)
{
	if (m_fieldMap[TypeField] == -1)
		return QString();

	return csv.get(m_fieldMap[TypeField]);
}


QString
CSVDecoder::getDescriptionField(const CSVParser& csv)
{
	if (m_fieldMap[DescField] == -1)
		return QString();

	QString text = csv.get(m_fieldMap[DescField]);

	if (text.isEmpty()) {
		setError("Description field is empty");
	}
	return text;
}

QDateTime
CSVDecoder::extractTransactionDate(ImportRecord& record)
{
	// Don't bother if there's an error
	if (!isValid())
		return QDateTime();

	// Format is "23DEC09 1210"
	QRegExp rx("(\\d\\d[A-Z]{3}\\d\\d \\d{4})");
	if (rx.indexIn(record.description) != -1) {
		return QDateTime::fromString (rx.cap(1), "ddMMMyy hhmm").addYears(100);
	}
	
	// Format is "06NOV10"
	rx.setPattern("(\\d{2}[A-Z]{3}\\d{2})");
	if (rx.indexIn(record.description) != -1) {
		return QDateTime::fromString (rx.cap(1), "ddMMMyy").addYears(100);
	}
	
	// Format is " 06NOV" <- note the stupid leading blank space..
	rx.setPattern(" (\\d\\d[A-Z]{3})");
	if (rx.indexIn(record.description) != -1) {
		// Add the year from date field to the transaction date
		return QDateTime::fromString (rx.cap(1)+record.date.toString("yyyy"), "ddMMMyyyy");
	}

	return QDateTime();
}


double
CSVDecoder::getCreditField(const CSVParser& csv)
{
	if (m_fieldMap[CreditField] == -1)
		return 0.0;

	QString text = csv.get(m_fieldMap[CreditField]);

	if (!QVariant(text).canConvert(QVariant::Double)) {
		setError ("Invalid credit field: " + text);
		return 0.0;
	}

	double d = QString(text).toDouble();

	d *= m_currencySign;

	if (d > 0.0)
		return d;

	return 0.0;
}


double
CSVDecoder::getDebitField(const CSVParser& csv)
{
	if (m_fieldMap[DebitField] == -1)
		return 0.0;

	QString text = csv.get(m_fieldMap[DebitField]);

	if (!QVariant(text).canConvert(QVariant::Double)) {
		setError ("Invalid debit field: " + text);
		return 0.0;
	}

	double d = QString(text).toDouble();

	d *= m_currencySign;

	if (d < 0.0)
		return d;

	return 0.0;
}

double
CSVDecoder::getBalanceField(const CSVParser& csv)
{
	if (m_fieldMap[BalanceField] == -1)
		return 0.0;

	QString text = csv.get(m_fieldMap[BalanceField]);

	bool ok;
	double d = QString(text).toDouble(&ok);
	
	if (text.isEmpty() || !ok) {
		setError("Invalid balance field: " + text);
	}
	
	return d;
}

	"""