#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import csv
from typing import List
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, QCoreApplication
from ipaddress import IPv4Address, IPv4Network, ip_network, get_mixed_type_key
from snmpclient import DeviceInfo
from logger import logger


class ScanResultsTableModel(QAbstractTableModel):
    ''' Модель реализует обертку, для отображения контейнера содержащего
        данные класса DeviceInfo в представлении таблицы
    '''
    HEADERS = [ QCoreApplication.translate('ScanResultsTableModel', 'Address'),
                QCoreApplication.translate('ScanResultsTableModel', 'System Name'),
                QCoreApplication.translate('ScanResultsTableModel', 'Description'),
                QCoreApplication.translate('ScanResultsTableModel', 'Location'),
                QCoreApplication.translate('ScanResultsTableModel', 'Contact'),
                QCoreApplication.translate('ScanResultsTableModel', 'UpTime') ]

    COLUMN_COUNT = len(HEADERS)


    def __init__(self, parent=None, *args):
        ''' Конструктор класса
        '''
        QAbstractTableModel.__init__(self, parent, *args)
        self._data : List[DeviceInfo] = []
        self._to_insert = []


    def rowCount(self, parent) -> int:
        ''' Возвращает количество строк в таблице
            переопреденённый метод родительского класса
        '''
        return len(self._data)


    def columnCount(self, parent: QModelIndex) -> int:
        ''' Возвращает количество колонок в таблице
            переопреденённый метод родительского класса
        '''
        return self.COLUMN_COUNT


    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> QVariant:
        ''' Возвращает данные находящиеся по индексу в таблице
            переопреденённый метод родительского класса
        '''
        if (not index.isValid()) or role != Qt.DisplayRole:
            return None

        row = index.row()
        column = index.column()

        devinfo = self._data[row]

        if(row > self.rowCount(QModelIndex()) or row < 0):
            return None

        devinfo = self._data[row]

        # порядок членов класса DeviceInfo соответствует порядку
        # заголовков в списке, т.е. если заголовок Description
        # в переменной HEADERS имеет индекс 2, то для devinfo[2]
        # будет возаращено значение переменной devinfo.description
        return str(devinfo[column])


    def headerData(self, section: int, orientation: Qt.Orientation,
        role: int = Qt.DisplayRole) -> QVariant:
        ''' Получение данных заголовка
            переопреденённый метод родительского класса
        '''
        result = None
        if role != Qt.DisplayRole:
            return result

        if orientation == Qt.Horizontal:
            result = self.HEADERS[section]

        return result


    def insertRows(self, position: int, rows: int, parent: QModelIndex) -> bool:
        ''' Вставка строк
            переопреденённый метод родительского класса
        '''
        if len(self._to_insert) == 0:
            return False

        self.beginInsertRows(QModelIndex(), position, position+rows-1)
        for row in self._to_insert:
            self._data.append(row)

        self._to_insert.clear()
        self.endInsertRows()
        self.dataChanged.emit(parent, parent)

        return True


    def removeRows(self, row: int, count: int, parent: QModelIndex) -> bool:
        ''' Удаление количества строк равное count, начиная с row
            переопреденённый метод родительского класса
        '''
        rowcount = self.rowCount(QModelIndex)
        if ((rowcount < row) or (rowcount > (row + count)) or (rowcount == 0)):
            return False

        self.beginRemoveRows(parent, row, row+count-1)
        for index in range(row+count-1, row, -1):
            del self._data[index]

        self.endRemoveRows()
        return True


    def sort(self, column: int, order: int):
        ''' Сортировка таблицы по колонке
            переопреденённый метод родительского класса
        '''
        self.layoutAboutToBeChanged.emit()

        sortkey = lambda x: x[column]
        # HACK: сортировка по ip-адресу
        if column == 0:
            sortkey = lambda x: get_mixed_type_key(IPv4Address(x.host))

        self._data.sort(key=sortkey, reverse=True if order == Qt.DescendingOrder else False)
        self.layoutChanged.emit()


    def add_row(self, devinfo: DeviceInfo):
        ''' Добавление строки, представляющей собой данные объекта DeviceInfo
        '''
        self._to_insert.append(devinfo)
        self.insertRows(self.rowCount(QModelIndex()), 1, QModelIndex())


    def remove_all_rows(self):
        ''' Очистка всех строк в таблице
            однако колонки не будут удалены
        '''
        self.beginRemoveRows(QModelIndex(), 0, self.rowCount(QModelIndex())-1)
        self._data.clear()
        self.endRemoveRows()


    def export(self, filename: str):
        ''' Экспорт данных в файл, в формате csv
            filename имя файла в который будут записаны данные
        '''
        with open(filename, 'w', newline='') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=';',
                    quotechar='|', quoting=csv.QUOTE_MINIMAL)

                spamwriter.writerow(self.HEADERS)
                for devinfo in self._data:
                    row = []
                    for record in devinfo:
                        if isinstance(record, str):
                            record = record.replace('\n', ' ').replace('\r', '')
                            record = record.replace(';', ' ').replace('|', ' ')
                        row.append(record)

                    spamwriter.writerow(row)
