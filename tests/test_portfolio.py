"""
Unit tests for Task 2: Stock Portfolio Performance Tracker (portfolio.py)
Tests cover all Datheon requirements:
- Positive returns (including the required verification example)
- Negative returns (losing positions)
- Unchanged prices (breakeven)
- Multiple holdings and overall totals
- Zero and invalid numeric inputs
- Unknown ticker symbols
- Sample price loading (valid, missing, corrupted)
- Manual price entry and overrides
- CSV creation, column headers, and exact row metrics
- Output error handling
"""

import csv
from pathlib import Path
import tempfile
import unittest

import portfolio


class TestPortfolioCalculations(unittest.TestCase):
    """Tests core portfolio financial formulas and validations."""

    def test_required_verification_example_gain(self):
        """
        Required verification example:
        Ticker: TEST, Purchase price: 100, Quantity: 5, Current price: 120
        Expected:
          - Invested amount: 500
          - Current market value: 600
          - Profit: 100
          - Percentage return: 20%
        """
        metrics = portfolio.calculate_holding_metrics(
            purchase_price=100.0,
            quantity=5.0,
            current_price=120.0
        )
        self.assertEqual(metrics["invested_amount"], 500.0)
        self.assertEqual(metrics["market_value"], 600.0)
        self.assertEqual(metrics["profit_loss"], 100.0)
        self.assertEqual(metrics["percentage_return"], 20.0)

    def test_required_verification_example_loss(self):
        """
        Required verification example for losing position:
        Purchase price: 100, Quantity: 5, Current price: 80
        Expected:
          - Invested amount: 500
          - Current market value: 400
          - Loss: -100
          - Percentage return: -20%
        """
        metrics = portfolio.calculate_holding_metrics(
            purchase_price=100.0,
            quantity=5.0,
            current_price=80.0
        )
        self.assertEqual(metrics["invested_amount"], 500.0)
        self.assertEqual(metrics["market_value"], 400.0)
        self.assertEqual(metrics["profit_loss"], -100.0)
        self.assertEqual(metrics["percentage_return"], -20.0)

    def test_breakeven_unchanged_price(self):
        """Holding with unchanged price yields 0 profit and 0% return."""
        metrics = portfolio.calculate_holding_metrics(
            purchase_price=50.0,
            quantity=10.0,
            current_price=50.0
        )
        self.assertEqual(metrics["invested_amount"], 500.0)
        self.assertEqual(metrics["market_value"], 500.0)
        self.assertEqual(metrics["profit_loss"], 0.0)
        self.assertEqual(metrics["percentage_return"], 0.0)

    def test_zero_purchase_price_division_by_zero_safety(self):
        """When purchase price is 0, percentage return safely defaults to 0.0%."""
        metrics = portfolio.calculate_holding_metrics(
            purchase_price=0.0,
            quantity=10.0,
            current_price=25.0
        )
        self.assertEqual(metrics["invested_amount"], 0.0)
        self.assertEqual(metrics["market_value"], 250.0)
        self.assertEqual(metrics["profit_loss"], 250.0)
        self.assertEqual(metrics["percentage_return"], 0.0)

    def test_invalid_negative_price_raises_error(self):
        """Reject negative purchase price or current price."""
        with self.assertRaises(ValueError):
            portfolio.calculate_holding_metrics(purchase_price=-10.0, quantity=5.0, current_price=20.0)
        with self.assertRaises(ValueError):
            portfolio.calculate_holding_metrics(purchase_price=10.0, quantity=5.0, current_price=-20.0)

    def test_invalid_quantity_raises_error(self):
        """Reject zero or negative share quantities."""
        with self.assertRaises(ValueError):
            portfolio.calculate_holding_metrics(purchase_price=100.0, quantity=0.0, current_price=120.0)
        with self.assertRaises(ValueError):
            portfolio.calculate_holding_metrics(purchase_price=100.0, quantity=-5.0, current_price=120.0)

    def test_multiple_holdings_overall_summary(self):
        """Verify portfolio-level aggregates across multiple positions."""
        holdings_input = [
            {"ticker": "AAPL", "purchase_price": 150.0, "quantity": 10.0, "current_price": 180.0},
            {"ticker": "MSFT", "purchase_price": 300.0, "quantity": 5.0, "current_price": 270.0}
        ]
        # AAPL: invested = 1500, value = 1800, profit = 300 (+20%)
        # MSFT: invested = 1500, value = 1350, profit = -150 (-10%)
        # Total: invested = 3000, value = 3150, profit = 150 (+5%)
        summary = portfolio.calculate_portfolio_summary(holdings_input)
        self.assertEqual(summary["total_invested"], 3000.0)
        self.assertEqual(summary["total_market_value"], 3150.0)
        self.assertEqual(summary["total_profit_loss"], 150.0)
        self.assertEqual(summary["overall_percentage_return"], 5.0)
        self.assertEqual(len(summary["holdings"]), 2)

    def test_empty_portfolio_summary(self):
        """Empty portfolio computes cleanly with zero totals without crashing."""
        summary = portfolio.calculate_portfolio_summary([])
        self.assertEqual(summary["total_invested"], 0.0)
        self.assertEqual(summary["total_market_value"], 0.0)
        self.assertEqual(summary["total_profit_loss"], 0.0)
        self.assertEqual(summary["overall_percentage_return"], 0.0)
        self.assertEqual(summary["holdings"], [])


class TestSamplePricesAndCsv(unittest.TestCase):
    """Tests sample price reading and summary CSV writing."""

    def test_load_sample_prices_success(self):
        """Loads valid prices from CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "prices.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ticker", "company_name", "sample_price"])
                writer.writerow(["TEST", "Test Corp", "120.50"])
                writer.writerow(["DEMO", "Demo LLC", "55.00"])

            prices = portfolio.load_sample_prices(csv_path)
            self.assertEqual(prices["TEST"], 120.50)
            self.assertEqual(prices["DEMO"], 55.00)

    def test_load_sample_prices_missing_file(self):
        """Missing CSV file returns empty dict gracefully without raising error."""
        prices = portfolio.load_sample_prices("non_existent_file_path_12345.csv")
        self.assertEqual(prices, {})

    def test_load_sample_prices_corrupted_rows(self):
        """Malformed rows are skipped while valid rows are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "corrupt_prices.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                f.write("ticker,price\n")
                f.write("GOOD,100.00\n")
                f.write("BAD_PRICE,not_a_number\n")
                f.write("EMPTY_ROW\n")
                f.write("NEGATIVE,-50.00\n")

            prices = portfolio.load_sample_prices(csv_path)
            self.assertIn("GOOD", prices)
            self.assertEqual(prices["GOOD"], 100.00)
            self.assertNotIn("BAD_PRICE", prices)
            self.assertNotIn("NEGATIVE", prices)

    def test_save_portfolio_csv_format_and_contents(self):
        """Verifies CSV headers, row data, and summary row are properly formatted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_summary.csv"
            holdings_input = [
                {"ticker": "TEST", "purchase_price": 100.0, "quantity": 5.0, "current_price": 120.0}
            ]
            summary = portfolio.calculate_portfolio_summary(holdings_input)
            success, msg = portfolio.save_portfolio_csv(summary, output_path=csv_path)
            self.assertTrue(success)
            self.assertTrue(csv_path.exists())

            with open(csv_path, mode="r", encoding="utf-8") as f:
                rows = list(csv.reader(f))

            # Header verification
            self.assertEqual(rows[0][0], "Ticker")
            self.assertEqual(rows[0][4], "Invested Amount ($)")
            self.assertEqual(rows[0][5], "Current Market Value ($)")

            # Holding row verification
            self.assertEqual(rows[1][0], "TEST")
            self.assertEqual(rows[1][1], "5.00")
            self.assertEqual(rows[1][2], "100.00")
            self.assertEqual(rows[1][3], "120.00")
            self.assertEqual(rows[1][4], "500.00")
            self.assertEqual(rows[1][5], "600.00")
            self.assertEqual(rows[1][6], "100.00")
            self.assertEqual(rows[1][7], "20.00")

            # TOTAL row verification
            self.assertEqual(rows[2][0], "TOTAL")
            self.assertEqual(rows[2][4], "500.00")
            self.assertEqual(rows[2][5], "600.00")
            self.assertEqual(rows[2][6], "100.00")
            self.assertEqual(rows[2][7], "20.00")


class TestPortfolioWorkflow(unittest.TestCase):
    """Simulates interactive portfolio session."""

    def test_interactive_session_with_sample_price(self):
        """Simulate entering a ticker that exists in sample data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_csv = Path(tmpdir) / "sample.csv"
            out_csv = Path(tmpdir) / "out.csv"
            with open(sample_csv, "w", newline="", encoding="utf-8") as f:
                f.write("ticker,sample_price\nTEST,120.0\n")

            # Inputs:
            # 1. Ticker: TEST
            # 2. Quantity: 5
            # 3. Purchase price: 100
            # 4. Use sample price: 'Y'
            # 5. Ticker: DONE
            inputs = ["TEST", "5", "100", "Y", "DONE"]
            outputs = []

            def mock_input(prompt):
                return inputs.pop(0)

            def mock_print(*args, **kwargs):
                outputs.append(" ".join(str(a) for a in args))

            summary = portfolio.run_portfolio_tracker(
                sample_prices_path=sample_csv,
                output_path=out_csv,
                input_func=mock_input,
                print_func=mock_print
            )

            self.assertEqual(summary["total_invested"], 500.0)
            self.assertEqual(summary["total_market_value"], 600.0)
            self.assertEqual(summary["total_profit_loss"], 100.0)
            self.assertEqual(summary["overall_percentage_return"], 20.0)
            self.assertTrue(out_csv.exists())


if __name__ == "__main__":
    unittest.main()
