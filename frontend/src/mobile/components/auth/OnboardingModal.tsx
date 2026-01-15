import React, { useState, useEffect } from 'react';
import { UserPreferences } from '../../../types';
import { ARXIV_CATEGORIES } from '../../../constants';
import { checkUsername, completeOnboarding } from '../../../services/backendService';
import { Check, X, Loader2 } from 'lucide-react';

interface OnboardingModalProps {
  isOpen: boolean;
  onComplete: (prefs: UserPreferences) => void;
}

const OnboardingModal: React.FC<OnboardingModalProps> = ({ isOpen, onComplete }) => {
  const [selectedCats, setSelectedCats] = useState<string[]>([]);
  const [keywords, setKeywords] = useState('');
  const [username, setUsername] = useState('');
  const [usernameStatus, setUsernameStatus] = useState<'idle' | 'checking' | 'available' | 'taken'>('idle');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Debounce check username
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (username.length >= 3) {
        setUsernameStatus('checking');
        const available = await checkUsername(username);
        setUsernameStatus(available ? 'available' : 'taken');
      } else if (username.length > 0) {
        setUsernameStatus('idle'); // Too short
      } else {
        setUsernameStatus('idle');
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [username]);

  if (!isOpen) return null;

  const toggleCat = (id: string) => {
    setSelectedCats(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const handleSubmit = async () => {
    if (usernameStatus === 'taken' || (username.length > 0 && username.length < 3)) return;

    setIsSubmitting(true);
    const kwList = keywords.split(',').map(k => k.trim()).filter(k => k.length > 0);

    // 1. Submit Preferences with Name
    const prefs: UserPreferences = {
      selectedCategories: selectedCats,
      keywords: kwList,
      name: username || undefined
    };
    onComplete(prefs);

    // NOTE: App.tsx handles the backend calls (updatePreferences & completeOnboarding)
    setIsSubmitting(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fade-in">
      <div className="bg-gray-900 border border-gray-700 w-full max-w-md rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        <div className="p-6 overflow-y-auto custom-scrollbar">
          <h2 className="text-2xl font-bold text-white mb-2">Welcome to FloPap</h2>
          <p className="text-gray-400 text-sm mb-6">Let's set up your profile. You can modify these later in your profile.</p>

          {/* 1. Username Input */}
          <div className="mb-6">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Choose a Username
            </label>
            <div className="relative">
              <input
                type="text"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  if (e.target.value.length === 0) setUsernameStatus('idle');
                  else if (e.target.value.length < 3) setUsernameStatus('idle');
                }}
                placeholder="Username (optional, min 3 chars)"
                className={`w-full bg-gray-800 border ${usernameStatus === 'taken' ? 'border-red-500' :
                  usernameStatus === 'available' ? 'border-green-500' : 'border-gray-700'
                  } text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm`}
              />
              <div className="absolute right-3 top-3 text-gray-400">
                {usernameStatus === 'checking' && <Loader2 size={20} className="animate-spin" />}
                {usernameStatus === 'available' && <Check size={20} className="text-green-500" />}
                {usernameStatus === 'taken' && <X size={20} className="text-red-500" />}
              </div>
            </div>
            {usernameStatus === 'taken' && <p className="text-red-500 text-xs mt-1">Username already taken.</p>}
          </div>

          {/* 2. Categories */}
          <div className="mb-6">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Select Areas of Interest
            </label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
              {ARXIV_CATEGORIES.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => toggleCat(cat.id)}
                  className={`text-left px-3 py-2 rounded-lg text-xs transition-colors border ${selectedCats.includes(cat.id)
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700'
                    }`}
                >
                  <span className="font-bold block">{cat.id}</span>
                  <span className="opacity-80 truncate">{cat.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 3. Keywords */}
          <div className="mb-8">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Keywords (Comma separated)
            </label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="e.g. transformers, diffusion, robotics..."
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={selectedCats.length === 0 || (username.length > 0 && username.length < 3) || usernameStatus === 'taken' || isSubmitting}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold py-3 rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSubmitting ? <Loader2 className="animate-spin" /> : 'Start Discovery'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OnboardingModal;