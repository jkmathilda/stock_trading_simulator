import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from datetime import date, timedelta

@st.cache_data(ttl=1200)  # Unit: seconds. never expire (default)
def get_stock_data(ticker, start_date, end_date):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    stock_data = stock_data.dropna(how='any')
    return stock_data

def calculate_atr(stock_data, breakout_multiplier):
    ##### 목표가 구하기 #####
    # 1) 고저 변동폭
    stock_data['Range'] = stock_data['High'] - stock_data['Low'] 
    stock_data['k'] = breakout_multiplier
    
    # 2) 목표가 한칸 내려주고 (shift), 이후 k값을 곱한 목표가 계산
    stock_data['Target'] = stock_data['Open'] + stock_data['Range'].shift(1) * breakout_multiplier
        
    ##### 매수 시뮬레이션 #####
    # 당일의 고가 df['High']가 df['target']값보다 클 경우, 이는 목표가를 상향돌파했다는 것이므로 이때는 df ['ror']에 df ['Close'] / df['Target']을 추가한다.
    # 만약 df['High']가 df['target']보다 낮을 경우, 당일에 목표가를 돌파한 적이 없다는 것이므로 df['ror']에 1을 추가한다.
    stock_data['Buy'] = stock_data['High'] > stock_data['Target']
    stock_data['ror'] = np.where(stock_data['High'] > stock_data['Target'], stock_data['Close'] / stock_data['Target'], 1)  

    # 최종 누적 산출
    stock_data['Profit'] = stock_data['ror'].cumprod()

    return stock_data

def initialize_trade_columns(stock_data, initial_investment):
    stock_data['Signal'] = 0
    stock_data['Trade_Amount'] = 0.0
    stock_data['Trade_Count'] = 0.0
    stock_data['Shares_held'] = 0.0
    stock_data['Portfolio_Value'] = float(initial_investment)
    return stock_data

@st.cache_data
def calculate_backtest(stock_data, breakout_multiplier, initial_investment):
    stock_data = add_stock_data(stock_data, breakout_multiplier)
    stock_data = simulate_trading(stock_data, initial_investment)
    stock_data = stock_data.sort_index(ascending=True)
    final_portfolio_value = stock_data['Portfolio_Value'].iloc[-1]
    total_profit_ratio = (final_portfolio_value - initial_investment) / initial_investment * 100
    return final_portfolio_value, total_profit_ratio

@st.cache_data
def add_stock_data(stock_data, breakout_multiplier):
    stock_data = pd.DataFrame(stock_data, dtype="float")
    stock_data = calculate_atr(stock_data, breakout_multiplier)
    return stock_data

@st.cache_data
def simulate_trading(stock_data, initial_investment):
    stock_data['Portfolio_Value'] = stock_data['Profit'] * initial_investment
    return stock_data

def plot_volatility(stock_data, breakout_multiplier):
    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax1.plot(stock_data.index, stock_data['Close'], label="Close Price", color='black', linestyle='-')
    ax1.fill_between(stock_data.index, 
                     stock_data['Low'].shift() - (stock_data['Range'] * breakout_multiplier), 
                     stock_data['High'].shift() + (stock_data['Range'] * breakout_multiplier), 
                     color='RED', alpha=0.3)
    
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price')
    ax1.legend(fontsize=8)
    ax1.grid(True, axis='y')
    plt.title('Stock Price with Volatility Breakout Levels')

def plot_signals(stock_data, show_buy_timing):
    if show_buy_timing:
        buy_signals = stock_data[stock_data['Buy'] == 1]
        plt.plot(buy_signals.index, buy_signals['Close'], '^', markersize=10, color='green', label='Buy Signal')

@st.cache_data
def generate_graph(stock_data, show_buy_timing, breakout_multiplier):
    plt.figure(figsize=(10, 5))
    plt.plot(stock_data.index, stock_data['Close'], label='Close Price', color='black')
    
    plot_volatility(stock_data, breakout_multiplier)  # Volatility breakout levels 그래프 추가
    plot_signals(stock_data, show_buy_timing)
    
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend(fontsize=8)
    plt.grid(True, axis='y')
    plt.title('Stock Price with Volatility Breakout Strategy')   
    st.pyplot(plt)

@st.cache_data
def generate_graph2(stock_data):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(stock_data.index, stock_data['Portfolio_Value'], label='Total Asset Values')

    plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
    plt.title('Portfolio Values Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Amount')
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
    
@st.cache_data
def generate_multiple_backtest(stock_data, initial_investment):
    st.markdown(f"<p style='font-size:18px; color:MediumAquaMarine;'>Backtesting Results</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        results = []
        for breakout_multiplier in np.arange(0.1, 0.9, 0.1):
            final_portfolio_value2, total_profit_ratio2 = calculate_backtest(stock_data, breakout_multiplier, initial_investment)
            results.append({
                'Magic Number(k)': breakout_multiplier,
                'Final Portfolio Value': final_portfolio_value2,
                'Total Profit Ratio (%)': total_profit_ratio2
            })
        results_df = pd.DataFrame(results)
        results_df['Profit Ranking'] = results_df['Final Portfolio Value'].rank(ascending=False, method='min').astype(int)
        styled_df = results_df.style.apply(
            lambda row: ['background-color:LightCyan'] * len(row) if row['Profit Ranking'] == 1 else [''] * len(row),
            axis=1
        )
        st.dataframe(styled_df, width=600, height=350)
        # st.write(styled_df)
        
    with col2:
        plt.figure(figsize=(10, 6))
        plt.plot(results_df['Magic Number(k)'], results_df['Final Portfolio Value'], marker='o', linestyle='-', color='b', label='Final Portfolio Value')
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))   # y-axis to integer
        plt.xlabel('Magic Number (k)')
        plt.ylabel('Final Portfolio Value')
        plt.title('Final Portfolio Value by Magic Number (k)')
        plt.grid(True)
        st.pyplot(plt)
        
def sidebar_options():
    ticker = st.sidebar.selectbox(
        "Select Stock Ticker", 
        ["TQQQ", "QQQ", "SOXL", "SOXX", "GOOGL", "MSFT", "AAPL", "NVDA", "AMZN"],
        index=0
    )
    
    today = date.today()
    default_start_date = today - timedelta(days=365)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start Date", default_start_date)
    with col2:
        end_date = st.date_input("End Date", today)
        
    if start_date > today or end_date > today or start_date > end_date:
        st.sidebar.error("Invalid date selection.")
        start_date = default_start_date
        end_date = today

    show_dataset_asecending = st.sidebar.checkbox("Show Dataset Ascending", value=True)
    show_multiple_backtest = st.sidebar.checkbox("Show Multiple Backtesting Results", value=False)
    breakout_multiplier = st.sidebar.slider("Breakout Multiplier(k)", min_value=0.0, max_value=1.0, value=0.4, step=0.1)
    
    show_buy_timing, show_sell_timing = False, False        
    with st.sidebar.expander("### Graph Options", expanded=True):
        show_buy_timing = st.checkbox("Display Buy Timing", key="buy", value=False, help="Display buy signals when the close price touches the lower Bollinger band.")
    
    initial_investment = st.sidebar.number_input("Initial Investment Amount", min_value=0, value=1500000, step=10000)

    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='text-align: center; font-size: 12px;'>Coded by Mathilda</p>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='text-align: center; font-size: 12px;'>@2024</p>", unsafe_allow_html=True)
    
    return (ticker, start_date, end_date, breakout_multiplier, 
            show_dataset_asecending, show_buy_timing,
            initial_investment, show_multiple_backtest)

def main():
    st.set_page_config(page_title="Stock Price Viewer", page_icon="📈", layout='wide')
    st.title("📈 Stock Investment Simulator (Volatility Breakout Strategy)")
    
    sidebar_result = sidebar_options()
    
    if sidebar_result is not None:
        (ticker, start_date, end_date, breakout_multiplier, 
        show_dataset_asecending, show_buy_timing,
        initial_investment, show_multiple_backtest) = sidebar_result
        
        stock_data = get_stock_data(ticker, start_date, end_date)
        # print(stock_data)

        stock_data = add_stock_data(stock_data, breakout_multiplier)
        stock_data = simulate_trading(stock_data, initial_investment).sort_index(ascending=show_dataset_asecending)
        stock_data = stock_data.sort_index(ascending=show_dataset_asecending)
        # print(stock_data)
        
        st.dataframe(stock_data, width=1200, height=400)
        
        final_portfolio_value = stock_data.sort_values(by='Date', ascending=True)['Portfolio_Value'].iloc[-1]
        total_profit_ratio = (final_portfolio_value - initial_investment) / initial_investment * 100
        color = "hotpink" if total_profit_ratio > 0 else "blue"
        st.markdown(f"<p style='font-size:18px; color:{color};'>Final Portfolio Amount : {final_portfolio_value:,.2f} ({total_profit_ratio:.2f}%)</p>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        if show_multiple_backtest:
            col1_expanded_flag, col2_expanded_flag = False, False
        else:
            col1_expanded_flag, col2_expanded_flag = True, True
            
        with col1:
            with st.expander("### Show Graph : Stock Price with Volatility Breakout", expanded=col1_expanded_flag):
                generate_graph(stock_data, show_buy_timing, breakout_multiplier)

        with col2:
            with st.expander("### Show Graph : Total Asset Change", expanded=col2_expanded_flag):
                generate_graph2(stock_data)
        
        if show_multiple_backtest:
            generate_multiple_backtest(stock_data, initial_investment)

if __name__ == "__main__":
    main()