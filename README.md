# CircuitPython RAG Experiments
My experiments with Retrieval-Augmented Generation (RAG) to setup a local LLM that is well suited to writing CircuitPython specific code and explanations.


### RAG Architecture Overview
Prompt Question → Vector Search → Relevant Code Examples → LLM + Context → CircuitPython-specific Answer


## Usage
Prompting a local model and using RAG requires several setup steps that must be done the first time. Subsequent prompts can load from cached files instead of doing the full process.

### Full Setup
The full process from scratch.

- Clone bundle and get submodules
```shell
git clone https://github.com/adafruit/Adafruit_CircuitPython_Bundle.git
cd Adafruit_CircuitPython_Bundle/
./update-submodules.sh
```
- Run data collector - This script is responsible for extracting relevant content from the material that we want to give the LLM access to. It outputs the `circuitpython_data/` directory with copies of python scripts, and metadata files about them. Right it pulls examples from the libraries in the adafruit bundle.
```shell
python collector.py
```
- Run data chunker - This script chunks the data into pieces that are sized appropriately for the RAG process. It outputs `rag_ready_chunks.json`
```shell
python chunker.py
```
- Process chunks & Build Vector Database - The first time the `CircuitPythonRAG` class is used it will process the chunks that it finds in `rag_ready_chunks.json` and load them into a Vector database. The Vector database gets saved into `chroma_db/`. This process takes several minutes to complete for the ~4400 chunks that result from bundle examples. Subsequent usages of `CircuitPythonRAG` will load from `chroma_db/` instead of having to process everything again.
- Prompt the model - To issue a prompt to the model create an instance of `CircuitPythonRAG` and call the `query()` function on it passing in prompt as a string. The `prompt.py` script does this when executed. There is a list of questions in the script that will be used as prompts when executed.
```shell
python prompt.py
```


### Use Cached Vector Database
Save time by using the cached chunk vector database instead of building it.

- Clone bundle and get submodules
```shell
git clone https://github.com/adafruit/Adafruit_CircuitPython_Bundle.git
cd Adafruit_CircuitPython_Bundle/
./update-submodules.sh
```
- No need to run `collector.py`, or `chunker.py`, just use `rag_ready_chunks.json` that is in the repo.
- `CircuitPythonRAG` will load the vector database from `chroma_db/` in the repo instead of generating it.
- Prompt the model - To issue a prompt to the model create an instance of `CircuitPythonRAG` and call the `query()` function on it passing in prompt as a string. The `prompt.py` script does this when executed. There is a list of questions in the script that will be used as prompts when executed.
```shell
python prompt.py
```

## File Descriptions

- `Training local LLM for CircuitPython - Claude.pdf` - A conversation log with Claude explaining to me many of the concepts used in this process and providing code that has been adapted and used in this repo.
- `observations.md` - Examples of question & answers that were generated using the RAG process documented in this repo.
- `chroma_db/` - The persistent cache directory for the vector database.
- `chroma_db_bundle_only/` - Clean copy chromadb containing a vector database generated from bundle examples.


## Ideas for Improvement

- Add more data to be processed
  - core stubs
  - library code itself (I think right now it's getting example code only)
  - Select code from learn guide repo i.e. everything from CircuitPython essentials guide
  - md files exported from Adafruit Learn
  - Board specific information from circuitpython.org site or the data that it is built from. I think this would make it better at not hallucinating device/built-in peripherals combinations that do not actually exist.
- Explore other Chunking strategies
  - Claude recommended "Semantic Chunking by Hardware Component" as one option to try. 