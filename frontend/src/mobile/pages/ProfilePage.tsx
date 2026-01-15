import UserProfile from '../components/UserProfile';
import { useNavigate } from 'react-router-dom';
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

    return (
        <UserProfile
            preferences={userStore.preferences}
            interactions={interactionStore}
            onUpdatePreferences={userStore.updatePreferences}
            onSelectPaper={(paper, collection) => {
                onSelectPaper(paper, collection);
                navigate('/');
            }}
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
