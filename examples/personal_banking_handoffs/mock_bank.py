"""Mock banking API for Personal Banking Customer Support Agent.

This module simulates banking API calls to fetch customer account information
based on verified user identity (name, DOB, SSN last four).
"""

from typing import Any, Dict, List, Optional

from config import BANK_NAME


class MockBankingAPI:
    """Mock banking API that simulates database lookups."""

    def __init__(self):
        """Initialize with mock customer data."""
        self._customers = {
            ("John Smith", "1985-03-15", "1234"): {
                "customer_id": "CUST_001",
                "accounts": {
                    "checking_001": {"type": "checking", "balance": 2500.75, "status": "active"},
                    "savings_002": {"type": "savings", "balance": 15000.00, "status": "active"},
                    "credit_card_003": {
                        "type": "credit_card",
                        "balance": -1250.50,
                        "limit": 5000.00,
                        "status": "active",
                    },
                },
                "recent_transactions": [
                    {
                        "date": "2024-01-15",
                        "amount": -45.67,
                        "description": "Grocery Store",
                        "account": "checking_001",
                    },
                    {
                        "date": "2024-01-14",
                        "amount": -120.00,
                        "description": "Gas Station",
                        "account": "checking_001",
                    },
                    {
                        "date": "2024-01-13",
                        "amount": 2000.00,
                        "description": "Direct Deposit",
                        "account": "checking_001",
                    },
                    {
                        "date": "2024-01-12",
                        "amount": 500.00,
                        "description": "Transfer to Savings",
                        "account": "savings_002",
                    },
                    {
                        "date": "2024-01-10",
                        "amount": -89.95,
                        "description": "Online Purchase",
                        "account": "credit_card_003",
                    },
                ],
                "credit_products": [f"{BANK_NAME} Platinum Credit Card", "Personal Line of Credit"],
                "preferences": {
                    "notifications": "email",
                    "statement_delivery": "electronic",
                    "overdraft_protection": True,
                    "preferred_contact": "email",
                },
            },
            ("Jane Doe", "1990-07-22", "5678"): {
                "customer_id": "CUST_002",
                "accounts": {
                    "checking_004": {"type": "checking", "balance": 1850.25, "status": "active"},
                    "savings_005": {"type": "savings", "balance": 8500.00, "status": "active"},
                },
                "recent_transactions": [
                    {
                        "date": "2024-01-15",
                        "amount": -75.00,
                        "description": "Restaurant",
                        "account": "checking_004",
                    },
                    {
                        "date": "2024-01-14",
                        "amount": -45.99,
                        "description": "Subscription",
                        "account": "checking_004",
                    },
                    {
                        "date": "2024-01-13",
                        "amount": 1500.00,
                        "description": "Paycheck",
                        "account": "checking_004",
                    },
                ],
                "credit_products": [f"{BANK_NAME} Active Cash Card"],
                "preferences": {
                    "notifications": "sms",
                    "statement_delivery": "paper",
                    "overdraft_protection": False,
                    "preferred_contact": "phone",
                },
            },
            ("Bob Johnson", "1975-12-08", "9876"): {
                "customer_id": "CUST_003",
                "accounts": {
                    "checking_006": {"type": "checking", "balance": 750.50, "status": "active"},
                    "savings_007": {"type": "savings", "balance": 25000.00, "status": "active"},
                    "mortgage_008": {
                        "type": "mortgage",
                        "balance": -285000.00,
                        "payment_due": "2024-02-01",
                        "status": "active",
                    },
                },
                "recent_transactions": [
                    {
                        "date": "2024-01-15",
                        "amount": -1850.00,
                        "description": "Mortgage Payment",
                        "account": "checking_006",
                    },
                    {
                        "date": "2024-01-10",
                        "amount": -250.00,
                        "description": "Utilities",
                        "account": "checking_006",
                    },
                    {
                        "date": "2024-01-05",
                        "amount": 3500.00,
                        "description": "Salary",
                        "account": "checking_006",
                    },
                ],
                "credit_products": [f"{BANK_NAME} Mortgage", "Home Equity Line of Credit"],
                "preferences": {
                    "notifications": "email",
                    "statement_delivery": "electronic",
                    "overdraft_protection": True,
                    "preferred_contact": "email",
                },
            },
        }

    def get_customer_data(
        self, name: str, date_of_birth: str, ssn_last_four: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch customer banking data by identity verification.

        Args:
            name: Customer's full name
            date_of_birth: Date of birth in YYYY-MM-DD format
            ssn_last_four: Last four digits of SSN

        Returns:
            Complete customer banking data or None if not found
        """
        customer_key = (name, date_of_birth, ssn_last_four)
        return self._customers.get(customer_key)

    def get_account_balances(
        self, name: str, date_of_birth: str, ssn_last_four: str
    ) -> Optional[Dict[str, float]]:
        """Get account balances for a verified customer.

        Args:
            name: Customer's full name
            date_of_birth: Date of birth in YYYY-MM-DD format
            ssn_last_four: Last four digits of SSN

        Returns:
            Dictionary mapping account IDs to balances or None if not found
        """
        customer_data = self.get_customer_data(name, date_of_birth, ssn_last_four)
        if not customer_data:
            return None

        return {
            account_id: account_info["balance"]
            for account_id, account_info in customer_data["accounts"].items()
        }

    def get_recent_transactions(
        self, name: str, date_of_birth: str, ssn_last_four: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get recent transactions for a verified customer.

        Args:
            name: Customer's full name
            date_of_birth: Date of birth in YYYY-MM-DD format
            ssn_last_four: Last four digits of SSN

        Returns:
            List of recent transactions or None if not found
        """
        customer_data = self.get_customer_data(name, date_of_birth, ssn_last_four)
        if not customer_data:
            return None

        return customer_data["recent_transactions"]

    def verify_customer_identity(self, name: str, date_of_birth: str, ssn_last_four: str) -> bool:
        """Verify if customer identity exists in the system.

        Args:
            name: Customer's full name
            date_of_birth: Date of birth in YYYY-MM-DD format
            ssn_last_four: Last four digits of SSN

        Returns:
            True if customer exists, False otherwise
        """
        customer_key = (name, date_of_birth, ssn_last_four)
        return customer_key in self._customers


# Global mock banking API instance
mock_bank_api = MockBankingAPI()
