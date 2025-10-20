from maix import gpio, pinmap, time, sys, err

pin_name = "A29" 
gpio_name = "GPIOA29" 

err.check_raise(pinmap.set_pin_function(pin_name, gpio_name), "set pin failed")
led = gpio.GPIO(gpio_name, gpio.Mode.OUT)
led.value(0)

while 1:
    led.low()
    time.sleep_ms(500)
