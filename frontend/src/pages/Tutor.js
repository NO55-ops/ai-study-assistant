import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { documentService } from '../services/api';
import { Brain, Send } from 'lucide-react';
import { toast } from 'sonner';

const Tutor = () => {
  const [searchParams] = useSearchParams();
  const docId = searchParams.get('doc');
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(docId || '');
  const [difficultyMode, setDifficultyMode] = useState('intermediate');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [sessionId] = useState(() => Math.random().toString(36).substring(7));

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const { data } = await documentService.list();
        setDocuments(data);
        if (docId && data.find((d) => d.id === docId)) {
          setSelectedDoc(docId);
        } else if (data.length > 0) {
          setSelectedDoc(data[0].id);
        }
      } catch (e) {
        toast.error('Failed to load documents');
      }
    };
    fetchDocs();
  }, [docId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleAsk = async () => {
    if (!question.trim() || !selectedDoc) {
      toast.error('Please enter a question and select a document');
      return;
    }

    const userMessage = { id: `u-${Date.now()}`, role: 'user', content: question };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion('');
    setLoading(true);

    const aiMessage = { id: `a-${Date.now()}`, role: 'assistant', content: '' };
    setMessages((prev) => [...prev, aiMessage]);

    try {
      const API = process.env.REACT_APP_BACKEND_URL + '/api';
      const response = await fetch(`${API}/ai/tutor`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          document_id: selectedDoc,
          question: userMessage.content,
          difficulty_mode: difficultyMode,
          session_id: sessionId,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6));
            if (data.content) {
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastMsg = newMessages[newMessages.length - 1];
                if (lastMsg.role === 'assistant') {
                  lastMsg.content += data.content;
                }
                return newMessages;
              });
            }
          }
        }
      }
    } catch (e) {
      toast.error('Failed to get response from tutor');
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const difficultyModes = [
    { value: 'beginner', label: 'Beginner', color: '#A2D2FF' },
    { value: 'intermediate', label: 'Intermediate', color: '#CDB4DB' },
    { value: 'advanced', label: 'Advanced', color: '#FF865E' },
    { value: 'exam_prep', label: 'Exam Prep', color: '#FFC857' },
  ];

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="max-w-5xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#FF5722] rounded-2xl border-2 border-[#0A0A0A] neo-shadow mb-4">
            <Brain className="w-8 h-8 text-[#FDFBF7]" strokeWidth={2.5} />
          </div>
          <h1 className="text-5xl font-black text-[#0A0A0A] tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            AI Tutor
          </h1>
          <p className="text-lg text-[#0A0A0A]" style={{ fontFamily: 'DM Sans, sans-serif' }}>
            Get personalized help with your study materials
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-bold text-[#0A0A0A] mb-2 uppercase tracking-wide">Document</label>
            <select
              value={selectedDoc}
              onChange={(e) => setSelectedDoc(e.target.value)}
              className="input-field"
              data-testid="select-document"
            >
              <option value="">Select a document</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.original_filename}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-bold text-[#0A0A0A] mb-2 uppercase tracking-wide">Difficulty Mode</label>
            <div className="flex gap-2">
              {difficultyModes.map((mode) => (
                <button
                  key={mode.value}
                  onClick={() => setDifficultyMode(mode.value)}
                  data-testid={`mode-${mode.value}-btn`}
                  className={`flex-1 py-2 px-3 rounded-xl border-2 border-[#0A0A0A] font-semibold text-xs transition-all ${
                    difficultyMode === mode.value
                      ? 'neo-shadow text-[#0A0A0A]'
                      : 'bg-white text-[#0A0A0A] hover:-translate-y-1'
                  }`}
                  style={difficultyMode === mode.value ? { background: mode.color } : {}}
                >
                  {mode.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="card mb-6" style={{ minHeight: '400px', maxHeight: '500px', overflowY: 'auto' }} data-testid="chat-container">
          {messages.length === 0 ? (
            <div className="text-center py-16">
              <Brain className="w-20 h-20 text-[#0A0A0A] mx-auto mb-4 opacity-20" strokeWidth={1.5} />
              <h3 className="text-xl font-black text-[#0A0A0A] mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
                Ask me anything!
              </h3>
              <p className="text-[#0A0A0A]">I'm here to help you understand your study material</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, idx) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  data-testid={`message-${idx}`}
                >
                  <div
                    className={`max-w-[80%] p-4 rounded-2xl border-2 border-[#0A0A0A] ${
                      msg.role === 'user'
                        ? 'bg-[#FF5722] text-[#FDFBF7] neo-shadow'
                        : 'bg-white text-[#0A0A0A]'
                    }`}
                  >
                    <p className="whitespace-pre-wrap" style={{ fontFamily: 'DM Sans, sans-serif' }}>
                      {msg.content}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !loading && handleAsk()}
            placeholder="Ask a question about your document..."
            className="input-field flex-1"
            disabled={loading}
            data-testid="question-input"
          />
          <button
            onClick={handleAsk}
            disabled={loading || !selectedDoc}
            className="btn-primary px-6"
            data-testid="send-question-btn"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-[#FDFBF7] border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Send className="w-5 h-5" strokeWidth={2.5} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Tutor;
