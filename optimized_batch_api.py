import numpy as np
import pandas as pd
import requests
import math
import sys
import os

try:
    from starter_files.secrets import FMP_FIN_MODEL_API_TOKEN
except ImportError:
    print("Error: starter_files/secrets.py not found or FMP_FIN_MODEL_API_TOKEN not defined.")
    sys.exit(1)

# Load stocks
try:
    stocks = pd.read_csv("starter_files/sp_500_stocks.csv")
except FileNotFoundError:
    print("Error: starter_files/sp_500_stocks.csv not found.")
    sys.exit(1)

# Function to chunk the list into batches
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))

my_columns = ['Ticker', 'Stock Price', 'Market Cap', 'Number Of Shares to buy']
final_dataframe = pd.DataFrame(columns = my_columns)

print("Starting batch API calls to FMP...")

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://financialmodelingprep.com/stable/quote?symbol={symbol_string}&apikey={FMP_FIN_MODEL_API_TOKEN}'
    try:
        data = requests.get(batch_api_call_url).json()
        
        # Create a dictionary for O(1) lookup for the current batch
        # Handle case where data might be None or not a list
        if isinstance(data, list):
            batch_data_dict = {item['symbol']: item for item in data}
            
            for symbol in symbol_string.split(','):
                if symbol in batch_data_dict:
                    try:
                        # Using pd.concat instead of append as append is deprecated
                        new_row = pd.DataFrame([{
                            'Ticker': symbol, 
                            'Stock Price': batch_data_dict[symbol]['price'], 
                            'Market Cap': batch_data_dict[symbol]['marketCap'], 
                            'Number Of Shares to buy': 'N/A'
                        }])
                        final_dataframe = pd.concat([final_dataframe, new_row], ignore_index=True)
                    except Exception as e:
                        print(f"Error processing ticker {symbol}: {e}")
                else:
                    print(f"Warning: No data found for {symbol}")
        else:
            print(f"Error: Unexpected API response structure: {data}")
            
    except Exception as e:
        print(f"Error making API call: {e}")

print("API calls completed.")

# Calculate number of shares to buy
try:
    portfolio_size = input("Enter the value of your portfolio: ")
    val = float(portfolio_size)
    
    if len(final_dataframe.index) > 0:
        position_size = val / len(final_dataframe.index)
        for i in range(0, len(final_dataframe.index)):
            stock_price = final_dataframe.loc[i, 'Stock Price']
            if stock_price and stock_price > 0:
                final_dataframe.loc[i, 'Number Of Shares to buy'] = math.floor(position_size / stock_price)
            else:
                 final_dataframe.loc[i, 'Number Of Shares to buy'] = 0
    else:
        print("No stocks found to calculate shares.")

except ValueError:
    print("That's not a number! Please try again.")

print(final_dataframe)
print(f"Total rows: {len(final_dataframe)}")
