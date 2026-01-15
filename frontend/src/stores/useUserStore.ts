import { create } from 'zustand';
import { User, UserPreferences } from '../types';
import * as StorageService from '../services/storageService';

interface UserState {
    isLoggedIn: boolean;
    user: User | undefined;
    preferences: UserPreferences;

    // Actions
    login: (token: string, user: any) => void;
    logout: () => void;
    refreshProfile: () => Promise<void>;
    updatePreferences: (prefs: UserPreferences) => Promise<void>;
    checkAuth: () => Promise<void>;
}

export const useUserStore = create<UserState>((set, get) => ({
    // Standalone edition: always logged in as default user
    isLoggedIn: true,
    user: {
        id: 'default',
        name: 'Local User',
        email: null,
        phone_number: null,
        avatar_url: null,
        onboarding_completed: true
    },
    preferences: { selectedCategories: [], keywords: [] },

    login: (token, user) => {
        // Standalone edition: no-op (already logged in)
        console.log('Standalone edition: login is not required');
    },

    logout: () => {
        // Standalone edition: no-op (cannot logout)
        console.log('Standalone edition: logout is not available');
    },

    refreshProfile: async () => {
        // Load local preferences from storage
        const localPrefs = await StorageService.getPreferences();
        if (localPrefs) {
            set(state => ({
                preferences: {
                    ...state.preferences,
                    ...localPrefs
                }
            }));
        }
    },

    updatePreferences: async (newPrefs) => {
        set({ preferences: newPrefs });
        await StorageService.savePreferences(newPrefs);
    },

    checkAuth: async () => {
        // Standalone edition: always authenticated
        set({ isLoggedIn: true });
        await get().refreshProfile();
    }
}));
