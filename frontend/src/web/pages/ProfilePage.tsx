import React from 'react';
import { useNavigate } from 'react-router-dom';
import UserProfile from '../components/UserProfile';
import { useUserStore } from '../../stores/useUserStore';
import { useInteractionStore } from '../../stores/useInteractionStore';
import { AppLanguage, AppTheme, Paper } from '../../types';

interface ProfilePageProps {
    onSelectPaper: (paper: Paper, collection: Paper[]) => void;
    language: AppLanguage;
    theme: AppTheme;
    isCloudEdition: boolean;
}

const ProfilePage: React.FC<ProfilePageProps> = ({
    onSelectPaper,
    language,
    theme,
    isCloudEdition
}) => {
    const userStore = useUserStore();
    const interactionStore = useInteractionStore();
    const navigate = useNavigate();

    // Wrap onSelectPaper to also navigate to Feed after setting collection
    const handleSelectPaper = (paper: Paper, collection: Paper[]) => {
        onSelectPaper(paper, collection);
        navigate('/');
    };

    return (
        <UserProfile
            preferences={userStore.preferences}
            interactions={interactionStore}
            onUpdatePreferences={userStore.updatePreferences}
            onSelectPaper={handleSelectPaper}
            onLogout={userStore.logout}
            user={userStore.user}
            language={language}
            theme={theme}
            isActive={true}
            isCloudEdition={isCloudEdition}
        />
    );
};

export default ProfilePage;

