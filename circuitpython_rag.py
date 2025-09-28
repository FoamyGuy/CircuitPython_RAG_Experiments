import json
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
import ollama


class CircuitPythonRAG:
    def __init__(self, persist_directory="./chroma_db"):
        # self.client = chromadb.Client()
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        # self.collection = self.client.create_collection("circuitpython_code")

        # Try to get existing collection, create if doesn't exist
        try:
            self.collection = self.client.get_collection("circuitpython_code")
            print(f"Loaded existing collection with {self.collection.count()} examples")
        except:
            self.collection = self.client.create_collection("circuitpython_code")
            print("Created new collection")
            self.populate_from_chunks("rag_ready_chunks.json")





    def add_code_example(self, code, description, metadata=None):
        """Add a single code example to the vector database"""
        # Create embedding from description + code
        embedding_text = f"{description}\n{code}"
        embedding = self.embedder.encode(embedding_text)

        self.collection.add(
            embeddings=[embedding.tolist()],
            documents=[code],
            metadatas=[metadata or {}],
            ids=[f"code_{len(self.collection.get()['ids'])}"]
        )

    def populate_from_chunks(self, chunks_file="rag_ready_chunks.json"):
        """Load all your processed chunks into the RAG system"""
        print("Loading chunks into vector database...")

        with open(chunks_file, 'r') as f:
            chunks = json.load(f)

        for i, chunk_data in enumerate(chunks):
            code = chunk_data['content']
            metadata = chunk_data['metadata']

            # Create a good description for embedding
            description = self._create_description(code, metadata)

            # Add to vector database
            self.add_code_example(
                code=code,
                description=description,
                metadata={
                    **metadata,
                    'chunk_id': i
                }
            )

            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1} chunks...")

        print(f"Successfully loaded {len(chunks)} code examples!")

    def _create_description(self, code, metadata):
        """Create a good description for embedding"""
        descriptions = []

        # Add chunk type info
        chunk_type = metadata.get('chunk_type', 'code')
        descriptions.append(f"CircuitPython {chunk_type}")

        # Add library info
        if 'library' in metadata:
            descriptions.append(f"using {metadata['library']} library")

        # Add function name if available
        if 'function_name' in metadata:
            descriptions.append(f"function: {metadata['function_name']}")

        # Add components if available
        if 'components' in metadata:
            components = ', '.join(metadata['components'])
            descriptions.append(f"components: {components}")

        # Extract key concepts from the code itself
        code_concepts = self._extract_code_concepts(code)
        if code_concepts:
            descriptions.append(f"concepts: {', '.join(code_concepts)}")

        return ' '.join(descriptions)

    def _extract_code_concepts(self, code):
        """Extract key concepts from code for better searchability"""
        concepts = []

        # Look for common CircuitPython patterns
        patterns = {
            'LED control': ['led', 'digitalio.DigitalInOut', 'board.LED'],
            'PWM': ['pwmio.PWMOut', 'duty_cycle'],
            'I2C communication': ['busio.I2C', 'i2c'],
            'SPI communication': ['busio.SPI', 'spi'],
            'Analog input': ['analogio.AnalogIn'],
            'NeoPixel': ['neopixel', 'NeoPixel'],
            'Servo control': ['servo', 'adafruit_motor.servo'],
            'Display': ['displayio'],
            'Sensor reading': ['temperature', 'humidity', 'pressure'],
            'Time delays': ['time.sleep'],
            'Loop control': ['while True', 'for '],
        }

        code_lower = code.lower()
        for concept, keywords in patterns.items():
            if any(keyword.lower() in code_lower for keyword in keywords):
                concepts.append(concept)

        return concepts[:5]  # Limit to avoid too long descriptions

    def query(self, question, model="gpt-oss:20b", n_results=3):
        """Query the RAG system"""
        # Search for relevant code
        query_embedding = self.embedder.encode(question)
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )

        if not results['documents'][0]:
            return "No relevant CircuitPython examples found."

        # Build context from retrieved examples
        context_parts = []
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            context_parts.append(f"Example {i + 1} ({metadata.get('chunk_type', 'code')}):\n{doc}")

        context = "\n\n" + "=" * 50 + "\n\n".join(context_parts)

        # Generate response with ollama
        prompt = f"""Based on these CircuitPython examples:

{context}

Question: {question}

Provide a specific CircuitPython solution with explanations:"""

        response = ollama.chat(model=model, messages=[{
            'role': 'user',
            'content': prompt
        }])

        return response['message']['content']