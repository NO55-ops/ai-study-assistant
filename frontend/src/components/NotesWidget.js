import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { notesService } from '../services/api';
import { NotebookPen, Plus, X, Pin, Trash2, ExternalLink, Save, ChevronLeft } from 'lucide-react';
import { toast } from 'sonner';

const COLOR_OPTIONS = [
  { key: 'butter', value: '#FFC857' },
  { key: 'mint', value: '#A2D2FF' },
  { key: 'lavender', value: '#CDB4DB' },
  { key: 'peach', value: '#FF865E' },
  { key: 'orange', value: '#FF5722' },
];

const getColorValue = (key) => COLOR_OPTIONS.find((c) => c.key === key)?.value || '#FFC857';

const NotesWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [expandedNoteId, setExpandedNoteId] = useState(null);
  const [editForm, setEditForm] = useState(null);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newColor, setNewColor] = useState('butter');
  const location = useLocation();
  const navigate = useNavigate();
  const panelRef = useRef(null);

  // Hide widget on auth pages
  const hiddenPaths = ['/login', '/onboarding'];
  const shouldHide = hiddenPaths.includes(location.pathname);

  const fetchNotes = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await notesService.list();
      setNotes(data);
    } catch (e) {
      console.error('Failed to fetch notes:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchNotes();
    }
  }, [isOpen, fetchNotes]);

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape' && isOpen) setIsOpen(false);
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen]);

  if (shouldHide) return null;

  const startCreate = () => {
    setCreating(true);
    setNewTitle('');
    setNewContent('');
    setNewColor('butter');
  };

  const cancelCreate = () => {
    setCreating(false);
    setNewTitle('');
    setNewContent('');
  };

  const saveNewNote = async () => {
    if (!newTitle.trim()) {
      toast.error('Add a title');
      return;
    }
    try {
      const docId = location.pathname.startsWith('/documents/')
        ? location.pathname.split('/documents/')[1]
        : null;
      await notesService.create({
        title: newTitle,
        content: newContent,
        color: newColor,
        tags: [],
        is_pinned: false,
        document_id: docId,
      });
      toast.success('Note saved');
      setCreating(false);
      setNewTitle('');
      setNewContent('');
      fetchNotes();
    } catch (e) {
      toast.error('Failed to save');
    }
  };

  const startEdit = (note) => {
    setExpandedNoteId(note.id);
    setEditForm({ ...note });
  };

  const saveEdit = async () => {
    if (!editForm.title.trim()) {
      toast.error('Add a title');
      return;
    }
    try {
      await notesService.update(editForm.id, {
        title: editForm.title,
        content: editForm.content,
        color: editForm.color,
        tags: editForm.tags || [],
        is_pinned: editForm.is_pinned || false,
        document_id: editForm.document_id,
      });
      toast.success('Note updated');
      setExpandedNoteId(null);
      setEditForm(null);
      fetchNotes();
    } catch (e) {
      toast.error('Failed to update');
    }
  };

  const togglePin = async (note, e) => {
    e.stopPropagation();
    try {
      await notesService.update(note.id, { ...note, is_pinned: !note.is_pinned });
      fetchNotes();
    } catch (err) {
      toast.error('Failed to pin');
    }
  };

  const deleteNote = async (note, e) => {
    e.stopPropagation();
    if (!window.confirm(`Delete "${note.title}"?`)) return;
    try {
      await notesService.delete(note.id);
      toast.success('Deleted');
      if (expandedNoteId === note.id) {
        setExpandedNoteId(null);
        setEditForm(null);
      }
      fetchNotes();
    } catch (err) {
      toast.error('Failed to delete');
    }
  };

  return (
    <>
      {/* Floating trigger button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          data-testid="notes-widget-trigger"
          className="fixed z-40 right-6 bottom-24 md:bottom-8 flex items-center justify-center rounded-full border-2 transition-all"
          style={{
            width: '60px',
            height: '60px',
            background: 'var(--accent)',
            color: '#FDFBF7',
            borderColor: 'var(--border-main)',
            boxShadow: '4px 4px 0px var(--shadow-color)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '6px 6px 0px var(--shadow-color)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '4px 4px 0px var(--shadow-color)';
          }}
          title="Open Notes (Ctrl+N)"
        >
          <NotebookPen className="w-6 h-6" strokeWidth={2.5} />
          {notes.length > 0 && (
            <span
              className="absolute -top-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border-2"
              style={{ background: '#FFC857', color: '#0A0A0A', borderColor: 'var(--border-main)' }}
            >
              {notes.length > 99 ? '99+' : notes.length}
            </span>
          )}
        </button>
      )}

      {/* Slide-in panel */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            style={{ background: 'rgba(0,0,0,0.3)' }}
            onClick={() => setIsOpen(false)}
            data-testid="notes-widget-backdrop"
          />
          <div
            ref={panelRef}
            data-testid="notes-widget-panel"
            className="fixed z-50 right-0 top-0 h-full flex flex-col animate-slide-in"
            style={{
              width: '100%',
              maxWidth: '420px',
              background: 'var(--bg-main)',
              borderLeft: '2px solid var(--border-main)',
              boxShadow: '-4px 0px 0px var(--shadow-color)',
            }}
          >
            {/* Header */}
            <div
              className="flex items-center justify-between p-4 border-b-2 shrink-0"
              style={{ borderColor: 'var(--border-main)', background: 'var(--bg-surface)' }}
            >
              <div className="flex items-center gap-2">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center border-2"
                  style={{ background: 'var(--accent)', borderColor: 'var(--border-main)' }}
                >
                  <NotebookPen className="w-5 h-5" style={{ color: '#FDFBF7' }} strokeWidth={2.5} />
                </div>
                <div>
                  <h2 className="text-lg font-black leading-tight" style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-main)' }}>
                    Quick Notes
                  </h2>
                  <p className="text-xs opacity-70" style={{ color: 'var(--text-main)' }}>
                    {notes.length} {notes.length === 1 ? 'note' : 'notes'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setIsOpen(false);
                    navigate('/notes');
                  }}
                  className="p-2 rounded-lg border-2"
                  style={{ background: 'var(--bg-surface)', color: 'var(--text-main)', borderColor: 'var(--border-main)' }}
                  data-testid="notes-widget-fullview-btn"
                  title="Full library"
                >
                  <ExternalLink className="w-4 h-4" strokeWidth={2.5} />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 rounded-lg border-2"
                  style={{ background: 'var(--bg-surface)', color: 'var(--text-main)', borderColor: 'var(--border-main)' }}
                  data-testid="notes-widget-close-btn"
                  title="Close (Esc)"
                >
                  <X className="w-4 h-4" strokeWidth={2.5} />
                </button>
              </div>
            </div>

            {/* Scrollable content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {/* New note card */}
              {creating ? (
                <div
                  className="rounded-2xl border-2 p-4 space-y-3"
                  style={{ background: getColorValue(newColor), borderColor: '#0A0A0A', boxShadow: '4px 4px 0px #0A0A0A' }}
                  data-testid="notes-widget-create-card"
                >
                  <input
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="Note title..."
                    className="w-full bg-transparent border-0 outline-none font-black text-lg"
                    style={{ fontFamily: 'Outfit, sans-serif', color: '#0A0A0A' }}
                    autoFocus
                    data-testid="notes-widget-new-title-input"
                  />
                  <textarea
                    value={newContent}
                    onChange={(e) => setNewContent(e.target.value)}
                    placeholder="Write your thoughts here..."
                    className="w-full bg-transparent border-0 outline-none resize-none text-sm"
                    style={{ color: '#0A0A0A', minHeight: '100px', fontFamily: 'DM Sans, sans-serif' }}
                    data-testid="notes-widget-new-content-input"
                  />
                  <div className="flex items-center justify-between pt-2 border-t-2" style={{ borderColor: '#0A0A0A' }}>
                    <div className="flex items-center gap-1.5">
                      {COLOR_OPTIONS.map((c) => (
                        <button
                          key={c.key}
                          onClick={() => setNewColor(c.key)}
                          className="w-6 h-6 rounded-full border-2 transition-all"
                          style={{
                            background: c.value,
                            borderColor: '#0A0A0A',
                            transform: newColor === c.key ? 'scale(1.25)' : 'scale(1)',
                          }}
                          data-testid={`notes-widget-color-${c.key}-btn`}
                        />
                      ))}
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={cancelCreate}
                        className="p-1.5 rounded-lg border-2"
                        style={{ background: '#FDFBF7', color: '#0A0A0A', borderColor: '#0A0A0A' }}
                        data-testid="notes-widget-cancel-btn"
                      >
                        <X className="w-3.5 h-3.5" strokeWidth={2.5} />
                      </button>
                      <button
                        onClick={saveNewNote}
                        className="flex items-center gap-1.5 py-1.5 px-3 rounded-full border-2 font-semibold text-sm"
                        style={{ background: '#0A0A0A', color: '#FDFBF7', borderColor: '#0A0A0A' }}
                        data-testid="notes-widget-save-new-btn"
                      >
                        <Save className="w-3.5 h-3.5" strokeWidth={2.5} />
                        Save
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <button
                  onClick={startCreate}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl border-2 border-dashed font-semibold transition-all hover:-translate-y-0.5"
                  style={{ background: 'var(--bg-surface)', color: 'var(--text-main)', borderColor: 'var(--border-main)' }}
                  data-testid="notes-widget-new-btn"
                >
                  <Plus className="w-4 h-4" strokeWidth={2.5} />
                  New Note
                </button>
              )}

              {loading && !creating && (
                <div className="text-center py-8">
                  <div className="w-8 h-8 border-4 border-t-transparent rounded-full animate-spin mx-auto" style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }}></div>
                </div>
              )}

              {!loading && notes.length === 0 && !creating && (
                <div className="text-center py-8">
                  <NotebookPen className="w-12 h-12 mx-auto mb-3 opacity-20" strokeWidth={1.5} style={{ color: 'var(--text-main)' }} />
                  <p className="text-sm" style={{ color: 'var(--text-main)' }}>No notes yet</p>
                  <p className="text-xs opacity-60 mt-1" style={{ color: 'var(--text-main)' }}>Click "New Note" to start</p>
                </div>
              )}

              {notes.map((note, idx) => (
                <div
                  key={note.id}
                  data-testid={`notes-widget-item-${idx}`}
                  className="rounded-2xl border-2 transition-all"
                  style={{
                    background: getColorValue(note.color),
                    borderColor: '#0A0A0A',
                    boxShadow: '3px 3px 0px #0A0A0A',
                    color: '#0A0A0A',
                  }}
                >
                  {expandedNoteId === note.id && editForm ? (
                    <div className="p-4 space-y-3">
                      <input
                        type="text"
                        value={editForm.title}
                        onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                        className="w-full bg-transparent border-0 outline-none font-black"
                        style={{ fontFamily: 'Outfit, sans-serif', color: '#0A0A0A' }}
                        data-testid={`notes-widget-edit-title-${idx}`}
                      />
                      <textarea
                        value={editForm.content}
                        onChange={(e) => setEditForm({ ...editForm, content: e.target.value })}
                        className="w-full bg-transparent border-0 outline-none resize-none text-sm"
                        style={{ color: '#0A0A0A', minHeight: '80px', fontFamily: 'DM Sans, sans-serif' }}
                        data-testid={`notes-widget-edit-content-${idx}`}
                      />
                      <div className="flex items-center justify-between pt-2 border-t-2" style={{ borderColor: '#0A0A0A' }}>
                        <div className="flex items-center gap-1.5">
                          {COLOR_OPTIONS.map((c) => (
                            <button
                              key={c.key}
                              onClick={() => setEditForm({ ...editForm, color: c.key })}
                              className="w-5 h-5 rounded-full border-2 transition-all"
                              style={{
                                background: c.value,
                                borderColor: '#0A0A0A',
                                transform: editForm.color === c.key ? 'scale(1.3)' : 'scale(1)',
                              }}
                            />
                          ))}
                        </div>
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => {
                              setExpandedNoteId(null);
                              setEditForm(null);
                            }}
                            className="p-1.5 rounded-lg border-2"
                            style={{ background: '#FDFBF7', color: '#0A0A0A', borderColor: '#0A0A0A' }}
                            data-testid={`notes-widget-cancel-edit-${idx}`}
                          >
                            <X className="w-3 h-3" strokeWidth={2.5} />
                          </button>
                          <button
                            onClick={saveEdit}
                            className="flex items-center gap-1 py-1.5 px-2.5 rounded-full border-2 font-semibold text-xs"
                            style={{ background: '#0A0A0A', color: '#FDFBF7', borderColor: '#0A0A0A' }}
                            data-testid={`notes-widget-save-edit-${idx}`}
                          >
                            <Save className="w-3 h-3" strokeWidth={2.5} /> Save
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="p-4 cursor-pointer" onClick={() => startEdit(note)}>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h3 className="font-black text-base leading-tight flex-1" style={{ fontFamily: 'Outfit, sans-serif' }}>
                          {note.title}
                        </h3>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => togglePin(note, e)}
                            className="p-1 rounded border-2 transition-all"
                            style={{
                              background: note.is_pinned ? '#0A0A0A' : 'transparent',
                              color: note.is_pinned ? '#FDFBF7' : '#0A0A0A',
                              borderColor: '#0A0A0A',
                            }}
                            data-testid={`notes-widget-pin-${idx}`}
                          >
                            <Pin className="w-3 h-3" strokeWidth={2.5} />
                          </button>
                          <button
                            onClick={(e) => deleteNote(note, e)}
                            className="p-1 rounded border-2"
                            style={{ background: '#FDFBF7', color: '#0A0A0A', borderColor: '#0A0A0A' }}
                            data-testid={`notes-widget-delete-${idx}`}
                          >
                            <Trash2 className="w-3 h-3" strokeWidth={2.5} />
                          </button>
                        </div>
                      </div>
                      {note.content && (
                        <p className="text-xs whitespace-pre-wrap line-clamp-3" style={{ fontFamily: 'DM Sans, sans-serif' }}>
                          {note.content}
                        </p>
                      )}
                      <p className="text-[10px] opacity-60 mt-2">
                        {new Date(note.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </>
  );
};

export default NotesWidget;
