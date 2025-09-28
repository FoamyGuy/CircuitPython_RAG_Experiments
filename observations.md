============================================================
Question: Please show me how to setup multiple neopixel animations and change between them with the press of a button.
============================================================
Below is a **complete, ready‑to‑run CircuitPython sketch** that shows how to:

1.  Create several NeoPixel animations with the `adafruit_led_animation` library.  
2.  Detect a button press (with a simple debounce).  
3.  Switch the running animation each time the button is pressed.  

The code is written for an Adafruit CircuitPython‑compatible board (e.g. Feather 32‑uC, Metro M4, etc.) with a 32‑pixel NeoPixel strip on **D6** and a momentary push‑button on **D3** that pulls the line high when pressed.

> **Why this approach?**  
> * The `adafruit_led_animation` library gives us a clean, object‑oriented interface for common patterns (Pulse, Rainbow, ColorWipe, Blink, etc.).  
> * A simple list (`animations`) and an index (`current_anim`) let us cycle through the animations without hard‑coding a new `if/elif` block each time.  
> * The button logic uses the *prev / current* method so you only need a single `DigitalInOut` object.  

---

## 1.  Imports & Pin Setup

```python
import board
import time
import neopixel
from digitalio import DigitalInOut, Direction, Pull

# Animation helpers
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.colorwipe import ColorWipe
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.color import RED, GREEN, BLUE, YELLOW
```

### NeoPixel strip

```python
# Pin that the NeoPixels are wired to
pixel_pin = board.D6

# Number of pixels in the strip (change this to match your hardware)
pixel_num = 32

# Initialise the NeoPixel object
pixels = neopixel.NeoPixel(
    pixel_pin,
    pixel_num,
    brightness=0.5,          # 0.0 to 1.0
    auto_write=False,        # we will call .show() ourselves
)
```

### Button

```python
button_pin = board.D3

# Pull‑up is *not* needed because the button pulls the line HIGH
# when pressed.  If you wired it the other way round just remove
# the `pull` argument.
button = DigitalInOut(button_pin)
button.direction = Direction.INPUT
```

---

## 2.  Create the Animation Objects

We’ll create **four** different animations:

| Index | Animation Type | Description | Color |
|-------|----------------|-------------|-------|
| 0     | `Pulse`        | A single‑pixel pulse that moves along the strip | RED |
| 1     | `Rainbow`      | A moving rainbow across all pixels | – |
| 2     | `ColorWipe`    | A sweep of GREEN pixels | GREEN |
| 3     | `Blink`        | All pixels blink YELLOW | YELLOW |

```python
animations = [
    Pulse(pixels, speed=0.1, color=RED, pulse_width=3, reverse=True),
    Rainbow(pixels, speed=0.05),
    ColorWipe(pixels, speed=0.02, color=GREEN),
    Blink(pixels, speed=0.5, color=YELLOW, frames=2),
]
```

> **Tip:** If you want to re‑configure an animation at runtime, just modify the object’s attributes (e.g., `animations[0].speed = 0.2`).

---

## 3.  Button‑Press Logic

We use the *previous‑state* method to detect a falling edge (button pressed).  
A tiny delay (`time.sleep(0.02)`) gives the button a chance to settle – a very light debounce.

```python
def button_pressed():
    """
    Return True only when the button is newly pressed.
    """
    # Read the current state (True = HIGH, False = LOW)
    current = button.value

    # Detect a rising edge: previous False → current True
    # (the button pulls HIGH when pressed)
    if current and not button_pressed.prev:
        button_pressed.prev = current
        return True

    button_pressed.prev = current
    return False

# Initialise static variable
button_pressed.prev = False
```

---

## 4.  Main Loop

```python
# Index of the currently active animation
current_anim = 0

while True:
    # 1. Run the current animation
    animations[current_anim].tick()
    pixels.show()

    # 2. Check for a button press
    if button_pressed():
        # Move to the next animation (wrap around)
        current_anim = (current_anim + 1) % len(animations)

    # 3. A very short pause keeps the CPU from burning out
    time.sleep(0.02)
```

---

## 5.  Full Code (All Together)

```python
import board
import time
import neopixel
from digitalio import DigitalInOut, Direction

# Animation helpers
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.colorwipe import ColorWipe
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.color import RED, GREEN, BLUE, YELLOW

# -----------  NeoPixel  -----------------
pixel_pin = board.D6
pixel_num = 32

pixels = neopixel.NeoPixel(
    pixel_pin,
    pixel_num,
    brightness=0.5,
    auto_write=False,
)

# -----------  Button  -------------------
button_pin = board.D3
button = DigitalInOut(button_pin)
button.direction = Direction.INPUT

# -----------  Animations  ---------------
animations = [
    Pulse(pixels, speed=0.1, color=RED, pulse_width=3, reverse=True),
    Rainbow(pixels, speed=0.05),
    ColorWipe(pixels, speed=0.02, color=GREEN),
    Blink(pixels, speed=0.5, color=YELLOW, frames=2),
]

# -----------  Button press helper  ------
def button_pressed():
    """
    Return True only when the button is newly pressed.
    """
    current = button.value
    if current and not button_pressed.prev:
        button_pressed.prev = current
        return True
    button_pressed.prev = current
    return False

button_pressed.prev = False

# -----------  Main loop  ----------------
current_anim = 0

while True:
    # Run the current animation
    animations[current_anim].tick()
    pixels.show()

    # Switch animation on button press
    if button_pressed():
        current_anim = (current_anim + 1) % len(animations)

    time.sleep(0.02)
```

---

## 6.  Customising

| What to change | Where |
|----------------|-------|
| **Number of pixels** | `pixel_num` |
| **Button pin** | `button_pin` |
| **Add a new animation** | Add a new `Pulse`, `Rainbow`, … to the `animations` list |
| **Change animation parameters** | Modify the constructor arguments or set attributes after creating the object |
| **Different debounce** | Replace `time.sleep(0.02)` in `button_pressed()` with a larger delay or a more sophisticated debouncer (e.g., check state over 50 ms) |

---

### Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Nothing happens when button is pressed | The button is wired the opposite way (HIGH → LOW). | Change the logic in `button_pressed()` to look for a *falling* edge (use `if not current and button_pressed.prev:`). |
| Animations flicker or show garbage | `auto_write=False` but `pixels.show()` missing. | Make sure `.show()` is called after each `.tick()`. |
| Power flicker or LEDs burn out | Too high brightness or too many pixels. | Reduce `brightness` or cut down `pixel_num`. |

---

Enjoy experimenting with different patterns, colors, and speeds! 🚀


============================================================
Question: Please show me how to set up a rotary encoder knob to change a Neopixel thru the colors of the rainbow
============================================================
Below is a **stand‑alone CircuitPython sketch** that ties a 5‑pin rotary encoder (via a Seesaw breakout) to a single NeoPixel (or a short strip).  
Turning the knob walks the pixel through the full 360‑degree rainbow.

> **Hardware**  
> * Seesaw I²C breakout (any I²C‑capable board will do – the sketch uses `board.I2C()`).
> * Rotary encoder with 4 pins:  
>   * A → `SEESAW_PIN_A` (e.g. 2)  
>   * B → `SEESAW_PIN_B` (e.g. 3)  
>   * GND, VCC wired normally
> * NeoPixel data pin wired to a free digital pin (example uses `board.D5` – change as needed)
> * Optional: an extra push‑button switch (not used here)

> **Libraries**  
> * `adafruit_seesaw` (for the encoder)  
> * `rainbowio` (for the `colorwheel()` helper)  
> * `neopixel` (built‑in)

> **What the sketch does**  
> 1. Polls the encoder’s absolute position each loop.  
> 2. Detects any change (either clockwise or counter‑clockwise).  
> 3. Adds a fixed amount to a *hue* variable (0–255).  
> 4. Looks up the corresponding RGB value with `colorwheel()`.  
> 5. Sets the NeoPixel’s color and displays it.

---

## Full Code

```python
# ------------------------------------------------------------
# Rotary‑encoder → NeoPixel rainbow wheel
# ------------------------------------------------------------
import board
import neopixel
import time

# ----- Seesaw & Encoder -------------------------------------
import adafruit_seesaw.seesaw as ss
import adafruit_seesaw.rotaryio as rotaryio
from rainbowio import colorwheel

# 1. Create the Seesaw object (default I²C address is 0x36)
seesaw = ss.Seesaw(board.I2C(), addr=0x36)

# 2. Attach the incremental encoder.
#    Use the pins that your encoder is connected to on the Seesaw.
#    For example: pin 2 → encoder A, pin 3 → encoder B
SEESAW_PIN_A = 2
SEESAW_PIN_B = 3
encoder = rotaryio.IncrementalEncoder(seesaw, SEESAW_PIN_A, SEESAW_PIN_B)

# ----- NeoPixel ---------------------------------------------
# Replace board.D5 with whatever pin you wired the NeoPixel to.
# 1 NeoPixel (you can change the second argument to the length of your strip)
pixel = neopixel.NeoPixel(board.D5, 1, brightness=0.5, auto_write=False)

# ----- State variables ---------------------------------------
last_position = encoder.position   # start from the current physical position
hue = 0                            # 0 = red, 128 = cyan, 255 = red again

# ----- Main loop ---------------------------------------------
while True:
    # Read the absolute encoder position
    position = encoder.position

    # If the encoder has moved …
    if position != last_position:
        # How many detents (steps) did we move?  Positive = CW, negative = CCW
        delta = position - last_position

        # Each detent changes hue by 10 steps (0‑255 range).  
        # Increase this number for faster colour change or decrease for finer control.
        hue = (hue + delta * 10) % 256

        # Convert the hue to an RGB value
        rgb = colorwheel(hue)

        # Apply the colour to the pixel
        pixel[0] = rgb
        pixel.show()

        # Remember where we are for the next loop
        last_position = position

    # A tiny delay keeps the loop from hogging the CPU
    time.sleep(0.001)
```

---

## How It Works (step‑by‑step)

| Step | What happens | Why it matters |
|------|--------------|----------------|
| **1** | `seesaw = ss.Seesaw(board.I2C(), addr=0x36)` | Opens I²C communication with the Seesaw. |
| **2** | `encoder = rotaryio.IncrementalEncoder(seesaw, A, B)` | Binds the two encoder pins to a high‑level incremental‑encoder class that tracks the absolute position. |
| **3** | `pixel = neopixel.NeoPixel(...)` | Creates a NeoPixel object. `auto_write=False` lets us batch the color update. |
| **4** | `last_position = encoder.position` | Snapshot of the starting position. |
| **5** | In the loop: `position = encoder.position` | Read the current position each cycle. |
| **6** | `if position != last_position:` | Detect a change; otherwise skip expensive work. |
| **7** | `delta = position - last_position` | Number of detents moved. |
| **8** | `hue = (hue + delta * 10) % 256` | Shift hue forward/backward. 10 is an arbitrary step size that gives a pleasant pace. |
| **9** | `rgb = colorwheel(hue)` | Convert the hue (0‑255) into an RGB triplet covering the full rainbow. |
| **10**| `pixel[0] = rgb; pixel.show()` | Update the LED. |
| **11**| `last_position = position` | Prepare for next iteration. |
| **12**| `time.sleep(0.001)` | Small delay keeps CPU from over‑running while still being responsive. |

### Tweaking the Experience

| Parameter | Effect | Typical Value |
|-----------|--------|---------------|
| `delta * 10` | Hue change per detent | 5–15 (lower = finer, higher = faster) |
| `pixel.brightness` | Overall lightness | 0.2–1.0 |
| `time.sleep()` | Loop latency | 0.001–0.01 s |
| `colorwheel()` | Hue range | 0–255 (full cycle) |

If you want the knob to *wrap* smoothly from 0 to 255, the modulo operation `% 256` already takes care of that.

---

## Quick Hardware Checklist

| Component | Pin on Seesaw | Pin on Host Board |
|-----------|---------------|-------------------|
| Rotary A | 2 | – |
| Rotary B | 3 | – |
| GND | GND | GND |
| VCC | VCC | 3.3 V (or 5 V if your Seesaw supports it) |
| NeoPixel | – | D5 (or any free GPIO) |
| NeoPixel GND | – | GND |
| NeoPixel VCC | – | 3.3 V |

> **Tip**: If you have a breakout with an integrated LED (e.g. a “NeoPixel” board), just use that LED instead of wiring your own.

---

## Running the Code

1. Save the file as `code.py` on the CircuitPython USB drive.  
2. Power the board.  
3. The LED should start at red (hue 0).  
4. Turn the knob clockwise → the LED sweeps through yellow → green → cyan → blue → magenta → back to red.  
5. Turn counter‑clockwise → it goes the other way.

Happy coding – enjoy your rainbow‑controlled NeoPixel!


============================================================
Question: Show me how to read temperature from a BMP388 sensor
============================================================
Below is a **minimal, fully‑working CircuitPython sketch** that

1. Installs the BMP388 sensor (via the `adafruit_bmp3xx` library).  
2. Configures the sensor (optional oversampling).  
3. Reads the temperature (°C) and prints it to the REPL.  
4. (Optional) displays the temperature on a connected 0.96‑inch OLED or e‑Paper display using `displayio`.

> **Prerequisites**  
> * CircuitPython 8.x+  
> * `adafruit_bmp3xx` library (add to `lib/` on the CIRCUITPY drive).  
> * If you want to show the value on a screen, also add the `displayio` and font libraries (e.g. `adafruit_display_text`, `terminalio`).

---

## 1. Wiring

| BMP388 Pin | CircuitPython board (typical) |
|-----------|------------------------------|
| VIN       | 3.3 V (or 5 V if you use a level‑shifter) |
| GND       | GND |
| SCL       | SCL (usually `board.SCL`) |
| SDA       | SDA (usually `board.SDA`) |
| CS        | *Leave unconnected for I²C mode* |
| RST       | *Leave unconnected or tie to 3.3 V* |

> **Tip**: If you want to use SPI instead of I²C, connect `SCK`, `MISO`, `MOSI`, `CS` and `RST`, then create a `SPI` object in the sketch.

---

## 2. The Sketch

### 2.1. Temperature‑only (print to REPL)

```python
# bmp388_temp_only.py
import time
import board
import busio
import adafruit_bmp3xx

# 1. Create I²C bus
i2c = busio.I2C(board.SCL, board.SDA)

# 2. Instantiate the sensor (BMP388)
bmp = adafruit_bmp3xx.BMP3XX_I2C(i2c)

# 3. (Optional) tweak oversampling – higher values give smoother data but use more power
bmp.pressure_oversampling = 8          # 8× oversampling (default 1×)
bmp.temperature_oversampling = 2       # 2× oversampling (default 1×)

# 4. Main loop: read & print
while True:
    temp_c = bmp.temperature  # value in °C
    print(f"Temperature: {temp_c:.2f} °C")
    time.sleep(1)
```

Run this on your device and you should see a line printed every second:

```
Temperature: 23.46 °C
Temperature: 23.44 °C
...
```

### 2.2. Temperature + Display (OLED e‑Paper, etc.)

Below is a full example that shows the temperature on an OLED screen.  
Replace `display = board.DISPLAY` with whatever display object you’re using (`adafruit_ssd1306`, `adafruit_st7735r`, `adafruit_il0373`, etc.).  

```python
# bmp388_with_display.py
import time
import board
import busio
import adafruit_bmp3xx
import displayio
from adafruit_display_text import label
from terminalio import FONT

# --------------------------------------------------
# 1. Create I²C bus
i2c = busio.I2C(board.SCL, board.SDA)

# 2. Create the BMP388 sensor object
bmp = adafruit_bmp3xx.BMP3XX_I2C(i2c)
bmp.pressure_oversampling = 8
bmp.temperature_oversampling = 2

# 3. Initialize the display (make sure you have the correct driver for your panel)
#    The default `board.DISPLAY` works for boards like the Adafruit Feather RP2040 with built‑in display.
display = board.DISPLAY

# 4. Create a group that will hold everything you want on the screen
main_group = displayio.Group()
display.show(main_group)

# 5. Create a text label that will show the temperature
temp_label = label.Label(FONT, text="Temp: --.- °C", color=0xFFFFFF, x=5, y=10)
main_group.append(temp_label)

# 6. (Optional) Add a small static label
title = label.Label(FONT, text="BMP388 Temp", color=0xFFFFFF, x=5, y=0)
main_group.append(title)

# --------------------------------------------------
# 7. Main loop: update the temperature on the screen
while True:
    temp_c = bmp.temperature
    temp_label.text = f"Temp: {temp_c:.2f} °C"
    time.sleep(1)
```

**What the code does**

| Step | Explanation |
|------|-------------|
| 1 | Sets up the I²C bus using the board’s default pins. |
| 2 | Instantiates the BMP388 (`BMP3XX_I2C`). |
| 3 | Optional oversampling for better stability. |
| 4 | Uses the board’s built‑in display object. If you’re using a custom display, replace with the appropriate driver. |
| 5–6 | Builds a `Group` containing two text labels (a title and the dynamic temperature). |
| 7 | In the loop, reads `bmp.temperature` and updates the label’s text. |

---

## 3. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `AttributeError: 'BMP3XX_I2C' object has no attribute 'temperature'` | Using an older library that doesn’t expose the property | Upgrade `adafruit_bmp3xx` from `adafruit-circuitpython-bmp3xx` in your `lib/` folder. |
| No data / sensor not detected | Wrong I²C address or pull‑ups missing | The BMP388 default address is `0x77`. Ensure pull‑up resistors (~4.7 kΩ) are on SCL/SDA and the sensor is powered. |
| Temperature values drift wildly | Oversampling too low, or sensor not stabilized | Increase oversampling or add a short delay after initialization. |
| Display flickers | `displayio` not properly refreshed | Make sure the display driver is correct and that you’re not resetting the display object each loop. |

---

## 4. Optional Enhancements

| Feature | How to Add |
|---------|------------|
| **Logging to SD card** | Use `os`/`io` to open a CSV file and append `bmp.temperature` with a timestamp. |
| **Humidity** | The BMP388 does **not** measure humidity; use a dedicated sensor (e.g., HTU21D). |
| **Pressure** | `bmp.pressure` returns the pressure in hPa. |
| **Altitude** | `bmp.altitude` (requires setting `sea_level_pressure`). |
| **Low‑power mode** | Set `bmp.mode = adafruit_bmp3xx.MODE_LOWPOWER` and `bmp.standby_period = adafruit_bmp3xx.STANDBY_TC_1000`. |

---

### TL;DR

```python
import board, busio, adafruit_bmp3xx
i2c = busio.I2C(board.SCL, board.SDA)
bmp = adafruit_bmp3xx.BMP3XX_I2C(i2c)
while True:
    print(f"{bmp.temperature:.2f} °C")
    time.sleep(1)
```

Add a few lines of `displayio` and `label` if you want the value on an OLED or e‑Paper screen. Happy hacking!




============================================================
Question: How do I blink an LED?
============================================================
## Blink an LED with CircuitPython  
Below are two “cook‑books” you can copy‑paste into your `code.py`.  
* **Option A** – a *single LED* connected to a regular GPIO pin.  
* **Option B** – a *NeoPixel* (or Neo‑Pico NeoPixel) that blinks like the examples you posted.  

Both are written for CircuitPython 8.x+ (works the same in 7.x).  
Feel free to swap the pin names or the number of LEDs to match your board.

---

## 1.  Blink a normal LED (GPIO pin)

```python
# code.py
import board
import digitalio
import time          # only used for the simple sleep demo

# ------------- 1️⃣  Choose your pin ----------------------------------
# On a Feather M4 Express, for example, a single LED is on D13.
led_pin = board.D13

# ------------- 2️⃣  Configure the pin as an OUTPUT ------------------
led = digitalio.DigitalInOut(led_pin)
led.direction = digitalio.Direction.OUTPUT

# ------------- 3️⃣  Blink loop ---------------------------------------
while True:
    led.value = True      # LED ON
    time.sleep(0.5)       # pause 0.5 s
    led.value = False     # LED OFF
    time.sleep(0.5)       # pause 0.5 s
```

### Why this works  
| Step | What CircuitPython does | Why it matters |
|------|--------------------------|----------------|
| 1 | `board.D13` resolves to the actual pin number for the chosen board. | Keeps your code portable. |
| 2 | `digitalio.DigitalInOut` creates a pin object. `direction = OUTPUT` tells the microcontroller that the pin will drive a voltage (not read it). | You can’t set a pin to `True` unless it is configured as an output. |
| 3 | `led.value = True` drives the pin high (≈3 V). On most boards a built‑in LED is connected between this pin and ground, so the LED lights. | `value = False` pulls the pin low, turning the LED off. |
| 4 | `time.sleep(0.5)` simply pauses the loop. | The blink rate is 0.5 s on / 0.5 s off → 1 Hz. Change the delay to speed up or slow down. |

---

## 2.  Blink a NeoPixel (or Neo‑Pico NeoPixel)

```python
# code.py
import board
import neopixel
import time

# ------------- 1️⃣  Set the pin and number of pixels -----------------
pixel_pin = board.A3          # the pin connected to the NeoPixel strip
pixel_num = 30                # how many pixels you have

# ------------- 2️⃣  Create the NeoPixel object ----------------------
# brightness: 0.0 (off) – 1.0 (full)
# auto_write=False lets you update many pixels at once, then call .show()
pixels = neopixel.NeoPixel(
    pixel_pin,
    pixel_num,
    brightness=0.5,
    auto_write=False
)

# ------------- 3️⃣  Define a simple blink routine -------------------
def blink_one_color(color, on_time=0.5, off_time=0.5):
    """Set every pixel to the same color, then turn them all off."""
    # Turn on
    pixels.fill(color)
    pixels.show()
    time.sleep(on_time)

    # Turn off
    pixels.fill((0, 0, 0))  # black/off
    pixels.show()
    time.sleep(off_time)

# ------------- 4️⃣  Main loop ---------------------------------------
# Example: blink green, then blue, then red forever
while True:
    blink_one_color((0, 255, 0))   # green
    blink_one_color((0, 0, 255))   # blue
    blink_one_color((255, 0, 0))   # red
```

### What each line does

| Line | Purpose | Notes |
|------|---------|-------|
| `import board, neopixel, time` | Load CircuitPython modules | `board` gives board‑specific pin names |
| `pixel_pin = board.A3` | Pin that drives the NeoPixel data line | On many boards this is a valid pin; pick the one you wired. |
| `pixel_num = 30` | Number of NeoPixels in the strip | Must match the actual count. |
| `pixels = neopixel.NeoPixel(...)` | Create an object that talks to all pixels | `auto_write=False` gives you manual control; you call `.show()` when you’re ready to update the strip. |
| `blink_one_color()` | Convenience helper that lights all pixels, shows them, waits, then turns them off | Accepts a tuple of RGB values (0‑255 each). |
| `while True:` | Infinite loop that keeps blinking | Replace or extend the body to use your own colors or patterns. |

---

## 3.  A quick “animation” with Adafruit‑LED‑Animation (the style you posted)

If you want a *non‑blocking* blink that can run *alongside* other code, use the animation library:

```python
# code.py
import board
import neopixel
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.color import PURPLE, YELLOW

pixel_pin = board.A3
pixel_num = 30

pixels = neopixel.NeoPixel(pixel_pin, pixel_num, brightness=0.5, auto_write=False)

# Blink animation: purple flashes over a yellow background
blink = Blink(pixels, speed=0.5, color=PURPLE, background_color=YELLOW)

while True:
    blink.update()   # <‑ non‑blocking call that updates the LED strip
```

**Why use `Blink.update()` instead of a loop that sleeps?**  
`update()` returns immediately; you can put other code (e.g. sensor reads, button handling) between calls. The animation library handles the timing internally.

---

## 4.  Checklist before you run

| Item | Check |
|------|-------|
| Wiring | For a single LED: **Anode to pin, Cathode to GND** (with a 220 Ω resistor in series). <br> For NeoPixels: **Data pin → pin** (and a common 5 V supply). |
| Power | NeoPixels consume ~60 mA per pixel at full white. 30 pixels ≈ 1.8 A. Ensure your power source can supply enough current. |
| Libraries | Make sure `adafruit_led_animation` is in `lib/` if you use it. |
| `code.py` | Place the code on the root of the CIRCUITPY drive. |
| Save & eject | Save, safely remove the drive, plug it back in. The sketch will start immediately. |

---

### TL;DR  
* **Single LED**: `digitalio` → `led.value = True/False` → `time.sleep()`  
* **NeoPixel**: `neopixel` → `pixels.fill(color)` → `pixels.show()` → `time.sleep()`  
* **Animation**: `adafruit_led_animation` → `Blink.update()` inside a `while True` loop.

Happy blinking! 🎉

============================================================
Question: Show me how to read temperature from a sensor
============================================================
Below is a **ready‑to‑run CircuitPython sketch** that shows how to read temperature from a **TMP007 I²C digital temperature sensor** (ambient and object temp) and print it to the serial console (or use the values elsewhere).  
The same pattern works for any other digital sensor – just swap the library and the read‑method calls.

---

## 1. Hardware wiring (TMP007)

| TMP007 pin | Feather / Pi‑Pico pin | Description |
|------------|----------------------|-------------|
| VCC        | 3.3 V                | Supply voltage |
| GND        | GND                  | Ground |
| SDA        | SDA (I²C‑SDA)        | I²C data line |
| SCL        | SCL (I²C‑SCL)        | I²C clock line |
| CS (optional) | Not used (default address) | If you want to change the I²C address, pull this pin low. |

> **Tip:** On many boards you can enable the internal pull‑ups (see `busio.I2C(..., pull_up=True)` if your board requires it).  
> If you’re using a Feather‑M4 Express, you can simply do:
> ```python
> i2c = busio.I2C(board.SCL, board.SDA)
> ```

---

## 2. Required libraries

```bash
pip install adafruit-circuitpython-tmp007
```

Upload the library to your `lib/` folder on the CIRCUITPY drive.

---

## 3. Complete sketch

```python
# tmp007_demo.py
# Read and display temperatures from a TMP007 sensor
# (Ambient + Object temperature)

import time
import board
import busio
import adafruit_tmp007

# ------------------------------------------------------------------
# 1️⃣  Set up the I²C bus and the sensor object
# ------------------------------------------------------------------
i2c = busio.I2C(board.SCL, board.SDA)

# Create a TMP007 sensor instance
# (The constructor arguments are optional, the default address is 0x40)
sensor = adafruit_tmp007.TMP007(i2c)

# ------------------------------------------------------------------
# 2️⃣  Utility: Convert Celsius to Fahrenheit
# ------------------------------------------------------------------
def c_to_f(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return celsius * 9.0 / 5.0 + 32.0

# ------------------------------------------------------------------
# 3️⃣  Main loop – read and print temperatures
# ------------------------------------------------------------------
while True:
    # Die (chip) temperature – the sensor’s own internal temp
    die_temp_c = sensor.die_temperature
    die_temp_f = c_to_f(die_temp_c)

    # Object temperature – the temperature of the surface the sensor faces
    obj_temp_c = sensor.object_temperature
    obj_temp_f = c_to_f(obj_temp_c)

    # Print nicely formatted output
    print(f"Die temperature   : {die_temp_c:0.3f} °C / {die_temp_f:0.3f} °F")
    print(f"Object temperature: {obj_temp_c:0.3f} °C / {obj_temp_f:0.3f} °F")
    print("-" * 40)

    # Delay a bit before the next sample
    time.sleep(1.0)
```

**What’s happening?**

| Step | Code | What it does |
|------|------|--------------|
| 1 | `i2c = busio.I2C(board.SCL, board.SDA)` | Opens the I²C bus using the board’s standard pins. |
| 2 | `sensor = adafruit_tmp007.TMP007(i2c)` | Instantiates the TMP007 driver. The driver talks to the sensor via I²C. |
| 3 | `sensor.die_temperature` | Reads the internal chip temperature (°C). |
| 4 | `sensor.object_temperature` | Reads the ambient surface temperature (°C). |
| 5 | `c_to_f` | Simple helper to convert °C → °F. |
| 6 | The `while True` loop | Continuously samples every second and prints. |

---

## 4. Adapting to other sensors

| Sensor | Library | How to read temp |
|--------|---------|------------------|
| TMP007 | `adafruit_tmp007` | `sensor.die_temperature` & `sensor.object_temperature` |
| TMP117 | `adafruit_tmp117` | `sensor.temperature` |
| DS18B20 | `adafruit_ds18x20` | `sensor.read_temp()` |
| TMP36 (analog) | `board.A0` & `analogio.AnalogIn` | Convert voltage to temp in code |
| Thermistor (example 2) | `adafruit_thermistor` | `thermistor.temperature` |

---

## 5. Running the sketch

1. Save the code as `tmp007_demo.py` on the CIRCUITPY drive.  
2. Plug in the Feather/Arduino board.  
3. Open the REPL (or a serial terminal) at 115 200 baud.  
4. You should see a stream of temperatures updating every second.

---

## 6. Common pitfalls & debugging

| Problem | Fix |
|---------|-----|
| **No output** | Make sure the sensor is powered and wired to the correct I²C pins. |
| **`OSError: [Errno 5] I/O error`** | Check that the I²C bus is enabled and that no other device is using the same address. |
| **`AttributeError: 'TMP007' object has no attribute 'die_temperature'`** | Make sure you installed the correct library version and that your CircuitPython firmware is recent enough. |
| **Temperature always 0 or NaN** | Verify the sensor is correctly connected and that the pull‑up resistors on SDA/SCL are present if your board doesn’t provide them. |

---

### TL;DR

```python
import time, board, busio, adafruit_tmp007

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_tmp007.TMP007(i2c)

while True:
    print(f"Die:  {sensor.die_temperature:.2f} °C")
    print(f"Obj:  {sensor.object_temperature:.2f} °C")
    time.sleep(1)
```

Add a helper function if you need Fahrenheit, and you’re done!