#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import webbrowser
from pathlib import Path
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (QMessageBox, QMainWindow, QApplication,
    QComboBox, QFileDialog)

from PyQt5.QtCore import QCoreApplication, pyqtSlot, pyqtSignal, QModelIndex
from ipaddress import IPv4Network, IPv4Address
from typing import Sequence

from ui_snmp_scanner_mainwindow import Ui_SNMPScannerWindow
from snmpscannerthread import ThreadPool, SNMPScannerThread
from util import CompletionsFile
from snmpclient import DeviceInfo
from scanresults_tablemodel import ScanResultsTableModel
from logger import logger

ICONS_PATH = 'icons'
HOST_COMPLETIONS_PATH = os.path.join(str(Path.home()), 'snmpscanner_host.lst')
COMMUNITY_COMPLETIONS_PATH = os.path.join(str(Path.home()), 'snmpscanner_community.lst')
ABOUT_MESSAGE = QCoreApplication.translate('About', '''
Author <a href=https://github.com/clericJ>Almaz Karimov</a>
<br>
Version 1.0.1<br>
New BSD License (c) 2018<br>
Icons by <a href=http://www.graphicrating.com>Andy Gongea</a>
''')

class SNMPScannerWindow(QMainWindow):
    ''' Класс главного окна программы
    '''
    def __init__(self):
        ''' Конструктор
        '''
        super(QMainWindow, self).__init__()

        self._thread_pool = ThreadPool()
        self.ui = Ui_SNMPScannerWindow()
        self.ui.setupUi(self)
        self.init_ui()
        self._init_signals_and_slots()


    def init_ui(self):
        ''' инициализация интерфейса
        '''
        self.setWindowIcon(QtGui.QIcon(os.path.join(ICONS_PATH, 'appicon.png')))
        self.ui.scanButton.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, 'start.png')))
        self.ui.actionStart.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, 'start.png')))

        self.ui.stopButton.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, 'stop.png')))
        self.ui.actionStop.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, 'stop.png')))

        self.ui.exportButton.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, 'export.png')))
        self.ui.actionExport.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, 'export.png')))

        self.ui.actionAbout.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, 'about.png')))
        self.ui.actionExit.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, 'close.png')))

        self.ui.scanResultsTableView.setModel(ScanResultsTableModel())
        self.ui.scanResultsTableView.resizeColumnsToContents()

        def load_completions(filename: str) -> Sequence:
            result = []
            try:
                result = CompletionsFile(filename).read()
            except (IOError, WindowsError) as err:
                self.add_record_to_message_list(str(err))

            return result

        self.ui.hostsCBox.addItems(load_completions(HOST_COMPLETIONS_PATH))
        self.ui.communityCBox.addItems(load_completions(COMMUNITY_COMPLETIONS_PATH))


    def _init_signals_and_slots(self):
        ''' первоначальное подключение сигналов
            к слотам
        '''
        self.ui.scanButton.clicked.connect(self.start_scan)
        self.ui.stopButton.clicked.connect(self.stop_scan)
        self.ui.exportButton.clicked.connect(self.export_results)
        self.ui.stopButton.setEnabled(False)
        self.ui.exportButton.setEnabled(False)

        self.ui.actionAbout.triggered.connect(self.show_about)
        self.ui.actionDonate.triggered.connect(self.open_donation_url)
        self._thread_pool.all_threads_finished.connect(self._scan_completeted)


    def scan_parameters_is_correct(self):
        ''' Проверка корренктности пользовательских данных
            введённых им в окне программы, в случае некоректных данных
            будет выведено сообщение
        '''
        network = None
        try:
            network = IPv4Network(self.ui.hostsCBox.currentText())
        except ValueError:
            QMessageBox.critical(self, self.tr('Error'),
             self.tr('Incorrect network\nfor example:\n\n192.168.1.0/27\n10.7.207.0/255.255.255.0'))
            return False

        if not self.ui.communityCBox.currentText():
            QMessageBox.critical(self, self.tr('Error'), self.tr('Community is empty'))
            return False
        return True


    def append_current_params_to_completions(self):
        ''' Добавление текущих введенных пользователем параметров
            в списки автозавершения
        '''
        def append_to_combobox(cbox: QComboBox):
            current = cbox.currentText()
            completions = set(cbox.itemText(i) for i in range(cbox.count()))
            completions.add(current)
            cbox.clear()
            cbox.addItems(completions)
            cbox.setCurrentIndex(cbox.findText(current))

        append_to_combobox(self.ui.hostsCBox)
        append_to_combobox(self.ui.communityCBox)


    @pyqtSlot(DeviceInfo)
    def add_record_to_results_table(self, devinfo: DeviceInfo):
        ''' Добавление информации об устройстве (первый параметр)
            в общую таблицу
        '''
        if not devinfo:
            return

        self.ui.scanResultsTableView.model().add_row(devinfo)
        self.ui.scanResultsTableView.resizeColumnsToContents()


    @pyqtSlot(str)
    def add_record_to_message_list(self, message: str):
        ''' Добавление сообщения об аномальном завершении в список
        '''
        if not message:
            return

        self.ui.messageListWidget.addItem(message)
        self.ui.messageListWidget.scrollToBottom()


    @pyqtSlot()
    def start_scan(self):
        ''' Слот реагирующий на нажатие кнопки начала сканирования
            проверяет начальные параметры и запускает процесс исследования
            сети
        '''
        if not self.scan_parameters_is_correct():
            return
        self.append_current_params_to_completions()

        logger.debug('scanning started')
        network = IPv4Network(self.ui.hostsCBox.currentText())
        community = self.ui.communityCBox.currentText()
        # очистка данных
        self.ui.scanResultsTableView.model().remove_all_rows()
        self.ui.messageListWidget.clear()

        self.add_record_to_message_list(
            self.tr('{}::{} scanning...'.format(network, community)))

        self.ui.scanButton.setEnabled(False)
        self.ui.stopButton.setEnabled(True)
        self.ui.exportButton.setEnabled(False)

        for host in network:
            scanner = SNMPScannerThread(host.exploded, community, self)
            scanner.recived_message.connect(self.add_record_to_message_list)
            scanner.work_done.connect(self.add_record_to_results_table)
            self._thread_pool.start(scanner)


    @pyqtSlot()
    def stop_scan(self):
        ''' Слот реагирующий на кнопку остановки сканирования
        '''
        logger.debug('scanning canceled')
        self.ui.stopButton.setEnabled(False)
        self._thread_pool.stop()
        self.add_record_to_message_list(self.tr(
            'scanning canceled, please wait...'))


    @pyqtSlot()
    def _scan_completeted(self):
        ''' Слот вызываемый при завершении всех рабочих потоков
        '''
        logger.debug('scan completed, clean pool')
        self._thread_pool = ThreadPool()
        self._thread_pool.all_threads_finished.connect(self._scan_completeted)

        self.add_record_to_message_list(self.tr('scanning completed'))
        self.ui.scanButton.setEnabled(True)
        self.ui.stopButton.setEnabled(False)

        if self.ui.scanResultsTableView.model().rowCount(QModelIndex()) > 0:
            self.ui.exportButton.setEnabled(True)


    @pyqtSlot()
    def export_results(self):
        ''' Экспорт таблицы результатов в файл
        '''
        if self.ui.scanResultsTableView.model().rowCount(QModelIndex()) == 0:
            return

        filename, _ = QFileDialog.getSaveFileName(self,
            self.tr('Save results'), 'results.csv')

        if filename:
            self.ui.scanResultsTableView.model().export(filename)


    @pyqtSlot()
    def show_about(self):
        ''' Отображение окна со сведениями о программе
        '''
        QMessageBox.about(self, 'SNMP Scanner', ABOUT_MESSAGE)


    @pyqtSlot()
    def open_donation_url(self):
        ''' Открытие сайта для принятий пожертвований
        '''
        webbrowser.open("https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=JG6BJDGECF6QS")


    def closeEvent(self, event):
        ''' Событие закрытия главного окна приложения
        '''
        def write_completions(filename: str, cbox: QComboBox):
            completions = set(cbox.itemText(i) for i in range(cbox.count()))
            CompletionsFile(filename).write(list(completions))
        try:
            write_completions(HOST_COMPLETIONS_PATH, self.ui.hostsCBox)
            write_completions(COMMUNITY_COMPLETIONS_PATH, self.ui.communityCBox)

        except (IOError, WindowsError) as error:
            logger.debug('exception handled: {}'.format(str(error)))

        logger.debug('mainwindow closed')
        super(QMainWindow, self).closeEvent(event)


def main():
    logger.debug('application started')
    app = QApplication(sys.argv)

    main_window = SNMPScannerWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
