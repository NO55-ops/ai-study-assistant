import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { documentService, aiService } from '../services/api';
import { HelpCircle, Check, X, Clock3, ChevronLeft, ChevronRight, Flag, Send } from 'lucide-react';
import { toast } from 'sonner';
import StudyWorkspace from '../components/StudyWorkspace';

const STORAGE_PREFIX = 'mock_exam_answers_';
const HISTORY_KEY = 'mock_exam_history';

const readStoredAttempts = () => {
  try {
    const parsed = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    return [];
  }
};

const defaultConfig = {
  difficulty: 'mixed',
  question_types: ['multiple_choice', 'short_answer'],
  num_questions: 8,
  duration_minutes: 45,
  topic_selection: [],
};

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${String(mins).padStart(2, '0')}:${String(remainingSeconds).padStart(2, '0')}`;
};

const getTypeLabel = (type) => {
  switch (type) {
    case 'multiple_choice':
      return 'Multiple Choice';
    case 'short_answer':
      return 'Short Answer';
    case 'structured':
      return 'Structured';
    default:
      return type;
  }
};

const Quiz = () => {
  const [searchParams] = useSearchParams();
  const docId = searchParams.get('doc');
  const [documents, setDocuments] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState(docId ? [docId] : []);
  const [questionTypes, setQuestionTypes] = useState(['multiple_choice', 'short_answer']);
  const [difficulty, setDifficulty] = useState('mixed');
  const [numQuestions, setNumQuestions] = useState(8);
  const [durationMinutes, setDurationMinutes] = useState(45);
  const [topicInput, setTopicInput] = useState('');
  const [topicSelection, setTopicSelection] = useState([]);
  const [exam, setExam] = useState(null);
  const [answers, setAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [reviewQuestions, setReviewQuestions] = useState({});
  const [timeRemaining, setTimeRemaining] = useState(45 * 60);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [previousAttempts, setPreviousAttempts] = useState(readStoredAttempts);
  const submittingRef = useRef(false);

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const { data } = await documentService.list();
        setDocuments(data);
        if (docId && data.length > 0) {
          setSelectedDocs([docId]);
        }
      } catch (e) {
        toast.error('Failed to load documents');
      }
    };
    fetchDocs();
  }, [docId]);

  useEffect(() => {
    if (!loading) return undefined;
    const stages = [
      { label: 'Scanning the document', progress: 20 },
      { label: 'Selecting topics and difficulty', progress: 45 },
      { label: 'Creating exam questions', progress: 72 },
      { label: 'Preparing the exam interface', progress: 96 },
    ];

    const interval = setInterval(() => {
      setLoadingStep((prev) => (prev + 1) % stages.length);
    }, 700);

    return () => clearInterval(interval);
  }, [loading]);

  useEffect(() => {
    if (!exam || result) return undefined;
    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [exam, result]);

  useEffect(() => {
    if (!exam) return;
    const storageKey = `${STORAGE_PREFIX}${exam.id}`;
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setAnswers(parsed.answers || {});
        setReviewQuestions(parsed.reviewQuestions || {});
      } catch (error) {
        // Ignore invalid saved state.
      }
    }
  }, [exam]);

  const selectedDocument = documents.find((doc) => selectedDocs.includes(doc.id)) || null;
  const currentQuestion = exam?.questions?.[currentQuestionIndex] || null;

  const persistExamState = (nextAnswers, nextReview) => {
    if (!exam) return;
    const storageKey = `${STORAGE_PREFIX}${exam.id}`;
    localStorage.setItem(storageKey, JSON.stringify({
      answers: nextAnswers,
      reviewQuestions: nextReview,
    }));
  };

  const toggleDoc = (id) => {
    setSelectedDocs((prev) => (prev.includes(id) ? prev.filter((d) => d !== id) : [id]));
  };

  const toggleQuestionType = (type) => {
    setQuestionTypes((prev) => (prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]));
  };

  const addTopic = () => {
    const value = topicInput.trim();
    if (!value) return;
    setTopicSelection((prev) => (prev.includes(value) ? prev : [...prev, value]));
    setTopicInput('');
  };

  const removeTopic = (topic) => {
    setTopicSelection((prev) => prev.filter((item) => item !== topic));
  };

  const generateExam = async () => {
    if (!selectedDocs[0] || questionTypes.length === 0) {
      toast.error('Select a document and at least one question type.');
      return;
    }

    setLoading(true);
    setLoadingStep(0);
    try {
      const { data } = await aiService.generateMockExam({
        document_id: selectedDocs[0],
        topic_selection: topicSelection.length ? topicSelection : ['General'],
        difficulty,
        question_types: questionTypes,
        num_questions: numQuestions,
        duration_minutes: durationMinutes,
      });

      setExam(data);
      setAnswers({});
      setReviewQuestions({});
      setCurrentQuestionIndex(0);
      setTimeRemaining(data.duration_minutes * 60);
      setResult(null);
      setShowResults(false);
      toast.success('Mock exam created successfully.');
    } catch (error) {
      toast.error(error?.response?.data?.detail || 'Unable to generate the mock exam.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers((prev) => {
      const next = { ...prev, [questionId]: value };
      persistExamState(next, reviewQuestions);
      return next;
    });
  };

  const toggleReview = (questionId) => {
    setReviewQuestions((prev) => {
      const next = { ...prev, [questionId]: !prev[questionId] };
      persistExamState(answers, next);
      return next;
    });
  };

  const handleSubmit = useCallback(async (autoSubmit = false) => {
    if (!exam || submittingRef.current) return;
    if (!autoSubmit && !window.confirm('Submit this mock exam now?')) return;

    submittingRef.current = true;
    setSubmitting(true);
    try {
      const { data } = await aiService.submitMockExam({ exam_id: exam.id, answers });
      setResult(data);
      setShowResults(true);
      const history = [
        ...readStoredAttempts(),
        {
          exam_id: exam.id,
          percentage: data.percentage,
          total_marks: data.total_marks,
          max_marks: data.max_marks,
          created_at: new Date().toISOString(),
        },
      ].slice(-5);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
      setPreviousAttempts(history);
      localStorage.removeItem(`${STORAGE_PREFIX}${exam.id}`);
      toast.success(autoSubmit ? 'Time expired. Your exam has been submitted.' : `Submitted! You scored ${data.percentage}%`);
    } catch (error) {
      toast.error(error?.response?.data?.detail || 'Unable to submit the exam.');
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }, [exam, answers]);

  // Auto-submit once the timer hits zero. Declared after handleSubmit so the dependency is initialized.
  useEffect(() => {
    if (exam && timeRemaining === 0 && !result) {
      handleSubmit(true);
    }
  }, [timeRemaining, exam, result, handleSubmit]);

  const allTypes = ['multiple_choice', 'short_answer', 'structured'];
  const difficulties = ['easy', 'medium', 'hard', 'mixed'];
  const loadingStages = [
    { label: 'Scanning the document', progress: 20 },
    { label: 'Selecting topics and difficulty', progress: 45 },
    { label: 'Creating exam questions', progress: 72 },
    { label: 'Preparing the exam interface', progress: 96 },
  ];
  const currentStage = loadingStages[loadingStep] || loadingStages[0];
  const workspaceTitle = selectedDocument?.original_filename || 'Mock examination';

  if (loading) {
    return (
      <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
        <StudyWorkspace document={selectedDocument} title={workspaceTitle} subtitle="Building your exam in real time.">
          <div className="study-workspace__section">
            <div className="card" data-testid="mock-exam-loading-state">
              <div className="text-center mb-4">
                <div className="quiz-badge">AI POWERED</div>
              </div>
              <h2 className="text-3xl font-black text-[#0A0A0A] mb-3">Preparing your mock exam</h2>
              <p className="text-[#0A0A0A] mb-5">{currentStage.label}</p>
              <div className="h-3 rounded-full bg-white border-2 border-[#0A0A0A] overflow-hidden">
                <div className="h-full bg-[#FF5722]" style={{ width: `${currentStage.progress}%` }} />
              </div>
            </div>
          </div>
        </StudyWorkspace>
      </div>
    );
  }

  if (result) {
    return (
      <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
        <StudyWorkspace document={selectedDocument} title="Exam results" subtitle="Review your performance, feedback, and targeted revision plan.">
          <div className="study-workspace__section space-y-8">
            <div className="card p-6 rounded-3xl border-2 border-[#0A0A0A] bg-[#FFFDF8]">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <p className="text-sm font-bold uppercase tracking-wide">Summary</p>
                  <h2 className="text-4xl font-black text-[#0A0A0A]">{result.total_marks} / {result.max_marks}</h2>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold uppercase tracking-wide">Percentage</p>
                  <h3 className="text-3xl font-black text-[#0A0A0A]">{result.percentage}%</h3>
                </div>
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <div className="card p-5">
                <h3 className="text-2xl font-black text-[#0A0A0A] mb-4">Performance by topic</h3>
                {Object.entries(result.performance_by_topic || {}).map(([topic, item]) => (
                  <div key={topic} className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-[#0A0A0A]">{topic}</span>
                      <span className="text-sm text-[#0A0A0A]">{item.score} / {item.max}</span>
                    </div>
                    <div className="h-3 rounded-full bg-white border-2 border-[#0A0A0A] overflow-hidden">
                      <div className="h-full bg-[#A2D2FF]" style={{ width: `${item.percentage}%` }} />
                    </div>
                  </div>
                ))}
              </div>

              <div className="card p-5">
                <h3 className="text-2xl font-black text-[#0A0A0A] mb-4">Revision priorities</h3>
                <ul className="space-y-3">
                  {(result.recommendations || []).map((item, index) => (
                    <li key={index} className="flex gap-3 text-[#0A0A0A]">
                      <span className="mt-1 h-2.5 w-2.5 rounded-full bg-[#FF5722]" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="card p-5">
              <h3 className="text-2xl font-black text-[#0A0A0A] mb-4">Question-by-question feedback</h3>
              <div className="space-y-5">
                {result.question_results?.map((question, index) => (
                  <div key={question.id || index} className="rounded-2xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-bold text-[#0A0A0A]">Question {index + 1}</h4>
                      <span className="badge badge-butter">{question.awarded_marks} / {question.marks}</span>
                    </div>
                    <p className="text-[#0A0A0A] mb-2">{question.feedback}</p>
                    <p className="text-sm text-[#0A0A0A] mb-2"><strong>Model answer:</strong> {question.model_answer}</p>
                    {question.misconceptions?.length > 0 && (
                      <p className="text-sm text-[#0A0A0A] mb-2"><strong>Misconceptions:</strong> {question.misconceptions.join(' ')}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="card p-5">
              <h3 className="text-2xl font-black text-[#0A0A0A] mb-4">Previous attempts</h3>
              {previousAttempts.length > 0 ? (
                <div className="space-y-3">
                  {previousAttempts.slice(-3).reverse().map((attempt, index) => (
                    <div key={`${attempt.exam_id}-${index}`} className="flex items-center justify-between rounded-xl border-2 border-[#0A0A0A] bg-white p-3">
                      <span className="font-semibold text-[#0A0A0A]">Attempt {index + 1}</span>
                      <span className="text-[#0A0A0A]">{attempt.percentage}%</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[#0A0A0A]">No previous attempts yet. Your first attempt is now recorded.</p>
              )}
            </div>
          </div>
        </StudyWorkspace>
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
        <StudyWorkspace document={selectedDocument} title={workspaceTitle} subtitle="Create a realistic mock exam from your study material.">
          <div className="study-workspace__section">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-[#CDB4DB] rounded-2xl border-2 border-[#0A0A0A] neo-shadow mb-4">
                <HelpCircle className="w-8 h-8 text-[#0A0A0A]" strokeWidth={2.5} />
              </div>
              <h1 className="text-5xl font-black text-[#0A0A0A] tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
                Mock Examination
              </h1>
              <p className="text-lg text-[#0A0A0A]" style={{ fontFamily: 'DM Sans, sans-serif' }}>
                Build a timed exam with AI-marked feedback.
              </p>
            </div>

            <div className="card p-6">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">Select document</label>
                  <div className="grid gap-3 md:grid-cols-2">
                    {documents.map((doc) => (
                      <button
                        key={doc.id}
                        onClick={() => toggleDoc(doc.id)}
                        className={`p-4 rounded-xl border-2 border-[#0A0A0A] font-semibold text-left transition-all ${selectedDocs.includes(doc.id) ? 'bg-[#A2D2FF] neo-shadow' : 'bg-white'}`}
                      >
                        {doc.original_filename}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">Topic or chapter focus</label>
                  <div className="flex gap-3">
                    <input value={topicInput} onChange={(e) => setTopicInput(e.target.value)} placeholder="e.g. Photosynthesis, Cell structure" className="input-field flex-1" />
                    <button onClick={addTopic} className="btn-secondary px-4">Add</button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {topicSelection.length === 0 ? (
                      <span className="text-sm text-[#0A0A0A] opacity-70">No specific topics selected — the full document will be used.</span>
                    ) : (
                      topicSelection.map((topic) => (
                        <button key={topic} onClick={() => removeTopic(topic)} className="badge badge-butter cursor-pointer">
                          {topic} ×
                        </button>
                      ))
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">Question types</label>
                  <div className="grid gap-3 md:grid-cols-3">
                    {allTypes.map((type) => (
                      <button
                        key={type}
                        onClick={() => toggleQuestionType(type)}
                        className={`py-3 px-4 rounded-xl border-2 border-[#0A0A0A] font-semibold ${questionTypes.includes(type) ? 'bg-[#FFC857] neo-shadow' : 'bg-white'}`}
                      >
                        {getTypeLabel(type)}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid gap-6 md:grid-cols-3">
                  <div>
                    <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">Difficulty</label>
                    <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="input-field">
                      {difficulties.map((item) => (
                        <option key={item} value={item}>{item}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">Questions</label>
                    <input type="number" min="3" max="20" value={numQuestions} onChange={(e) => setNumQuestions(Math.max(3, Math.min(20, Number(e.target.value) || 3)))} className="input-field" />
                  </div>

                  <div>
                    <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">Duration</label>
                    <input type="number" min="15" max="180" value={durationMinutes} onChange={(e) => setDurationMinutes(Math.max(15, Math.min(180, Number(e.target.value) || 15)))} className="input-field" />
                  </div>
                </div>

                <button onClick={generateExam} className="btn-primary w-full py-3">Generate mock examination</button>
              </div>
            </div>
          </div>
        </StudyWorkspace>
      </div>
    );
  }

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <StudyWorkspace document={selectedDocument} title={exam.document_name || workspaceTitle} subtitle="Answer all questions, flag items for review, and submit when ready.">
        <div className="study-workspace__section space-y-6">
          <div className="card p-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              <div>
                <p className="text-sm font-bold uppercase tracking-wide text-[#0A0A0A]">Exam</p>
                <h2 className="text-2xl font-black text-[#0A0A0A]">{exam.document_name}</h2>
              </div>
              <div className="flex items-center gap-3">
                <div className="inline-flex items-center gap-2 badge badge-butter">
                  <Clock3 className="w-4 h-4" />
                  {formatTime(timeRemaining)}
                </div>
                <button onClick={() => handleSubmit(false)} disabled={submitting} className="btn-primary flex items-center gap-2">
                  <Send className="w-4 h-4" />
                  {submitting ? 'Submitting...' : 'Submit Exam'}
                </button>
              </div>
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-[250px_minmax(0,1fr)]">
            <div className="card p-4">
              <h3 className="font-black text-[#0A0A0A] mb-4">Question navigation</h3>
              <div className="grid grid-cols-5 gap-2">
                {exam.questions.map((question, index) => {
                  const selected = answers[question.id] !== undefined || answers[String(index)] !== undefined;
                  const flagged = reviewQuestions[question.id];
                  return (
                    <button
                      key={question.id}
                      onClick={() => setCurrentQuestionIndex(index)}
                      className={`relative rounded-xl border-2 border-[#0A0A0A] h-10 font-bold ${
                        index === currentQuestionIndex ? 'bg-[#FF5722] text-white' : selected ? 'bg-[#A2D2FF]' : 'bg-white'
                      }`}
                    >
                      {index + 1}
                      {flagged && <Flag className="absolute -top-1 -right-1 w-3 h-3 text-red-600" />}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <p className="text-sm font-bold uppercase tracking-wide text-[#0A0A0A]">Question {currentQuestionIndex + 1}</p>
                  <p className="text-sm text-[#0A0A0A] opacity-75">{getTypeLabel(currentQuestion?.type)} • {currentQuestion?.marks || 0} marks</p>
                </div>
                <button
                  onClick={() => toggleReview(currentQuestion.id)}
                  className={`btn-secondary px-3 py-2 text-sm ${reviewQuestions[currentQuestion.id] ? 'bg-[#FFC857]' : ''}`}
                >
                  {reviewQuestions[currentQuestion.id] ? 'Marked for review' : 'Mark for review'}
                </button>
              </div>

              <h3 className="text-2xl font-black text-[#0A0A0A] mb-4">{currentQuestion?.question}</h3>

              {currentQuestion?.type === 'multiple_choice' && currentQuestion.options && (
                <div className="space-y-3">
                  {currentQuestion.options.map((option, optionIndex) => {
                    const selectedValue = answers[currentQuestion.id] ?? answers[String(currentQuestionIndex)] ?? '';
                    const isSelected = String(selectedValue) === String(option);
                    return (
                      <button
                        key={option}
                        onClick={() => {
                          handleAnswerChange(currentQuestion.id, option);
                          setAnswers((prev) => ({ ...prev, [currentQuestion.id]: option }));
                        }}
                        className={`w-full text-left p-4 rounded-xl border-2 border-[#0A0A0A] ${isSelected ? 'bg-[#A2D2FF] neo-shadow' : 'bg-white'}`}
                      >
                        <span className="font-semibold">{String.fromCharCode(65 + optionIndex)}.</span> {option}
                      </button>
                    );
                  })}
                </div>
              )}

              {(currentQuestion?.type === 'short_answer' || currentQuestion?.type === 'structured') && (
                <textarea
                  value={answers[currentQuestion.id] || ''}
                  onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                  className="input-field min-h-[180px]"
                  placeholder="Write your answer here..."
                />
              )}

              <div className="flex flex-wrap gap-3 mt-6">
                <button onClick={() => setCurrentQuestionIndex((prev) => Math.max(0, prev - 1))} disabled={currentQuestionIndex === 0} className="btn-secondary flex items-center gap-2 disabled:opacity-50">
                  <ChevronLeft className="w-4 h-4" /> Previous
                </button>
                <button onClick={() => setCurrentQuestionIndex((prev) => Math.min(exam.questions.length - 1, prev + 1))} disabled={currentQuestionIndex === exam.questions.length - 1} className="btn-primary flex items-center gap-2 disabled:opacity-50">
                  Next <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </StudyWorkspace>
    </div>
  );
};

export default Quiz;
