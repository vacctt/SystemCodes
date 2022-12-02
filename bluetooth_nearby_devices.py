import bluetooth

addresses_to_look_for = ['00:B8:B6:53:F9:E4']
devices_discovered_nearby = bluetooth.discover_devices(lookup_names=True)

for device_address, device_name in devices_discovered_nearby:
    for address in addresses_to_look_for:
        if address == device_address:
            print("Dispositivo encontrado. Estableciendo conexión")
            bluetooth_socket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            bluetooth_socket.connect((address,1))