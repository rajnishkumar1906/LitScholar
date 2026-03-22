// src/components/UpgradeButton.jsx
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

const UpgradeButton = () => {
  const { user, subscription } = useApp();
  const navigate = useNavigate();

  if (!user || subscription?.is_active) return null;

  return (
    <button
      onClick={() => navigate('/pricing')}
      className="bg-gradient-to-r from-amber-400 to-amber-600 hover:from-amber-500 hover:to-amber-700 text-white font-bold py-2 px-4 rounded-full shadow-lg transform transition hover:scale-105 active:scale-95 flex items-center gap-2"
    >
      <span>✨</span>
      Upgrade to Premium
    </button>
  );
};

export default UpgradeButton;