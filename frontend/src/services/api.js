import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1'; // Backend URL

export const getHouseholds = async () => {
  const response = await axios.get(`${API_URL}/households`);
  return response.data.household_ids;
};

export const analyzeHousehold = async (id) => {
    const response = await axios.get(`${API_URL}/analyse/${id}`);
    return response.data;
}

