import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { UI_STRINGS } from '../../constants';
import { AppLanguage } from '../../types';

interface HideConfirmModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    isDark: boolean;
    language: AppLanguage;
}

const HideConfirmModal: React.FC<HideConfirmModalProps> = ({ isOpen, onClose, onConfirm, isDark, language }) => {
    if (!isOpen) return null;
    const ui = UI_STRINGS[language];

    return (
        <div className="fixed inset-0 z-[60] bg-black/80 backdrop-blur-sm flex items-center justify-center px-6">
            <div className={`rounded-2xl p-6 border shadow-2xl w-full max-w-sm ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                <div className="flex justify-center text-yellow-500 mb-4">
                    <AlertTriangle size={40} />
                </div>
                <h3 className={`text-xl font-bold text-center mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>{ui.hideConfirmTitle}</h3>
                <p className={`text-sm text-center mb-6 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{ui.hideConfirmText}</p>
                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        className={`flex-1 py-3 rounded-xl font-bold transition-colors ${isDark ? 'bg-gray-700 text-white hover:bg-gray-600' : 'bg-gray-200 text-gray-800 hover:bg-gray-300'}`}
                    >
                        {ui.cancel}
                    </button>
                    <button
                        onClick={onConfirm}
                        className="flex-1 py-3 bg-red-600 text-white rounded-xl font-bold hover:bg-red-500 transition-colors"
                    >
                        {ui.confirm}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default HideConfirmModal;
