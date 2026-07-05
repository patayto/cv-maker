import { useState, type KeyboardEvent } from 'react';

interface TagInputProps {
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  editable?: boolean;
}

export function TagInput({ value = [], onChange, placeholder = 'Add a tag...', editable = true }: TagInputProps) {
  const [inputValue, setInputValue] = useState('');

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!editable) return;

    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag();
    } else if (e.key === 'Backspace' && inputValue === '' && value.length > 0) {
      // Remove last tag if input is empty
      removeTag(value.length - 1);
    }
  };

  const addTag = () => {
    const trimmed = inputValue.trim();
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed]);
      setInputValue('');
    }
  };

  const removeTag = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    if (!editable) return;

    const pastedText = e.clipboardData.getData('text');
    if (pastedText.includes(',')) {
      e.preventDefault();
      const tags = pastedText
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag && !value.includes(tag));

      if (tags.length > 0) {
        onChange([...value, ...tags]);
        setInputValue('');
      }
    }
  };

  return (
    <div className="space-y-2">
      {/* Tag Display */}
      <div className="flex flex-wrap gap-2">
        {value.map((tag, index) => (
          <span
            key={`${tag}-${index}`}
            className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
          >
            {tag}
            {editable && (
              <button
                type="button"
                onClick={() => removeTag(index)}
                className="hover:bg-blue-200 rounded-full p-0.5 transition-colors"
                aria-label={`Remove ${tag}`}
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
          </span>
        ))}
      </div>

      {/* Input Field */}
      {editable && (
        <div>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            onBlur={addTag}
            placeholder={value.length === 0 ? placeholder : ''}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="mt-1 text-xs text-gray-500">
            Press Enter or comma to add. Paste comma-separated list to add multiple.
          </p>
        </div>
      )}

      {!editable && value.length === 0 && (
        <p className="text-sm text-gray-500 italic">No tags</p>
      )}
    </div>
  );
}
