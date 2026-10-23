import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, BookOpen, CheckCircle2, Lightbulb, Brain, NotebookPen } from 'lucide-react';
import { libraryService } from '../services/api';

const LibraryTopic = () => {
  const { qualificationSlug, subjectSlug, topicSlug } = useParams();
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTopic = async () => {
      try {
        const { data } = await libraryService.getTopic(qualificationSlug, subjectSlug, topicSlug);
        setPayload(data || null);
      } catch (error) {
        setPayload(null);
      } finally {
        setLoading(false);
      }
    };

    fetchTopic();
  }, [qualificationSlug, subjectSlug, topicSlug]);

  if (loading) {
    return <div className="min-h-screen" style={{ background: 'var(--bg-main)' }}><div className="mx-auto max-w-6xl px-4 py-10 text-center text-[#0A0A0A]">Loading topic...</div></div>;
  }

  if (!payload || !payload.topic) {
    return <div className="min-h-screen" style={{ background: 'var(--bg-main)' }}><div className="mx-auto max-w-6xl px-4 py-10 text-center text-[#0A0A0A]">Topic not found.</div></div>;
  }

  const { qualification, subject, topic } = payload;

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-main)' }}>
      <div className="mx-auto max-w-6xl px-4 py-10 md:px-8">
        <div className="mb-6 flex items-center gap-3">
          <Link to={`/library/${qualificationSlug}/${subjectSlug}`} className="inline-flex items-center gap-2 rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] px-3 py-2 font-semibold text-[#0A0A0A]">
            <ArrowLeft className="h-4 w-4" strokeWidth={2.5} />
            Back to subject
          </Link>
        </div>

        <div className="mb-8 rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6 shadow-[6px_6px_0px_rgba(0,0,0,0.9)]">
          <div className="mb-3 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border-2 border-[#0A0A0A] bg-[#FF865E]">
              <BookOpen className="h-6 w-6 text-[#0A0A0A]" strokeWidth={2.5} />
            </div>
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-[#0A0A0A]">{qualification.name}</p>
              <h1 className="text-3xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>{topic.title}</h1>
            </div>
          </div>
          <p className="text-base text-[#0A0A0A]">{topic.summary}</p>
          <p className="mt-4 rounded-2xl border-2 border-dashed border-[#0A0A0A] bg-[#FFF5E6] p-3 text-sm text-[#0A0A0A]">
            <strong>Note:</strong> This is a sample catalog entry. Confirm the exact syllabus version before labeling it as fully syllabus-aligned.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6">
            <div className="mb-4 flex items-center gap-2">
              <NotebookPen className="h-5 w-5 text-[#0A0A0A]" strokeWidth={2.5} />
              <h2 className="text-xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>Notes</h2>
            </div>
            {(topic.notes || []).map((section, index) => (
              <div key={`${section.heading}-${index}`} className="mb-5">
                <h3 className="mb-2 text-base font-black uppercase tracking-[0.12em] text-[#0A0A0A]">{section.heading}</h3>
                <ul className="space-y-2 text-sm text-[#0A0A0A]">
                  {(section.content || []).map((line, idx) => (
                    <li key={`${section.heading}-${idx}`} className="flex gap-2">
                      <span className="mt-1 h-2 w-2 rounded-full bg-[#FF5722]" />
                      <span>{line}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6">
            <div className="mb-4 flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-[#0A0A0A]" strokeWidth={2.5} />
              <h2 className="text-xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>Formulas & key facts</h2>
            </div>
            <ul className="space-y-2 text-sm text-[#0A0A0A]">
              {(topic.formulae || []).map((formula, idx) => (
                <li key={`${formula}-${idx}`} className="rounded-2xl border-2 border-[#0A0A0A] bg-[#FFF5E6] p-3">{formula}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6">
            <div className="mb-4 flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-[#0A0A0A]" strokeWidth={2.5} />
              <h2 className="text-xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>Worked examples</h2>
            </div>
            {(topic.worked_examples || []).map((example, idx) => (
              <div key={`${example.question}-${idx}`} className="mb-5 rounded-2xl border-2 border-[#0A0A0A] bg-[#F4F8FF] p-4">
                <p className="mb-2 font-bold text-[#0A0A0A]">{example.question}</p>
                <ol className="list-decimal space-y-2 pl-5 text-sm text-[#0A0A0A]">
                  {(example.steps || []).map((step, stepIndex) => (
                    <li key={`${example.question}-${stepIndex}`}>{step}</li>
                  ))}
                </ol>
                <p className="mt-3 text-sm font-bold text-[#0A0A0A]">Answer: {example.answer}</p>
              </div>
            ))}
          </div>

          <div className="rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6">
            <div className="mb-4 flex items-center gap-2">
              <Brain className="h-5 w-5 text-[#0A0A0A]" strokeWidth={2.5} />
              <h2 className="text-xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>Exam tips & common mistakes</h2>
            </div>
            <div className="space-y-4 text-sm text-[#0A0A0A]">
              <div className="rounded-2xl border-2 border-[#0A0A0A] bg-[#F4F8FF] p-4">
                <p className="mb-2 font-black uppercase tracking-[0.12em] text-[#0A0A0A]">Exam tips</p>
                <ul className="space-y-2">
                  {(topic.exam_tips || []).map((tip, idx) => <li key={`tip-${idx}`}>• {tip}</li>)}
                </ul>
              </div>
              <div className="rounded-2xl border-2 border-[#0A0A0A] bg-[#FFF5E6] p-4">
                <p className="mb-2 font-black uppercase tracking-[0.12em] text-[#0A0A0A]">Common mistakes</p>
                <ul className="space-y-2">
                  {(topic.common_mistakes || []).map((mistake, idx) => <li key={`mistake-${idx}`}>• {mistake}</li>)}
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6">
          <div className="mb-4 flex items-center gap-2">
            <Brain className="h-5 w-5 text-[#0A0A0A]" strokeWidth={2.5} />
            <h2 className="text-xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>Flashcards</h2>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            {(topic.flashcards || []).map((card, idx) => (
              <div key={`${card.front}-${idx}`} className="rounded-2xl border-2 border-[#0A0A0A] bg-[#F4F8FF] p-4">
                <p className="mb-2 text-xs font-black uppercase tracking-[0.12em] text-[#0A0A0A]">Front</p>
                <p className="font-semibold text-[#0A0A0A]">{card.front}</p>
                <p className="mt-3 text-xs font-black uppercase tracking-[0.12em] text-[#0A0A0A]">Back</p>
                <p className="text-sm text-[#0A0A0A]">{card.back}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 rounded-3xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-6">
          <div className="mb-4 flex items-center gap-2">
            <NotebookPen className="h-5 w-5 text-[#0A0A0A]" strokeWidth={2.5} />
            <h2 className="text-xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>Practice questions</h2>
          </div>
          <div className="space-y-4">
            {(topic.practice_questions || []).map((item, idx) => (
              <div key={`${item.question}-${idx}`} className="rounded-2xl border-2 border-[#0A0A0A] bg-[#FFF5E6] p-4">
                <p className="font-bold text-[#0A0A0A]">{idx + 1}. {item.question}</p>
                <ul className="mt-2 space-y-2 text-sm text-[#0A0A0A]">
                  {(item.options || []).map((option, optionIndex) => (
                    <li key={`${item.question}-${optionIndex}`}>• {option}</li>
                  ))}
                </ul>
                <p className="mt-2 font-bold text-[#0A0A0A]">Answer: {item.answer}</p>
                <p className="mt-2 text-sm text-[#0A0A0A]">{item.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LibraryTopic;
