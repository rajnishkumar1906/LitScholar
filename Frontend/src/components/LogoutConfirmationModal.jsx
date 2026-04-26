import { useState, useEffect, useRef } from 'react';

export default function LogoutConfirmationModal({ onConfirm, onCancel }) {
  const modalRef = useRef();

  // Close modal if user clicks outside of it
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        onCancel();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onCancel]);

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div ref={modalRef} className="bg-white rounded-2xl shadow-2xl p-8 max-w-sm w-full text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Are you sure?</h2>
        <p className="text-gray-600 mb-8">You will be returned to the login screen.</p>
        <div className="flex justify-center gap-4">
          <button
            onClick={onCancel}
            className="px-8 py-3 bg-gray-200 text-gray-800 font-bold rounded-xl hover:bg-gray-300 transition-all"
          >
            Stay Logged In
          </button>
          <button
            onClick={onConfirm}
            className="px-8 py-3 bg-red-600 text-white font-bold rounded-xl hover:bg-red-700 transition-all shadow-lg shadow-red-500/20"
          >
            Log Out
          </button>
        </div>
      </div>
    </div>
  );
}
