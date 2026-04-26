// src/components/LogoutConfirmModal.jsx
import { useApp } from '../context/AppContext';

export default function LogoutConfirmModal() {
  const { showLogoutConfirm, confirmLogout, cancelLogout } = useApp();

  if (!showLogoutConfirm) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm">
      <div className="bg-white/10 rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 border border-amber-100 transform transition-all scale-100">
        <h3 className="text-2xl font-bold text-white mb-4 text-center">
          Log out of BookBuddy?
        </h3>
        <p className="text-white mb-8 text-center text-lg">
          You’ll need to sign in again to access your recommendations and saved books.
        </p>

        <div className="flex gap-4 justify-center">
          <button
            onClick={cancelLogout}
            className="px-8 py-3 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300"
          >
            Cancel
          </button>

          <button
            onClick={confirmLogout}
            className="px-8 py-3 bg-red-600 text-white font-medium rounded-xl hover:bg-red-700 transition-colors focus:outline-none focus:ring-2 focus:ring-red-300"
          >
            Log Out
          </button>
        </div>
      </div>
    </div>
  );
}