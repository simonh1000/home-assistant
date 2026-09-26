"""Quick Modbus sanity check for the EcoFlow PowerOcean inverter.
Run: python3 test.py
Confirms the installer's Modbus control mode fix worked before touching any HA config.
"""

from pymodbus.client import ModbusTcpClient
from pymodbus.client.mixin import ModbusClientMixin

client = ModbusTcpClient('192.168.0.165', port=502, timeout=5)
client.connect()


def read_holding(address, count, data_type, name, word_order='big'):
    rr = client.read_holding_registers(address=address, count=count, device_id=1)
    if rr.isError():
        print(f'FAIL  {name} (addr {address}): {rr}')
        return None
    val = ModbusClientMixin.convert_from_registers(
        rr.registers, data_type, word_order=word_order
    )
    print(f'OK    {name} (addr {address}): {val}')
    return val


read_holding(526, 1, ModbusClientMixin.DATATYPE.UINT16, 'Battery SOC (%)')
read_holding(520, 2, ModbusClientMixin.DATATYPE.FLOAT32, 'Grid Power (W)', word_order='little')
read_holding(524, 2, ModbusClientMixin.DATATYPE.FLOAT32, 'Battery Power (W)', word_order='little')
read_holding(522, 2, ModbusClientMixin.DATATYPE.FLOAT32, 'Solar Power (W)', word_order='little')

client.close()
