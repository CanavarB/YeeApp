from Yeelight import Yeelight
from pydbus import SessionBus
from gi.repository import GLib
import urllib.request
from colorthief import ColorThief

yee = Yeelight()

def color_flow(message : str):
    art_URL = message['mpris:artUrl']
    urllib.request.urlretrieve(art_URL.replace('https', 'http'),"/tmp/dominantcolor")
    colors = ColorThief('/tmp/dominantcolor').get_palette(color_count=6)
    flow_ex = list()
        
    for color in colors:
        time = '10000'
        colormode = '1'
        brightness = '5'
        calc_color = Yeelight.calc_rgb(color)
        if len(flow_ex) == 0:
            time = '1000'
        ex = ','.join([time,colormode,str(calc_color),brightness])
        flow_ex.append(ex)
    yee.start_cf(flow_expression=', '.join(flow_ex))


def propertiesChangeHandler(*arg):
    message = arg[1]
    
    if 'Metadata' in message:
        color_flow(message=message['Metadata'])

    elif 'PlaybackStatus' in message:
        if message['PlaybackStatus'] == 'Paused':
            yee.stop_cf()
        else:
            if yee.last_cf is not None:
                yee.continue_cf()
            else:
                color_flow(message=proxy.Metadata)
            

def main():
    try:
        bus = SessionBus()
        global proxy
        proxy = bus.get(
            "org.mpris.MediaPlayer2.spotify", # Bus name
            "/org/mpris/MediaPlayer2" # Object path
        )
        loop = GLib.MainLoop()
        proxy.onPropertiesChanged = propertiesChangeHandler
        loop.run()
    except RuntimeError as err:
        print(err)
        
    


if __name__ == "__main__":
    main()