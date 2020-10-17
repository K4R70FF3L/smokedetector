import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

patterns = {'alarm': [1.5, 0.5, 0.5], 'battery': [33.7, 33.7, 33.7]}
pattern_tolerance = 0.15
MIN_PAUSE_BETWEEN_INTERRUPTS = 0.1

def alarm_callback():
  print('ALARM!!!')

def battery_callback():
  print('Batterie ist fast leer, bitte wechseln.')

callbacks = {'alarm': alarm_callback, 'battery': battery_callback}

buffer = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
last_interrupt = time.time()

def check_for_pattern(buffer):
  print(buffer)
  for name, pattern in patterns.items():
    if matches_pattern(pattern, buffer):
      callbacks[name]()
      return
  
def matches_pattern(pattern, buffer):
  for index in range(len(pattern)):
    if pattern[index] + pattern_tolerance < buffer[index] or pattern[index] - pattern_tolerance > buffer[index]:
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

GPIO.add_event_detect(26, GPIO.RISING)
GPIO.add_event_callback(26, callback)
input()
