import re
import socket

kelvin_table = {
    1700: (255, 121, 0),
    1800: (255, 126, 0),
    1900: (255, 131, 0),
    2000: (255, 138, 18),
    2100: (255, 142, 33),
    2200: (255, 147, 44),
    2300: (255, 152, 54),
    2400: (255, 157, 63),
    2500: (255, 161, 72),
    2600: (255, 165, 79),
    2700: (255, 169, 87),
    2800: (255, 173, 94),
    2900: (255, 177, 101),
    3000: (255, 180, 107),
    3100: (255, 184, 114),
    3200: (255, 187, 120),
    3300: (255, 190, 126),
    3400: (255, 193, 132),
    3500: (255, 196, 137),
    3600: (255, 199, 143),
    3700: (255, 201, 148),
    3800: (255, 204, 153),
    3900: (255, 206, 159),
    4000: (255, 209, 163),
    4100: (255, 211, 168),
    4200: (255, 213, 173),
    4300: (255, 215, 177),
    4400: (255, 217, 182),
    4500: (255, 219, 186),
    4600: (255, 221, 190),
    4700: (255, 223, 194),
    4800: (255, 225, 198),
    4900: (255, 227, 202),
    5000: (255, 228, 206),
    5100: (255, 230, 210),
    5200: (255, 232, 213),
    5300: (255, 233, 217),
    5400: (255, 235, 220),
    5500: (255, 236, 224),
    5600: (255, 238, 227),
    5700: (255, 239, 230),
    5800: (255, 240, 233),
    5900: (255, 242, 236),
    6000: (255, 243, 239),
    6100: (255, 244, 242),
    6200: (255, 245, 245),
    6300: (255, 246, 247),
    6400: (255, 248, 251),
    6500: (255, 249, 253)}




class Yeelight():
    last_cf = None
    def __init__(self) -> None:
        search_data = Yeelight.search_yeelight()
        
        if search_data is not None:
            add_port = Yeelight.__extract_info(search_data)
            self.IP = add_port[0]
            self.PORT = add_port[1]

            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(0.5)
            self.tcp_socket.connect((self.IP, int(self.PORT)))
        else:
            raise RuntimeError
    
    @staticmethod
    def search_yeelight() -> bytes:
        scan_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        scan_socket.settimeout(0.5)
        multicase_address = ("239.255.255.250", 1982)
        searchMessage = ( 'M-SEARCH * HTTP/1.1\r\n'
                            'HOST: 239.255.255.250:1982\r\n'
                            'MAN: \"ssdp:discover\"\r\n'
                            'ST: wifi_bulb')
        scan_socket.sendto(bytes(searchMessage,"ascii"), multicase_address)
        
        data = None
        try:
            data = scan_socket.recv(1024)
        except TimeoutError as toe:
            print("There is no bulb")
        scan_socket.close()
        return data
    @staticmethod
    def __extract_info(data):
        location_re = re.compile("Location.*yeelight[^0-9]*([0-9]{1,3}(\.[0-9]{1,3}){3}):([0-9]*)")
        match = location_re.search(str(data))
        ip = match.group(1)
        port = match.group(3)
        return (ip, port)

    @staticmethod
    def calc_rgb(rgb):
        red = rgb[0] << 16
        green = rgb[1] << 8
        blue = rgb[2]
        return red + green + blue

    def send(self, packet: str) -> bytes:
        buff = None
        packet = str(packet).replace('\'', '\"') + "\r\n"
        try:
            self.tcp_socket.send(bytes(packet,"ascii"))
            buff = self.tcp_socket.recv(1024)
        except TimeoutError as toe:
            print('Time out')
        return buff

    def __get_command(f):
        def wraper(*args, **kwargs):
            shema = {"id": 0, "method" : f.__name__, "params" : []}
            return f(command = shema, *args, **kwargs)
        return wraper
    
    @__get_command
    def get_prop(self, *arg, command) -> bytes:
        #TODO: encapsulation
        command['params'] = list(arg)
        return self.send(command)
    
    @__get_command
    def set_ct_abx(self, command, ct_value = 1700, effect = 'smooth', duration = 30):
        if not (ct_value <= 6500 and ct_value >= 1700):
            raise RuntimeError
        if not (effect == 'smooth' or effect == 'sudden'):
            raise RuntimeError
        if not (duration >= 30):
            raise RuntimeError
        
        command['params'] = list((ct_value, effect, duration))
        self.send(command)
        
    
    @__get_command
    def set_rgb(self, command, rgb = (0,0,0), effect = 'smooth', duration = 30):
        rgbVal = Yeelight.calc_rgb(rgb)
        command['params'] = list((rgbVal, effect, duration))
        self.send(command)
    
    @__get_command
    def set_bright(self, command, bright, effect = 'smooth', duration = 30):
        command['params'] = list((bright, effect, duration))
        self.send(command)
    
    @__get_command
    def set_power(self, command, power = 'on', effect = 'smooth', duration = 30, mode = 0):
        command['params'] = list((power, effect, duration, mode))
        self.send(command)

    @__get_command
    def toggle(self, command):
        self.send(command)
    
    @__get_command
    def start_cf(self, command, count = 0, action = 0, flow_expression = "500, 1, 7, -1"):
        command['params'] = list((count, action, flow_expression))
        self.last_cf = command
        self.send(command)
    
    @__get_command
    def stop_cf(self, command):
        self.send(command)

    def continue_cf(self):
        try:
            self.send(self.last_cf)
        except:
            pass
    


    def __str__(self) -> str:
        return 'Yeelight: IP ' + str(self.IP) + ' PORT ' + str(self.PORT)
    def __del__(self):
        try:
            self.tcp_socket.close()
        except AttributeError as A:
            pass


