import pandas as pd
import numpy as np


def main():
    # Load the dataset
    df = pd.read_excel("data.xlsx")

    portfolio = {}

    for _, row in df.iterrows():    
        stock = row["Stock"]
        shares = row["Shares"]
        price1 = row["Price1"]

        if stock in portfolio:
            portfolio[stock]["Shares"] += shares
            portfolio[stock]["Total Value"] += shares * price1
        else:
            portfolio[stock] = {"Shares": shares, "Total Value": shares * price1}
        
        print(f"Added {shares} shares of {stock} at ${price1} each. Total value: ${portfolio[stock]['Total Value']}")


if __name__ == "__main__":
    main()
