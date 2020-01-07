import array
import math
import time
import board
import random
import audiobusio
import adafruit_hcsr04
from varspeed import Vspeed
from adafruit_crickit import crickit

# definition for mic input normalization
def mean(values):
    return sum(values) / len(values)

def normalized_rms(values):
    minbuf = int(mean(values))
    samples_sum = sum(
        float(sample - minbuf) * (sample - minbuf)
        for sample in values
    )

    return math.sqrt(samples_sum / len(values))

# declare arbitrary numbers for microphone, servo and distance sensor
NUM_SAMPLES = 160
magnitude_new = -1000
magnitude_sum = 0
sum_limit = 60000

angle_1 = random.randint(125, 180)

inti_dis = 25

ss = crickit.seesaw


# declare sensors and servos
# the mic input
mic = audiobusio.PDMIn(board.MICROPHONE_CLOCK, board.MICROPHONE_DATA,
                       sample_rate=16000, bit_depth=16)

# Record an initial sample to calibrate. Assume it's quiet when we start.
samples = array.array('H', [0] * NUM_SAMPLES)

# Servos(servo1 controles head, servo2 controles arm)
servo1_position = servo2_position = servo3_position = Vspeed(False)

# read sonar to control blush
sonar = adafruit_hcsr04.HCSR04(trigger_pin=(board.A2), echo_pin=(board.A3))

# the blush on drive 1
led = crickit.drive_1
led_brightness = Vspeed(True)

# motion
while True:
    mic.record(samples, len(samples))
    magnitude = normalized_rms(samples)
    magnitude_sum = 0
    try:
        print("distance is: ", sonar.distance)
        print("mag is: ", magnitude)

        while sonar.distance < inti_dis:
           # blush when you're inside the intimacy range: very nervos
           value, running, changed = led_brightness.loop(0, 20, 100, 20)
           if running and changed:
                led.fraction = value/100

           while sonar.distance < inti_dis and magnitude > 30 and magnitude_sum< sum_limit:
                value, running, changed = led_brightness.loop(0, 20, 100, 20)
                if running and changed:
                    led.fraction = value/100

                magnitude_new = magnitude
                magnitude_sum = magnitude_sum + magnitude_new
                print("mag new is: ", magnitude_new)
                print("mag sum is: ", magnitude_sum)

                value, running, changed = servo1_position.sequence([(angle_1, 5), (angle_1, 5), (angle_1, 5)],False)
                if running and changed:
                    crickit.servo_1.angle = value
                if running== False:
                    angle_1 = random.randint(90, 130)

           while magnitude_sum > sum_limit: # when you speak to a certain amount, give you the candy
                value, running, changed = servo2_position.sequence([(90, 3), (45, 3)], False)
                if running and changed:
                    crickit.servo_2.angle = crickit.servo_3.angle= value

                if running== False:
                    time.sleep(1)
                    while True:
                        value, running, changed = servo2_position.sequence([(0, 5), (90, 5)], False)
                        if running and changed:
                            crickit.servo_2.angle = crickit.servo_3.angle= value
                        if running== False:
                            print("moving")
                            magnitude_sum = 0
                            print("magnitude sum reset to ", magnitude_sum) # reset to start listening again
                            break


        # blush when you're outside the intimacy range: a little shy
        while sonar.distance > inti_dis:
           value, running, changed = led_brightness.loop(0, 5, 20, 5) # slower blush
           if running and changed:
                led.fraction = value/100

    except RuntimeError:
        print("Retrying!")
    time.sleep(0.1)
