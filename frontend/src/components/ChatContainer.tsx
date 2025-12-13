/**
 * ChatContainer component - Main container for the chat interface
 */
import { useState, useEffect } from 'react'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import { Message, CartItem } from '../types/chat'
import { sendChatMessage } from '../services/api'

export default function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([])
  const [cartItems, setCartItems] = useState<CartItem[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(false)

  // Initial greeting
  useEffect(() => {
    const initialMessage: Message = {
      role: 'assistant',
      content: 'Hello! Welcome to our Pizza Delivery service! How can I help you today?',
      timestamp: new Date(),
    }
    setMessages([initialMessage])
  }, [])

  const handleSendMessage = async (content: string) => {
    // Add user message to UI
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      // Send to backend
      const response = await sendChatMessage({
        message: content,
        conversation_history: messages,
      })

      // Add assistant response
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])

      // Update cart
      setCartItems(response.cart_items)
      setTotal(response.total)
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-xl overflow-hidden">
      {/* Chat header */}
      <div className="bg-primary-600 text-white p-4">
        <h2 className="text-xl font-semibold">Chat with Pizza Bot</h2>
        {total > 0 && (
          <p className="text-sm mt-1">Cart Total: ${total.toFixed(2)}</p>
        )}
      </div>

      {/* Messages area */}
      <div className="h-96 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />

      {/* Cart summary */}
      {cartItems.length > 0 && (
        <div className="border-t p-4 bg-gray-50">
          <h3 className="font-semibold mb-2">Your Cart:</h3>
          <ul className="text-sm space-y-1">
            {cartItems.map((item, index) => (
              <li key={index} className="flex justify-between">
                <span>{item.name}</span>
                <span>${item.price.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
