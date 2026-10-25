"""
Datheon Python Programming Internship - Task 2: Stock Portfolio Performance Tracker

Calculates accurate investment performance metrics and generates portfolio_summary.csv:
- Supports multiple stock tickers with purchase price, quantity, and current price.
- Loads demonstration sample prices from sample_data/portfolio_prices.csv.
- Clearly distinguishes demonstration prices from real-time market data.
- Allows user overrides and manual price entry for any ticker.
- Computes invested capital, current market value, profit/loss, and percentage return.
- Generates a well-formatted console summary and a CSV summary report.
- Handles division-by-zero, invalid numeric inputs, and missing files safely.
"""

import csv
from datetime import datetime
from pathlib import Path
import sys

DEFAULT_SAMPLE_PRICES_PATH = Path("sample_data") / "portfolio_prices.csv"
DEFAULT_OUTPUT_CSV_PATH = Path("portfolio_summary.csv")

# Baseline illustrative demonstration prices for recognized companies
DEFAULT_DEMO_PRICES = {
    "TEST": 120.00,
    "AAPL": 185.50,
    "MSFT": 420.25,
    "GOOGL": 175.80,
    "AMZN": 180.00,
    "TSLA": 210.30,
    "NVDA": 125.00,
    "META": 490.00,
    "MMM": 105.00
}


def load_sample_prices(csv_path=DEFAULT_SAMPLE_PRICES_PATH):
    """
    Loads sample stock prices from a CSV file.
    Supports Datheon S&P 500 dataset as well as custom ticker-price tables.
    Returns a dictionary mapping uppercase tickers to float prices.
    Missing, corrupted, or invalid rows are handled gracefully without crashing.
    """
    path = Path(csv_path)
    if not path.exists():
        return {}

    # For default dataset, provide baseline demo prices as fallbacks
    if path == DEFAULT_SAMPLE_PRICES_PATH:
        prices = dict(DEFAULT_DEMO_PRICES)
    else:
        prices = {}

    try:
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return prices

            # Determine column indices from header
            lower_header = [h.strip().lower() for h in header]
            ticker_idx = 0
            price_idx = None

            for i, col in enumerate(lower_header):
                if col in ("ticker", "symbol"):
                    ticker_idx = i
                elif "price" in col:
                    price_idx = i

            for row in reader:
                if not row or len(row) <= ticker_idx:
                    continue
                ticker = row[ticker_idx].strip().upper()
                if not ticker:
                    continue

                if price_idx is not None and len(row) > price_idx:
                    try:
                        price = float(row[price_idx].strip())
                        if price >= 0:
                            prices[ticker] = price
                    except ValueError:
                        pass
                elif len(row) >= 2 and price_idx is None:
                    # Check if second or third column is a price number
                    for col_val in row[1:3]:
                        try:
                            val = float(col_val.strip())
                            if val >= 0:
                                prices[ticker] = val
                                break
                        except ValueError:
                            continue
    except (OSError, UnicodeDecodeError):
        return dict(DEFAULT_DEMO_PRICES)

    return prices


def calculate_holding_metrics(purchase_price, quantity, current_price):
    """
    Calculates key financial metrics for a single stock holding.
    Formulas:
      - Invested amount = purchase price * quantity
      - Current market value = current price * quantity
      - Profit/Loss = current market value - invested amount
      - Percentage return = (profit/loss / invested amount) * 100

    Raises ValueError on negative prices or non-positive quantities.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")
    if purchase_price < 0 or current_price < 0:
        raise ValueError("Prices cannot be negative.")

    invested_amount = round(float(purchase_price) * float(quantity), 2)
    market_value = round(float(current_price) * float(quantity), 2)
    profit_loss = round(market_value - invested_amount, 2)

    # Prevent division by zero if invested amount is zero (e.g., gift/free share)
    if invested_amount == 0:
        percentage_return = 0.0
    else:
        percentage_return = round((profit_loss / invested_amount) * 100.0, 2)

    return {
        "invested_amount": invested_amount,
        "market_value": market_value,
        "profit_loss": profit_loss,
        "percentage_return": percentage_return
    }


def calculate_portfolio_summary(holdings_input):
    """
    Calculates overall metrics across all holdings in a portfolio.
    Input: list of dicts with keys: ticker, purchase_price, quantity, current_price.
    Returns a summary dictionary with detailed holding metrics and totals.
    """
    holdings_results = []
    total_invested = 0.0
    total_market_value = 0.0
    total_profit_loss = 0.0

    for item in holdings_input:
        ticker = item.get("ticker", "").strip().upper()
        purchase_price = float(item["purchase_price"])
        quantity = float(item["quantity"])
        current_price = float(item["current_price"])

        metrics = calculate_holding_metrics(purchase_price, quantity, current_price)

        total_invested += metrics["invested_amount"]
        total_market_value += metrics["market_value"]
        total_profit_loss += metrics["profit_loss"]

        holdings_results.append({
            "ticker": ticker,
            "purchase_price": purchase_price,
            "quantity": quantity,
            "current_price": current_price,
            "invested_amount": metrics["invested_amount"],
            "market_value": metrics["market_value"],
            "profit_loss": metrics["profit_loss"],
            "percentage_return": metrics["percentage_return"]
        })

    total_invested = round(total_invested, 2)
    total_market_value = round(total_market_value, 2)
    total_profit_loss = round(total_profit_loss, 2)

    if total_invested > 0:
        overall_percentage_return = round((total_profit_loss / total_invested) * 100.0, 2)
    else:
        overall_percentage_return = 0.0

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "holdings": holdings_results,
        "total_invested": total_invested,
        "total_market_value": total_market_value,
        "total_profit_loss": total_profit_loss,
        "overall_percentage_return": overall_percentage_return,
        "timestamp": timestamp
    }


def format_portfolio_table(summary_data):
    """
    Formats the portfolio summary into a clean, aligned console table.
    """
    lines = []
    lines.append("\n" + "=" * 90)
    lines.append("                  STOCK PORTFOLIO PERFORMANCE SUMMARY")
    lines.append(f"  Report Generated: {summary_data.get('timestamp', 'N/A')}")
    lines.append("  [NOTICE] Sample prices are illustrative demonstration values, not live market data.")
    lines.append("=" * 90)

    header = f"{'Ticker':<8} {'Qty':>8} {'Buy Price':>12} {'Curr Price':>12} {'Invested':>13} {'Market Val':>13} {'P/L ($)':>11} {'Return (%)':>11}"
    lines.append(header)
    lines.append("-" * 90)

    holdings = summary_data.get("holdings", [])
    if not holdings:
        lines.append("  (No holdings in portfolio)")
    else:
        for h in holdings:
            p_sign = "+" if h["profit_loss"] > 0 else ""
            r_sign = "+" if h["percentage_return"] > 0 else ""
            row = (
                f"{h['ticker']:<8} "
                f"{h['quantity']:>8.2f} "
                f"${h['purchase_price']:>11.2f} "
                f"${h['current_price']:>11.2f} "
                f"${h['invested_amount']:>12.2f} "
                f"${h['market_value']:>12.2f} "
                f"{p_sign}${h['profit_loss']:>9.2f} "
                f"{r_sign}{h['percentage_return']:>9.2f}%"
            )
            lines.append(row)

    lines.append("-" * 90)
    tot_p_sign = "+" if summary_data.get("total_profit_loss", 0) > 0 else ""
    tot_r_sign = "+" if summary_data.get("overall_percentage_return", 0) > 0 else ""
    tot_row = (
        f"{'TOTAL':<8} "
        f"{'-':>8} "
        f"{'-':>12} "
        f"{'-':>12} "
        f"${summary_data.get('total_invested', 0.0):>12.2f} "
        f"${summary_data.get('total_market_value', 0.0):>12.2f} "
        f"{tot_p_sign}${summary_data.get('total_profit_loss', 0.0):>9.2f} "
        f"{tot_r_sign}{summary_data.get('overall_percentage_return', 0.0):>9.2f}%"
    )
    lines.append(tot_row)
    lines.append("=" * 90)

    return "\n".join(lines)


def save_portfolio_csv(summary_data, output_path=DEFAULT_OUTPUT_CSV_PATH):
    """
    Saves the portfolio summary report to a CSV file.
    Returns: (success: bool, message: str)
    """
    dest = Path(output_path)
    try:
        # Ensure parent directory exists if a custom path is specified
        if dest.parent and not dest.parent.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)

        with open(dest, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([
                "Ticker",
                "Quantity",
                "Purchase Price ($)",
                "Current Price ($)",
                "Invested Amount ($)",
                "Current Market Value ($)",
                "Profit/Loss ($)",
                "Percentage Return (%)"
            ])

            for h in summary_data.get("holdings", []):
                writer.writerow([
                    h["ticker"],
                    f"{h['quantity']:.2f}",
                    f"{h['purchase_price']:.2f}",
                    f"{h['current_price']:.2f}",
                    f"{h['invested_amount']:.2f}",
                    f"{h['market_value']:.2f}",
                    f"{h['profit_loss']:.2f}",
                    f"{h['percentage_return']:.2f}"
                ])

            # Write Summary Total row
            writer.writerow([
                "TOTAL",
                "-",
                "-",
                "-",
                f"{summary_data.get('total_invested', 0.0):.2f}",
                f"{summary_data.get('total_market_value', 0.0):.2f}",
                f"{summary_data.get('total_profit_loss', 0.0):.2f}",
                f"{summary_data.get('overall_percentage_return', 0.0):.2f}"
            ])

        return True, f"Report successfully saved to {dest.resolve()}"
    except (OSError, PermissionError) as e:
        return False, f"Failed to save CSV file: {e}"


def prompt_positive_number(prompt_text, allow_zero=False, input_func=input, print_func=print):
    """
    Repeatedly prompts for a positive numeric value until valid input is given.
    """
    while True:
        try:
            val_str = input_func(prompt_text).strip()
            val = float(val_str)
            if allow_zero and val >= 0:
                return val
            if not allow_zero and val > 0:
                return val
            bound = "zero or positive" if allow_zero else "strictly positive (greater than 0)"
            print_func(f"[!] Invalid value. Please enter a number that is {bound}.")
        except ValueError:
            print_func("[!] Invalid number format. Please enter a valid decimal number.")


def run_portfolio_tracker(sample_prices_path=DEFAULT_SAMPLE_PRICES_PATH,
                          output_path=DEFAULT_OUTPUT_CSV_PATH,
                          input_func=input,
                          print_func=print):
    """
    Runs the full portfolio tracker interactive workflow:
    - Loads sample prices from CSV
    - Collects user holdings
    - Computes metrics
    - Prints summary table
    - Saves portfolio_summary.csv
    """
    sample_prices = load_sample_prices(sample_prices_path)

    print_func("\n" + "=" * 65)
    print_func("    WELCOME TO THE STOCK PORTFOLIO PERFORMANCE TRACKER")
    print_func("=" * 65)
    print_func("Track your stock investments, gain/loss metrics, and returns.")
    print_func("[NOTICE] Sample prices in sample_data/portfolio_prices.csv are")
    print_func("         illustrative demonstration values, not live market quotes.\n")

    holdings = []

    while True:
        try:
            ticker_input = input_func("Enter stock ticker symbol (or 'DONE' to finish): ").strip()
        except (KeyboardInterrupt, EOFError):
            print_func("\nInput interrupted. Finalizing report with current holdings...")
            break

        if not ticker_input:
            print_func("[!] Ticker symbol cannot be empty.")
            continue

        if ticker_input.upper() == "DONE":
            break

        ticker = ticker_input.upper()

        quantity = prompt_positive_number(
            f"Enter quantity of shares for {ticker}: ",
            allow_zero=False,
            input_func=input_func,
            print_func=print_func
        )

        purchase_price = prompt_positive_number(
            f"Enter purchase price per share for {ticker} ($): ",
            allow_zero=True,
            input_func=input_func,
            print_func=print_func
        )

        # Current price resolution: check sample prices first
        current_price = None
        if ticker in sample_prices:
            sample_val = sample_prices[ticker]
            print_func(f"[i] Sample price found for {ticker}: ${sample_val:.2f} (Demonstration value).")
            use_sample = input_func("    Use this sample price? (Y/n, or enter custom price): ").strip()
            if use_sample == "" or use_sample.upper() in ["Y", "YES"]:
                current_price = sample_val
            else:
                try:
                    custom_val = float(use_sample)
                    if custom_val >= 0:
                        current_price = custom_val
                except ValueError:
                    pass

        if current_price is None:
            current_price = prompt_positive_number(
                f"Enter current market price per share for {ticker} ($): ",
                allow_zero=True,
                input_func=input_func,
                print_func=print_func
            )

        holdings.append({
            "ticker": ticker,
            "quantity": quantity,
            "purchase_price": purchase_price,
            "current_price": current_price
        })
        print_func(f"[OK] Added {quantity} share(s) of {ticker} to portfolio.\n")

    if not holdings:
        print_func("\n[i] No holdings entered. Creating empty portfolio summary.")

    summary = calculate_portfolio_summary(holdings)
    table_str = format_portfolio_table(summary)
    print_func(table_str)

    success, msg = save_portfolio_csv(summary, output_path=output_path)
    if success:
        print_func(f"\n[OK] {msg}")
    else:
        print_func(f"\n[!] {msg}")

    return summary


def main():
    """Main entry point."""
    run_portfolio_tracker()


if __name__ == "__main__":
    main()
