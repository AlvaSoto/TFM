import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

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