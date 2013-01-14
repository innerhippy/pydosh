/*
 * doshLogger - Bank statement transaction manager
 * Copyright (C) 2008 - Will Hall
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 */

#include "tagDialog.h"
#include "helpBrowser.h"
#include <QInputDialog>
#include <QFileDialog>
#include <QSqlError>
#include <QMessageBox>
#include <dbConnection.h>
#include <QSqlQuery>
#include <QDebug>


TagDialog::TagDialog(const QStringList& recordids, QWidget* parent) :
	QDialog(parent),
	m_recordids(recordids)
{
	setAttribute(Qt::WA_DeleteOnClose); 
	ui.setupUi(this);

	ui.tagListWidget->setSelectionMode(QAbstractItemView::ExtendedSelection);
	ui.deleteTagButton->setEnabled(false);

	QSqlQuery query(QString(
				"SELECT tagname, tagid, (SELECT COUNT(*) "
				"FROM recordtags "
				"WHERE tagid=tags.tagid "
				"AND recordid in (%1)) "
				"FROM tags "
				"WHERE userid=%2 ORDER BY tagname").arg(m_recordids.join(","))
								  .arg(Database::Instance().userId()));

	while (query.next()) {

		QListWidgetItem *item = new QListWidgetItem(query.value(0).toString());

		item->setData(Qt::UserRole, query.value(1).toInt());

		if (query.value(2).toInt() == recordids.size()) {
			item->setCheckState(Qt::Checked);
		}
		else if (query.value(2).toInt() == 0) {
			item->setCheckState(Qt::Unchecked);
		}
		else {
			item->setCheckState(Qt::PartiallyChecked);
		}
		ui.tagListWidget->addItem(item);
	}

	connect (this, SIGNAL(accepted()), this, SLOT(saveTags()));
	connect (ui.addTagButton, SIGNAL(pressed()), this, SLOT(addTag()));
	connect (ui.deleteTagButton, SIGNAL(pressed()), this, SLOT(setDeleteTags()));
	connect (ui.tagListWidget->selectionModel(), SIGNAL(selectionChanged(const QItemSelection&, const QItemSelection&)),
			this, SLOT(activateDeleteTagButton()));

	connect (ui.helpButton, SIGNAL(pressed()), this, SLOT(showHelp()));
}

void TagDialog::showHelp()
{
	HelpBrowser::showPage("main.html#Tags");
}

void TagDialog::activateDeleteTagButton()
{
	ui.deleteTagButton->setEnabled(ui.tagListWidget->selectionModel()->selectedRows().size() > 0);
}


void TagDialog::addTag()
{
	 bool ok;
     QString tagname = QInputDialog::getText(this, tr("Create New Tag"), 
     				tr("Tag:"), QLineEdit::Normal, QString(), &ok);
     				
     if (ok && !tagname.isEmpty()) {
     
	 	QSqlQuery query;
		query.prepare("INSERT INTO tags (tagname, userid) VALUES (?, ?)");
		query.addBindValue(tagname);
		query.addBindValue(Database::Instance().userId());
		query.exec();

     	if (query.lastError().isValid()) {
     		QMessageBox::critical( this, tr("Tag Error"), query.lastError().text(), QMessageBox::Ok);
     		return;
     	}
     	
     	// lastInsertId does not seem to work with psql - do it the hard way.
     	query.prepare("SELECT tagid from tags WHERE tagname=? AND userid=?");
		query.addBindValue(tagname);
		query.addBindValue(Database::Instance().userId());
		query.exec();
     	query.next();
     	
		QListWidgetItem *item = new QListWidgetItem(tagname);
		item->setData(Qt::UserRole, query.value(0).toInt());
		item->setCheckState(Qt::Checked);
		ui.tagListWidget->addItem(item);
     }
}


void TagDialog::setDeleteTags()
{
	QList<QListWidgetItem*> items = ui.tagListWidget->selectedItems();

	for (int i=0; i< items.size(); i++) {
		QFont font = items.at(i)->font();
		font.setStrikeOut(true);
		items.at(i)->setFont(font);
	}
}


void TagDialog::deleteTags()
{
	QStringList tagsToDelete;
	
	for (int i=0; i< ui.tagListWidget->count(); i++) {
		QListWidgetItem* item = ui.tagListWidget->item(i);
		if (item->font().strikeOut()) {
			tagsToDelete << item->data(Qt::UserRole).toString();
		}
	}
	
	if (tagsToDelete.size() > 0) {
		QSqlQuery query(QString("DELETE FROM tags WHERE tagid IN (%1)").arg(tagsToDelete.join(",")));
	} 
}

void TagDialog::saveTags()
{
	// This could take a long time...
	QApplication::setOverrideCursor(Qt::WaitCursor);

	deleteTags();
	
	for (int i=0; i< ui.tagListWidget->count(); i++) {
		QListWidgetItem* item = ui.tagListWidget->item(i);
		
		if (item->font().strikeOut()) {
			// No point, they've gone.
			continue;
		}
		
		int tagId = item->data(Qt::UserRole).toInt();

		if (item->checkState() == Qt::Unchecked) {

			QSqlQuery query(QString ("DELETE FROM recordtags where tagid=%1 and recordid in (%2)")
					.arg(tagId)
					.arg(m_recordids.join(",")));
		}
		else if (item->checkState() == Qt::Checked) {

			QStringList existingRecs;
			QSqlQuery query(QString("SELECT recordid from recordtags where tagid=%1").arg(tagId));

			while (query.next()) {
				existingRecs << query.value(0).toString();
			}

			for (int i=0; i< m_recordids.size(); i++) {

				if (!existingRecs.contains(m_recordids.at(i))) {

					QSqlQuery query (QString("INSERT INTO recordtags (recordid, tagid) VALUES (%1, %2)")
							.arg(m_recordids.at(i))
							.arg(tagId));

					if (query.lastError().isValid()) {
						QApplication::restoreOverrideCursor();
						QMessageBox::critical( this, tr("Tag Error"), query.lastError().text(), QMessageBox::Ok);
     					return;
					}
				}
			}
		}
		else {
			// partial check - do nothing as values have not changed!
		}
	}
	QApplication::restoreOverrideCursor();
}
