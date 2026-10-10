import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Loader2, Info, AlertTriangle } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const Assistant = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState('research');
  const [message, setMessage] = useState('');
  const [history, setHistory] = useState([
    { type: 'assistant', text: 'Hello. I am the ClimateTwin AI Assistant. How can I help you understand the current digital twin state?' }
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const quickQuestions = {
    research: [
      "Why is flood risk high?",
      "What are the main prediction factors?",
      "How reliable is the forecast?",
      "What is the uncertainty range?"
    ],
    operator: [
      "Which hazard needs attention?",
      "What is the available lead time?",
      "Are sensors healthy?",
      "What action is recommended?"
    ],
    citizen: [
      "What is the current risk?",
      "What should I do?",
      "Why is the risk elevated?"
    ],
    evaluator: [
      "What datasets are used?",
      "How does the Digital Twin work?",
      "What is the model performance?",
      "What are the project limitations?"
    ]
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [history]);

  const handleSend = async (textToSend) => {
    const text = textToSend || message;
    if (!text.trim()) return;

    const userMessage = { type: 'user', text };
    setHistory((prev) => [...prev, userMessage]);
    setMessage('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/assistant/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, mode })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch response');
      }

      const data = await response.json();
      setHistory((prev) => [...prev, { 
        type: 'assistant', 
        text: data.answer,
        confidence: data.confidence
      }]);
    } catch (error) {
      console.error(error);
      setHistory((prev) => [...prev, { 
        type: 'assistant', 
        text: "Sorry, I couldn't connect to the backend service. Is the API running?" 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full p-4 shadow-xl z-50 transition-transform transform hover:scale-105 flex items-center justify-center"
      >
        {isOpen ? <X className="h-6 w-6" /> : <MessageSquare className="h-6 w-6" />}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 max-w-[90vw] h-[600px] max-h-[80vh] bg-slate-900 border border-slate-700 rounded-xl shadow-2xl flex flex-col z-50 overflow-hidden">
          
          {/* Header */}
          <div className="bg-slate-800 p-4 border-b border-slate-700 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-indigo-400" />
              <h3 className="font-bold text-white">Digital Twin AI Assistant</h3>
            </div>
            <button onClick={() => setHistory([])} className="text-xs text-slate-400 hover:text-white">Clear</button>
          </div>

          {/* Mode Selector */}
          <div className="flex bg-slate-800/50 border-b border-slate-700 text-xs">
            {['research', 'operator', 'citizen', 'evaluator'].map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 py-2 text-center capitalize transition-colors ${
                  mode === m ? 'bg-indigo-600 text-white font-medium' : 'text-slate-400 hover:bg-slate-700 hover:text-white'
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          {/* Disclaimer */}
          <div className={`p-2 text-xs border-b border-slate-700 flex items-start gap-2 ${
            mode === 'citizen' ? 'bg-rose-900/30 text-rose-300' : 'bg-slate-800/50 text-slate-400'
          }`}>
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <p>
              ClimateTwin AI Assistant provides data-grounded information from an academic prototype. It is not an official emergency-warning or evacuation system.
            </p>
          </div>

          {/* Chat History */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {history.map((msg, idx) => (
              <div key={idx} className={`flex flex-col ${msg.type === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`max-w-[85%] rounded-lg p-3 text-sm ${
                  msg.type === 'user' 
                    ? 'bg-indigo-600 text-white rounded-br-none' 
                    : 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700'
                }`}>
                  {msg.text}
                </div>
                {msg.type === 'assistant' && msg.confidence && (
                  <span className="text-[10px] text-slate-500 mt-1 ml-1 flex items-center gap-1">
                    <Info className="h-3 w-3" /> Grounded context: {msg.confidence}
                  </span>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex items-start">
                <div className="bg-slate-800 text-slate-400 rounded-lg rounded-bl-none p-3 border border-slate-700 flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
                  <span className="text-sm">Analyzing digital twin state...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions */}
          <div className="px-4 pb-2 flex overflow-x-auto gap-2 no-scrollbar">
            {quickQuestions[mode].map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                className="whitespace-nowrap text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-full border border-slate-700 transition"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Input Area */}
          <div className="p-4 bg-slate-800 border-t border-slate-700 flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder={`Ask as ${mode}...`}
              className="flex-1 bg-slate-900 border border-slate-700 text-sm text-white rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !message.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:hover:bg-indigo-600 text-white rounded-lg p-2 transition"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default Assistant;
