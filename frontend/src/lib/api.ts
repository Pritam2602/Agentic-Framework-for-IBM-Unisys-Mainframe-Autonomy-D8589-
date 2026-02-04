import axios from 'axios';
import { CatalogEntry, CatalogEntryDetail } from '@/types/catalog';

const API_BASE_URL = 'http://localhost:5000/api';

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface CatalogResponse extends CatalogEntry { }

export const fetchCatalog = async (family?: string): Promise<CatalogEntry[]> => {
    const params = family ? { family } : {};
    const response = await api.get<CatalogEntry[]>('/catalog', { params });
    return response.data;
};

export const fetchCapability = async (command: string): Promise<CatalogEntryDetail> => {
    const response = await api.get<CatalogEntryDetail>('/capability', {
        params: { command },
    });
    return response.data;
};
