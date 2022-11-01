# Pitch Deck Review

PITCH DECK REVIEWING TOOL is a Flask projet to scoring and reviewing pdf pitch deck.

## Installation

### Step 1: Create a new conda environment

```bash
conda create -m env_name python==3.8
```

### Step 2: Activate the environment

On linux

```bash
source env_name/bin/activate
```

On Windows

```bash
activate env_name
```

### Step 3: install Microsoft visual C++ (Only on windows)

Install [Microsoft visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/). During the installation select Desktop developement with c++ and install.

### Step 4: Install dependancies in your environment

Use the following command to install all requirements.

```bash
pip install -r requirements.txt
```

### Step 5: Environment manager

```bash
pip install python-dotenv
```

### Step 6: Change dictionary path

-Open .env file and find "DIC_PATH" and "AFF_PATH".
-Add root path to data folder in the project.
example : DIC_PATH=C:\Users\tabou\Desktop\Pitch_deck/data/dictionnary/en_US
DIC_PATH=C:\Users\tabou\Desktop\Pitch_deck/data/dictionnary/en_US

### step 7: Install tesseract-OCR

-Download on this link [tesseract-w32.exe](https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w32-setup-v4.0.0-beta.1.20180414.exe) and install

-Add tesseract installation to the PATH variable environment.

-restart you system to update changes.

-Active the environment like mentionned in step 2.

## Usage

To start the project enter the following command.

```python
flask run
```

Past this link in your browser http://127.0.0.1:5000/

## License

[MIT](https://choosealicense.com/licenses/mit/)
