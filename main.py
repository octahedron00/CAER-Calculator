import pandas as pd
from math import log10
from datetime import datetime


def split_purchase(purchase: dict, stocks_amount: int, date: datetime = None, cost1: float = 0, cost2: float = 0):
    if purchase["Shares"] <= stocks_amount:
        sold_purchase = purchase.copy()
        sold_purchase["Date_sell"] = date if date is not None else datetime.now()
        sold_purchase["Sold1"] = cost1 * purchase["Shares"] / stocks_amount if stocks_amount > 0 else 0
        sold_purchase["Sold2"] = cost2 * purchase["Shares"] / stocks_amount if stocks_amount > 0 else 0
        return sold_purchase, None, stocks_amount - purchase["Shares"], cost1 - sold_purchase["Sold1"], cost2 - sold_purchase["Sold2"]
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
        return purchase_first_half, purchase_second_half, leftover_stocks, 0, 0


def main():
    # Load the dataset
    df = pd.read_excel("data.xlsx")

    portfolio = {}

    portfolio_sold = {}

    df["Date"] = df["Date"].fillna(datetime.now().strftime("%Y-%m-%d"))
    df["Date"] = pd.to_datetime(df["Date"])
    date_min = df["Date"].min()
    date_max = df["Date"].max()

    stock_list = df["Stock"].unique().tolist()

    # date에 따른 total cost 계산 필요. 얼마나 많이, 얼마나 오래 가지고 있었는가!
    
    asset_amount_over_time = []

    start_asset_amount = {
        "Date": date_min,
        "Total1": 0,
        "Total2": 0,
    }

    for stock in stock_list:
        start_asset_amount[stock+"1"] = 0
        start_asset_amount[stock+"2"] = 0

    asset_amount_over_time.append(start_asset_amount)

    for _, row in df.iterrows():    
        stock = row["Stock"]
        shares = row["Shares"]
        change_type = row["Type"]
        cost1 = row["Cost1"]
        cost2 = row["Cost2"]
        date = row["Date"]

        cost_original1 = 0
        cost_original2 = 0

        # print(f"Processing {change_type} of {shares} shares of {stock} at ${cost1} on {date}")

        if stock not in portfolio:
            portfolio[stock] = []
            portfolio_sold[stock] = []

        if shares == "" or shares == 0:
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
            left_cost1 = cost1
            left_cost2 = cost2
            for i, purchase in enumerate(portfolio[stock]):
                # debug


                sold_purchase, leftover_purchase, stocks_to_sell, left_cost1, left_cost2 = split_purchase(purchase, stocks_to_sell, date, left_cost1, left_cost2)
                cost_original1 += sold_purchase["Cost1"]
                cost_original2 += sold_purchase["Cost2"]
                portfolio_sold[stock].append(sold_purchase)
                if stocks_to_sell == 0 and leftover_purchase is not None:
                    portfolio[stock][i] = leftover_purchase # Update the original purchase with the leftover part
                    break
                else:
                    portfolio[stock][i] = None # Remove the original purchase as it has been fully sold
            
            portfolio[stock] = [purchase for purchase in portfolio[stock] if purchase is not None] # Clean up the portfolio by removing fully sold purchases

        elif change_type == "dividend":
            total_stock = sum(purchase["Shares"] for purchase in portfolio[stock])
            for purchase in portfolio[stock]:
                if purchase["Shares"] > 0:
                    purchase["Acc_dividend1"] += cost1 * purchase["Shares"] / total_stock if total_stock > 0 else 0
                    purchase["Acc_dividend2"] += cost2 * purchase["Shares"] / total_stock if total_stock > 0 else 0
            if total_stock == 0:
                print(f"Warning: Dividend of {cost1} and {cost2} for stock {stock} on {date} could not be allocated because there are no shares in the portfolio.")


        asset_amount = asset_amount_over_time[-1].copy()
    
        date = pd.to_datetime(row["Date"])

        if change_type == "buy":
            asset_amount[stock+"1"] += cost1
            asset_amount[stock+"2"] += cost2
            asset_amount["Total1"] += cost1
            asset_amount["Total2"] += cost2
        elif change_type == "sell":
            asset_amount[stock+"1"] -= cost_original1
            asset_amount[stock+"2"] -= cost_original2
            asset_amount["Total1"] -= cost_original1
            asset_amount["Total2"] -= cost_original2

        asset_amount["Date"] = date

        if asset_amount_over_time[-1]["Date"] != date:
            before_asset_amount = asset_amount_over_time[-1].copy()
            before_asset_amount["Date"] = date

            asset_amount_over_time.append(before_asset_amount)
            asset_amount_over_time.append(asset_amount)
        else:
            asset_amount_over_time[-1] = asset_amount


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

            sold_purchase["CAER1"] = ((1+(sold_purchase["Total_profit1"] / sold_purchase["Cost1"])) ** (365/date_delta) - 1).real if sold_purchase["Cost1"] > 0 and date_delta > 0 else 0
            sold_purchase["CAER2"] = ((1+(sold_purchase["Total_profit2"] / sold_purchase["Cost2"])) ** (365/date_delta) - 1).real if sold_purchase["Cost2"] > 0 and date_delta > 0 else 0

            sold_purchase["CAER_market1"] = (((sold_purchase["Sold1"] / sold_purchase["Cost1"])) ** (365/date_delta) - 1).real if sold_purchase["Cost1"] > 0 and date_delta > 0 else 0
            sold_purchase["CAER_market2"] = (((sold_purchase["Sold2"] / sold_purchase["Cost2"])) ** (365/date_delta)  - 1).real if sold_purchase["Cost2"] > 0 and date_delta > 0 else 0

            sold_purchase["CAER_dividend1"] = ((1+(sold_purchase["Acc_dividend1"] / sold_purchase["Cost1"])) ** (365/date_delta) - 1).real if sold_purchase["Cost1"] > 0 and date_delta > 0 else 0
            sold_purchase["CAER_dividend2"] = ((1+(sold_purchase["Acc_dividend2"] / sold_purchase["Cost2"])) ** (365/date_delta) - 1).real if sold_purchase["Cost2"] > 0 and date_delta > 0 else 0   

            sold_purchase["Date_delta"] = date_delta
    

    portfolio_sold_summary = [{}]



    all_purchase_total = portfolio_sold_summary[0]
    all_purchase_total["Stock"] = "Total"
    all_purchase_total["Shares"] = 1

    ddc1_sum, ddc2_sum = 0, 0
    ddc1_weighted_lcaer1_sum, ddc2_weighted_lcaer2_sum = 0, 0
    ddc1_weighted_lcaer_market1_sum, ddc2_weighted_lcaer_market2_sum = 0, 0
    ddc1_weighted_lcaer_dividend1_sum, ddc2_weighted_lcaer_dividend2_sum = 0, 0


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

        stock_ddc1_sum = sum(purchase["Date_delta"] * purchase["Cost1"] for purchase in sold_purchases)
        stock_ddc2_sum = sum(purchase["Date_delta"] * purchase["Cost2"] for purchase in sold_purchases)

        stock_ddc1_weighted_lcaer1_sum = sum(purchase["Date_delta"] * purchase["Cost1"] * log10(purchase["CAER1"]+1) for purchase in sold_purchases)
        stock_ddc2_weighted_lcaer2_sum = sum(purchase["Date_delta"] * purchase["Cost2"] * log10(purchase["CAER2"]+1) for purchase in sold_purchases)

        stock_ddc1_weighted_lcaer_market1_sum = sum(purchase["Date_delta"] * purchase["Cost1"] * log10(purchase["CAER_market1"]+1) for purchase in sold_purchases)
        stock_ddc2_weighted_lcaer_market2_sum = sum(purchase["Date_delta"] * purchase["Cost2"] * log10(purchase["CAER_market2"]+1) for purchase in sold_purchases)
        stock_ddc1_weighted_lcaer_dividend1_sum = sum(purchase["Date_delta"] * purchase["Cost1"] * log10(purchase["CAER_dividend1"]+1) for purchase in sold_purchases)
        stock_ddc2_weighted_lcaer_dividend2_sum = sum(purchase["Date_delta"] * purchase["Cost2"] * log10(purchase["CAER_dividend2"]+1) for purchase in sold_purchases)

        ddc1_sum += stock_ddc1_sum
        ddc2_sum += stock_ddc2_sum
        ddc1_weighted_lcaer1_sum += stock_ddc1_weighted_lcaer1_sum
        ddc2_weighted_lcaer2_sum += stock_ddc2_weighted_lcaer2_sum
        ddc1_weighted_lcaer_market1_sum += stock_ddc1_weighted_lcaer_market1_sum
        ddc2_weighted_lcaer_market2_sum += stock_ddc2_weighted_lcaer_market2_sum
        ddc1_weighted_lcaer_dividend1_sum += stock_ddc1_weighted_lcaer_dividend1_sum
        ddc2_weighted_lcaer_dividend2_sum += stock_ddc2_weighted_lcaer_dividend2_sum

        stock_purchase_total["DDC1"] = stock_ddc1_sum
        stock_purchase_total["DDC2"] = stock_ddc2_sum

        stock_purchase_total["CAER1"] = 10**(stock_ddc1_weighted_lcaer1_sum / stock_ddc1_sum).real - 1 if stock_ddc1_sum > 0 else 0
        stock_purchase_total["CAER2"] = 10**(stock_ddc2_weighted_lcaer2_sum / stock_ddc2_sum).real - 1 if stock_ddc2_sum > 0 else 0

        stock_purchase_total["CAER_market1"] = 10**(stock_ddc1_weighted_lcaer_market1_sum / stock_ddc1_sum).real - 1 if stock_ddc1_sum > 0 else 0
        stock_purchase_total["CAER_market2"] = 10**(stock_ddc2_weighted_lcaer_market2_sum / stock_ddc2_sum).real - 1 if stock_ddc2_sum > 0 else 0
        stock_purchase_total["CAER_dividend1"] = 10**(stock_ddc1_weighted_lcaer_dividend1_sum / stock_ddc1_sum).real - 1 if stock_ddc1_sum > 0 else 0
        stock_purchase_total["CAER_dividend2"] = 10**(stock_ddc2_weighted_lcaer_dividend2_sum / stock_ddc2_sum).real - 1 if stock_ddc2_sum > 0 else 0

        portfolio_sold_summary.append(stock_purchase_total)

    all_purchase_total["Cost1"] = sum(stock_total["Cost1"] for stock_total in portfolio_sold_summary[1:]) # Exclude the total row itself
    all_purchase_total["Cost2"] = sum(stock_total["Cost2"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["Profit1"] = sum(stock_total["Profit1"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["Profit2"] = sum(stock_total["Profit2"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["Total_profit1"] = sum(stock_total["Total_profit1"] for stock_total in portfolio_sold_summary[1:])   
    all_purchase_total["Total_profit2"] = sum(stock_total["Total_profit2"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["Acc_dividend1"] = sum(stock_total["Acc_dividend1"] for stock_total in portfolio_sold_summary[1:])
    all_purchase_total["Acc_dividend2"] = sum(stock_total["Acc_dividend2"] for stock_total in portfolio_sold_summary[1:])

    all_purchase_total["DDC1"] = ddc1_sum
    all_purchase_total["DDC2"] = ddc2_sum

    all_purchase_total["CAER1"] = 10**(ddc1_weighted_lcaer1_sum / ddc1_sum).real - 1 if ddc1_sum > 0 else 0
    all_purchase_total["CAER2"] = 10**(ddc2_weighted_lcaer2_sum / ddc2_sum).real - 1 if ddc2_sum > 0 else 0
    all_purchase_total["CAER_market1"] = 10**(ddc1_weighted_lcaer_market1_sum / ddc1_sum).real - 1 if ddc1_sum > 0 else 0
    all_purchase_total["CAER_market2"] = 10**(ddc2_weighted_lcaer_market2_sum / ddc2_sum).real - 1 if ddc2_sum > 0 else 0
    all_purchase_total["CAER_dividend1"] = 10**(ddc1_weighted_lcaer_dividend1_sum / ddc1_sum).real - 1 if ddc1_sum > 0 else 0
    all_purchase_total["CAER_dividend2"] = 10**(ddc2_weighted_lcaer_dividend2_sum / ddc2_sum).real - 1 if ddc2_sum > 0 else 0

    portfolio_sold_summary[0] = all_purchase_total

    portfolio_sold_summary_df = pd.DataFrame(portfolio_sold_summary)
    portfolio_sold_summary_df_sheet = portfolio_sold_summary_df[["Stock", "Shares", "Cost1", "DDC1", "Total_profit1", "Profit1", "Acc_dividend1", "CAER1", "CAER_market1", "CAER_dividend1", "Cost2", "DDC2", "Total_profit2", "Profit2", "Acc_dividend2", "CAER2", "CAER_market2", "CAER_dividend2"]]  
    portfolio_sold_summary_df_sheet.to_excel("profit_summary.xlsx", index=False)


    total_sold_purchases = [purchase for sold_purchases in portfolio_sold.values() for purchase in sold_purchases]


    df_total_sold = pd.DataFrame(total_sold_purchases)
    df_total_sold_sheet = df_total_sold[["Stock", "Shares", "Date_buy", "Date_sell", "Date_delta", "Cost1", "Sold1", "Acc_dividend1", "Total_profit1", "Total_profit_ratio1", "Profit_ratio1", "Dividend_ratio1", "CAER1", "CAER_market1", "CAER_dividend1", "Cost2", "Sold2", "Acc_dividend2", "Total_profit2", "Total_profit_ratio2", "Profit_ratio2", "Dividend_ratio2", "CAER2", "CAER_market2", "CAER_dividend2"]]
    df_total_sold_sheet.to_excel("profit_raw.xlsx", index=False)

    df_total_leftover = pd.DataFrame([purchase for stock_purchases in portfolio.values() for purchase in stock_purchases])
    if df_total_leftover.empty:
        df_total_leftover = pd.DataFrame(columns=["Stock", "Shares", "Date_buy", "Cost1", "Acc_dividend1", "Cost2", "Acc_dividend2"])
    df_total_leftover_sheet = df_total_leftover[["Stock", "Shares", "Date_buy", "Cost1", "Acc_dividend1", "Cost2", "Acc_dividend2"]]
    df_total_leftover_sheet.to_excel("leftover_raw.xlsx", index=False)

    asset_amount_over_time_df = pd.DataFrame(asset_amount_over_time)
    asset_amount_over_time_df_sheet = asset_amount_over_time_df[["Date", "Total1"] + [stock+"1" for stock in portfolio.keys()] + ["Total2"] + [stock+"2" for stock in portfolio.keys()]]
    asset_amount_over_time_df_sheet.to_excel("assets_over_time.xlsx", index=False)





if __name__ == "__main__":
    main()

# 시간에 대한 평균 자산까지 확인하기.