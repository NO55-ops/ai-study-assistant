import React, { useEffect, useMemo, useState } from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { BookOpen, CheckCircle2, Eye, Save, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { libraryService } from '../services/api';

const slugify = (value) =>
  String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'untitled';

const defaultResource = {
  slug: '',
  title: 'New resource',
  resource_type: 'notes',
  status: 'draft',
  payload: { content: '<p>Start writing study content here.</p>' },
};

const emptySelection = {
  qualificationSlug: '',
  subjectSlug: '',
  topicSlug: '',
  resourceSlug: '',
};

const LibraryAdminEditor = () => {
  const { user } = useAuth();
  const [catalog, setCatalog] = useState({ qualifications: [] });
  const [selection, setSelection] = useState(emptySelection);
  const [resourceForm, setResourceForm] = useState(defaultResource);
  const [editorHtml, setEditorHtml] = useState('<p>Start writing study content here.</p>');
  const [status, setStatus] = useState({ type: 'idle', message: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        const { data } = await libraryService.getAdminCatalog();
        const qualifications = Array.isArray(data?.qualifications) ? data.qualifications : [];
        setCatalog({ qualifications });
        if (qualifications[0]) {
          const firstQualification = qualifications[0];
          const firstSubject = firstQualification.subjects?.[0];
          const firstTopic = firstSubject?.topics?.[0];
          setSelection({
            qualificationSlug: firstQualification.slug,
            subjectSlug: firstSubject?.slug || '',
            topicSlug: firstTopic?.slug || '',
            resourceSlug: firstTopic?.resources?.[0]?.slug || '',
          });
          if (firstTopic?.resources?.[0]) {
            const firstResource = firstTopic.resources[0];
            setResourceForm({
              slug: firstResource.slug,
              title: firstResource.title,
              resource_type: firstResource.resource_type,
              status: firstResource.status,
              payload: firstResource.payload || { content: '<p>...</p>' },
            });
            setEditorHtml(firstResource.payload?.content || firstResource.payload?.notes?.[0]?.content?.[0] || '<p>...</p>');
          }
        }
      } catch (error) {
        setStatus({ type: 'error', message: 'Unable to load the Library catalog.' });
      } finally {
        setLoading(false);
      }
    };

    fetchCatalog();
  }, []);

  const qualification = useMemo(
    () => catalog.qualifications.find((item) => item.slug === selection.qualificationSlug) || catalog.qualifications[0] || null,
    [catalog, selection.qualificationSlug]
  );

  const subject = useMemo(
    () => qualification?.subjects?.find((item) => item.slug === selection.subjectSlug) || qualification?.subjects?.[0] || null,
    [qualification, selection.subjectSlug]
  );

  const topic = useMemo(
    () => subject?.topics?.find((item) => item.slug === selection.topicSlug) || subject?.topics?.[0] || null,
    [subject, selection.topicSlug]
  );

  const selectedResource = useMemo(
    () => topic?.resources?.find((item) => item.slug === selection.resourceSlug) || topic?.resources?.[0] || null,
    [topic, selection.resourceSlug]
  );

  useEffect(() => {
    if (!selectedResource) {
      const defaultContent = '<p>Start writing study content here.</p>';
      setResourceForm({ ...defaultResource, slug: '', title: 'New resource', payload: { content: defaultContent } });
      setEditorHtml(defaultContent);
      return;
    }

    const payload = selectedResource.payload || { content: '<p>Start writing study content here.</p>' };
    const content =
      typeof payload.content === 'string'
        ? payload.content
        : Array.isArray(payload.notes) && payload.notes[0]?.content?.[0]
          ? payload.notes[0].content[0]
          : '<p>Start writing study content here.</p>';

    setResourceForm({
      slug: selectedResource.slug,
      title: selectedResource.title,
      resource_type: selectedResource.resource_type,
      status: selectedResource.status,
      payload,
    });
    setEditorHtml(content);
  }, [selectedResource]);

  const onSelectQualification = (slug) => {
    const nextQualification = catalog.qualifications.find((item) => item.slug === slug);
    const nextSubject = nextQualification?.subjects?.[0];
    const nextTopic = nextSubject?.topics?.[0];
    setSelection({
      qualificationSlug: slug,
      subjectSlug: nextSubject?.slug || '',
      topicSlug: nextTopic?.slug || '',
      resourceSlug: nextTopic?.resources?.[0]?.slug || '',
    });
  };

  const onSelectSubject = (slug) => {
    const nextSubject = qualification?.subjects?.find((item) => item.slug === slug);
    const nextTopic = nextSubject?.topics?.[0];
    setSelection({
      qualificationSlug: qualification?.slug || '',
      subjectSlug: slug,
      topicSlug: nextTopic?.slug || '',
      resourceSlug: nextTopic?.resources?.[0]?.slug || '',
    });
  };

  const onSelectTopic = (slug) => {
    const nextTopic = subject?.topics?.find((item) => item.slug === slug);
    setSelection({
      qualificationSlug: qualification?.slug || '',
      subjectSlug: subject?.slug || '',
      topicSlug: slug,
      resourceSlug: nextTopic?.resources?.[0]?.slug || '',
    });
  };

  const handleSave = async () => {
    if (!selection.qualificationSlug || !selection.subjectSlug || !selection.topicSlug) {
      setStatus({ type: 'error', message: 'Select a qualification, subject, and topic before saving.' });
      return;
    }

    const nextResource = {
      slug: resourceForm.slug || slugify(resourceForm.title),
      topic_slug: selection.topicSlug,
      title: resourceForm.title || 'Untitled resource',
      resource_type: resourceForm.resource_type,
      status: resourceForm.status,
      payload: {
        content: editorHtml,
      },
    };

    try {
      const response = await libraryService.saveResource(nextResource);
      setStatus({ type: 'success', message: response.data?.status === 'updated' ? 'Resource updated.' : 'Resource saved.' });
      const refreshed = await libraryService.getAdminCatalog();
      setCatalog({ qualifications: refreshed.data?.qualifications || [] });
    } catch (error) {
      const detail = error.response?.data?.detail || error.message || 'Save failed.';
      setStatus({ type: 'error', message: String(detail) });
    }
  };

  if (user && String(user.role || '').toLowerCase() !== 'admin') {
    return (
      <div className="min-h-screen bg-[var(--bg-main)] px-4 py-10 text-[#0A0A0A]">
        <div className="mx-auto max-w-4xl rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-8 text-center shadow-[6px_6px_0px_rgba(0,0,0,0.9)]">
          <ShieldCheck className="mx-auto mb-3 h-8 w-8" />
          <h1 className="text-3xl font-black">Admin access required</h1>
          <p className="mt-4">Only authenticated admins can edit shared Library content.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-main)] px-4 py-10 text-[#0A0A0A]">
        <div className="mx-auto max-w-6xl rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-8 text-center shadow-[6px_6px_0px_rgba(0,0,0,0.9)]">
          Loading Library editor...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-main)] px-4 py-10 text-[#0A0A0A]">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6 shadow-[6px_6px_0px_rgba(0,0,0,0.9)]">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border-2 border-[#0A0A0A] bg-[#A2D2FF]">
              <BookOpen className="h-6 w-6" strokeWidth={2.5} />
            </div>
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em]">Admin</p>
              <h1 className="text-3xl font-black">Library content editor</h1>
            </div>
          </div>
          <p className="max-w-2xl text-sm opacity-80">
            Create and edit shared study resource content without affecting personal student notes.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
          <aside className="rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-4 shadow-[6px_6px_0px_rgba(0,0,0,0.9)]">
            <div className="mb-4">
              <label className="mb-2 block text-xs font-black uppercase tracking-[0.12em]">Qualification</label>
              <select
                value={selection.qualificationSlug}
                onChange={(event) => onSelectQualification(event.target.value)}
                className="w-full rounded-xl border-2 border-[#0A0A0A] bg-white px-3 py-2"
              >
                {catalog.qualifications.map((item) => (
                  <option key={item.slug} value={item.slug}>{item.name}</option>
                ))}
              </select>
            </div>

            <div className="mb-4">
              <label className="mb-2 block text-xs font-black uppercase tracking-[0.12em]">Subject</label>
              <select
                value={selection.subjectSlug}
                onChange={(event) => onSelectSubject(event.target.value)}
                className="w-full rounded-xl border-2 border-[#0A0A0A] bg-white px-3 py-2"
              >
                {(qualification?.subjects || []).map((item) => (
                  <option key={item.slug} value={item.slug}>{item.name}</option>
                ))}
              </select>
            </div>

            <div className="mb-4">
              <label className="mb-2 block text-xs font-black uppercase tracking-[0.12em]">Topic</label>
              <select
                value={selection.topicSlug}
                onChange={(event) => onSelectTopic(event.target.value)}
                className="w-full rounded-xl border-2 border-[#0A0A0A] bg-white px-3 py-2"
              >
                {(subject?.topics || []).map((item) => (
                  <option key={item.slug} value={item.slug}>{item.title}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-2 block text-xs font-black uppercase tracking-[0.12em]">Resource</label>
              <select
                value={selection.resourceSlug}
                onChange={(event) => setSelection((prev) => ({ ...prev, resourceSlug: event.target.value }))}
                className="w-full rounded-xl border-2 border-[#0A0A0A] bg-white px-3 py-2"
              >
                {(topic?.resources || []).map((item) => (
                  <option key={item.slug} value={item.slug}>{item.title}</option>
                ))}
              </select>
            </div>
          </aside>

          <div className="space-y-6 rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6 shadow-[6px_6px_0px_rgba(0,0,0,0.9)]">
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <label className="mb-2 block text-xs font-black uppercase tracking-[0.12em]">Title</label>
                <input
                  value={resourceForm.title}
                  onChange={(event) => setResourceForm((prev) => ({ ...prev, title: event.target.value }))}
                  className="w-full rounded-xl border-2 border-[#0A0A0A] bg-white px-3 py-2"
                />
              </div>
              <div>
                <label className="mb-2 block text-xs font-black uppercase tracking-[0.12em]">Slug</label>
                <input
                  value={resourceForm.slug}
                  onChange={(event) => setResourceForm((prev) => ({ ...prev, slug: event.target.value }))}
                  className="w-full rounded-xl border-2 border-[#0A0A0A] bg-white px-3 py-2"
                />
              </div>
              <div>
                <label className="mb-2 block text-xs font-black uppercase tracking-[0.12em]">Status</label>
                <select
                  value={resourceForm.status}
                  onChange={(event) => setResourceForm((prev) => ({ ...prev, status: event.target.value }))}
                  className="w-full rounded-xl border-2 border-[#0A0A0A] bg-white px-3 py-2"
                >
                  <option value="draft">Draft</option>
                  <option value="published">Published</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-black uppercase tracking-[0.12em]">Resource type</label>
              <select
                value={resourceForm.resource_type}
                onChange={(event) => setResourceForm((prev) => ({ ...prev, resource_type: event.target.value }))}
                className="w-full rounded-xl border-2 border-[#0A0A0A] bg-white px-3 py-2 md:max-w-xs"
              >
                <option value="summary">Summary</option>
                <option value="notes">Notes</option>
                <option value="formulae">Formulae</option>
                <option value="worked_examples">Worked examples</option>
                <option value="exam_tips">Exam tips</option>
                <option value="common_mistakes">Common mistakes</option>
                <option value="flashcards">Flashcards</option>
                <option value="practice_questions">Practice questions</option>
              </select>
            </div>

            <div className="rounded-2xl border-2 border-[#0A0A0A] bg-white p-3">
              <ReactQuill theme="snow" value={editorHtml} onChange={setEditorHtml} />
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={handleSave}
                className="inline-flex items-center gap-2 rounded-xl border-2 border-[#0A0A0A] bg-[#FFD166] px-4 py-2 font-bold"
              >
                <Save className="h-4 w-4" />
                Save resource
              </button>
              <button
                type="button"
                onClick={() => setStatus({ type: 'info', message: 'Preview is powered by the same HTML editor content.' })}
                className="inline-flex items-center gap-2 rounded-xl border-2 border-[#0A0A0A] bg-[#F4F8FF] px-4 py-2 font-bold"
              >
                <Eye className="h-4 w-4" />
                Preview
              </button>
            </div>

            {status.message && (
              <div
                className={`rounded-2xl border-2 p-3 text-sm ${
                  status.type === 'error'
                    ? 'border-red-700 bg-red-50 text-red-700'
                    : status.type === 'success'
                      ? 'border-green-700 bg-green-50 text-green-700'
                      : 'border-[#0A0A0A] bg-[#FFF5E6] text-[#0A0A0A]'
                }`}
              >
                {status.message}
              </div>
            )}

            <div className="rounded-2xl border-2 border-dashed border-[#0A0A0A] bg-[#FFF5E6] p-4 text-sm">
              <div className="mb-2 flex items-center gap-2 font-black uppercase tracking-[0.12em]">
                <CheckCircle2 className="h-4 w-4" />
                Preview
              </div>
              <div dangerouslySetInnerHTML={{ __html: editorHtml }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LibraryAdminEditor;
