import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, ArrowRight, GraduationCap } from 'lucide-react';
import { libraryService } from '../services/api';

const Library = () => {
  const [qualifications, setQualifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchQualifications = async () => {
      try {
        const { data } = await libraryService.listQualifications();
        setQualifications(data || []);
      } catch (error) {
        setQualifications([]);
      } finally {
        setLoading(false);
      }
    };

    fetchQualifications();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen" style={{ background: 'var(--bg-main)' }}>
        <div className="mx-auto max-w-6xl px-4 py-10">
          <div className="text-center text-[#0A0A0A] font-semibold">Loading Library...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-main)' }}>
      <div className="mx-auto max-w-6xl px-4 py-10 md:px-8">
        <div className="mb-8 rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6 shadow-[6px_6px_0px_rgba(0,0,0,0.9)]">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border-2 border-[#0A0A0A] bg-[#A2D2FF]">
              <BookOpen className="h-6 w-6 text-[#0A0A0A]" strokeWidth={2.5} />
            </div>
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-[#0A0A0A]">Study AI</p>
              <h1 className="text-3xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>Library</h1>
            </div>
          </div>
          <p className="max-w-2xl text-base text-[#0A0A0A]">
            Explore published, curriculum-aligned study content. Start with a qualification and work through subjects and topics in a clear learning path.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {qualifications.map((qualification) => (
            <Link
              key={qualification.id}
              to={`/library/${qualification.slug}`}
              className="group rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6 transition-transform hover:-translate-y-1 hover:shadow-[6px_6px_0px_rgba(0,0,0,0.9)]"
            >
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl border-2 border-[#0A0A0A] bg-[#FFD166]">
                    <GraduationCap className="h-5 w-5 text-[#0A0A0A]" strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="text-xs font-black uppercase tracking-[0.18em] text-[#0A0A0A]">Qualification</p>
                    <h2 className="text-2xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
                      {qualification.name}
                    </h2>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 text-[#0A0A0A] transition-transform group-hover:translate-x-1" strokeWidth={2.5} />
              </div>

              <p className="mb-4 text-sm text-[#0A0A0A] opacity-80">{qualification.description || 'Browse published study content.'}</p>

              <div className="flex items-center justify-between text-sm font-semibold text-[#0A0A0A]">
                <span>{(qualification.subjects || []).length} subjects</span>
                <span>Open</span>
              </div>
            </Link>
          ))}
        </div>

        {qualifications.length === 0 && (
          <div className="mt-8 rounded-3xl border-2 border-dashed border-[#0A0A0A] bg-[#FDFBF7] p-8 text-center text-[#0A0A0A]">
            No published catalog entries are available yet.
          </div>
        )}
      </div>
    </div>
  );
};

export default Library;
