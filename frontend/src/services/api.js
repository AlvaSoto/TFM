import axios from 'axios';

// 127.0.0.1 explícito (no "localhost"): en macOS el navegador puede resolver
// localhost a IPv6 (::1) y acabar en otro proceso que escuche en ese puerto.
const API_URL = 'http://127.0.0.1:8000/api/v1';

export const getHouseholds = async () => {
    const response = await axios.get(`${API_URL}/households`);
    // CORRECCIÓN: El backend devuelve { "households": [...] }, no "household_ids"
    return response.data.households; 
};

export const getRegions = async () => {
    const response = await axios.get(`${API_URL}/regions`);
    return response.data;
};

export const analyzeHousehold = async (id, region) => {
    const url = `${API_URL}/consumption/dashboard/${id}?region=${encodeURIComponent(region)}`;
    const response = await axios.get(url);
    return response.data;
};

// --- VISTA OPERADOR (gestora) ---

export const getFleetOverview = async (region) => {
    const url = `${API_URL}/fleet/overview?region=${encodeURIComponent(region)}`;
    const response = await axios.get(url);
    return response.data;
};

export const scoreFleet = async (limit, region) => {
    const url = `${API_URL}/fleet/score?limit=${limit}&region=${encodeURIComponent(region)}`;
    // El scoring ejecuta el modelo sobre varios hogares: puede tardar minutos
    const response = await axios.post(url, null, { timeout: 600000 });
    return response.data;
};

export const getFleetTrends = async () => {
    const response = await axios.get(`${API_URL}/fleet/trends`);
    return response.data;
};

export const getSystemInfo = async () => {
    const response = await axios.get(`${API_URL}/system/info`);
    return response.data;
};