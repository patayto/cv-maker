import { useState } from 'react';

interface EditableListProps {
  items: string[];
  onChange: (items: string[]) => void;
  editable?: boolean;
  placeholder?: string;
}

export function EditableList({ items = [], onChange, editable = true, placeholder = 'Add an item...' }: EditableListProps) {
  const [newItem, setNewItem] = useState('');
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingValue, setEditingValue] = useState('');

  const addItem = () => {
    const trimmed = newItem.trim();
    if (trimmed) {
      onChange([...items, trimmed]);
      setNewItem('');
    }
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const startEditing = (index: number) => {
    setEditingIndex(index);
    setEditingValue(items[index]);
  };

  const saveEdit = () => {
    if (editingIndex !== null) {
      const trimmed = editingValue.trim();
      if (trimmed) {
        const newItems = [...items];
        newItems[editingIndex] = trimmed;
        onChange(newItems);
      }
      setEditingIndex(null);
      setEditingValue('');
    }
  };

  const cancelEdit = () => {
    setEditingIndex(null);
    setEditingValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent, isNew: boolean) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (isNew) {
        addItem();
      } else {
        saveEdit();
      }
    } else if (e.key === 'Escape' && !isNew) {
      cancelEdit();
    }
  };

  return (
    <div className="space-y-3">
      {/* Item List */}
      {items.length > 0 ? (
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li key={index} className="flex items-start gap-2">
              {editingIndex === index ? (
                // Edit mode
                <div className="flex-1 flex gap-2">
                  <textarea
                    value={editingValue}
                    onChange={(e) => setEditingValue(e.target.value)}
                    onKeyDown={(e) => handleKeyDown(e, false)}
                    className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={3}
                    autoFocus
                  />
                  <div className="flex flex-col gap-1">
                    <button
                      type="button"
                      onClick={saveEdit}
                      className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                    >
                      Save
                    </button>
                    <button
                      type="button"
                      onClick={cancelEdit}
                      className="px-3 py-1 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                // View mode
                <>
                  <span className="text-gray-400 mt-1">•</span>
                  <span className="flex-1 text-gray-700">{item}</span>
                  {editable && (
                    <div className="flex gap-1">
                      <button
                        type="button"
                        onClick={() => startEditing(index)}
                        className="text-blue-600 hover:text-blue-800 text-sm"
                        title="Edit"
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
                            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                          />
                        </svg>
                      </button>
                      <button
                        type="button"
                        onClick={() => removeItem(index)}
                        className="text-red-600 hover:text-red-800 text-sm"
                        title="Remove"
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
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </div>
                  )}
                </>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-gray-500 italic">No items</p>
      )}

      {/* Add New Item */}
      {editable && (
        <div className="flex gap-2">
          <textarea
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, true)}
            placeholder={placeholder}
            className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={2}
          />
          <button
            type="button"
            onClick={addItem}
            disabled={!newItem.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Add
          </button>
        </div>
      )}
    </div>
  );
}
