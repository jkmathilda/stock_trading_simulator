# Stock Trading Simulator

This simulator is designed to implement and optimize the Bollinger Bands trading strategy. It automatically buys stock when the close price touches or drops below the lower Bollinger Band and sells stock when the close price meets or exceeds the upper Bollinger Band. You can customize the amount of stock to buy and sell with each trade, allowing you to experiment with different strategies. The simulator also tests various combinations of buy and sell amounts, identifying the most effective strategy among those tested to optimize your trading performance.

## Getting Started

### Cloning the Repository

    git clone https://github.com/jkmathilda/stock_trading_simulator.git

### Setting up a Virtual Environment

    cd stock_trading_simulator

    pyenv versions

    pyenv local 3.12.5

    echo '.env'  >> .gitignore
    echo '.venv' >> .gitignore

    python -m venv .venv        # create a new virtual environment

    source .venv/bin/activate   # Activate the virtual environment

    python -V                   # Check a python version

    # pyenv install -list | grep 3.12
    # pyenv install 3.12.5
    
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
<img width="1710" src="https://github.com/user-attachments/assets/74af0def-76d6-45f0-a0e5-e45641d9d4ac">
