import { CatalogEntry, CatalogEntryDetail } from '@/types/catalog';

const API_BASE_URL = 'http://localhost:8000/api';

export interface CatalogResponse extends CatalogEntry { }

export const fetchCatalog = async (family?: string): Promise<CatalogEntry[]> => {
    const params = family ? `?family=${encodeURIComponent(family)}` : '';
    const response = await fetch(`${API_BASE_URL}/catalog/commands${params}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch catalog: ${response.statusText}`);
    }
    return response.json();
};

export const fetchCapability = async (command: string): Promise<CatalogEntryDetail> => {
    const response = await fetch(`${API_BASE_URL}/capability?command=${encodeURIComponent(command)}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch capability: ${response.statusText}`);
    }
    return response.json();
};
