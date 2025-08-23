"""Context management for Personal Banking Customer Support Agent.

This module defines the BankContext structure that is passed
between agents and tools to maintain conversation state.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class UserDetails(BaseModel):
    """User identity and verification information."""

    name: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD format
    ssn_last_four: Optional[str] = None
    verified: bool = False
    verification_attempts: int = 0


class BankDetails(BaseModel):
    """Banking information loaded after verification."""

    account_balances: Dict[str, float] = Field(default_factory=dict)
    recent_transactions: List[Dict[str, object]] = Field(default_factory=list)


class BankContext(BaseModel):
    """Context shared across all agents and handoffs."""

    session_id: str = ""
    user_details: UserDetails = Field(default_factory=UserDetails)
    bank_details: BankDetails = Field(default_factory=BankDetails)

    def dump_context(self) -> str:
        """Build detailed context summary for LLM consumption.

        Returns:
            Detailed formatted context information
        """
        context_lines = ["Customer Information:"]

        if self.user_details.name:
            context_lines.append(f"- Name: {self.user_details.name}")
        context_lines.append(
            f"- Verification Status: {'Verified' if self.user_details.verified else 'Not Verified'}"
        )

        if self.bank_details.account_balances:
            context_lines.append("\nAccount Balances:")
            for account_id, balance in self.bank_details.account_balances.items():
                context_lines.append(f"- {account_id}: ${balance:,.2f}")

        if self.bank_details.recent_transactions:
            context_lines.append(
                f"\nRecent Transactions ({len(self.bank_details.recent_transactions)} total):"
            )
            for transaction in self.bank_details.recent_transactions[:5]:  # Show last 5
                amount_str = f"${abs(transaction['amount']):,.2f}"
                if transaction["amount"] < 0:
                    amount_str = f"-{amount_str}"
                else:
                    amount_str = f"+{amount_str}"
                context_lines.append(f"- {transaction['date']}: {amount_str} - {transaction['description']}")

        return "\n".join(context_lines)
