import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { GraduationCap, Calendar, Target } from 'lucide-react';
import { toast } from 'sonner';

const Onboarding = () => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    grade_level: '',
    subjects: [],
    curriculum: '',
    exam_dates: [],
    daily_study_goal: 60,
  });
  const { completeOnboarding } = useAuth();
  const navigate = useNavigate();

  const gradeLevels = ['9th Grade', '10th Grade', '11th Grade', '12th Grade', 'College'];
  const curriculums = ['IB', 'AP', 'IGCSE', 'SAT', 'A-Levels', 'Other'];
  const commonSubjects = ['Math', 'Science', 'English', 'History', 'Physics', 'Chemistry', 'Biology', 'Computer Science'];
  const studyGoals = [30, 60, 90, 120];

  const toggleSubject = (subject) => {
    setFormData((prev) => ({
      ...prev,
      subjects: prev.subjects.includes(subject)
        ? prev.subjects.filter((s) => s !== subject)
        : [...prev.subjects, subject],
    }));
  };

  const handleSubmit = async () => {
    if (!formData.grade_level || formData.subjects.length === 0 || !formData.curriculum) {
      toast.error('Please complete all required fields');
      return;
    }

    const result = await completeOnboarding(formData);
    if (result.success) {
      toast.success('Welcome aboard! 🎉');
      navigate('/dashboard');
    } else {
      toast.error(result.error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#CDB4DB] rounded-2xl border-2 border-[#0A0A0A] neo-shadow mb-4">
            <GraduationCap className="w-8 h-8 text-[#0A0A0A]" strokeWidth={2.5} />
          </div>
          <h1 className="text-4xl font-black text-[#0A0A0A] tracking-tight" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Let's Get Started
          </h1>
          <p className="text-base text-[#0A0A0A] mt-2" style={{ fontFamily: 'DM Sans, sans-serif' }}>
            Tell us about yourself to personalize your experience
          </p>
        </div>

        <div className="bg-white rounded-2xl border-2 border-[#0A0A0A] neo-shadow p-8" data-testid="onboarding-card">
          <div className="mb-8">
            <div className="flex gap-2">
              {[1, 2, 3].map((s) => (
                <div
                  key={s}
                  className={`h-2 flex-1 rounded-full border border-[#0A0A0A] ${
                    step >= s ? 'bg-[#FF5722]' : 'bg-white'
                  }`}
                />
              ))}
            </div>
          </div>

          {step === 1 && (
            <div className="space-y-6 animate-fade-up">
              <div>
                <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">
                  Grade Level
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {gradeLevels.map((grade) => (
                    <button
                      key={grade}
                      onClick={() => setFormData({ ...formData, grade_level: grade })}
                      data-testid={`grade-${grade.toLowerCase().replace(/\s+/g, '-')}-btn`}
                      className={`py-3 px-4 rounded-xl border-2 border-[#0A0A0A] font-semibold transition-all ${
                        formData.grade_level === grade
                          ? 'bg-[#FF5722] text-[#FDFBF7] neo-shadow'
                          : 'bg-white text-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow'
                      }`}
                    >
                      {grade}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">
                  Curriculum
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {curriculums.map((curr) => (
                    <button
                      key={curr}
                      onClick={() => setFormData({ ...formData, curriculum: curr })}
                      data-testid={`curriculum-${curr.toLowerCase()}-btn`}
                      className={`py-3 px-4 rounded-xl border-2 border-[#0A0A0A] font-semibold transition-all ${
                        formData.curriculum === curr
                          ? 'bg-[#A2D2FF] text-[#0A0A0A] neo-shadow'
                          : 'bg-white text-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow'
                      }`}
                    >
                      {curr}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6 animate-fade-up">
              <div>
                <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">
                  Subjects (Select all that apply)
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {commonSubjects.map((subject) => (
                    <button
                      key={subject}
                      onClick={() => toggleSubject(subject)}
                      data-testid={`subject-${subject.toLowerCase().replace(/\s+/g, '-')}-btn`}
                      className={`py-3 px-4 rounded-xl border-2 border-[#0A0A0A] font-semibold transition-all ${
                        formData.subjects.includes(subject)
                          ? 'bg-[#CDB4DB] text-[#0A0A0A] neo-shadow'
                          : 'bg-white text-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow'
                      }`}
                    >
                      {subject}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6 animate-fade-up">
              <div>
                <label className="block text-sm font-bold text-[#0A0A0A] mb-3 uppercase tracking-wide">
                  Daily Study Goal (minutes)
                </label>
                <div className="grid grid-cols-4 gap-3">
                  {studyGoals.map((goal) => (
                    <button
                      key={goal}
                      onClick={() => setFormData({ ...formData, daily_study_goal: goal })}
                      data-testid={`study-goal-${goal}-btn`}
                      className={`py-4 px-4 rounded-xl border-2 border-[#0A0A0A] font-bold text-lg transition-all ${
                        formData.daily_study_goal === goal
                          ? 'bg-[#FFC857] text-[#0A0A0A] neo-shadow'
                          : 'bg-white text-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow'
                      }`}
                    >
                      {goal}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-4 mt-8">
            {step > 1 && (
              <button
                onClick={() => setStep(step - 1)}
                className="btn-secondary flex-1"
                data-testid="onboarding-back-btn"
              >
                Back
              </button>
            )}
            {step < 3 ? (
              <button
                onClick={() => setStep(step + 1)}
                className="btn-primary flex-1"
                data-testid="onboarding-next-btn"
              >
                Next
              </button>
            ) : (
              <button onClick={handleSubmit} className="btn-primary flex-1" data-testid="onboarding-complete-btn">
                Complete Setup
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
