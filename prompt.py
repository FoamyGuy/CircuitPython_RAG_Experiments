
from circuitpython_rag import CircuitPythonRAG

# Usage
if __name__ == "__main__":
    # Setup (run once)
    rag = CircuitPythonRAG()


    # Test queries
    questions = [
        # "How do I blink an LED?",
        # "Show me how to read temperature from a BMP388 sensor",
        # "Please show me how to set up a rotary encoder knob to change a Neopixel thru the colors of the rainbow",
        #"Please show me how to setup multiple neopixel animations and change between them with the press of a button."
        # "How to control a servo motor?",
        #"How do can I fetch the latest value from an AdafruitIO feed and show it on a built-in display with a custom font?"
        # "Setup I2C communication with a display"

        #"Can you write an CircuitPython example that uses one digital input connected to a switch and one digital output connected to a LED. When the switch is in position A the LED should blink, and when the switch is in position B the LED should be off."
        "For CircuitPython, can you tell me what the `digitalio` core module does and how to use it, with a basic example?"
    ]

    for question in questions:
        print(f"\n{'=' * 60}")
        print(f"Question: {question}")
        print("=" * 60)
        answer = rag.query(question)
        print(answer)