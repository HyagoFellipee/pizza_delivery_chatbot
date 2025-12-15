/**
 * ChatMessage component - Displays a single chat message
 */
import { Message } from '../types/chat'

interface ChatMessageProps {
  message: Message
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-xs lg:max-w-md xl:max-w-lg px-4 py-2 rounded-lg ${
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-gray-200 text-gray-800'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        {message.timestamp && (
          <p className="text-xs mt-1 opacity-70">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>
    </div>
  )
}
