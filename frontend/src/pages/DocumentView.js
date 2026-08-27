import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { documentService, aiService } from '../services/api';
import { FileText, Brain, HelpCircle, Layers, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const DocumentView = () => {
  const { id } = useParams();
  const [document, setDocument] = useState(null);
  const [summaryType, setSummaryType] = useState('detailed');
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        const { data } = await documentService.get(id);
        setDocument(data);
      } catch (e) {
        toast.error('Failed to load document');
      } finally {
        setLoading(false);
      }
    };
    fetchDocument();
  }, [id]);

  const generateSummary = async (type) => {
    setLoadingSummary(true);
    setSummaryType(type);
    try {
      const { data } = await aiService.generateSummary(id, type);
      setSummary(data);
      toast.success('Summary generated!');
    } catch (e) {
      toast.error('Failed to generate summary');
    } finally {
      setLoadingSummary(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: 'var(--bg-main)' }}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#FF5722] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-[#0A0A0A] font-semibold">Loading document...</p>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-main)' }}>
        <div className="text-center">
          <h2 className="text-2xl font-black text-[#0A0A0A]">Document not found</h2>
          <Link to="/documents" className="btn-primary mt-4 inline-block">
            Back to Documents
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="max-w-6xl mx-auto px-4 py-12">
        <div className="mb-8">
          <Link to="/documents" className="text-sm font-semibold text-[#FF5722] underline mb-4 inline-block">
            ← Back to Documents
          </Link>
          <h1 className="text-5xl font-black text-[#0A0A0A] tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            {document.original_filename}
          </h1>
          <p className="text-lg text-[#0A0A0A]" style={{ fontFamily: 'DM Sans, sans-serif' }}>
            Uploaded {new Date(document.created_at).toLocaleDateString()}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Link
            to={`/tutor?doc=${id}`}
            className="card text-center hover:-translate-y-2 transition-all cursor-pointer"
            data-testid="ask-tutor-btn"
          >
            <Brain className="w-12 h-12 text-[#FF5722] mx-auto mb-3" strokeWidth={2.5} />
            <h3 className="font-bold text-[#0A0A0A] mb-1">Ask AI Tutor</h3>
            <p className="text-sm text-[#0A0A0A]">Get personalized help</p>
          </Link>

          <Link
            to={`/quiz?doc=${id}`}
            className="card text-center hover:-translate-y-2 transition-all cursor-pointer"
            data-testid="generate-quiz-btn"
          >
            <HelpCircle className="w-12 h-12 text-[#A2D2FF] mx-auto mb-3" strokeWidth={2.5} />
            <h3 className="font-bold text-[#0A0A0A] mb-1">Generate Quiz</h3>
            <p className="text-sm text-[#0A0A0A]">Test your knowledge</p>
          </Link>

          <button
            onClick={() => {
              aiService.generateFlashcards(id).then(() => {
                toast.success('Flashcards generated!');
              }).catch(() => toast.error('Failed to generate flashcards'));
            }}
            className="card text-center hover:-translate-y-2 transition-all cursor-pointer"
            data-testid="generate-flashcards-btn"
          >
            <Layers className="w-12 h-12 text-[#CDB4DB] mx-auto mb-3" strokeWidth={2.5} />
            <h3 className="font-bold text-[#0A0A0A] mb-1">Create Flashcards</h3>
            <p className="text-sm text-[#0A0A0A]">Review key concepts</p>
          </button>
        </div>

        <div className="card" data-testid="summary-section">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-3xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
              AI Summary
            </h2>
            <Sparkles className="w-8 h-8 text-[#FFC857]" strokeWidth={2.5} />
          </div>

          <div className="flex flex-wrap gap-3 mb-6">
            {['short', 'detailed', 'bullet_points', 'timeline'].map((type) => (
              <button
                key={type}
                onClick={() => generateSummary(type)}
                disabled={loadingSummary}
                className={`py-2 px-4 rounded-xl border-2 border-[#0A0A0A] font-semibold transition-all ${
                  summaryType === type && summary
                    ? 'bg-[#FF5722] text-[#FDFBF7] neo-shadow'
                    : 'bg-white text-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow'
                }`}
                data-testid={`summary-type-${type}-btn`}
              >
                {type.replace('_', ' ').toUpperCase()}
              </button>
            ))}
          </div>

          {loadingSummary && (
            <div className="text-center py-12">
              <div className="w-12 h-12 border-4 border-[#FF5722] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-[#0A0A0A] font-semibold">Generating summary...</p>
            </div>
          )}

          {summary && !loadingSummary && (
            <div className="bg-[#FDFBF7] rounded-xl border-2 border-[#0A0A0A] p-6" data-testid="summary-content">
              <div className="prose prose-lg max-w-none" style={{ fontFamily: 'DM Sans, sans-serif' }}>
                <div className="whitespace-pre-wrap text-[#0A0A0A]">{summary.content}</div>
              </div>
            </div>
          )}

          {!summary && !loadingSummary && (
            <div className="text-center py-12 bg-[#FDFBF7] rounded-xl border-2 border-[#0A0A0A]" data-testid="no-summary-state">
              <FileText className="w-16 h-16 text-[#0A0A0A] mx-auto mb-4 opacity-20" />
              <p className="text-[#0A0A0A]">Select a summary type above to get started</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentView;
