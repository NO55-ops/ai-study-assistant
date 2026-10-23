import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, BookOpen, ArrowRight } from 'lucide-react';
import { libraryService } from '../services/api';

const LibrarySubject = () => {
  const { qualificationSlug, subjectSlug } = useParams();
  const [subject, setSubject] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSubject = async () => {
      try {
        const { data } = await libraryService.getSubject(qualificationSlug, subjectSlug);
        setSubject(data || null);
      } catch (error) {
        setSubject(null);
      } finally {
        setLoading(false);
      }
    };

    fetchSubject();
  }, [qualificationSlug, subjectSlug]);

  if (loading) {
    return <div className="min-h-screen" style={{ background: 'var(--bg-main)' }}><div className="mx-auto max-w-6xl px-4 py-10 text-center text-[#0A0A0A]">Loading subject...</div></div>;
  }

  if (!subject) {
    return <div className="min-h-screen" style={{ background: 'var(--bg-main)' }}><div className="mx-auto max-w-6xl px-4 py-10 text-center text-[#0A0A0A]">Subject not found.</div></div>;
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-main)' }}>
      <div className="mx-auto max-w-6xl px-4 py-10 md:px-8">
        <div className="mb-6 flex items-center gap-3">
          <Link to={`/library/${qualificationSlug}`} className="inline-flex items-center gap-2 rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] px-3 py-2 font-semibold text-[#0A0A0A]">
            <ArrowLeft className="h-4 w-4" strokeWidth={2.5} />
            Back to qualification
          </Link>
        </div>

        <div className="mb-8 rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6 shadow-[6px_6px_0px_rgba(0,0,0,0.9)]">
          <div className="mb-3 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border-2 border-[#0A0A0A] bg-[#CDB4DB]">
              <BookOpen className="h-6 w-6 text-[#0A0A0A]" strokeWidth={2.5} />
            </div>
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-[#0A0A0A]">Subject</p>
              <h1 className="text-3xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>{subject.name}</h1>
            </div>
          </div>
          <p className="text-base text-[#0A0A0A]">{subject.description || 'Published study topics are listed below.'}</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {(subject.topics || []).map((topic) => (
            <Link
              key={topic.id}
              to={`/library/${qualificationSlug}/${subject.slug}/${topic.slug}`}
              className="group rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6 transition-transform hover:-translate-y-1 hover:shadow-[6px_6px_0px_rgba(0,0,0,0.9)]"
            >
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-[#0A0A0A]">Topic</p>
                  <h2 className="text-xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>{topic.title}</h2>
                </div>
                <ArrowRight className="h-5 w-5 text-[#0A0A0A] transition-transform group-hover:translate-x-1" strokeWidth={2.5} />
              </div>
              <p className="text-sm text-[#0A0A0A] opacity-80">{topic.summary || 'Open this topic to review detailed study notes and examples.'}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LibrarySubject;
