import React, { useEffect, useMemo, useState } from 'react';
import { CalendarRange, CheckCircle2, Clock3, Sparkles, Target } from 'lucide-react';
import { toast } from 'sonner';
import { aiService, dashboardService } from '../services/api';

const weekdayOptions = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const emptyForm = {
  title: 'My study plan',
  subject: 'Mathematics',
  topics: 'Algebra, Geometry, Practice questions',
  goal: 'Reach 85% confidence before the exam',
  examDate: '',
  availableDays: ['Monday', 'Wednesday', 'Friday'],
  dailyStudyTime: 60,
  weeksCount: 4,
};

const Planner = () => {
  const [form, setForm] = useState(emptyForm);
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchCurrentPlan = async () => {
    try {
      const response = await dashboardService.getCurrentStudyPlan();
      const currentPlan = response.data?.plan_data || response.data || null;
      if (currentPlan && currentPlan.weeks && currentPlan.weeks.length) {
        setPlan(currentPlan);
        setForm((prev) => ({
          ...prev,
          title: currentPlan.title || prev.title,
          subject: currentPlan.subject || prev.subject,
          topics: Array.isArray(currentPlan.topics) ? currentPlan.topics.join(', ') : prev.topics,
          goal: currentPlan.goal || prev.goal,
          availableDays: Array.isArray(currentPlan.available_days) && currentPlan.available_days.length ? currentPlan.available_days : prev.availableDays,
          dailyStudyTime: currentPlan.daily_study_time || prev.dailyStudyTime,
          weeksCount: currentPlan.weeks_count || prev.weeksCount,
        }));
      }
    } catch (error) {
      // no plan yet; keep the blank form
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentPlan();
  }, []);

  const weeklySummary = useMemo(() => {
    if (!plan || !Array.isArray(plan.weeks)) return [];
    return plan.weeks.map((week) => ({
      ...week,
      tasksCount: (week.days || []).reduce((sum, day) => sum + ((day.tasks || []).length || 0), 0),
      totalMinutes: (week.days || []).reduce((sum, day) => sum + ((day.tasks || []).reduce((daySum, task) => daySum + Number(task.duration_minutes || 0), 0)), 0),
    }));
  }, [plan]);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const toggleDay = (day) => {
    setForm((prev) => {
      const hasDay = prev.availableDays.includes(day);
      return {
        ...prev,
        availableDays: hasDay
          ? prev.availableDays.filter((entry) => entry !== day)
          : [...prev.availableDays, day],
      };
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);

    try {
      const payload = {
        title: form.title,
        subject: form.subject,
        topics: form.topics
          .split(',')
          .map((topic) => topic.trim())
          .filter(Boolean),
        goal: form.goal,
        exam_date: form.examDate || undefined,
        available_days: form.availableDays,
        daily_study_time: Number(form.dailyStudyTime) || 60,
        weeks_count: Number(form.weeksCount) || 4,
      };

      const response = await aiService.generateStudyPlan(payload);
      const nextPlan = response.data?.plan_data || response.data || null;
      setPlan(nextPlan);
      toast.success('Your study plan has been generated.');
    } catch (error) {
      toast.error('Unable to generate a study plan right now.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ background: 'var(--bg-main)' }}>
        <div className="text-center">
          <div className="mx-auto h-16 w-16 animate-spin rounded-full border-4 border-[#FF5722] border-t-transparent" />
          <p className="mt-4 font-semibold text-[#0A0A0A]">Loading your planner...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="mx-auto max-w-7xl px-4 py-8 md:px-6">
        <div className="mb-8 flex flex-col gap-2">
          <p className="text-xs uppercase tracking-[0.26em] text-[#0A0A0A]/70">Planner</p>
          <h1 className="text-4xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
            AI Study Planner & Intelligent Scheduler
          </h1>
        </div>

        <div className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
          <form onSubmit={handleSubmit} className="card space-y-5" data-testid="planner-form">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl border-2 border-[#0A0A0A] bg-[#FF5722]">
                <Sparkles className="h-6 w-6 text-[#FDFBF7]" strokeWidth={2.5} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-[#0A0A0A]/70">Plan setup</p>
                <h2 className="text-2xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
                  Build your schedule
                </h2>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-[#0A0A0A]">Plan title</label>
              <input
                value={form.title}
                onChange={(event) => updateField('title', event.target.value)}
                className="w-full rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] px-3 py-2 text-[#0A0A0A] outline-none"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-[#0A0A0A]">Subject</label>
                <input
                  value={form.subject}
                  onChange={(event) => updateField('subject', event.target.value)}
                  className="w-full rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] px-3 py-2 text-[#0A0A0A] outline-none"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-[#0A0A0A]">Exam date</label>
                <input
                  type="date"
                  value={form.examDate}
                  onChange={(event) => updateField('examDate', event.target.value)}
                  className="w-full rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] px-3 py-2 text-[#0A0A0A] outline-none"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-[#0A0A0A]">Topics</label>
              <input
                value={form.topics}
                onChange={(event) => updateField('topics', event.target.value)}
                placeholder="Algebra, Biology, Essay writing"
                className="w-full rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] px-3 py-2 text-[#0A0A0A] outline-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-[#0A0A0A]">Target goal</label>
              <input
                value={form.goal}
                onChange={(event) => updateField('goal', event.target.value)}
                className="w-full rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] px-3 py-2 text-[#0A0A0A] outline-none"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-[#0A0A0A]">Daily study time</label>
                <div className="flex items-center gap-2 rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] px-3 py-2">
                  <Clock3 className="h-4 w-4 text-[#0A0A0A]" />
                  <input
                    type="number"
                    min="15"
                    max="420"
                    value={form.dailyStudyTime}
                    onChange={(event) => updateField('dailyStudyTime', event.target.value)}
                    className="w-full bg-transparent text-[#0A0A0A] outline-none"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-[#0A0A0A]">Weeks</label>
                <input
                  type="number"
                  min="1"
                  max="12"
                  value={form.weeksCount}
                  onChange={(event) => updateField('weeksCount', event.target.value)}
                  className="w-full rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] px-3 py-2 text-[#0A0A0A] outline-none"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-[#0A0A0A]">Available study days</label>
              <div className="flex flex-wrap gap-2">
                {weekdayOptions.map((day) => {
                  const active = form.availableDays.includes(day);
                  return (
                    <button
                      key={day}
                      type="button"
                      onClick={() => toggleDay(day)}
                      className={`rounded-full border-2 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.12em] ${
                        active ? 'border-[#0A0A0A] bg-[#FF5722] text-[#FDFBF7]' : 'border-[#0A0A0A] bg-[#FDFBF7] text-[#0A0A0A]'
                      }`}
                    >
                      {day.slice(0, 3)}
                    </button>
                  );
                })}
              </div>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="w-full rounded-xl border-2 border-[#0A0A0A] bg-[#A2D2FF] px-4 py-3 font-black text-[#0A0A0A] shadow-[4px_4px_0px_#0A0A0A] transition-transform hover:-translate-y-0.5 disabled:opacity-60"
            >
              {saving ? 'Generating plan...' : 'Generate plan'}
            </button>
          </form>

          <div className="space-y-6">
            <div className="card">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-[#0A0A0A]/70">Current plan</p>
                  <h2 className="text-2xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    {plan?.title || 'Study plan preview'}
                  </h2>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl border-2 border-[#0A0A0A] bg-[#CFFFE1]">
                  <CalendarRange className="h-6 w-6 text-[#0A0A0A]" strokeWidth={2.5} />
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#0A0A0A]/70">Goal</p>
                  <p className="mt-2 text-sm font-bold text-[#0A0A0A]">{plan?.goal || form.goal}</p>
                </div>
                <div className="rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#0A0A0A]/70">Focus</p>
                  <p className="mt-2 text-sm font-bold text-[#0A0A0A]">{plan?.subject || form.subject}</p>
                </div>
                <div className="rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#0A0A0A]/70">Time</p>
                  <p className="mt-2 text-sm font-bold text-[#0A0A0A]">{plan?.daily_study_time || form.dailyStudyTime} min/day</p>
                </div>
              </div>
            </div>

            {plan && Array.isArray(plan.weeks) && plan.weeks.length > 0 ? (
              <div className="space-y-4">
                {weeklySummary.map((week) => (
                  <div key={week.week_number} className="card">
                    <div className="mb-4 flex items-center justify-between">
                      <h3 className="text-xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
                        Week {week.week_number}
                      </h3>
                      <div className="flex items-center gap-2 rounded-full border-2 border-[#0A0A0A] bg-[#CFFFE1] px-2 py-1 text-xs font-bold text-[#0A0A0A]">
                        <Target className="h-3.5 w-3.5" />
                        {week.tasksCount} tasks
                      </div>
                    </div>

                    <div className="grid gap-3">
                      {(week.days || []).map((day) => (
                        <div key={`${week.week_number}-${day.day}`} className="rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] p-3">
                          <div className="mb-2 flex items-center justify-between">
                            <p className="font-black text-[#0A0A0A]">{day.day}</p>
                            <span className="text-xs font-semibold text-[#0A0A0A]">
                              {(day.tasks || []).reduce((sum, task) => sum + Number(task.duration_minutes || 0), 0)} min
                            </span>
                          </div>

                          <div className="space-y-2">
                            {(day.tasks || []).map((task, index) => (
                              <div key={`${day.day}-${task.topic || index}`} className="flex items-start gap-2 rounded-lg border border-[#0A0A0A]/20 bg-white p-2">
                                <CheckCircle2 className="mt-0.5 h-4 w-4 text-[#3BB273]" strokeWidth={2.5} />
                                <div className="flex-1">
                                  <div className="flex items-center justify-between gap-2">
                                    <p className="font-bold text-[#0A0A0A]">{task.topic || 'Revision block'}</p>
                                    <span className="rounded-full bg-[#F2E8CF] px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.08em] text-[#0A0A0A]">
                                      {task.task_type || 'study'}
                                    </span>
                                  </div>
                                  <p className="text-xs text-[#0A0A0A]/70">{task.subject || plan.subject || form.subject}</p>
                                  <p className="mt-1 text-xs text-[#0A0A0A]">
                                    {task.duration_minutes || 0} minutes • {task.focus || 'Focused practice'}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="card text-sm text-[#0A0A0A]">
                No study plan is active yet. Use the planner form to generate a tailored schedule.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Planner;
