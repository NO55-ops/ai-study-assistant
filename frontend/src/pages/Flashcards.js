import React, { useState, useEffect } from 'react';
import { flashcardService } from '../services/api';
import { Layers, ArrowLeft, ArrowRight, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

const Flashcards = () => {
  const [flashcardSets, setFlashcardSets] = useState([]);
  const [selectedSet, setSelectedSet] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFlashcards = async () => {
      try {
        const { data } = await flashcardService.list();
        setFlashcardSets(data);
        if (data.length > 0) {
          setSelectedSet(data[0]);
        }
      } catch (e) {
        toast.error('Failed to load flashcards');
      } finally {
        setLoading(false);
      }
    };
    fetchFlashcards();
  }, []);

  const currentCard = selectedSet?.flashcards[currentIndex];

  const nextCard = () => {
    if (currentIndex < selectedSet.flashcards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setFlipped(false);
    }
  };

  const prevCard = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setFlipped(false);
    }
  };

  const shuffle = () => {
    if (selectedSet) {
      const shuffled = [...selectedSet.flashcards].sort(() => Math.random() - 0.5);
      setSelectedSet({ ...selectedSet, flashcards: shuffled });
      setCurrentIndex(0);
      setFlipped(false);
      toast.success('Flashcards shuffled!');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: 'var(--bg-main)' }}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#FF5722] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-[#0A0A0A] font-semibold">Loading flashcards...</p>
        </div>
      </div>
    );
  }

  if (flashcardSets.length === 0) {
    return (
      <div className="min-h-screen noise-overlay flex items-center justify-center" style={{ background: 'var(--bg-main)' }}>
        <div className="text-center">
          <Layers className="w-24 h-24 text-[#0A0A0A] mx-auto mb-6 opacity-20" strokeWidth={1.5} />
          <h2 className="text-3xl font-black text-[#0A0A0A] mb-4" style={{ fontFamily: 'Outfit, sans-serif' }}>
            No Flashcards Yet
          </h2>
          <p className="text-[#0A0A0A] mb-6">Generate flashcards from your documents to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#FFC857] rounded-2xl border-2 border-[#0A0A0A] neo-shadow mb-4">
            <Layers className="w-8 h-8 text-[#0A0A0A]" strokeWidth={2.5} />
          </div>
          <h1 className="text-5xl font-black text-[#0A0A0A] tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Flashcards
          </h1>
          <p className="text-lg text-[#0A0A0A]" style={{ fontFamily: 'DM Sans, sans-serif' }}>
            Review and master key concepts
          </p>
        </div>

        {flashcardSets.length > 1 && (
          <div className="mb-6">
            <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">Select Set</label>
            <select
              value={selectedSet?.id || ''}
              onChange={(e) => {
                const set = flashcardSets.find((s) => s.id === e.target.value);
                setSelectedSet(set);
                setCurrentIndex(0);
                setFlipped(false);
              }}
              className="input-field"
              data-testid="select-flashcard-set"
            >
              {flashcardSets.map((set, idx) => (
                <option key={set.id} value={set.id}>
                  Set {idx + 1} - {set.document_id}
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedSet && currentCard && (
          <>
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="badge badge-butter">
                  {currentIndex + 1} / {selectedSet.flashcards.length}
                </span>
                <span className="text-sm font-semibold text-[#0A0A0A]">
                  Progress: {Math.round(((currentIndex + 1) / selectedSet.flashcards.length) * 100)}%
                </span>
              </div>
              <button
                onClick={shuffle}
                className="btn-secondary py-2 px-4 text-sm flex items-center gap-2"
                data-testid="shuffle-btn"
              >
                <RefreshCw className="w-4 h-4" strokeWidth={2.5} />
                Shuffle
              </button>
            </div>

            <div
              onClick={() => setFlipped(!flipped)}
              className="card cursor-pointer min-h-[400px] flex items-center justify-center transition-all hover:-translate-y-2"
              data-testid="flashcard"
              style={{ perspective: '1000px' }}
            >
              <div className="text-center px-8">
                <div className="mb-6">
                  <span className="badge">{flipped ? 'ANSWER' : 'QUESTION'}</span>
                </div>
                <p
                  className="text-3xl font-bold text-[#0A0A0A]"
                  style={{ fontFamily: 'Outfit, sans-serif' }}
                >
                  {flipped ? currentCard.back : currentCard.front}
                </p>
                {!flipped && currentCard.hint && (
                  <p className="text-sm text-[#0A0A0A] mt-6 opacity-60">
                    Hint: {currentCard.hint}
                  </p>
                )}
                <p className="text-sm text-[#0A0A0A] mt-8 opacity-40">
                  Click to flip
                </p>
              </div>
            </div>

            <div className="flex gap-4 mt-6">
              <button
                onClick={prevCard}
                disabled={currentIndex === 0}
                className="btn-secondary flex-1 py-3 flex items-center justify-center gap-2 disabled:opacity-30"
                data-testid="prev-card-btn"
              >
                <ArrowLeft className="w-5 h-5" strokeWidth={2.5} />
                Previous
              </button>
              <button
                onClick={nextCard}
                disabled={currentIndex === selectedSet.flashcards.length - 1}
                className="btn-primary flex-1 py-3 flex items-center justify-center gap-2 disabled:opacity-30"
                data-testid="next-card-btn"
              >
                Next
                <ArrowRight className="w-5 h-5" strokeWidth={2.5} />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Flashcards;
