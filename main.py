import pandas as pd
import numpy as np
from datetime import datetime


def split_purchase(purchase: dict, stocks_amount: int, date: datetime = None, cost1: float = 0, cost2: float = 0):
    if purchase["Shares"] <= stocks_amount:
        purchase["Date_sell"] = date if date is not None else datetime.now()
        purchase["Sold1"] = cost1
        purchase["Sold2"] = cost2
        return purchase, None, stocks_amount - purchase["Shares"]
    else:
        purchase_first_half = purchase.copy()
        purchase_first_half["Shares"] = stocks_amount
        purchase_first_half["Cost1"] = purchase["Cost1"] * stocks_amount / purchase["Shares"]
        purchase_first_half["Cost2"] = purchase["Cost2"] * stocks_amount / purchase["Shares"]
        purchase_first_half["Acc_dividend1"] = purchase["Acc_dividend1"] * stocks_amount / purchase["Shares"]
        purchase_first_half["Acc_dividend2"] = purchase["Acc_dividend2"] * stocks_amount / purchase["Shares"]

        purchase_first_half["Date_sell"] = date if date is not None else datetime.now()
        purchase_first_half["Sold1"] = cost1
        purchase_first_half["Sold2"] = cost2

        purchase_second_half = purchase.copy()
        purchase_second_half["Shares"] -= stocks_amount
        purchase_second_half["Cost1"] -= purchase_first_half["Cost1"]
        purchase_second_half["Cost2"] -= purchase_first_half["Cost2"]
        purchase_second_half["Acc_dividend1"] -= purchase_first_half["Acc_dividend1"]
        purchase_second_half["Acc_dividend2"] -= purchase_first_half["Acc_dividend2"]
        
        leftover_stocks = 0
        return purchase_first_half, purchase_second_half, leftover_stocks


def main():
    # Load the dataset
    df = pd.read_excel("data.xlsx")

    portfolio = {}

    portfolio_sold = {}

    date_min = 0
    date_max = datetime.now()

    # date에 따른 total cost 계산 필요. 얼마나 많이, 얼마나 오래 가지고 있었는가!

    for _, row in df.iterrows():    
        stock = row["Stock"]
        shares = row["Shares"]
        change_type = row["Type"]
        cost1 = row["Cost1"]
        cost2 = row["Cost2"]
        date = pd.to_datetime(row["Date"])
        if date_min == 0 or date < date_min:
            date_min = date
        if date > date_max:
            date_max = date

        print(f"Processing {change_type} of {shares} shares of {stock} at ${cost1} on {date}")

        if stock not in portfolio:
            portfolio[stock] = []
            portfolio_sold[stock] = []

        if shares == "":
            shares = 0
            for purchase in portfolio[stock]:
                if purchase["Shares"] > 0:
                    shares += purchase["Shares"]
            
        if change_type == "buy":
            portfolio[stock].append({
                "Stock": stock,
                "Date_buy": date,
                "Shares": shares,
                "Cost1": cost1,
                "Cost2": cost2,
                "Price1": cost1/shares if shares > 0 else 0,
                "Price2": cost2/shares if shares > 0 else 0,
                "Acc_dividend1": 0,
                "Acc_dividend2": 0,
            })
        elif change_type == "sell":
            stocks_to_sell = shares
            for purchase in portfolio[stock]:
                sold_purchase, leftover_purchase, stocks_to_sell = split_purchase(purchase, stocks_to_sell, date, cost1, cost2)
                portfolio_sold[stock].append(sold_purchase)
                if stocks_to_sell == 0 and leftover_purchase is not None:
                    purchase = leftover_purchase
                    break
                else:
                    portfolio[stock].remove(purchase)

        elif change_type == "dividend":
            for purchase in portfolio[stock]:
                if purchase["Shares"] > 0:
                    purchase["Acc_dividend1"] += cost1
                    purchase["Acc_dividend2"] += cost2


    for stock, purchases in portfolio.items():
        print(f"Current portfolio for {stock}:")
        for purchase in purchases:
            print(purchase)

    for stock, sold_purchases in portfolio_sold.items():
        for sold_purchase in sold_purchases:

            sold_purchase["Profit1"] = sold_purchase["Sold1"] - sold_purchase["Cost1"]
            sold_purchase["Profit2"] = sold_purchase["Sold2"] - sold_purchase["Cost2"]

            sold_purchase["Profit_ratio1"] = sold_purchase["Profit1"] / sold_purchase["Cost1"] if sold_purchase["Cost1"] > 0 else 0
            sold_purchase["Profit_ratio2"] = sold_purchase["Profit2"] / sold_purchase["Cost2"] if sold_purchase["Cost2"] > 0 else 0

            sold_purchase["Total_profit1"] = sold_purchase["Profit1"] + sold_purchase["Acc_dividend1"]
            sold_purchase["Total_profit2"] = sold_purchase["Profit2"] + sold_purchase["Acc_dividend2"]

            sold_purchase["Total_profit_ratio1"] = sold_purchase["Total_profit1"] / sold_purchase["Cost1"] if sold_purchase["Cost1"] > 0 else 0
            sold_purchase["Total_profit_ratio2"] = sold_purchase["Total_profit2"] / sold_purchase["Cost2"] if sold_purchase["Cost2"] > 0 else 0

            sold_purchase["Dividend_ratio1"] = sold_purchase["Acc_dividend1"] / sold_purchase["Cost1"] if sold_purchase["Cost1"] > 0 else 0
            sold_purchase["Dividend_ratio2"] = sold_purchase["Acc_dividend2"] / sold_purchase["Cost2"] if sold_purchase["Cost2"] > 0 else 0

            date_delta = (sold_purchase["Date_sell"] - sold_purchase["Date_buy"]).days

            sold_purchase["CAER1"] = (1+(sold_purchase["Total_profit1"] / sold_purchase["Cost1"])) ** (365/date_delta) - 1 if sold_purchase["Cost1"] > 0 and date_delta > 0 else 0
            sold_purchase["CAER2"] = (1+(sold_purchase["Total_profit2"] / sold_purchase["Cost2"])) ** (365/date_delta) - 1 if sold_purchase["Cost2"] > 0 and date_delta > 0 else 0

            sold_purchase["CAER_market1"] = ((sold_purchase["Sold1"] / sold_purchase["Cost1"])) ** (365/date_delta) - 1 if sold_purchase["Price1"] > 0 and date_delta > 0 else 0
            sold_purchase["CAER_market2"] = ((sold_purchase["Sold2"] / sold_purchase["Cost2"])) ** (365/date_delta)  - 1 if sold_purchase["Price2"] > 0 and date_delta > 0 else 0

            sold_purchase["CAER_dividend1"] = (1+(sold_purchase["Acc_dividend1"] / sold_purchase["Cost1"])) ** (365/date_delta) - 1 if sold_purchase["Cost1"] > 0 and date_delta > 0 else 0
            sold_purchase["CAER_dividend2"] = (1+(sold_purchase["Acc_dividend2"] / sold_purchase["Cost2"])) ** (365/date_delta) - 1 if sold_purchase["Cost2"] > 0 and date_delta > 0 else 0   

            sold_purchase["Date_delta"] = date_delta
    

    portfolio_sold_summary = [{}]



    for stock, sold_purchases in portfolio_sold.items():
        
        stock_purchase_total = {
            "Stock": stock,
        }

        stock_purchase_total["Cost1"] = sum(purchase["Cost1"] for purchase in sold_purchases)
        stock_purchase_total["Cost2"] = sum(purchase["Cost2"] for purchase in sold_purchases)

        stock_purchase_total["Shares"] = sum(purchase["Shares"] for purchase in sold_purchases)

        stock_purchase_total["Profit1"] = sum(purchase["Profit1"] for purchase in sold_purchases)
        stock_purchase_total["Profit2"] = sum(purchase["Profit2"] for purchase in sold_purchases)

        stock_purchase_total["Total_profit1"] = sum(purchase["Total_profit1"] for purchase in sold_purchases)
        stock_purchase_total["Total_profit2"] = sum(purchase["Total_profit2"] for purchase in sold_purchases)

        stock_purchase_total["Acc_dividend1"] = sum(purchase["Acc_dividend1"] for purchase in sold_purchases)
        stock_purchase_total["Acc_dividend2"] = sum(purchase["Acc_dividend2"] for purchase in sold_purchases)

        stock_time_delta_times_cost1_sum = sum(purchase["Date_delta"] * purchase["Cost1"] for purchase in sold_purchases)
        stock_time_delta_times_cost2_sum = sum(purchase["Date_delta"] * purchase["Cost2"] for purchase in sold_purchases)

        stock_time_delta_times_cost1_weighted_caer1_sum = sum(purchase["Date_delta"] * purchase["Cost1"] * purchase["CAER1"] for purchase in sold_purchases)
        stock_time_delta_times_cost2_weighted_caer2_sum = sum(purchase["Date_delta"] * purchase["Cost2"] * purchase["CAER2"] for purchase in sold_purchases)

        stock_time_delta_times_cost1_weighted_caer_market1_sum = sum(purchase["Date_delta"] * purchase["Cost1"] * purchase["CAER_market1"] for purchase in sold_purchases)
        stock_time_delta_times_cost2_weighted_caer_market2_sum = sum(purchase["Date_delta"] * purchase["Cost2"] * purchase["CAER_market2"] for purchase in sold_purchases)
        stock_time_delta_times_cost1_weighted_caer_dividend1_sum = sum(purchase["Date_delta"] * purchase["Cost1"] * purchase["CAER_dividend1"] for purchase in sold_purchases)
        stock_time_delta_times_cost2_weighted_caer_dividend2_sum = sum(purchase["Date_delta"] * purchase["Cost2"] * purchase["CAER_dividend2"] for purchase in sold_purchases)

        stock_purchase_total["stdtc1sum"] = stock_time_delta_times_cost1_sum
        stock_purchase_total["stdtc2sum"] = stock_time_delta_times_cost2_sum
        stock_purchase_total["stdtc1wcaer1sum"] = stock_time_delta_times_cost1_weighted_caer1_sum
        stock_purchase_total["stdtc2wcaer2sum"] = stock_time_delta_times_cost2_weighted_caer2_sum
        stock_purchase_total["stdtc1wcaermarket1sum"] = stock_time_delta_times_cost1_weighted_caer_market1_sum
        stock_purchase_total["stdtc2wcaermarket2sum"] = stock_time_delta_times_cost2_weighted_caer_market2_sum
        stock_purchase_total["stdtc1wcaerdividend1sum"] = stock_time_delta_times_cost1_weighted_caer_dividend1_sum
        stock_purchase_total["stdtc2wcaerdividend2sum"] = stock_time_delta_times_cost2_weighted_caer_dividend2_sum

        stock_purchase_total["CAER1"] = stock_time_delta_times_cost1_weighted_caer1_sum / stock_time_delta_times_cost1_sum if stock_time_delta_times_cost1_sum > 0 else 0
        stock_purchase_total["CAER2"] = stock_time_delta_times_cost2_weighted_caer2_sum / stock_time_delta_times_cost2_sum if stock_time_delta_times_cost2_sum > 0 else 0

        stock_purchase_total["CAER_market1"] = stock_time_delta_times_cost1_weighted_caer_market1_sum / stock_time_delta_times_cost1_sum if stock_time_delta_times_cost1_sum > 0 else 0
        stock_purchase_total["CAER_market2"] = stock_time_delta_times_cost2_weighted_caer_market2_sum / stock_time_delta_times_cost2_sum if stock_time_delta_times_cost2_sum > 0 else 0
        stock_purchase_total["CAER_dividend1"] = stock_time_delta_times_cost1_weighted_caer_dividend1_sum / stock_time_delta_times_cost1_sum if stock_time_delta_times_cost1_sum > 0 else 0
        stock_purchase_total["CAER_dividend2"] = stock_time_delta_times_cost2_weighted_caer_dividend2_sum / stock_time_delta_times_cost2_sum if stock_time_delta_times_cost2_sum > 0 else 0

        portfolio_sold_summary.append(stock_purchase_total)

    all_purchase_total = portfolio_sold_summary[0]
    all_purchase_total["Stock"] = "Total"
    all_purchase_total["Shares"] = 1
    all_purchase_total["Cost1"] = sum(stock_total["Cost1"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["Cost2"] = sum(stock_total["Cost2"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["Profit1"] = sum(stock_total["Profit1"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["Profit2"] = sum(stock_total["Profit2"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["Total_profit1"] = sum(stock_total["Total_profit1"] for stock_total in portfolio_sold_summary[1:])   
    all_purchase_total["Total_profit2"] = sum(stock_total["Total_profit2"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["Acc_dividend1"] = sum(stock_total["Acc_dividend1"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["Acc_dividend2"] = sum(stock_total["Acc_dividend2"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["stdtc1sum"] = sum(stock_total["stdtc1sum"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["stdtc2sum"] = sum(stock_total["stdtc2sum"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["stdtc1wcaer1sum"] = sum(stock_total["stdtc1wcaer1sum"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["stdtc2wcaer2sum"] = sum(stock_total["stdtc2wcaer2sum"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["stdtc1wcaermarket1sum"] = sum(stock_total["stdtc1wcaermarket1sum"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["stdtc2wcaermarket2sum"] = sum(stock_total["stdtc2wcaermarket2sum"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["stdtc1wcaerdividend1sum"] = sum(stock_total["stdtc1wcaerdividend1sum"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["stdtc2wcaerdividend2sum"] = sum(stock_total["stdtc2wcaerdividend2sum"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["CAER1"] = all_purchase_total["stdtc1wcaer1sum"] / all_purchase_total["stdtc1sum"] if all_purchase_total["stdtc1sum"] > 0 else 0
    all_purchase_total["CAER2"] = all_purchase_total["stdtc2wcaer2sum"] / all_purchase_total["stdtc2sum"] if all_purchase_total["stdtc2sum"] > 0 else 0
    all_purchase_total["CAER_market1"] = all_purchase_total["stdtc1wcaermarket1sum"] / all_purchase_total["stdtc1sum"] if all_purchase_total["stdtc1sum"] > 0 else 0
    all_purchase_total["CAER_market2"] = all_purchase_total["stdtc2wcaermarket2sum"] / all_purchase_total["stdtc2sum"] if all_purchase_total["stdtc2sum"] > 0 else 0
    all_purchase_total["CAER_dividend1"] = all_purchase_total["stdtc1wcaerdividend1sum"] / all_purchase_total["stdtc1sum"] if all_purchase_total["stdtc1sum"] > 0 else 0
    all_purchase_total["CAER_dividend2"] = all_purchase_total["stdtc2wcaerdividend2sum"] / all_purchase_total["stdtc2sum"] if all_purchase_total["stdtc2sum"] > 0 else 0

    portfolio_sold_summary[0]   = all_purchase_total

    portfolio_sold_summary_df = pd.DataFrame(portfolio_sold_summary)
    portfolio_sold_summary_df_sheet = portfolio_sold_summary_df[["Stock", "Shares", "Cost1", "Total_profit1", "Profit1", "Acc_dividend1", "CAER1", "CAER_market1", "CAER_dividend1", "Cost2", "Total_profit2", "Profit2", "Acc_dividend2", "CAER2", "CAER_market2", "CAER_dividend2"]]  
    portfolio_sold_summary_df_sheet.to_excel("profit_summary.xlsx", index=False)


    total_sold_purchases = [purchase for sold_purchases in portfolio_sold.values() for purchase in sold_purchases]

    df_total_sold = pd.DataFrame(total_sold_purchases)

    df_total_sold_sheet = df_total_sold[["Stock", "Shares", "Date_buy", "Date_sell", "Date_delta", "Cost1", "Sold1", "Acc_dividend1", "Total_profit1", "Total_profit_ratio1", "Profit_ratio1", "Dividend_ratio1", "CAER1", "CAER_market1", "CAER_dividend1", "Cost2", "Sold2", "Acc_dividend2", "Total_profit2", "Total_profit_ratio2", "Profit_ratio2", "Dividend_ratio2", "CAER2", "CAER_market2", "CAER_dividend2"]]
    df_total_sold_sheet.to_excel("profit_raw.xlsx", index=False)


if __name__ == "__main__":
    main()
