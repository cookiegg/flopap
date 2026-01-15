import React from 'react';
import { User } from '../../types';
import { LogOut, X, User as UserIcon, Settings } from 'lucide-react';
import { UI_STRINGS } from '../../constants';
import { AppLanguage, AppTheme } from '../../types';

interface UserMenuProps {
    isOpen: boolean;
    onClose: () => void;
    onLogout: () => void;
    user?: User;
    language: AppLanguage;
    theme: AppTheme;
    isCloudEdition?: boolean;
}

const UserMenu: React.FC<UserMenuProps> = ({
    isOpen,
    onClose,
    onLogout,
    user,
    language,
    theme,
    isCloudEdition = false
}) => {
    const isDark = theme === 'dark';
    const ui = UI_STRINGS[language];

    return (
        <>
            {/* Overlay */}
            <div
                className={`fixed inset-0 bg-black/80 backdrop-blur-sm z-[70] transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
                onClick={onClose}
            />

            {/* Right Drawer */}
            <div className={`fixed top-0 right-0 h-full w-72 ${isDark ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} border-l z-[80] transform transition-transform duration-300 ${isOpen ? 'translate-x-0' : 'translate-x-full'} shadow-2xl flex flex-col`}>
                <div className="p-6 h-full flex flex-col">
                    <div className="flex justify-between items-center mb-8">
                        <h2 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{ui.profile}</h2>
                        <button onClick={onClose} className={`p-1 rounded-full ${isDark ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}>
                            <X size={20} />
                        </button>
                    </div>

                    <div className="flex-1 space-y-6">
                        {/* User Info Summary */}
                        <div className={`p-4 rounded-2xl border ${isDark ? 'bg-black/20 border-white/5' : 'bg-gray-50 border-gray-100'}`}>
                            <div className="flex flex-col items-center gap-3">
                                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 p-[2px]">
                                    <div className={`w-full h-full rounded-full flex items-center justify-center overflow-hidden ${isDark ? 'bg-black' : 'bg-white'}`}>
                                        {user?.avatar_url ? (
                                            <img src={user.avatar_url} alt="Profile" className="w-full h-full object-cover" />
                                        ) : (
                                            <UserIcon size={40} className="text-gray-400" />
                                        )}
                                    </div>
                                </div>
                                <div className="text-center">
                                    <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                        {user?.name || user?.phone_number || ui.guestUser}
                                    </h3>
                                    <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                                        {user?.name && user?.phone_number ? 
                                            `${user.phone_number} • ${ui.cloudUser}` : 
                                            (user?.email ? `${user.email} • ${ui.cloudUser}` : 
                                             `${ui.cloudUser}`)}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="space-y-2">
                            <button
                                onClick={onLogout}
                                className={`w-full flex items-center gap-3 p-4 rounded-xl transition-colors ${isDark ? 'bg-gray-800 text-red-400 hover:bg-gray-700' : 'bg-gray-100 text-red-500 hover:bg-gray-200'}`}
                            >
                                <LogOut size={20} />
                                <span className="font-bold">{ui.logout}</span>
                            </button>
                        </div>
                    </div>

                    <div className={`text-center text-[10px] ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                        v0.1.0 • Flopap
                    </div>
                </div>
            </div>
        </>
    );
};

export default UserMenu;
