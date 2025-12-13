/**
 * TypeScript type definitions for chat functionality
 */

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: Date
}

export interface CartItem {
  name: string
  price: number
  quantity?: number
}

export interface ChatRequest {
  message: string
  conversation_history: Message[]
}

export interface ChatResponse {
  response: string
  cart_items: CartItem[]
  total: number
}
