import React, { useRef, useEffect } from 'react';
import { Search } from 'lucide-react';
interface SearchModalProps {
    isOpen: boolean;
    onClose: () => void;
    searchPhrase: string;
    setSearchPhrase: (val: string) => void;
    onSearch: () => void;
    isDark: boolean;
}

const SearchModal: React.FC<SearchModalProps> = ({ isOpen, onClose, searchPhrase, setSearchPhrase, onSearch, isDark }) => {
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex items-start pt-20 justify-center px-4">
            <div className={`w-full max-w-md rounded-xl p-4 shadow-2xl border ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                <h3 className={`font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Search ArXiv</h3>
                <div className="flex gap-2">
                    <input
                        ref={inputRef}
                        type="text"
                        value={searchPhrase}
                        onChange={(e) => setSearchPhrase(e.target.value)}
                        placeholder="Keywords, authors, or ID..."
                        className={`flex-1 px-4 py-3 rounded-lg border outline-none ${isDark ? 'bg-black text-white border-gray-600 focus:border-blue-500' : 'bg-gray-50 text-gray-900 border-gray-300 focus:border-blue-500'}`}
                        onKeyDown={(e) => e.key === 'Enter' && onSearch()}
                    />
                    <button onClick={onSearch} className="bg-blue-600 text-white px-4 rounded-lg font-bold">Go</button>
                </div>
                <button onClick={onClose} className="mt-4 text-sm text-gray-400 w-full py-2">Cancel</button>
            </div>
        </div>
    );
};

export default SearchModal;
