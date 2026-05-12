import { useState, useRef, useEffect } from "react"
import "./App.css"

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMessage = input
    setInput("")
    setMessages(prev => [...prev, { role: "user", content: userMessage, tools: [] }])
    setLoading(true)

    try {
      const response = await fetch("http://localhost:8002/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage })
      })
      const data = await response.json()
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.response,
        tools: data.tools_used || []
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Something went wrong. Is the backend running?",
        tools: []
      }])
    } finally {
      setLoading(false)
    }
  }

  const clearHistory = async () => {
    await fetch("http://localhost:8002/history", { method: "DELETE" })
    setMessages([])
  }

  return (
    <div className="app">
      <div className="sidebar">
        <h2>AI Tool Agent</h2>
        <p className="sidebar-sub">An agent that can search the web, remember things, and interact with GitHub</p>
        <div className="tools-list">
          <p className="tools-label">Available tools</p>
          <div className="tool-badge">🔍 Web search</div>
          <div className="tool-badge">🧠 Memory</div>
          <div className="tool-badge">🐙 GitHub</div>
        </div>
        <button className="clear-btn" onClick={clearHistory}>
          Clear conversation
        </button>
      </div>

      <div className="chat">
        <div className="messages">
          {messages.length === 0 && (
            <div className="empty">
              <h3>What can I help you with?</h3>
              <div className="suggestions">
                <div className="suggestion">Search the web for AI engineering jobs</div>
                <div className="suggestion">What do you remember about me?</div>
                <div className="suggestion">Show me my GitHub repos</div>
                <div className="suggestion">Create a GitHub issue in my repo</div>
              </div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="bubble">
                {msg.content}
                {msg.tools && msg.tools.length > 0 && (
                  <div className="tools-used">
                    {msg.tools.map((t, j) => (
                      <span key={j} className="tool-tag">⚡ {t}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <div className="bubble typing">
                <span /><span /><span />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="input-area">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Ask anything..."
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading}>
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default App
