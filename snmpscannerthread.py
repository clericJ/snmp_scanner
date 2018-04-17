#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import QObject, QThread, QMutex, pyqtSlot, pyqtSignal
from snmpclient import SNMPClient, SNMPError, DeviceInfo, get_deviceinfo

from logger import logger
from util import timestamp


class ThreadPool(QObject):
    ''' Класс представляет собой пул для управления группой потоков
        в отличии от встроенного класса QThreadPool, добавлен сигнал завершения
        all_threads_finished - сигнал запускается как только последений
        поток завершил свою работу
    '''

    all_threads_finished = pyqtSignal()


    def __init__(self, active_threads = 10, parent=None):
        ''' active_threads количество одновременно выполняющихся потоков
        '''
        super(QObject, self).__init__(parent)
        self._mutex = QMutex(QMutex.Recursive)
        self._max_active_thread_count = active_threads
        self._active_thread_count = 0
        self._thread_queue = []


    def start(self, thread: QThread):
        ''' Запуск потока на выполнение, если в данный момент количество
            выполняющихся потоков больше или равно заданного в параметре
            active_threads, то следующий поток ставится в очередь и запускается
            только после того как завершится предыдущий
        '''
        self._mutex.lock()
        try:
            if self._active_thread_count < self._max_active_thread_count:
                self._active_thread_count += 1
                thread.finished.connect(self._thread_finished)
                logger.debug('thread started')
                thread.start()
            else:
                logger.debug('thread queued')
                self._thread_queue.append(thread)
        finally:
            self._mutex.unlock()


    def stop(self):
        ''' Остановка запуска потоков стоящих в очереди
            уже запущенные потоки продолжат работать
        '''
        self._mutex.lock()
        try:
            self._thread_queue = []
        finally:
            self._mutex.unlock()


    @pyqtSlot()
    def _thread_finished(self):
        ''' Слот обрабатывающий событие завершения выполнения потока в пуле
        '''
        logger.debug('thread finished')
        self._mutex.lock()
        try:
            self._active_thread_count -= 1
            if len(self._thread_queue) > 0:
                self.start(self._thread_queue.pop())

            elif self._active_thread_count == 0:
                logger.debug('all threads finished')
                self.all_threads_finished.emit()
        finally:
            self._mutex.unlock()


    @property
    def active_threads(self) -> int:
        ''' Количество выполняющихся в данный момент потоков
        '''
        return self._active_thread_count


    @property
    def max_active_threads_count(self) -> int:
        ''' Функция вернёт максимальное количество
            одновременно выполняющихся потоков
        '''
        return self._max_active_thread_count


class SNMPScannerThread(QThread):
    ''' Поток собирающий информацию о хосте по протоколу SNMP
        при нормальном завершении запускает сигнал recived_message с информацией
        собранной о хосте в параметре (объект DeviceInfo)
        так-же для передачи текстовых сообщений о ходе выполнения
        используется сигнал recived_message
    '''

    work_done = pyqtSignal(DeviceInfo)
    recived_message = pyqtSignal(str)


    def __init__(self, host, community, parent=None):
        ''' host - имя хоста например 192.168.1.1
            community - SNMP комьюнити с доступом на чтение
        '''
        super(QThread, self).__init__(parent)

        self._host = host
        self._community = community


    def run(self):
        ''' Метод собирающий информацию о хосте, по результатам выполнения
            вызывает два сигнала SNMPScannerThread.work_done(DeviceInfo)
            и SNMPScannerThread.recived_message(str)
        '''
        devinfo = None

        msg = self.tr('{}|info|host: {} |msg: {}').format(timestamp(),
            self._host, self.tr('processing...'))

        self.recived_message.emit(msg)
        try:
            client = SNMPClient(self._host, community=self._community)
            devinfo = get_deviceinfo(client)

        except SNMPError as err:
            msg = self.tr('{}|error|host: {} |msg: {}').format(timestamp(), self._host, err)
            self.recived_message.emit(msg)
            return

        if devinfo:
            msg = self.tr('{}|info|host: {} |msg: {}').format(timestamp(),
                self._host, self.tr('complete'))

            self.recived_message.emit(msg)
            self.work_done.emit(devinfo)

