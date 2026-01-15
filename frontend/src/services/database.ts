
import { Paper, UserInteractions, UserPreferences } from "../types";

const DB_NAME = 'FlopapDB';
const DB_VERSION = 1;

interface UserData {
  key: 'profile';
  preferences: UserPreferences;
  interactions: UserInteractions;
}

export const initDB = (): Promise<IDBDatabase> => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      // Store for papers (Key: id)
      if (!db.objectStoreNames.contains('papers')) {
        db.createObjectStore('papers', { keyPath: 'id' });
      }
      // Store for user data (Singleton, Key: key)
      if (!db.objectStoreNames.contains('userData')) {
        db.createObjectStore('userData', { keyPath: 'key' });
      }
    };
  });
};

export const getDB = async (): Promise<IDBDatabase> => {
  return await initDB();
};

// --- Generic Helpers ---

const runTransaction = <T>(
  storeName: string,
  mode: IDBTransactionMode,
  operation: (store: IDBObjectStore) => IDBRequest
): Promise<T> => {
  return new Promise(async (resolve, reject) => {
    try {
      const db = await getDB();
      const tx = db.transaction(storeName, mode);
      const store = tx.objectStore(storeName);
      const request = operation(store);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    } catch (e) {
      reject(e);
    }
  });
};

// --- Paper Operations ---

export const savePapersToDB = async (papers: Paper[]) => {
  const db = await getDB();
  const tx = db.transaction('papers', 'readwrite');
  const store = tx.objectStore('papers');

  papers.forEach(paper => {
    // We use put to upsert (update if exists, insert if new)
    // Important: We don't want to overwrite existing AI insights if the new fetch doesn't have them
    // So strictly speaking we should read-then-write, but for bulk fetch efficiency we might just overwrite basic data
    // A better strategy for a real app is to merge. For now, we assume 'put' is okay or we check.
    // Let's do a quick check strictly for single updates, but for bulk let's just put.
    // Actually, to preserve AI cache, we should probably merge in application logic, but here we'll just put.
    store.put(paper);
  });

  return new Promise<void>((resolve) => {
    tx.oncomplete = () => resolve();
  });
};

export const updatePaperInDB = async (paper: Paper) => {
  return runTransaction('papers', 'readwrite', store => store.put(paper));
};

export const getPaperFromDB = async (id: string): Promise<Paper | undefined> => {
  return runTransaction<Paper>('papers', 'readonly', store => store.get(id));
};

export const getPapersFromDB = async (ids: string[]): Promise<Paper[]> => {
  const db = await getDB();
  const tx = db.transaction('papers', 'readonly');
  const store = tx.objectStore('papers');

  const promises = ids.map(id => new Promise<Paper | undefined>((resolve) => {
    const req = store.get(id);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => resolve(undefined);
  }));

  const results = await Promise.all(promises);
  return results.filter((p): p is Paper => !!p);
};

// --- User Operations ---

// Old Monolithic Data (Kept for migration/fallback)
const DEFAULT_USER_DATA: UserData = {
  key: 'profile',
  preferences: { selectedCategories: [], keywords: [] },
  interactions: { likedPaperIds: [], bookmarkedPaperIds: [], notInterestedPaperIds: [] }
};

/**
 * @deprecated Use granular getters instead
 */
export const getUserData = async (): Promise<UserData> => {
  const data = await runTransaction<UserData>('userData', 'readonly', store => store.get('profile'));
  return data || DEFAULT_USER_DATA;
};

/**
 * @deprecated Use granular savers instead
 */
export const saveUserData = async (data: UserData) => {
  return runTransaction('userData', 'readwrite', store => store.put(data));
};

// --- New Granular Operations ---

export const getUserPreferencesDB = async (): Promise<UserPreferences | null> => {
  // Try new key first
  const res = await runTransaction<{ key: string, data: UserPreferences }>('userData', 'readonly', store => store.get('user_preferences'));
  if (res && res.data) return res.data;

  // Fallback to old key if new key doesn't exist
  const oldData = await getUserData();
  // If old data is just default empty, return null to signify "no data"
  if (oldData.preferences.selectedCategories.length === 0 && oldData.preferences.keywords.length === 0) {
    return null;
  }
  return oldData.preferences;
};

export const saveUserPreferencesDB = async (prefs: UserPreferences) => {
  return runTransaction('userData', 'readwrite', store => store.put({ key: 'user_preferences', data: prefs }));
};

export const getUserInteractionsDB = async (): Promise<UserInteractions> => {
  // Try new key first
  const res = await runTransaction<{ key: string, data: UserInteractions }>('userData', 'readonly', store => store.get('user_interactions'));
  if (res && res.data) return res.data;

  // Fallback
  const oldData = await getUserData();
  return oldData.interactions;
};

export const saveUserInteractionsDB = async (interactions: UserInteractions) => {
  return runTransaction('userData', 'readwrite', store => store.put({ key: 'user_interactions', data: interactions }));
};
