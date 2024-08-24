# Stock Trading Simulator

## Getting Started

### Cloning the Repository

    git clone https://github.com/jkmathilda/stock_trading_simulator.git

### Setting up a Virtual Environment
    pyenv versions

    pyenv local 3.11.6

    echo '.env'  >> .gitignore
    echo '.venv' >> .gitignore

    python -m venv .venv        # create a new virtual environment

    source .venv/bin/activate   # Activate the virtual environment

    python -V                   # Check a python version

### Install the required dependencies

    pip list

    pip install -r requirements.txt

    pip freeze | tee requirements.txt.detail

### Running the Application

    python -m streamlit run main.py

### Deactivate the virtual environment

    deactivate

### Example
<img width="1710" alt="Screenshot 2024-08-24 at 11 03 07 AM" src="https://github.com/user-attachments/assets/40ab0c78-91f0-4920-b0c1-a6e8cb49e843">