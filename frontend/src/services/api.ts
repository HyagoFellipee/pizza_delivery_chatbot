/**
 * API service for backend communication using Axios
 */
import axios, { AxiosInstance } from 'axios'
import { ChatRequest, ChatResponse } from '../types/chat'

// Get API URL from environment variable
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create Axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Send a chat message to the backend
 */
export const sendChatMessage = async (
  request: ChatRequest,
  currentCartItems?: any[],
  currentTotal?: number
): Promise<ChatResponse> => {
  try {
    const payload = {
      ...request,
      cart_items: currentCartItems || [],
      total: currentTotal || 0.0
    }
    const response = await apiClient.post<ChatResponse>('/api/chat', payload)
    return response.data
  } catch (error) {
    console.error('Error sending chat message:', error)
    throw error
  }
}

/**
 * Check backend health
 */
export const checkHealth = async (): Promise<{ status: string }> => {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error) {
    console.error('Error checking health:', error)
    throw error
  }
}

export default apiClient
