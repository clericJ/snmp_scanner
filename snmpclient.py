#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
from pprint import pprint
from typing import Sequence, Mapping, NamedTuple
from pysnmp.entity.rfc3413.oneliner import cmdgen

from snmp_constants import *


class InterfaceInfo(NamedTuple):
    ''' Кортеж содерждащий общие сведенья об интерфейсе устройства
    '''

    description: str
    interface_type: str
    admin_status: str
    oper_status: str
    mac_address: str
    errors: str
    speed: str
    mtu: str


class DeviceInfo(NamedTuple):
    ''' Кортеж содержащий общие сведенья об устройстве
    '''

    host: str
    name: str
    description: str
    location: str
    contact: str
    uptime: datetime.timedelta


class SNMPError(Exception):
    ''' Ошибка при работе с протоколом SNMP
        входные параметры это возвращаемые значения таких функций
        как getCmd из библиотеки pysnmp
    '''
    def __init__(self, error_indication, error_status, error_index, var_binds):
        self.error_indication = error_indication
        self.error_status = error_status
        self.error_index = error_index
        self.message = ''

        if error_indication:
            self.message = error_indication
        elif error_status:
            self.message = '{} at {}'.format(error_status.prettyPrint(),
                                error_index and var_binds[int(error_index) - 1][0] or '?')

        super().__init__(self.message)


class SNMPClient:
    ''' SNMP клиент работающий с PySNMP '''

    def __init__(self, host = "localhost", port = 161,
                community = "public", version = "SNMPv2-MIB"):

        self.cmd_gen = cmdgen.CommandGenerator()
        self.host = host
        self.port = port
        self.community = community
        self.version = version


    def getbulk(self, non_repeaters: int, max_repetitions: int, *oid) -> Sequence:
        '''
        SNMP getbulk request
        non_repeaters: This specifies the number of supplied variables that should not be iterated over.
        max_repetitions: This specifies the maximum number of iterations over the repeating variables.
        oid: oid list
        '''
        error_indication, error_status, error_index, var_binds = self.cmd_gen.bulkCmd(
            cmdgen.CommunityData(self.community),
            cmdgen.UdpTransportTarget((self.host, self.port)),
            non_repeaters,
            max_repetitions,
            *oid
        )
        result = []
        if error_indication or error_status:
            raise SNMPError(error_indication, error_status, error_index, var_binds)

        for row in var_binds:
            item = {}
            for name, val in row:
                if (str(val) == ''):
                    item[name.prettyPrint()] = ''
                else:
                    item[name.prettyPrint()] = val.prettyPrint()
            result.append(item)
        return result


    def get(self, *oid) -> Sequence:
        ''' SNMP запрос на получение единичного значения, по параментрам, пример:

            >>> client.get('1.3.6.1.2.1.1.5.0')
            ['BVL-RUES_stantion-3528.7.207.245']
        '''
        error_indication, error_status, error_index, var_binds = self.cmd_gen.getCmd(
            cmdgen.CommunityData(self.community),
            cmdgen.UdpTransportTarget((self.host, self.port)),
            *oid
        )
        reuslt = []
        if error_indication or error_status:
            raise SNMPError(error_indication, error_status, error_index, var_binds)

        for name, val in var_binds:
            reuslt.append(val.prettyPrint())

        return reuslt


def get_deviceinfo(client: SNMPClient) -> DeviceInfo:
    ''' Получение основной информации от устройства взятой из
    iso.org.dod.internet/mgmt/mib2/system
    '''
    data = client.getbulk(0, 10, OID_SYSTEM)
    info_table = {}

    for elem in data:
        for key, item in elem.items():
            info_table[key] = item

    ticks = int(info_table['SNMPv2-MIB::sysUpTime.0'])
    result = DeviceInfo(
        client.host,
        info_table['SNMPv2-MIB::sysName.0'],
        info_table['SNMPv2-MIB::sysDescr.0'],
        info_table['SNMPv2-MIB::sysLocation.0'],
        info_table['SNMPv2-MIB::sysContact.0'],
        datetime.timedelta(seconds = ticks / 100))
    return result


def main():

    client = SNMPClient(host='192.168.8.1', community='public')
    data = get_deviceinfo(client)
    pprint(data)
    return

    client = SNMPClient(host='10.7.207.240', community='tatZxl761xH147')
    data  = client.getbulk(0,10, OID_INTERFACES_TABLE)
    interface_count = int(client.get(OID_INTERFACES_COUNT)[0])

    info_table = {}
    for elem in data:
        for key, item in elem.items():
            info_table[key] = item

    interfaces =  []
    for index in range(0, interface_count):
        #pprint(info_table)
        #pprint(info_table['{}.{}'.format(OID_INTERFACE_DESCR_NAME, index+1)])

        description =  info_table.get('{}.{}'.format(OID_INTERFACE_DESCR_NAME, index+1), '')
        admin_status = info_table.get('{}.{}'.format(OID_INTERFACE_ADMIN_STATUS_NAME, index+1))
        oper_status = info_table.get('{}.{}'.format(OID_INTERFACE_OPER_STATUS_NAME, index+1))
        mac_address = info_table.get('{}.{}'.format(OID_INTERFACE_MAC_ADDRESS_NAME, index+1))
        interface_type = info_table.get('{}.{}'.format(OID_INTERFACE_INTTYPE_NAME, index+1))
        mtu = info_table.get('{}.{}'.format(OID_INTERFACE_MTU_NAME, index+1))
        errors = info_table.get('{}.{}'.format(OID_INTERFACE_ERRORS_NAME, index+1))
        speed = info_table.get('{}.{}'.format(OID_INTERFACE_SPEED_NAME, index+1))

        interfaces[index] = InterfaceInfo(description, admin_status, oper_status,
            mac_address, interface_type, mtu, errors, speed)

    pprint(interfaces)



if __name__ == "__main__":
    main()
