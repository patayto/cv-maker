import { useState, useEffect } from 'react';

// Types
interface SalaryCalculatorProps {
  initialSalary?: string; // e.g., "£80,000 - £100,000"
  onCalculated?: (result: SalaryResult) => void;
}

interface SalaryRequest {
  grossSalary: number;
  isMonthly: boolean;
  pensionContribution: number;
  includeStudentLoan: boolean;
  studentLoanPlan?: 'plan1' | 'plan2' | 'plan4';
}

interface SalaryResult {
  grossYearly: number;
  grossMonthly: number;
  netYearly: number;
  netMonthly: number;
  incomeTax: number;
  nationalInsurance: number;
  pensionDeduction: number;
  studentLoanDeduction: number;
  effectiveTaxRate: number;
  taxBreakdown: {
    basicRate: number;
    higherRate: number;
    additionalRate: number;
  };
  budgetRecommendation?: {
    needs: number;
    wants: number;
    savings: number;
  };
}

// Tax thresholds for UK 2024/25 tax year
const TAX_THRESHOLDS = {
  personalAllowance: 12570,
  basicRateLimit: 50270,
  higherRateLimit: 125140,
  basicRate: 0.20,
  higherRate: 0.40,
  additionalRate: 0.45,
};

const NI_THRESHOLDS = {
  weeklyThreshold: 242,
  yearlyThreshold: 12570,
  upperThreshold: 50270,
  standardRate: 0.08,
  higherRate: 0.02,
};

const STUDENT_LOAN_THRESHOLDS = {
  plan1: 24990,
  plan2: 27295,
  plan4: 31395,
  rate: 0.09,
};

// Mock API call function (to be replaced with actual endpoint later)
const calculateSalary = async (request: SalaryRequest): Promise<SalaryResult> => {
  // TODO: Replace with actual API call when endpoint is ready
  // const response = await api.post('/calculate-salary', request);
  // return response.data;

  // Calculate gross yearly salary
  const grossYearly = request.isMonthly ? request.grossSalary * 12 : request.grossSalary;
  const grossMonthly = grossYearly / 12;

  // Calculate pension contribution
  const pensionDeduction = grossYearly * (request.pensionContribution / 100);
  const taxableIncome = grossYearly - pensionDeduction;

  // Calculate income tax
  let incomeTax = 0;
  let basicRate = 0;
  let higherRate = 0;
  let additionalRate = 0;

  if (taxableIncome > TAX_THRESHOLDS.personalAllowance) {
    const taxableAmount = taxableIncome - TAX_THRESHOLDS.personalAllowance;

    if (taxableAmount <= TAX_THRESHOLDS.basicRateLimit - TAX_THRESHOLDS.personalAllowance) {
      basicRate = taxableAmount * TAX_THRESHOLDS.basicRate;
      incomeTax = basicRate;
    } else if (taxableAmount <= TAX_THRESHOLDS.higherRateLimit - TAX_THRESHOLDS.personalAllowance) {
      basicRate = (TAX_THRESHOLDS.basicRateLimit - TAX_THRESHOLDS.personalAllowance) * TAX_THRESHOLDS.basicRate;
      higherRate = (taxableAmount - (TAX_THRESHOLDS.basicRateLimit - TAX_THRESHOLDS.personalAllowance)) * TAX_THRESHOLDS.higherRate;
      incomeTax = basicRate + higherRate;
    } else {
      basicRate = (TAX_THRESHOLDS.basicRateLimit - TAX_THRESHOLDS.personalAllowance) * TAX_THRESHOLDS.basicRate;
      higherRate = (TAX_THRESHOLDS.higherRateLimit - TAX_THRESHOLDS.basicRateLimit) * TAX_THRESHOLDS.higherRate;
      additionalRate = (taxableAmount - (TAX_THRESHOLDS.higherRateLimit - TAX_THRESHOLDS.personalAllowance)) * TAX_THRESHOLDS.additionalRate;
      incomeTax = basicRate + higherRate + additionalRate;
    }
  }

  // Calculate National Insurance
  let nationalInsurance = 0;
  if (grossYearly > NI_THRESHOLDS.yearlyThreshold) {
    const niableAmount = grossYearly - NI_THRESHOLDS.yearlyThreshold;
    if (grossYearly <= NI_THRESHOLDS.upperThreshold) {
      nationalInsurance = niableAmount * NI_THRESHOLDS.standardRate;
    } else {
      const standardPortion = (NI_THRESHOLDS.upperThreshold - NI_THRESHOLDS.yearlyThreshold) * NI_THRESHOLDS.standardRate;
      const higherPortion = (grossYearly - NI_THRESHOLDS.upperThreshold) * NI_THRESHOLDS.higherRate;
      nationalInsurance = standardPortion + higherPortion;
    }
  }

  // Calculate student loan repayment
  let studentLoanDeduction = 0;
  if (request.includeStudentLoan && request.studentLoanPlan) {
    const threshold = STUDENT_LOAN_THRESHOLDS[request.studentLoanPlan];
    if (grossYearly > threshold) {
      studentLoanDeduction = (grossYearly - threshold) * STUDENT_LOAN_THRESHOLDS.rate;
    }
  }

  // Calculate net income
  const totalDeductions = incomeTax + nationalInsurance + pensionDeduction + studentLoanDeduction;
  const netYearly = grossYearly - totalDeductions;
  const netMonthly = netYearly / 12;

  // Calculate effective tax rate
  const effectiveTaxRate = (totalDeductions / grossYearly) * 100;

  // Calculate budget recommendation (50:30:20 rule)
  const budgetRecommendation = {
    needs: netMonthly * 0.50,
    wants: netMonthly * 0.30,
    savings: netMonthly * 0.20,
  };

  return {
    grossYearly,
    grossMonthly,
    netYearly,
    netMonthly,
    incomeTax,
    nationalInsurance,
    pensionDeduction,
    studentLoanDeduction,
    effectiveTaxRate,
    taxBreakdown: {
      basicRate,
      higherRate,
      additionalRate,
    },
    budgetRecommendation,
  };
};

// Parse initial salary string to extract a number
const parseSalaryString = (salary: string): number | null => {
  // Remove currency symbols and commas
  const cleaned = salary.replace(/[£$,]/g, '');

  // Try to extract first number
  const match = cleaned.match(/(\d+(?:\.\d+)?)/);
  if (match) {
    const value = parseFloat(match[1]);
    // If it's less than 1000, assume it's in thousands
    return value < 1000 ? value * 1000 : value;
  }

  return null;
};

export default function SalaryCalculator({ initialSalary, onCalculated }: SalaryCalculatorProps) {
  const [grossSalary, setGrossSalary] = useState<string>('');
  const [isMonthly, setIsMonthly] = useState(false);
  const [pensionContribution, setPensionContribution] = useState(5);
  const [includeStudentLoan, setIncludeStudentLoan] = useState(false);
  const [studentLoanPlan, setStudentLoanPlan] = useState<'plan1' | 'plan2' | 'plan4'>('plan2');
  const [result, setResult] = useState<SalaryResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Parse initial salary if provided
  useEffect(() => {
    if (initialSalary) {
      const parsed = parseSalaryString(initialSalary);
      if (parsed) {
        setGrossSalary(parsed.toString());
      }
    }
  }, [initialSalary]);

  const handleCalculate = async () => {
    const salary = parseFloat(grossSalary);
    if (isNaN(salary) || salary <= 0) {
      setError('Please enter a valid salary amount');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const request: SalaryRequest = {
        grossSalary: salary,
        isMonthly,
        pensionContribution,
        includeStudentLoan,
        studentLoanPlan: includeStudentLoan ? studentLoanPlan : undefined,
      };

      const calculatedResult = await calculateSalary(request);
      setResult(calculatedResult);

      if (onCalculated) {
        onCalculated(calculatedResult);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to calculate salary');
      console.error('Error calculating salary:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-6">Salary Calculator</h2>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Salary Information</h3>

          {/* Gross Salary Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Gross Salary *
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2 text-gray-500 text-lg">£</span>
              <input
                type="number"
                value={grossSalary}
                onChange={(e) => setGrossSalary(e.target.value)}
                className="w-full border border-gray-300 rounded-md pl-8 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="80000"
                min="0"
              />
            </div>
          </div>

          {/* Yearly/Monthly Toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Payment Frequency
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setIsMonthly(false)}
                className={`flex-1 py-2 px-4 rounded-md transition-colors ${
                  !isMonthly
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                }`}
              >
                Yearly
              </button>
              <button
                type="button"
                onClick={() => setIsMonthly(true)}
                className={`flex-1 py-2 px-4 rounded-md transition-colors ${
                  isMonthly
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                }`}
              >
                Monthly
              </button>
            </div>
          </div>

          {/* Pension Contribution Slider */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Pension Contribution: {pensionContribution}%
            </label>
            <input
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={pensionContribution}
              onChange={(e) => setPensionContribution(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0%</span>
              <span>5%</span>
              <span>10%</span>
            </div>
          </div>

          {/* Student Loan Section */}
          <div>
            <div className="flex items-center mb-2">
              <input
                type="checkbox"
                id="studentLoan"
                checked={includeStudentLoan}
                onChange={(e) => setIncludeStudentLoan(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="studentLoan" className="ml-2 text-sm font-medium text-gray-700">
                Include Student Loan Repayment
              </label>
            </div>

            {includeStudentLoan && (
              <select
                value={studentLoanPlan}
                onChange={(e) => setStudentLoanPlan(e.target.value as 'plan1' | 'plan2' | 'plan4')}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="plan1">Plan 1 (threshold: £24,990)</option>
                <option value="plan2">Plan 2 (threshold: £27,295)</option>
                <option value="plan4">Plan 4 (threshold: £31,395)</option>
              </select>
            )}
          </div>

          {/* Calculate Button */}
          <button
            onClick={handleCalculate}
            disabled={isLoading || !grossSalary}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors font-medium"
          >
            {isLoading ? 'Calculating...' : 'Calculate Take-Home Pay'}
          </button>
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {result ? (
            <>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Take-Home Pay</h3>

              {/* Net Income Display */}
              <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6">
                <div className="text-center">
                  <p className="text-sm text-green-700 mb-1">Net Yearly</p>
                  <p className="text-4xl font-bold text-green-900 mb-4">
                    {formatCurrency(result.netYearly)}
                  </p>
                  <p className="text-sm text-green-700 mb-1">Net Monthly</p>
                  <p className="text-2xl font-bold text-green-900">
                    {formatCurrency(result.netMonthly)}
                  </p>
                </div>
              </div>

              {/* Tax Breakdown */}
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-900">Deductions Breakdown</h4>

                <div className="space-y-2">
                  <div className="flex justify-between items-center py-2 border-b border-gray-200">
                    <span className="text-gray-700">Income Tax</span>
                    <span className="font-medium text-red-600">
                      -{formatCurrency(result.incomeTax)}
                    </span>
                  </div>

                  {result.taxBreakdown.basicRate > 0 && (
                    <div className="flex justify-between items-center text-sm pl-4">
                      <span className="text-gray-600">Basic Rate (20%)</span>
                      <span className="text-gray-700">
                        {formatCurrency(result.taxBreakdown.basicRate)}
                      </span>
                    </div>
                  )}

                  {result.taxBreakdown.higherRate > 0 && (
                    <div className="flex justify-between items-center text-sm pl-4">
                      <span className="text-gray-600">Higher Rate (40%)</span>
                      <span className="text-gray-700">
                        {formatCurrency(result.taxBreakdown.higherRate)}
                      </span>
                    </div>
                  )}

                  {result.taxBreakdown.additionalRate > 0 && (
                    <div className="flex justify-between items-center text-sm pl-4">
                      <span className="text-gray-600">Additional Rate (45%)</span>
                      <span className="text-gray-700">
                        {formatCurrency(result.taxBreakdown.additionalRate)}
                      </span>
                    </div>
                  )}

                  <div className="flex justify-between items-center py-2 border-b border-gray-200">
                    <span className="text-gray-700">National Insurance</span>
                    <span className="font-medium text-red-600">
                      -{formatCurrency(result.nationalInsurance)}
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-2 border-b border-gray-200">
                    <span className="text-gray-700">Pension ({pensionContribution}%)</span>
                    <span className="font-medium text-red-600">
                      -{formatCurrency(result.pensionDeduction)}
                    </span>
                  </div>

                  {result.studentLoanDeduction > 0 && (
                    <div className="flex justify-between items-center py-2 border-b border-gray-200">
                      <span className="text-gray-700">Student Loan</span>
                      <span className="font-medium text-red-600">
                        -{formatCurrency(result.studentLoanDeduction)}
                      </span>
                    </div>
                  )}

                  <div className="flex justify-between items-center py-3 bg-gray-50 px-3 rounded-md mt-2">
                    <span className="font-semibold text-gray-900">Effective Tax Rate</span>
                    <span className="font-bold text-gray-900">
                      {result.effectiveTaxRate.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Budget Recommendation */}
              {result.budgetRecommendation && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-900 mb-3">
                    50:30:20 Budget Recommendation
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-blue-700">Needs (50%)</span>
                      <span className="font-medium text-blue-900">
                        {formatCurrency(result.budgetRecommendation.needs)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-700">Wants (30%)</span>
                      <span className="font-medium text-blue-900">
                        {formatCurrency(result.budgetRecommendation.wants)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-700">Savings (20%)</span>
                      <span className="font-medium text-blue-900">
                        {formatCurrency(result.budgetRecommendation.savings)}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-500">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400 mb-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                  />
                </svg>
                <p>Enter your salary details and click Calculate</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
