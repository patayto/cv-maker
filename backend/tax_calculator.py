"""
UK Tax Calculator Module

Provides accurate tax, national insurance, student loan, and pension calculations
for UK taxpayers based on the 2025/26 tax year.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class TaxConfig:
    """UK Tax Year Configuration for 2025/26"""

    tax_year: str = "2025/26"

    # Personal allowance
    personal_allowance: Decimal = Decimal("12750.00")

    # Income tax rates
    basic_rate: Decimal = Decimal("0.20")
    higher_rate: Decimal = Decimal("0.40")
    additional_rate: Decimal = Decimal("0.45")

    # Income tax thresholds (after personal allowance)
    higher_rate_threshold: Decimal = Decimal("37700.00")
    additional_rate_threshold: Decimal = Decimal("125140.00")

    # National Insurance rates
    ni_rate_high: Decimal = Decimal("0.08")
    ni_rate_low: Decimal = Decimal("0.02")
    ni_threshold: Decimal = Decimal("50270.00")

    # Student loan thresholds and rates
    student_loan_plan1_threshold: Decimal = Decimal("26065.00")
    student_loan_plan1_rate: Decimal = Decimal("0.09")
    student_loan_plan2_threshold: Decimal = Decimal("27295.00")
    student_loan_plan2_rate: Decimal = Decimal("0.09")


@dataclass
class SalaryBreakdown:
    """Comprehensive salary breakdown with all deductions"""

    gross_yearly: Decimal
    gross_monthly: Decimal
    net_yearly: Decimal
    net_monthly: Decimal
    income_tax: Decimal
    national_insurance: Decimal
    student_loan: Decimal
    pension: Decimal
    effective_tax_rate: Decimal
    tax_breakdown: dict = field(default_factory=dict)

    def __str__(self) -> str:
        """Human-readable string representation"""
        return (
            f"Salary Breakdown:\n"
            f"  Gross (yearly):  £{self.gross_yearly:,.2f}\n"
            f"  Gross (monthly): £{self.gross_monthly:,.2f}\n"
            f"  Net (yearly):    £{self.net_yearly:,.2f}\n"
            f"  Net (monthly):   £{self.net_monthly:,.2f}\n"
            f"\n"
            f"Deductions:\n"
            f"  Income Tax:      £{self.income_tax:,.2f}\n"
            f"    - Basic rate (20%):      £{self.tax_breakdown.get('basic', Decimal('0')):,.2f}\n"
            f"    - Higher rate (40%):     £{self.tax_breakdown.get('higher', Decimal('0')):,.2f}\n"
            f"    - Additional rate (45%): £{self.tax_breakdown.get('additional', Decimal('0')):,.2f}\n"
            f"  National Insurance: £{self.national_insurance:,.2f}\n"
            f"  Student Loan:       £{self.student_loan:,.2f}\n"
            f"  Pension:            £{self.pension:,.2f}\n"
            f"\n"
            f"Effective Tax Rate: {self.effective_tax_rate:.2f}%"
        )


class TaxCalculator:
    """
    UK Tax Calculator for 2025/26 tax year

    Calculates income tax, national insurance, student loan repayments,
    and pension contributions based on UK tax law.
    """

    def __init__(self, config: Optional[TaxConfig] = None):
        """
        Initialize the tax calculator

        Args:
            config: Optional TaxConfig instance. If not provided, uses 2025/26 defaults.
        """
        self.config = config or TaxConfig()

    def calculate_net_salary(
        self,
        gross: Decimal,
        pension_pct: Decimal = Decimal("0.05"),
        include_student_loan: bool = True,
        student_loan_plan: str = "plan1"
    ) -> SalaryBreakdown:
        """
        Calculate comprehensive salary breakdown

        Args:
            gross: Gross annual salary
            pension_pct: Pension contribution as percentage (default 5%)
            include_student_loan: Whether to include student loan repayments
            student_loan_plan: Student loan plan ("plan1" or "plan2")

        Returns:
            SalaryBreakdown with all calculations
        """
        # Convert to Decimal if needed
        gross = Decimal(str(gross))
        pension_pct = Decimal(str(pension_pct))

        # Calculate pension contribution
        pension = gross * pension_pct

        # Calculate student loan repayment
        if include_student_loan:
            student_loan = self.calculate_student_loan(gross, student_loan_plan)
        else:
            student_loan = Decimal("0")

        # Calculate taxable income (after personal allowance and pension)
        taxable_income = gross - self.config.personal_allowance - pension

        # Calculate income tax
        tax_result = self.calculate_income_tax(taxable_income)
        income_tax = tax_result["total"]

        # Calculate national insurance
        national_insurance = self.calculate_national_insurance(taxable_income)

        # Calculate net salary
        total_deductions = income_tax + national_insurance + student_loan + pension
        net_yearly = gross - total_deductions

        # Calculate effective tax rate
        effective_tax_rate = (total_deductions / gross * Decimal("100")) if gross > 0 else Decimal("0")

        return SalaryBreakdown(
            gross_yearly=gross,
            gross_monthly=gross / Decimal("12"),
            net_yearly=net_yearly,
            net_monthly=net_yearly / Decimal("12"),
            income_tax=income_tax,
            national_insurance=national_insurance,
            student_loan=student_loan,
            pension=pension,
            effective_tax_rate=effective_tax_rate,
            tax_breakdown={
                "basic": tax_result["basic"],
                "higher": tax_result["higher"],
                "additional": tax_result["additional"]
            }
        )

    def calculate_income_tax(self, taxable_income: Decimal) -> dict:
        """
        Calculate income tax based on UK tax brackets

        Args:
            taxable_income: Income after personal allowance and pension deductions

        Returns:
            Dict with total tax and breakdown by bracket
        """
        taxable_income = Decimal(str(taxable_income))

        basic_tax = Decimal("0")
        higher_tax = Decimal("0")
        additional_tax = Decimal("0")

        # Return zero if taxable income is not positive
        if taxable_income <= 0:
            return {
                "total": Decimal("0"),
                "basic": Decimal("0"),
                "higher": Decimal("0"),
                "additional": Decimal("0")
            }

        # Additional rate (45% on income above £125,140)
        if taxable_income > self.config.additional_rate_threshold:
            additional_tax = (
                (taxable_income - self.config.additional_rate_threshold)
                * self.config.additional_rate
            )
            taxable_income = self.config.additional_rate_threshold

        # Higher rate (40% on income between £37,700 and £125,140)
        if taxable_income > self.config.higher_rate_threshold:
            higher_tax = (
                (taxable_income - self.config.higher_rate_threshold)
                * self.config.higher_rate
            )
            taxable_income = self.config.higher_rate_threshold

        # Basic rate (20% on income up to £37,700)
        basic_tax = taxable_income * self.config.basic_rate

        total_tax = basic_tax + higher_tax + additional_tax

        return {
            "total": total_tax,
            "basic": basic_tax,
            "higher": higher_tax,
            "additional": additional_tax
        }

    def calculate_national_insurance(self, income: Decimal) -> Decimal:
        """
        Calculate National Insurance contributions

        Args:
            income: Taxable income (after personal allowance and pension)

        Returns:
            Total National Insurance contribution
        """
        income = Decimal(str(income))

        if income <= 0:
            return Decimal("0")

        ni_contribution = Decimal("0")

        # 2% on income above £50,270
        if income > self.config.ni_threshold:
            ni_contribution += (income - self.config.ni_threshold) * self.config.ni_rate_low
            income = self.config.ni_threshold

        # 8% on remaining income
        ni_contribution += income * self.config.ni_rate_high

        return ni_contribution

    def calculate_student_loan(self, gross: Decimal, plan: str = "plan1") -> Decimal:
        """
        Calculate student loan repayment

        Args:
            gross: Gross annual salary
            plan: Student loan plan ("plan1" or "plan2")

        Returns:
            Annual student loan repayment amount
        """
        gross = Decimal(str(gross))

        if plan.lower() == "plan1":
            threshold = self.config.student_loan_plan1_threshold
            rate = self.config.student_loan_plan1_rate
        elif plan.lower() == "plan2":
            threshold = self.config.student_loan_plan2_threshold
            rate = self.config.student_loan_plan2_rate
        else:
            raise ValueError(f"Unknown student loan plan: {plan}")

        # Only repay if earning above threshold
        if gross <= threshold:
            return Decimal("0")

        repayable_income = gross - threshold
        return repayable_income * rate


def recommend_budget(monthly_income: Decimal) -> dict:
    """
    Generate budget recommendation using 50:30:20 rule

    50% - Essentials (rent, bills, groceries, etc.)
    30% - Spending (entertainment, clothes, etc.)
    20% - Savings (savings and investments)

    Args:
        monthly_income: Net monthly income

    Returns:
        Dict with budget breakdown
    """
    monthly_income = Decimal(str(monthly_income))

    budget = {
        "income": monthly_income,
        "Essentials": {
            "total": monthly_income * Decimal("0.50"),
            "items": {
                "Rent": monthly_income * Decimal("0.35"),
                "Bills": monthly_income * Decimal("0.05"),
                "Groceries": monthly_income * Decimal("0.07"),
                "Phone": monthly_income * Decimal("0.01"),
                "Medical Bills": monthly_income * Decimal("0.01"),
                "Gym": monthly_income * Decimal("0.01")
            }
        },
        "Savings": {
            "total": monthly_income * Decimal("0.20"),
            "items": {
                "Savings": monthly_income * Decimal("0.10"),
                "Investments": monthly_income * Decimal("0.10")
            }
        },
        "Spending": {
            "total": monthly_income * Decimal("0.30"),
            "items": {
                "Eating Out": monthly_income * Decimal("0.05"),
                "Pub": monthly_income * Decimal("0.05"),
                "Flowers": monthly_income * Decimal("0.05"),
                "Clothes": monthly_income * Decimal("0.05"),
                "Skincare": monthly_income * Decimal("0.05"),
                "Vitamins": monthly_income * Decimal("0.05")
            }
        }
    }

    # Add percentages for clarity
    for category in ["Essentials", "Savings", "Spending"]:
        budget[category]["percentage"] = (
            budget[category]["total"] / monthly_income * Decimal("100")
        )

    return budget


def format_budget(budget: dict) -> str:
    """
    Format budget as human-readable string

    Args:
        budget: Budget dict from recommend_budget()

    Returns:
        Formatted budget string
    """
    lines = [f"Monthly Income: £{budget['income']:,.2f}\n"]

    for category in ["Essentials", "Savings", "Spending"]:
        cat_data = budget[category]
        lines.append(
            f"|___ {category}: £{cat_data['total']:,.2f} ({cat_data['percentage']:.2f}%)"
        )
        for item, amount in cat_data["items"].items():
            pct = (amount / budget['income'] * Decimal("100"))
            lines.append(f"    |___ {item}: £{amount:,.2f} ({pct:.2f}%)")

    total_budgeted = sum(budget[cat]["total"] for cat in ["Essentials", "Savings", "Spending"])
    leftover = budget["income"] - total_budgeted
    lines.append(f"\nLeftover: £{leftover:,.2f}")

    return "\n".join(lines)


# Convenience function for quick calculations
def calculate_take_home(
    gross_salary: float,
    pension_pct: float = 0.05,
    include_student_loan: bool = True
) -> dict:
    """
    Quick calculation of take-home pay

    Args:
        gross_salary: Gross annual salary
        pension_pct: Pension contribution percentage (default 5%)
        include_student_loan: Whether to include student loan repayments

    Returns:
        Dict with net yearly and monthly amounts
    """
    calculator = TaxCalculator()
    breakdown = calculator.calculate_net_salary(
        Decimal(str(gross_salary)),
        Decimal(str(pension_pct)),
        include_student_loan
    )

    return {
        "gross_yearly": float(breakdown.gross_yearly),
        "gross_monthly": float(breakdown.gross_monthly),
        "net_yearly": float(breakdown.net_yearly),
        "net_monthly": float(breakdown.net_monthly),
        "effective_tax_rate": float(breakdown.effective_tax_rate)
    }
