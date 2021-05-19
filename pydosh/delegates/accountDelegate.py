from PyQt5 import QtGui, QtCore, QtWidgets
from pydosh import enums

class AccountDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent=None):
        super(AccountDelegate, self).__init__(parent=parent)

    def createEditor(self, parent, option, index):
        lineEdit = QtWidgets.QLineEdit(parent=parent)
        pattern = None

        if index.column() in (
                enums.kAccountType__DateField,
                enums.kAccountType__DescriptionField,
                enums.kAccountType__CreditField,
                enums.kAccountType__DebitField):
            pattern = QtCore.QRegExp('[0-9]+')

        elif index.column() == enums.kAccountType__DateFormat:
            pattern = QtCore.QRegExp('[dMy/- ]+')

        elif index.column() == enums.kAccountType__CurrencySign:
            pattern = QtCore.QRegExp('-1|1')

        if pattern:
            lineEdit.setValidator(QtGui.QRegExpValidator(pattern))

        return lineEdit

    def setModelData(self, editor, model, index):

        if not index.isValid():
            return

        if editor:
            model.setData(index, editor.text())

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
