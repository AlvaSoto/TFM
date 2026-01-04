import React from 'react';
import { AlertCircle, CheckCircle } from 'lucide-react';

const AlertMessage = ({ message, type = 'error' }) => {
  const isError = type === 'error';
  
  const containerStyles = `border-l-4 p-4 mb-6 rounded-r-lg flex items-start gap-3 ${
    isError 
      ? "bg-red-50 border-red-500 text-red-800" 
      : "bg-green-50 border-green-500 text-green-800"
  }`;

  return (
    <div className={containerStyles} role="alert">
      {isError ? <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" /> : <CheckCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />}
      <div>
        <p className="font-medium">{isError ? 'Error' : 'Éxito'}</p>
        <p className="text-sm mt-1 opacity-90">{message}</p>
      </div>
    </div>
  );
};

export default AlertMessage;