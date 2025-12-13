import { useState } from 'react'
import ChatContainer from './components/ChatContainer'
import './App.css'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary-700 mb-2">
            🍕 Pizza Delivery Chatbot
          </h1>
          <p className="text-gray-600">
            Order your favorite pizza through our AI assistant
          </p>
        </header>

        <ChatContainer />
      </div>
    </div>
  )
}

export default App
