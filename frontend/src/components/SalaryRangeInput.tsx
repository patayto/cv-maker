interface SalaryRangeInputProps {
  min: number | undefined;
  max: number | undefined;
  currency: string | undefined;
  onChange: (data: { min?: number; max?: number; currency?: string }) => void;
  editable?: boolean;
}

export function SalaryRangeInput({ min, max, currency, onChange, editable = true }: SalaryRangeInputProps) {
  const handleMinChange = (value: string) => {
    const num = value ? parseInt(value, 10) : undefined;
    onChange({ min: num, max, currency });
  };

  const handleMaxChange = (value: string) => {
    const num = value ? parseInt(value, 10) : undefined;
    onChange({ min, max: num, currency });
  };

  const handleCurrencyChange = (value: string) => {
    onChange({ min, max, currency: value || undefined });
  };

  const formatNumber = (num: number | undefined) => {
    if (num === undefined) return '';
    return num.toLocaleString('en-GB');
  };

  const parseNumber = (str: string) => {
    return str.replace(/,/g, '');
  };

  return (
    <div className="space-y-4">
      {/* Currency Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Currency
        </label>
        <select
          value={currency || ''}
          onChange={(e) => handleCurrencyChange(e.target.value)}
          disabled={!editable}
          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        >
          <option value="">Select currency...</option>
          <option value="GBP">£ GBP (British Pound)</option>
          <option value="USD">$ USD (US Dollar)</option>
          <option value="EUR">€ EUR (Euro)</option>
        </select>
      </div>

      {/* Salary Range Inputs */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Minimum Salary
          </label>
          <input
            type="text"
            value={min !== undefined ? formatNumber(min) : ''}
            onChange={(e) => handleMinChange(parseNumber(e.target.value))}
            disabled={!editable}
            placeholder="e.g., 50000"
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Maximum Salary
          </label>
          <input
            type="text"
            value={max !== undefined ? formatNumber(max) : ''}
            onChange={(e) => handleMaxChange(parseNumber(e.target.value))}
            disabled={!editable}
            placeholder="e.g., 80000"
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
        </div>
      </div>

      {/* Validation Message */}
      {min !== undefined && max !== undefined && min > max && (
        <p className="text-sm text-red-600">
          Minimum salary cannot be greater than maximum salary
        </p>
      )}

      {/* Display Range */}
      {min !== undefined && max !== undefined && currency && min <= max && (
        <div className="bg-gray-50 p-3 rounded-md">
          <p className="text-sm font-medium text-gray-700">
            Salary Range:{' '}
            <span className="text-gray-900">
              {currency === 'GBP' && '£'}
              {currency === 'USD' && '$'}
              {currency === 'EUR' && '€'}
              {formatNumber(min)} - {formatNumber(max)}
            </span>
          </p>
        </div>
      )}
    </div>
  );
}
