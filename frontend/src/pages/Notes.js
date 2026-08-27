import React, { useEffect, useState, useCallback } from 'react';
import { notesService } from '../services/api';
import { NotebookPen, Plus, Pin, Trash2, Search, X, Save, PinOff } from 'lucide-react';
import { toast } from 'sonner';

const COLOR_OPTIONS = [
  { key: 'butter', value: '#FFC857', name: 'Butter' },
  { key: 'mint', value: '#A2D2FF', name: 'Sky' },
  { key: 'lavender', value: '#CDB4DB', name: 'Lavender' },
  { key: 'peach', value: '#FF865E', name: 'Peach' },
  { key: 'orange', value: '#FF5722', name: 'Sunset' },
];

const getColorValue = (key) => COLOR_OPTIONS.find((c) => c.key === key)?.value || '#FFC857';

const emptyNote = { title: '', content: '', tags: [], color: 'butter', is_pinned: false };

const Notes = () => {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [search, setSearch] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchNotes = useCallback(async () => {
    try {
      const { data } = await notesService.list();
      setNotes(data);
    } catch (e) {
      toast.error('Failed to load notes');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  const openNewNote = () => {
    setEditingNote({ ...emptyNote });
    setEditorOpen(true);
  };

  const openEditNote = (note) => {
    setEditingNote({ ...note });
    setEditorOpen(true);
  };

  const closeEditor = () => {
    setEditorOpen(false);
    setEditingNote(null);
  };

  const saveNote = async () => {
    if (!editingNote.title.trim()) {
      toast.error('Please add a title');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        title: editingNote.title,
        content: editingNote.content,
        tags: editingNote.tags || [],
        color: editingNote.color,
        is_pinned: editingNote.is_pinned || false,
      };
      if (editingNote.id) {
        await notesService.update(editingNote.id, payload);
        toast.success('Note updated');
      } else {
        await notesService.create(payload);
        toast.success('Note created');
      }
      await fetchNotes();
      closeEditor();
    } catch (e) {
      toast.error('Failed to save note');
    } finally {
      setSaving(false);
    }
  };

  const togglePin = async (note, e) => {
    e.stopPropagation();
    try {
      await notesService.update(note.id, { ...note, is_pinned: !note.is_pinned });
      await fetchNotes();
    } catch (err) {
      toast.error('Failed to update pin');
    }
  };

  const deleteNote = async (note, e) => {
    e.stopPropagation();
    if (!window.confirm(`Delete "${note.title}"?`)) return;
    try {
      await notesService.delete(note.id);
      toast.success('Note deleted');
      await fetchNotes();
    } catch (err) {
      toast.error('Failed to delete note');
    }
  };

  const filteredNotes = notes.filter(
    (n) =>
      !search ||
      n.title.toLowerCase().includes(search.toLowerCase()) ||
      n.content.toLowerCase().includes(search.toLowerCase())
  );

  const pinnedNotes = filteredNotes.filter((n) => n.is_pinned);
  const regularNotes = filteredNotes.filter((n) => !n.is_pinned);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: 'var(--bg-main)' }}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto" style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }}></div>
          <p className="mt-4 font-semibold" style={{ color: 'var(--text-main)' }}>Loading notes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl border-2 neo-shadow mb-4"
              style={{ background: 'var(--accent)', borderColor: 'var(--border-main)' }}>
              <NotebookPen className="w-8 h-8" style={{ color: '#FDFBF7' }} strokeWidth={2.5} />
            </div>
            <h1 className="text-5xl font-black tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-main)' }}>
              My Notes
            </h1>
            <p className="text-lg" style={{ fontFamily: 'DM Sans, sans-serif', color: 'var(--text-main)' }}>
              {notes.length} {notes.length === 1 ? 'note' : 'notes'} · Capture ideas, key concepts, and study reminders
            </p>
          </div>
          <button onClick={openNewNote} className="btn-primary flex items-center gap-2" data-testid="new-note-btn">
            <Plus className="w-5 h-5" strokeWidth={2.5} />
            New Note
          </button>
        </div>

        <div className="mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: 'var(--text-main)' }} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search notes..."
              className="input-field"
              style={{ paddingLeft: '3rem' }}
              data-testid="notes-search-input"
            />
          </div>
        </div>

        {notes.length === 0 ? (
          <div className="card text-center py-16" data-testid="empty-notes-state">
            <NotebookPen className="w-24 h-24 mx-auto mb-6 opacity-20" strokeWidth={1.5} style={{ color: 'var(--text-main)' }} />
            <h2 className="text-2xl font-black mb-2" style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-main)' }}>
              Your notebook is empty
            </h2>
            <p className="mb-6" style={{ color: 'var(--text-main)' }}>Start capturing your study insights</p>
            <button onClick={openNewNote} className="btn-primary inline-flex items-center gap-2">
              <Plus className="w-5 h-5" strokeWidth={2.5} />
              Create your first note
            </button>
          </div>
        ) : (
          <>
            {pinnedNotes.length > 0 && (
              <>
                <div className="flex items-center gap-2 mb-4">
                  <Pin className="w-4 h-4" style={{ color: 'var(--text-main)' }} strokeWidth={2.5} />
                  <span className="text-xs uppercase tracking-wider font-bold" style={{ color: 'var(--text-main)' }}>Pinned</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
                  {pinnedNotes.map((note, idx) => (
                    <NoteCard key={note.id} note={note} idx={idx} onOpen={openEditNote} onPin={togglePin} onDelete={deleteNote} />
                  ))}
                </div>
              </>
            )}

            {regularNotes.length > 0 && (
              <>
                {pinnedNotes.length > 0 && (
                  <div className="flex items-center gap-2 mb-4">
                    <NotebookPen className="w-4 h-4" style={{ color: 'var(--text-main)' }} strokeWidth={2.5} />
                    <span className="text-xs uppercase tracking-wider font-bold" style={{ color: 'var(--text-main)' }}>All Notes</span>
                  </div>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {regularNotes.map((note, idx) => (
                    <NoteCard key={note.id} note={note} idx={idx} onOpen={openEditNote} onPin={togglePin} onDelete={deleteNote} />
                  ))}
                </div>
              </>
            )}

            {filteredNotes.length === 0 && (
              <div className="card text-center py-12">
                <p style={{ color: 'var(--text-main)' }}>No notes match "{search}"</p>
              </div>
            )}
          </>
        )}
      </div>

      {editorOpen && editingNote && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.5)' }}
          onClick={closeEditor}
          data-testid="note-editor-overlay"
        >
          <div
            className="w-full max-w-2xl rounded-2xl border-2 neo-shadow-lg"
            style={{
              background: getColorValue(editingNote.color),
              borderColor: 'var(--border-main)',
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
            data-testid="note-editor"
          >
            <div className="p-6 space-y-4">
              <div className="flex items-start justify-between gap-4">
                <input
                  type="text"
                  value={editingNote.title}
                  onChange={(e) => setEditingNote({ ...editingNote, title: e.target.value })}
                  placeholder="Note title..."
                  className="flex-1 text-2xl font-black bg-transparent border-0 outline-none"
                  style={{ fontFamily: 'Outfit, sans-serif', color: '#0A0A0A' }}
                  data-testid="note-title-input"
                  autoFocus
                />
                <button
                  onClick={closeEditor}
                  className="p-2 rounded-lg border-2"
                  style={{ background: '#FDFBF7', borderColor: '#0A0A0A' }}
                  data-testid="close-editor-btn"
                >
                  <X className="w-5 h-5" style={{ color: '#0A0A0A' }} strokeWidth={2.5} />
                </button>
              </div>

              <textarea
                value={editingNote.content}
                onChange={(e) => setEditingNote({ ...editingNote, content: e.target.value })}
                placeholder="Start writing your thoughts, key concepts, formulas..."
                className="w-full bg-transparent border-0 outline-none resize-none"
                style={{ color: '#0A0A0A', minHeight: '300px', fontFamily: 'DM Sans, sans-serif' }}
                data-testid="note-content-input"
              />

              <div className="flex items-center justify-between pt-4 border-t-2" style={{ borderColor: '#0A0A0A' }}>
                <div className="flex items-center gap-2">
                  {COLOR_OPTIONS.map((c) => (
                    <button
                      key={c.key}
                      onClick={() => setEditingNote({ ...editingNote, color: c.key })}
                      data-testid={`color-${c.key}-btn`}
                      className="w-8 h-8 rounded-full border-2 transition-all"
                      style={{
                        background: c.value,
                        borderColor: '#0A0A0A',
                        transform: editingNote.color === c.key ? 'scale(1.2)' : 'scale(1)',
                        boxShadow: editingNote.color === c.key ? '2px 2px 0px #0A0A0A' : 'none',
                      }}
                      title={c.name}
                    />
                  ))}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setEditingNote({ ...editingNote, is_pinned: !editingNote.is_pinned })}
                    className="p-2 rounded-lg border-2 transition-all"
                    style={{
                      background: editingNote.is_pinned ? '#0A0A0A' : '#FDFBF7',
                      color: editingNote.is_pinned ? '#FDFBF7' : '#0A0A0A',
                      borderColor: '#0A0A0A',
                    }}
                    data-testid="editor-pin-btn"
                  >
                    {editingNote.is_pinned ? <PinOff className="w-4 h-4" strokeWidth={2.5} /> : <Pin className="w-4 h-4" strokeWidth={2.5} />}
                  </button>
                  <button
                    onClick={saveNote}
                    disabled={saving}
                    className="flex items-center gap-2 py-2 px-4 rounded-full border-2 font-semibold"
                    style={{ background: '#0A0A0A', color: '#FDFBF7', borderColor: '#0A0A0A' }}
                    data-testid="save-note-btn"
                  >
                    <Save className="w-4 h-4" strokeWidth={2.5} />
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const NoteCard = ({ note, idx, onOpen, onPin, onDelete }) => {
  return (
    <div
      onClick={() => onOpen(note)}
      className="rounded-2xl border-2 p-5 cursor-pointer transition-all hover:-translate-y-1 flex flex-col animate-fade-up"
      style={{
        background: getColorValue(note.color),
        borderColor: '#0A0A0A',
        boxShadow: '4px 4px 0px #0A0A0A',
        color: '#0A0A0A',
        minHeight: '220px',
        animationDelay: `${idx * 0.05}s`,
      }}
      onMouseEnter={(e) => (e.currentTarget.style.boxShadow = '6px 6px 0px #0A0A0A')}
      onMouseLeave={(e) => (e.currentTarget.style.boxShadow = '4px 4px 0px #0A0A0A')}
      data-testid={`note-card-${idx}`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-black text-lg leading-tight flex-1" style={{ fontFamily: 'Outfit, sans-serif' }}>
          {note.title}
        </h3>
        <button
          onClick={(e) => onPin(note, e)}
          className="p-1.5 rounded-lg border-2 transition-all"
          style={{
            background: note.is_pinned ? '#0A0A0A' : 'transparent',
            color: note.is_pinned ? '#FDFBF7' : '#0A0A0A',
            borderColor: '#0A0A0A',
          }}
          data-testid={`note-pin-${idx}-btn`}
          title={note.is_pinned ? 'Unpin' : 'Pin'}
        >
          <Pin className="w-3.5 h-3.5" strokeWidth={2.5} />
        </button>
      </div>
      <p className="text-sm flex-1 whitespace-pre-wrap break-words line-clamp-6" style={{ fontFamily: 'DM Sans, sans-serif' }}>
        {note.content || <span className="opacity-50">Empty note</span>}
      </p>
      <div className="flex items-center justify-between mt-3 pt-3 border-t-2" style={{ borderColor: '#0A0A0A' }}>
        <span className="text-xs opacity-70">
          {new Date(note.updated_at).toLocaleDateString()}
        </span>
        <button
          onClick={(e) => onDelete(note, e)}
          className="p-1.5 rounded-lg border-2"
          style={{ background: '#FDFBF7', borderColor: '#0A0A0A', color: '#0A0A0A' }}
          data-testid={`note-delete-${idx}-btn`}
        >
          <Trash2 className="w-3.5 h-3.5" strokeWidth={2.5} />
        </button>
      </div>
    </div>
  );
};

export default Notes;
