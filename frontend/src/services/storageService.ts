
import { Paper, UserInteractions, UserPreferences } from "../types";
import * as DB from "./database";

// --- Preferences ---

export const getPreferences = async (): Promise<UserPreferences | null> => {
  return await DB.getUserPreferencesDB();
};

export const savePreferences = async (prefs: UserPreferences) => {
  await DB.saveUserPreferencesDB(prefs);
};

// --- Interactions ---

export const getInteractions = async (): Promise<UserInteractions> => {
  return await DB.getUserInteractionsDB();
};

export const saveInteractions = async (interactions: UserInteractions) => {
  await DB.saveUserInteractionsDB(interactions);
};

// --- Papers ---

export const savePaper = async (paper: Paper) => {
  await DB.updatePaperInDB(paper);
};

export const getPapersByIds = async (ids: string[]): Promise<Paper[]> => {
  return await DB.getPapersFromDB(ids);
};

export const getCachedPaper = async (id: string): Promise<Paper | undefined> => {
  return await DB.getPaperFromDB(id);
};
