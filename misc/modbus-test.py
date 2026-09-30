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


# Wire addresses are the protocol doc's hex offset + 40001 (e.g. SOC is 0x020E =
# 526 in the doc, but 40527 on the wire) — confirmed against MaxGrmm/EF-PowerOcean-TcpModbus's
# const.py, whose registers (grid_power=40521, battery_power=40525, battery_soc=40527,
# heartbeat=40608, control_command=40534, ...) all match offset+40001 exactly.
read_holding(40527, 1, ModbusClientMixin.DATATYPE.UINT16, 'Battery SOC (%)')
read_holding(40521, 2, ModbusClientMixin.DATATYPE.FLOAT32, 'Grid Power (W)', word_order='little')
read_holding(40525, 2, ModbusClientMixin.DATATYPE.FLOAT32, 'Battery Power (W)', word_order='little')
read_holding(40523, 2, ModbusClientMixin.DATATYPE.FLOAT32, 'Solar Power (W)', word_order='little')

client.close()
