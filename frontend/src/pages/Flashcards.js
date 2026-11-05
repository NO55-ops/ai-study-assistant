import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { flashcardService, documentService } from '../services/api';
import { Layers, ArrowLeft, ArrowRight, RefreshCw, Plus, Trash2, NotebookPen } from 'lucide-react';
import { toast } from 'sonner';
import StudyWorkspace from '../components/StudyWorkspace';

const emptyCard = () => ({ front: '', back: '', hint: '' });

const Flashcards = () => {
  const navigate = useNavigate();

  const [flashcardSets, setFlashcardSets] = useState([]);
  const [selectedSet, setSelectedSet] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newDeck, setNewDeck] = useState({
    name: '',
    document_id: '',
    flashcards: [emptyCard()],
  });

  const fetchFlashcards = async () => {
    try {
      const [{ data: flashcardsData }, { data: documentsData }] = await Promise.all([
        flashcardService.list(),
        documentService.list(),
      ]);

      setDocuments(documentsData);
      setFlashcardSets(flashcardsData);
      if (flashcardsData.length > 0) {
        setSelectedSet(flashcardsData[0]);
        setCurrentIndex(0);
        setFlipped(false);
      } else {
        setSelectedSet(null);
      }
    } catch (e) {
      toast.error('Failed to load flashcards');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFlashcards();
  }, []);

  const currentCard = selectedSet?.flashcards?.[currentIndex] || null;
  const selectedDocument = documents.find((doc) => doc.id === selectedSet?.document_id) || null;

  const nextCard = () => {
    if (selectedSet && currentIndex < selectedSet.flashcards.length - 1) {
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

  const handleCreateDeck = async () => {
    const cards = newDeck.flashcards.filter((card) => card.front.trim() || card.back.trim() || card.hint.trim());
    if (!cards.length) {
      toast.error('Add at least one complete flashcard.');
      return;
    }

    try {
      const payload = {
        name: newDeck.name || 'Custom Study Deck',
        document_id: newDeck.document_id || null,
        document_name: documents.find((doc) => doc.id === newDeck.document_id)?.original_filename || 'Custom Study Deck',
        flashcards: cards.map((card) => ({
          front: card.front.trim(),
          back: card.back.trim(),
          hint: card.hint.trim(),
        })),
      };

      const { data } = await flashcardService.create(payload);
      setNewDeck({ name: '', document_id: '', flashcards: [emptyCard()] });
      setCreating(false);
      setFlashcardSets((prev) => [data, ...prev]);
      setSelectedSet(data);
      setCurrentIndex(0);
      setFlipped(false);
      toast.success('Flashcard deck created!');
    } catch (error) {
      toast.error(error?.response?.data?.detail || 'Could not create your flashcard deck.');
    }
  };

  const handleDeleteDeck = async (deckId) => {
    try {
      await flashcardService.remove(deckId);
      const nextSets = flashcardSets.filter((set) => set.id !== deckId);
      setFlashcardSets(nextSets);
      if (selectedSet?.id === deckId) {
        setSelectedSet(nextSets[0] || null);
        setCurrentIndex(0);
        setFlipped(false);
      }
      toast.success('Deck deleted.');
    } catch (error) {
      toast.error('Unable to delete deck.');
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

  if (flashcardSets.length === 0 && !creating) {
    return (
      <div className="min-h-screen noise-overlay flex items-center justify-center" style={{ background: 'var(--bg-main)' }}>
        <div className="text-center max-w-xl">
          <Layers className="w-24 h-24 text-[#0A0A0A] mx-auto mb-6 opacity-20" strokeWidth={1.5} />
          <h2 className="text-3xl font-black text-[#0A0A0A] mb-4" style={{ fontFamily: 'Outfit, sans-serif' }}>
            No Flashcards Yet
          </h2>
          <p className="text-[#0A0A0A] mb-8">Generate flashcards from a document or create a custom deck from scratch.</p>
          <button onClick={() => setCreating(true)} className="btn-primary px-6 py-3">
            Create Your First Deck
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <StudyWorkspace
        document={selectedDocument}
        title={selectedSet?.document_name || selectedDocument?.original_filename || 'Flashcards'}
        subtitle="Review key concepts while keeping the original material visible beside your study set."
      >
        <div className="study-workspace__section">
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

          <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
            <button
              onClick={() => setCreating((prev) => !prev)}
              className="btn-secondary py-2 px-4 text-sm flex items-center gap-2"
            >
              <NotebookPen className="w-4 h-4" strokeWidth={2.5} />
              {creating ? 'Hide Composer' : 'New Deck'}
            </button>
            {flashcardSets.length > 1 && (
              <div className="w-full md:w-72">
                <label className="block text-sm font-bold text-[#0A0A0A] mb-2 uppercase tracking-wide">Select Set</label>
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
                      {set.name || set.document_name || `Set ${idx + 1}`}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {creating && (
            <div className="mb-8 rounded-3xl border-2 border-dashed border-[#0A0A0A] bg-[#FFFDF8] p-6">
              <h3 className="text-2xl font-black text-[#0A0A0A] mb-4">Create custom flashcard deck</h3>
              <div className="grid gap-4 md:grid-cols-2">
                <input
                  value={newDeck.name}
                  onChange={(e) => setNewDeck((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="Deck name"
                  className="input-field"
                />
                <select
                  value={newDeck.document_id}
                  onChange={(e) => setNewDeck((prev) => ({ ...prev, document_id: e.target.value }))}
                  className="input-field"
                >
                  <option value="">No linked document</option>
                  {documents.map((doc) => (
                    <option key={doc.id} value={doc.id}>{doc.original_filename || doc.filename}</option>
                  ))}
                </select>
              </div>

              <div className="mt-5 space-y-4">
                {newDeck.flashcards.map((card, index) => (
                  <div key={index} className="grid gap-3 rounded-2xl border border-black/10 bg-white p-4 md:grid-cols-[1fr_1fr_auto]">
                    <input
                      value={card.front}
                      onChange={(e) => {
                        const cards = [...newDeck.flashcards];
                        cards[index].front = e.target.value;
                        setNewDeck((prev) => ({ ...prev, flashcards: cards }));
                      }}
                      placeholder="Front (term / question)"
                      className="input-field"
                    />
                    <input
                      value={card.back}
                      onChange={(e) => {
                        const cards = [...newDeck.flashcards];
                        cards[index].back = e.target.value;
                        setNewDeck((prev) => ({ ...prev, flashcards: cards }));
                      }}
                      placeholder="Back (answer / definition)"
                      className="input-field"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        if (newDeck.flashcards.length === 1) {
                          setNewDeck((prev) => ({ ...prev, flashcards: [emptyCard()] }));
                          return;
                        }
                        setNewDeck((prev) => ({
                          ...prev,
                          flashcards: prev.flashcards.filter((_, cardIndex) => cardIndex !== index),
                        }));
                      }}
                      className="btn-secondary px-3 py-2 text-sm"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <input
                      value={card.hint}
                      onChange={(e) => {
                        const cards = [...newDeck.flashcards];
                        cards[index].hint = e.target.value;
                        setNewDeck((prev) => ({ ...prev, flashcards: cards }));
                      }}
                      placeholder="Optional hint"
                      className="input-field md:col-span-3"
                    />
                  </div>
                ))}
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => setNewDeck((prev) => ({ ...prev, flashcards: [...prev.flashcards, emptyCard()] }))}
                  className="btn-secondary py-2 px-4 text-sm flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" strokeWidth={2.5} />
                  Add Card
                </button>
                <button onClick={handleCreateDeck} className="btn-primary py-2 px-4 text-sm">Save Deck</button>
              </div>
            </div>
          )}

          {selectedSet && currentCard && (
            <>
              <div className="mb-4 flex items-center justify-between gap-4">
                <div>
                  <h2
                    className="text-2xl font-black text-[#0A0A0A]"
                    style={{ fontFamily: 'Outfit, sans-serif' }}
                  >
                    {selectedSet.name || selectedSet.document_name || 'Untitled Deck'}
                  </h2>
                  <p className="text-sm text-gray-600">
                    {selectedSet.document_name ? 'Flashcards from this document' : 'Custom study deck'}
                  </p>
                </div>

                {selectedSet.document_id && (
                  <button
                    onClick={() => navigate(`/documents/${selectedSet.document_id}`)}
                    className="btn-secondary py-2 px-4 text-sm"
                  >
                    View Source Document
                  </button>
                )}
                <button
                  onClick={() => handleDeleteDeck(selectedSet.id)}
                  className="btn-secondary py-2 px-4 text-sm text-red-600 border-red-200"
                >
                  Delete Deck
                </button>
              </div>

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
      </StudyWorkspace>
    </div>
  );
};

export default Flashcards;
