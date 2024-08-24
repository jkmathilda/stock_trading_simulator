import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from datetime import date, timedelta

@st.cache_data
def get_stock_data(ticker, start_date, end_date):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    return stock_data

@st.cache_data
def calculate_moving_averages(stock_data, periods):
    for period in periods:
        stock_data[f'SMA_{period}'] = stock_data['Close'].rolling(window=period).mean()
    return stock_data

@st.cache_data
def calculate_bollinger_bands(stock_data):
    rolling_mean = stock_data['Close'].rolling(window=20).mean()
    rolling_std = stock_data['Close'].rolling(window=20).std()
    stock_data['BB_mid_20'] = rolling_mean
    stock_data['BB_upper_20'] = rolling_mean + (rolling_std * 2)
    stock_data['BB_lower_20'] = rolling_mean - (rolling_std * 2)
    return stock_data

def initialize_trade_columns(stock_data, initial_investment):
    stock_data['Signal'] = 0
    stock_data['Trade_Amount'] = 0.0
    stock_data['Trade_Count'] = 0.0
    stock_data['Shares_held'] = 0.0
    stock_data['Portfolio_Value'] = float(initial_investment)
    return stock_data

@st.cache_data
def calculate_signals(stock_data):
    stock_data.loc[stock_data['Close'] < stock_data['BB_lower_20'], 'Signal'] = 1
    stock_data.loc[stock_data['Close'] > stock_data['BB_upper_20'], 'Signal'] = -1
    return stock_data

@st.cache_data
def calculate_backtest(stock_data, moving_average_periods, initial_investment, buy_portion, sell_portion):
    stock_data = add_stock_data(stock_data, moving_average_periods, initial_investment, buy_portion, sell_portion)
    
    stock_data = stock_data.sort_index(ascending=True)
    
    final_portfolio_value = stock_data['Portfolio_Value'].iloc[-1]
    total_profit_ratio = (final_portfolio_value - initial_investment) / initial_investment * 100
                
    return final_portfolio_value, total_profit_ratio

@st.cache_data
def add_stock_data(stock_data, moving_average_periods, initial_investment, buy_portion, sell_portion):
    df = stock_data
    df = calculate_moving_averages(df, moving_average_periods)
    df = calculate_bollinger_bands(df)
    
    df = initialize_trade_columns(df, initial_investment)
    df = calculate_signals(df)
    df = process_trades(df, initial_investment, buy_portion, sell_portion)
    
    # print(df)
    return df

@st.cache_data
def process_trades(stock_data, initial_investment, buy_portion, sell_portion):
    cash = initial_investment
    trade_money = initial_investment // buy_portion
    shares = 0
    
    for index, row in stock_data.iterrows():
        # Buy signal
        if row['Signal'] == 1 and trade_money > row['Close'] and cash >= trade_money:
            shares_bought = trade_money // row['Close']
            cash -= shares_bought * row['Close']
            shares += shares_bought
            stock_data.at[index, 'Trade_Amount'] = shares_bought * row['Close'] # Show shares bought
            stock_data.at[index, 'Trade_Count'] = shares_bought  # Show shares bought in this trade
        
        # Sell signal
        elif row['Signal'] == -1 and shares > 0:
            shares_to_sell = shares // sell_portion
            if shares_to_sell > 0:
                sell_amount = shares_to_sell * row['Close']
                cash += sell_amount
                shares -= shares_to_sell
                stock_data.at[index, 'Trade_Amount'] = -sell_amount  # Show shares sold
                stock_data.at[index, 'Trade_Count'] = shares_to_sell  # Show shares sold in this trade
        
        # Update shares held and portfolio value
        stock_data.at[index, 'Shares_held'] = shares
        stock_data.at[index, 'Portfolio_Value'] = shares * row['Close'] + cash
        
    return stock_data

def plot_moving_averages(stock_data, periods):
    colors = ['blue', 'green', 'red', 'orange', 'purple', 'brown']
    for i, period in enumerate(periods):
        color = colors[i % len(colors)]  # Cycle through colors
        plt.plot(stock_data.index, stock_data[f'SMA_{period}'], label=f'SMA {period}', color=color)

def plot_bollinger_bands(stock_data, show_bollinger):
    if show_bollinger:
        valid_data = stock_data.dropna(subset=['BB_upper_20', 'BB_lower_20'])
        plt.fill_between(
            valid_data.index, valid_data['BB_upper_20'], valid_data['BB_lower_20'], 
            color='blue', alpha=0.1, label='Bollinger Bands (20-day)'
        )

def plot_signals(stock_data, show_buy_timing, show_sell_timing):
    if show_buy_timing:
        buy_signals = stock_data[stock_data['Signal'] == 1]
        plt.plot(buy_signals.index, buy_signals['Close'], '^', markersize=10, color='red', label='Buy Signal')

    if show_sell_timing:
        sell_signals = stock_data[stock_data['Signal'] == -1]
        plt.plot(sell_signals.index, sell_signals['Close'], 'v', markersize=10, color='blue', label='Sell Signal')

@st.cache_data
def generate_graph(stock_data, moving_average_periods, show_bollinger, show_buy_timing, show_sell_timing):
    plt.figure(figsize=(10, 5))
    plt.plot(stock_data.index, stock_data['Close'], label='Close Price', color='black')
    
    plot_moving_averages(stock_data, moving_average_periods)
    plot_bollinger_bands(stock_data, show_bollinger)
    plot_signals(stock_data, show_buy_timing, show_sell_timing)
    
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend(fontsize=8)
    plt.grid(True, axis='y')
    plt.title('Stock Price with SMA')   
    st.pyplot(plt)

@st.cache_data
def generate_graph2(stock_data):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(stock_data.index, stock_data['Portfolio_Value'], label='Total Asset Values')

    # y-axis to integer
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
        
    positive_trades = stock_data[stock_data['Trade_Amount'] * stock_data['Signal'] > 0]
    ax.bar(positive_trades.index, positive_trades['Trade_Amount'], color='green', alpha=1, label='Buy Amount')
    
    negative_trades = stock_data[stock_data['Trade_Amount'] * stock_data['Signal'] < 0]
    ax.bar(negative_trades.index, negative_trades['Trade_Amount'], color='red', alpha=1, label='Sell Amount')
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Amount')
    ax.legend()
    ax.grid(True)
    plt.title('Portfolio Values Over Time')
    st.pyplot(fig)

@st.cache_data
def generate_multiple_backtest(stock_data_orig, moving_average_periods, initial_investment):
    st.markdown(f"<p style='font-size:18px; color:MediumAquaMarine;'>Backtesting Results</p>", unsafe_allow_html=True)
    stock_data_for_backtest = stock_data_orig.drop(columns=['Open', 'High', 'Low'])
    
    col1, col2 = st.columns(2)
    with col1:
        # Initialize a list to store the results
        results = []

        # Loop through buy and sell portions
        for buy_portion in range(2, 21):  # from 2 to 20
            for sell_portion in range(2, 11):  # from 2 to 10
                final_portfolio_value2, total_profit_ratio2 = calculate_backtest(stock_data_for_backtest, moving_average_periods, initial_investment, buy_portion, sell_portion)
                results.append({
                    'Buy Portion': buy_portion,
                    'Sell Portion': sell_portion,
                    'Final Portfolio Value': final_portfolio_value2,
                    'Total Profit Ratio (%)': total_profit_ratio2
                })

        # Convert the list to a DataFrame
        results_df = pd.DataFrame(results)

        # Final Portfolio Value sort descending, add ranking
        results_df['Profit Ranking'] = results_df['Final Portfolio Value'].rank(ascending=False, method='min').astype(int)
        # results_df = results_df.sort_values(by='Final Portfolio Value', ascending=False)
        
        styled_df = results_df.style.apply(
            lambda row: ['background-color:LightCyan'] * len(row) if row['Profit Ranking'] == 1 else [''] * len(row),
            axis=1
        )
        
        st.write(styled_df)
        
    with col2:
        # graph
        plt.figure(figsize=(10, 6))
        for key, grp in results_df.groupby('Sell Portion'):
            plt.plot(grp['Buy Portion'], grp['Final Portfolio Value'], label=f'Sell Portion {key}', marker='o')
            
        # y-axis to integer
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
        
        plt.title('Final Portfolio Value by Buy and Sell Portion Units')
        plt.xlabel('Buy Portion Unit')
        plt.ylabel('Final Portfolio Value')
        plt.legend(title='Sell Portion Unit')
        plt.grid(True)
        st.pyplot(plt)

def sidebar_options():
    ticker = st.sidebar.selectbox(
        "Select Stock Ticker", 
        ["TQQQ", "QQQ", "SOXL", "SOXX", "GOOGL", "MSFT", "AAPL", "NVDA", "AMZN", "TSLA", "COST"],
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
    show_bollinger = st.sidebar.checkbox("Show Bollinger Bands", value=True)
    
    show_buy_timing, show_sell_timing = False, False        
    if show_bollinger: 
        with st.sidebar.expander("### Bollinger Bands Options", expanded=True):
            show_buy_timing = st.checkbox("Display Buy Timing", key="buy", value=False, help="Display buy signals when the close price touches the lower Bollinger band.")
            show_sell_timing = st.checkbox("Display Sell Timing", key="sell", value=False, help="Display sell signals when the close price touches the upper Bollinger band.")

    moving_average_periods = st.sidebar.multiselect(
        "Select Moving Average Periods", 
        options=[3, 5, 10, 20, 60, 120, 200],
        default=[20, 5]
    )
    
    initial_investment = st.sidebar.number_input("Initial Investment Amount", min_value=0, value=1500000, step=10000)
    buy_portion = st.sidebar.number_input("Buy Portion(5 = 100/5 = 20%)", min_value=1, value=5, step=1)
    sell_portion = st.sidebar.number_input(" Sell Portion(4 = 100/4 = 25%)", min_value=1, value=4, step=1)
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='text-align: center; font-size: 12px;'>Coded by Mathilda</p>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='text-align: center; font-size: 12px;'>@2024</p>", unsafe_allow_html=True)
    
    return (ticker, start_date, end_date, show_dataset_asecending, 
            show_bollinger, show_buy_timing, show_sell_timing, 
            moving_average_periods, 
            initial_investment, buy_portion, sell_portion, show_multiple_backtest)

def main():
    # Set page configuration at the top of the script
    st.set_page_config(page_title="Stock Price Viewer", page_icon="📈", layout='wide')
    st.title("📈 Stock Investment Simulator (Bollinger Band Strategy)")
    # st.markdown("<h2>📈 Stock Investment Simulator (<a href='https://www.tradingwithrayner.com/bollinger-bands-trading-strategy/' target='_blank'>Bollinger Band Strategy</a>)</h2>", unsafe_allow_html=True)
    
    sidebar_result = sidebar_options()
    
    if sidebar_result is not None:
        (ticker, start_date, end_date, show_dataset_asecending, 
        show_bollinger, show_buy_timing, show_sell_timing, 
        moving_average_periods, 
        initial_investment, buy_portion, sell_portion, show_multiple_backtest) = sidebar_result
        
        stock_data_orig = get_stock_data(ticker, start_date, end_date)
        stock_data = stock_data_orig.drop(columns=['Open', 'High', 'Low'])
        print(stock_data)

        stock_data = add_stock_data(stock_data, moving_average_periods, initial_investment, buy_portion, sell_portion)
        stock_data = stock_data.sort_index(ascending=show_dataset_asecending)
        
        st.dataframe(stock_data, width=1200, height=400)
        
        final_portfolio_value = stock_data['Portfolio_Value'].iloc[-1]
        total_profit_ratio = (final_portfolio_value - initial_investment) / initial_investment * 100
        color = "hotpink" if total_profit_ratio > 0 else "blue"
        st.markdown(f"<p style='font-size:18px; color:{color};'>Final Portfolio Amount : {final_portfolio_value:,.2f} ({total_profit_ratio:.2f}%)</p>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        # col1_expanded_flag = col2_expanded_flag = not show_multiple_backtest        
        if show_multiple_backtest:
            col1_expanded_flag, col2_expanded_flag = False, False
        else:
            col1_expanded_flag, col2_expanded_flag = True, True
            
        with col1:
            with st.expander("### Show Graph : Stock Price with Moving Averages", expanded=col1_expanded_flag):
                generate_graph(stock_data, moving_average_periods, show_bollinger, show_buy_timing, show_sell_timing)

        with col2:
            with st.expander("### Show Graph : Total Asset Change", expanded=col2_expanded_flag):
                generate_graph2(stock_data)
        
        if show_multiple_backtest:
            generate_multiple_backtest(stock_data_orig, moving_average_periods, initial_investment)

if __name__ == "__main__":
    main()
