import React from 'react';
import { BeakerIcon } from '@heroicons/react/24/outline';

interface DummyDataToggleProps {
  isDummyMode: boolean;
  onToggle: (enabled: boolean) => void;
  className?: string;
}

export const DummyDataToggle: React.FC<DummyDataToggleProps> = ({
  isDummyMode,
  onToggle,
  className = ''
}) => {
  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* Toggle Switch */}
      <button
        onClick={() => onToggle(!isDummyMode)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
          isDummyMode ? 'bg-blue-600' : 'bg-gray-200'
        }`}
        role="switch"
        aria-checked={isDummyMode}
        aria-label="Toggle test data mode"
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            isDummyMode ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
      
      <div className="flex items-center space-x-2">
        <BeakerIcon className={`h-4 w-4 ${isDummyMode ? 'text-blue-600' : 'text-gray-400'}`} />
        <span className={`text-sm font-medium ${isDummyMode ? 'text-blue-600' : 'text-gray-500'}`}>
          Test
        </span>
      </div>
      
      {/* Status Badge */}
      <div className={`px-2 py-1 rounded-full text-xs font-medium ${
        isDummyMode 
          ? 'bg-blue-100 text-blue-800' 
          : 'bg-green-100 text-green-800'
      }`}>
        {isDummyMode ? 'Test Data' : 'Live Data'}
      </div>
    </div>
  );
};