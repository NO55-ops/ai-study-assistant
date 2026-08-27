import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { documentService, aiService } from '../services/api';
import { HelpCircle, Check, X } from 'lucide-react';
import { toast } from 'sonner';

const Quiz = () => {
  const [searchParams] = useSearchParams();
  const docId = searchParams.get('doc');
  const [documents, setDocuments] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState(docId ? [docId] : []);
  const [questionTypes, setQuestionTypes] = useState(['multiple_choice']);
  const [difficulty, setDifficulty] = useState('medium');
  const [numQuestions, setNumQuestions] = useState(10);
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const { data } = await documentService.list();
        setDocuments(data);
      } catch (e) {
        toast.error('Failed to load documents');
      }
    };
    fetchDocs();
  }, []);

  useEffect(() => {
    if (!generating) return undefined;

    const stages = [
      { label: 'Scanning documents', progress: 20 },
      { label: 'Finding key ideas', progress: 45 },
      { label: 'Drafting quiz questions', progress: 72 },
      { label: 'Finalizing answers', progress: 94 },
    ];

    const interval = setInterval(() => {
      setLoadingStep((prev) => {
        const next = (prev + 1) % stages.length;
        return next;
      });
    }, 700);

    return () => clearInterval(interval);
  }, [generating]);

  const toggleDoc = (id) => {
    setSelectedDocs((prev) => (prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]));
  };

  const toggleQuestionType = (type) => {
    setQuestionTypes((prev) => (prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]));
  };

  const generateQuiz = async () => {
    if (selectedDocs.length === 0 || questionTypes.length === 0) {
      toast.error('Please select at least one document and question type');
      return;
    }

    setGenerating(true);
    setLoadingStep(0);
    try {
      const { data } = await aiService.generateQuiz(selectedDocs, questionTypes, difficulty, numQuestions);
      setQuiz(data);
      setAnswers({});
      setShowResults(false);
      toast.success('Quiz generated!');
    } catch (e) {
      toast.error('Failed to generate quiz');
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmit = () => {
    setShowResults(true);
    const correct = quiz.quiz_data.questions.filter(
      (q, idx) => answers[idx] === q.correct_answer
    ).length;
    toast.success(`You scored ${correct} out of ${quiz.quiz_data.questions.length}!`);
  };

  const allTypes = ['multiple_choice', 'true_false', 'fill_in_blank', 'short_answer'];
  const difficulties = ['easy', 'medium', 'hard', 'exam_level'];
  const loadingStages = [
    { label: 'Scanning documents', progress: 20 },
    { label: 'Finding key ideas', progress: 45 },
    { label: 'Drafting quiz questions', progress: 72 },
    { label: 'Finalizing answers', progress: 94 },
  ];
  const currentStage = loadingStages[loadingStep] || loadingStages[0];

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="max-w-5xl mx-auto px-4 py-12">
        {generating && !quiz && (
          <div className="quiz-loading-shell card" data-testid="quiz-loading-state">
            <div className="quiz-loading-header">
              <div className="quiz-badge">AI POWERED</div>
              <div className="quiz-loader-dots" aria-label="Loading">
                <span />
                <span />
                <span />
              </div>
            </div>

            <h2 className="quiz-loading-title">Crafting your quiz</h2>
            <p className="quiz-loading-text">{currentStage.label}</p>

            <div className="quiz-loading-bar">
              <div className="quiz-loading-progress" style={{ width: `${currentStage.progress}%` }} />
            </div>

            <div className="quiz-loading-pills">
              {loadingStages.map((stage, index) => (
                <span
                  key={stage.label}
                  className={`quiz-loading-pill ${index === loadingStep ? 'active' : ''}`}
                >
                  {stage.label}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#CDB4DB] rounded-2xl border-2 border-[#0A0A0A] neo-shadow mb-4">
            <HelpCircle className="w-8 h-8 text-[#0A0A0A]" strokeWidth={2.5} />
          </div>
          <h1 className="text-5xl font-black text-[#0A0A0A] tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Quiz Generator
          </h1>
          <p className="text-lg text-[#0A0A0A]" style={{ fontFamily: 'DM Sans, sans-serif' }}>
            Test your knowledge with AI-generated quizzes
          </p>
        </div>

        {!quiz ? (
          <div className="card" data-testid="quiz-setup-card">
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">
                  Select Documents
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {documents.map((doc) => (
                    <button
                      key={doc.id}
                      onClick={() => toggleDoc(doc.id)}
                      data-testid={`doc-select-${doc.id}`}
                      className={`p-4 rounded-xl border-2 border-[#0A0A0A] font-semibold text-left transition-all truncate ${
                        selectedDocs.includes(doc.id)
                          ? 'bg-[#A2D2FF] text-[#0A0A0A] neo-shadow'
                          : 'bg-white text-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow'
                      }`}
                    >
                      {doc.original_filename}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">
                  Question Types
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {allTypes.map((type) => (
                    <button
                      key={type}
                      onClick={() => toggleQuestionType(type)}
                      data-testid={`type-${type}-btn`}
                      className={`py-3 px-4 rounded-xl border-2 border-[#0A0A0A] font-semibold text-xs transition-all ${
                        questionTypes.includes(type)
                          ? 'bg-[#CDB4DB] text-[#0A0A0A] neo-shadow'
                          : 'bg-white text-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow'
                      }`}
                    >
                      {type.replace('_', ' ').toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">Difficulty</label>
                  <div className="grid grid-cols-2 gap-2">
                    {difficulties.map((diff) => (
                      <button
                        key={diff}
                        onClick={() => setDifficulty(diff)}
                        data-testid={`difficulty-${diff}-btn`}
                        className={`py-2 px-4 rounded-xl border-2 border-[#0A0A0A] font-semibold text-xs transition-all ${
                          difficulty === diff
                            ? 'bg-[#FFC857] text-[#0A0A0A] neo-shadow'
                            : 'bg-white text-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow'
                        }`}
                      >
                        {diff.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">
                    Number of Questions
                  </label>
                  <input
                    type="number"
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(parseInt(e.target.value) || 10)}
                    min="5"
                    max="20"
                    className="input-field"
                    data-testid="num-questions-input"
                  />
                </div>
              </div>

              <button
                onClick={generateQuiz}
                disabled={generating}
                className="btn-primary w-full"
                data-testid="generate-quiz-btn"
              >
                {generating ? 'Generating Quiz...' : 'Generate Quiz'}
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="card" data-testid="quiz-card">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
                  Quiz Questions
                </h2>
                <span className="badge badge-butter">
                  {quiz.quiz_data.questions?.length || 0} QUESTIONS
                </span>
              </div>

              <div className="space-y-6">
                {quiz.quiz_data.questions?.map((q, idx) => (
                  <div key={idx} className="p-6 bg-[#FDFBF7] rounded-xl border-2 border-[#0A0A0A]" data-testid={`question-${idx}`}>
                    <div className="flex items-start gap-4 mb-4">
                      <span className="flex-shrink-0 w-8 h-8 bg-[#FF5722] rounded-lg flex items-center justify-center text-[#FDFBF7] font-bold border-2 border-[#0A0A0A]">
                        {idx + 1}
                      </span>
                      <p className="font-semibold text-[#0A0A0A] flex-1">{q.question}</p>
                    </div>

                    {q.type === 'multiple_choice' && q.options && (
                      <div className="space-y-2 ml-12">
                        {q.options.map((option, optIdx) => {
                          const isSelected = answers[idx] === option;
                          const isCorrect = q.correct_answer === option;
                          const showStatus = showResults && isSelected;

                          return (
                            <button
                              key={optIdx}
                              onClick={() => !showResults && setAnswers({ ...answers, [idx]: option })}
                              disabled={showResults}
                              data-testid={`question-${idx}-option-${optIdx}`}
                              className={`w-full text-left p-3 rounded-lg border-2 border-[#0A0A0A] font-medium transition-all ${
                                isSelected
                                  ? showStatus
                                    ? isCorrect
                                      ? 'bg-green-200 text-[#0A0A0A]'
                                      : 'bg-red-200 text-[#0A0A0A]'
                                    : 'bg-[#A2D2FF] text-[#0A0A0A] neo-shadow'
                                  : 'bg-white text-[#0A0A0A] hover:bg-[#FDFBF7]'
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <span>{option}</span>
                                {showStatus && (
                                  isCorrect ? (
                                    <Check className="w-5 h-5 text-green-600" strokeWidth={3} />
                                  ) : (
                                    <X className="w-5 h-5 text-red-600" strokeWidth={3} />
                                  )
                                )}
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {showResults && q.explanation && (
                      <div className="mt-4 ml-12 p-4 bg-white rounded-lg border-2 border-[#0A0A0A]">
                        <p className="text-sm font-semibold text-[#0A0A0A] mb-1">Explanation:</p>
                        <p className="text-sm text-[#0A0A0A]">{q.explanation}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-4">
              <button onClick={() => setQuiz(null)} className="btn-secondary flex-1" data-testid="new-quiz-btn">
                Generate New Quiz
              </button>
              {!showResults && (
                <button onClick={handleSubmit} className="btn-primary flex-1" data-testid="submit-quiz-btn">
                  Submit Quiz
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Quiz;
