import RPi.GPIO as GPIO
from socket import socket, AF_INET, SOCK_DGRAM
import time
import argparse
import requests
from apscheduler.schedulers.background import BackgroundScheduler

ID = 'smokedetector_id'

GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)

patterns = {'alarm': [0.5, 0.5, 0.5, 0.5, 0.5],
            'regular': [33.75, 33.75, 33.75]}
PATTERN_TOLERANCE = 0.1
MIN_PAUSE_BETWEEN_INTERRUPTS = 0.1
BROADCAST_PREFIX = 'SMS-Server:'
BROADCAST_PORT = 44566

hub_url = None

parser = argparse.ArgumentParser()
parser.add_argument('--debug', type=str2bool, nargs='?', const=True,
                    default=False, help='Prints log messages to the console.')
args = parser.parse_args()


scheduler = BackgroundScheduler()
scheduler.start()


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def alarm_callback():
    if args.debug:
        print('ALARM!!!')
    requests.post(hub_url + '/fire/alarm/' + ID)


def regular_callback():
    if args.debug:
        print('Batterie ist fast leer, bitte wechseln.')
    requests.post(hub_url + '/fire/battery/' + ID)


def heartbeat():
    if args.debug:
        print('Heartbeat')
    requests.post(hub_url + '/fire/heartbeat/' + ID)


def configure_hub():
    s = socket(AF_INET, SOCK_DGRAM)  # create UDP socket
    s.bind(('', BROADCAST_PORT))
    while hub_url == None:
        data, addr = s.recvfrom(1024)  # wait for a packet
        if data.startswith(BROADCAST_PREFIX):
            print("got service announcement from" +
                  str(data[len(BROADCAST_PREFIX):]))
            print(addr)
    requests.post(hub_url + '/fire/register/' + ID)
    scheduler.add_job(heartbeat, 'interval', minutes=5, id='heartbeat')


callbacks = {'alarm': alarm_callback, 'regular': regular_callback}

buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
last_interrupt = time.time()


def check_for_pattern(buffer):
    if args.debug:
        print(buffer)
    for name, pattern in patterns.items():
        if matches_pattern(pattern, buffer):
            callbacks[name]()
            return


def matches_pattern(pattern, buffer):
    for index in range(len(pattern)):
        if abs(pattern[index] - buffer[index]) > PATTERN_TOLERANCE:
            return False
    return True


def callback(arg):
    global buffer
    global last_interrupt
    current_interrupt = time.time()
    time_since_last_interrupt = current_interrupt - last_interrupt
    last_interrupt = current_interrupt
    if time_since_last_interrupt > MIN_PAUSE_BETWEEN_INTERRUPTS:
        buffer = [time_since_last_interrupt] + buffer[:-1]
        check_for_pattern(buffer)


configure_hub()

GPIO.add_event_detect(26, GPIO.FALLING)
GPIO.add_event_callback(26, callback)

input()
requests.delete(hub_url + '/fire/unregister/' + ID)
