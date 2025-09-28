
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
        "Please show me how to setup multiple neopixel animations and change between them with the press of a button."
        # "How to control a servo motor?",
        # "Setup I2C communication with a display"
    ]

    for question in questions:
        print(f"\n{'=' * 60}")
        print(f"Question: {question}")
        print("=" * 60)
        answer = rag.query(question)
        print(answer)