import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { dashboardService, progressService } from '../services/api';
import { Link } from 'react-router-dom';
import { FileText, BookOpen, Brain, Award, TrendingUp, Calendar, Flame, NotebookPen, Target, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

const Dashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [studySummary, setStudySummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const [dashboardResp, summaryResp] = await Promise.all([
          dashboardService.get(),
          progressService.getSummary(),
        ]);
        setDashboardData(dashboardResp.data);
        setStudySummary(summaryResp.data);
      } catch (e) {
        toast.error('Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: 'var(--bg-main)' }}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#FF5722] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-[#0A0A0A] font-semibold">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  const stats = dashboardData?.stats || {};
  const summary = studySummary || dashboardData?.study_summary || {};
  const dailyGoal = summary.daily_goal || { goal_minutes: 60, minutes_completed: 0, minutes_remaining: 60, progress_percent: 0, goal_reached: false };
  const weeklyActivity = summary.weekly_activity || [];
  const recentActivity = summary.recent_activity || [];
  const activeDays = summary.active_days || [];

  const activityCalendar = Array.from({ length: 35 }, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() - (34 - index));
    const iso = date.toISOString().slice(0, 10);
    const minuteTotal = summary.calendar?.[iso] || 0;
    return {
      date: iso,
      minutes: minuteTotal,
      active: minuteTotal > 0,
      label: date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    };
  });

  const sortedRecentActivity = recentActivity.slice(0, 5);

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-5xl font-black text-[#0A0A0A] tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Welcome back, {user?.name || 'Student'}! 👋
          </h1>
          <p className="text-lg text-[#0A0A0A]" style={{ fontFamily: 'DM Sans, sans-serif' }}>
            Ready to continue your learning journey?
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 mb-8">
          <div className="card animate-fade-up stagger-1" data-testid="streak-card">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-[#FF5722] rounded-xl flex items-center justify-center border-2 border-[#0A0A0A]">
                <Flame className="w-6 h-6 text-[#FDFBF7]" strokeWidth={2.5} />
              </div>
              <span className="badge badge-peach">STREAK</span>
            </div>
            <h3 className="text-3xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
              {stats.current_streak || 0} Days
            </h3>
            <p className="text-sm text-[#0A0A0A] mt-1">Longest: {stats.longest_streak || 0} days</p>
          </div>

          <div className="card animate-fade-up stagger-2" data-testid="documents-card">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-[#A2D2FF] rounded-xl flex items-center justify-center border-2 border-[#0A0A0A]">
                <FileText className="w-6 h-6 text-[#0A0A0A]" strokeWidth={2.5} />
              </div>
              <span className="badge badge-mint">DOCS</span>
            </div>
            <h3 className="text-3xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
              {stats.documents_uploaded || 0}
            </h3>
            <p className="text-sm text-[#0A0A0A] mt-1">Documents uploaded</p>
          </div>

          <div className="card animate-fade-up stagger-3" data-testid="quizzes-card">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-[#CDB4DB] rounded-xl flex items-center justify-center border-2 border-[#0A0A0A]">
                <Brain className="w-6 h-6 text-[#0A0A0A]" strokeWidth={2.5} />
              </div>
              <span className="badge">QUIZZES</span>
            </div>
            <h3 className="text-3xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
              {stats.quizzes_taken || 0}
            </h3>
            <p className="text-sm text-[#0A0A0A] mt-1">Quizzes completed</p>
          </div>

          <div className="card animate-fade-up stagger-4" data-testid="study-time-card">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-[#FFC857] rounded-xl flex items-center justify-center border-2 border-[#0A0A0A]">
                <TrendingUp className="w-6 h-6 text-[#0A0A0A]" strokeWidth={2.5} />
              </div>
              <span className="badge badge-butter">TIME</span>
            </div>
            <h3 className="text-3xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
              {Math.round((stats.total_study_minutes || 0) / 60)}h
            </h3>
            <p className="text-sm text-[#0A0A0A] mt-1">Total study time</p>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mt-8">
          <div className="card animate-fade-up stagger-5" data-testid="streak-dashboard-card">
            <div className="flex items-center justify-between mb-5">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-[#0A0A0A]/70">Study streak</p>
                <h2 className="text-2xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
                  Progress tracker
                </h2>
              </div>
              <div className="w-12 h-12 bg-[#FF5722] rounded-xl flex items-center justify-center border-2 border-[#0A0A0A]">
                <Flame className="w-6 h-6 text-[#FDFBF7]" strokeWidth={2.5} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-5">
              <div className="p-3 rounded-xl bg-[#FDFBF7] border-2 border-[#0A0A0A]">
                <p className="text-xs uppercase tracking-[0.15em] text-[#0A0A0A]/60">Current</p>
                <p className="text-3xl font-black text-[#0A0A0A]">{summary.current_streak || 0}</p>
              </div>
              <div className="p-3 rounded-xl bg-[#FDFBF7] border-2 border-[#0A0A0A]">
                <p className="text-xs uppercase tracking-[0.15em] text-[#0A0A0A]/60">Longest</p>
                <p className="text-3xl font-black text-[#0A0A0A]">{summary.longest_streak || 0}</p>
              </div>
              <div className="p-3 rounded-xl bg-[#FDFBF7] border-2 border-[#0A0A0A] col-span-2">
                <p className="text-xs uppercase tracking-[0.15em] text-[#0A0A0A]/60">Active study days</p>
                <p className="text-3xl font-black text-[#0A0A0A]">{summary.total_active_days || 0}</p>
              </div>
            </div>

            <div className="space-y-2">
              {weeklyActivity.length > 0 ? weeklyActivity.map((day, index) => (
                <div key={`${day.date}-${index}`} className="flex items-center gap-3">
                  <span className="w-10 text-xs font-semibold text-[#0A0A0A]">{day.day}</span>
                  <div className="flex-1 h-2.5 rounded-full bg-[#F2E8CF] border border-[#0A0A0A] overflow-hidden">
                    <div
                      className="h-full rounded-full bg-[#FF5722]"
                      style={{ width: `${Math.min(100, (day.minutes / Math.max(1, dailyGoal.goal_minutes || 60)) * 100)}%` }}
                    />
                  </div>
                  <span className="w-8 text-right text-xs font-semibold text-[#0A0A0A]">{day.minutes || 0}m</span>
                </div>
              )) : (
                <p className="text-sm text-[#0A0A0A]">No study activity recorded yet this week.</p>
              )}
            </div>
          </div>

          <div className="card animate-fade-up stagger-6" data-testid="today-goal-card">
            <div className="flex items-center justify-between mb-5">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-[#0A0A0A]/70">Daily goal</p>
                <h2 className="text-2xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
                  Today&apos;s progress
                </h2>
              </div>
              <div className="w-12 h-12 bg-[#A2D2FF] rounded-xl flex items-center justify-center border-2 border-[#0A0A0A]">
                <Target className="w-6 h-6 text-[#0A0A0A]" strokeWidth={2.5} />
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-end">
                <div>
                  <p className="text-4xl font-black text-[#0A0A0A]">{dailyGoal.minutes_completed || 0}m</p>
                  <p className="text-sm text-[#0A0A0A]">of {dailyGoal.goal_minutes || 60} minute goal</p>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-full border-2 border-[#0A0A0A] bg-[#CFFFE1]">
                  <CheckCircle2 className="w-4 h-4 text-[#0A0A0A]" />
                  <span className="text-xs font-bold text-[#0A0A0A]">{dailyGoal.goal_reached ? 'Goal reached' : 'In progress'}</span>
                </div>
              </div>

              <div className="h-3 bg-[#F2E8CF] border-2 border-[#0A0A0A] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#3BB273]"
                  style={{ width: `${Math.min(100, dailyGoal.progress_percent || 0)}%` }}
                />
              </div>

              <div className="flex justify-between text-sm text-[#0A0A0A]">
                <span>Remaining</span>
                <span className="font-bold">{dailyGoal.minutes_remaining || 0} minutes</span>
              </div>
            </div>
          </div>

          <div className="card animate-fade-up stagger-7" data-testid="recent-study-card">
            <div className="flex items-center justify-between mb-5">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-[#0A0A0A]/70">Recent activity</p>
                <h2 className="text-2xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
                  Study log
                </h2>
              </div>
              <div className="w-12 h-12 bg-[#FFC857] rounded-xl flex items-center justify-center border-2 border-[#0A0A0A]">
                <Calendar className="w-6 h-6 text-[#0A0A0A]" strokeWidth={2.5} />
              </div>
            </div>

            <div className="space-y-3">
              {sortedRecentActivity.length > 0 ? sortedRecentActivity.map((entry, idx) => (
                <div key={`${entry.started_at || idx}-${idx}`} className="p-3 rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7]">
                  <div className="flex justify-between gap-3">
                    <p className="font-bold text-[#0A0A0A]">{entry.session_type || 'Study session'}</p>
                    <span className="text-xs font-semibold text-[#0A0A0A]">{entry.duration_minutes || 0}m</span>
                  </div>
                  <p className="text-xs text-[#0A0A0A] mt-1">
                    {new Date(entry.started_at).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                  </p>
                </div>
              )) : (
                <p className="text-sm text-[#0A0A0A]">No study sessions logged yet.</p>
              )}
            </div>
          </div>
        </div>

        <div className="card mt-8 animate-fade-up stagger-8" data-testid="calendar-card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-[#0A0A0A]/70">Calendar</p>
              <h2 className="text-2xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
                Study activity over time
              </h2>
            </div>
            <div className="flex items-center gap-2 text-sm text-[#0A0A0A]">
              <span className="inline-block w-3 h-3 rounded-sm bg-[#FF5722] border border-[#0A0A0A]" /> Active day
            </div>
          </div>

          <div className="grid grid-cols-7 gap-2">
            {activityCalendar.map((day) => (
              <div key={day.date} className="text-center">
                <div
                  className={`h-12 rounded-xl border-2 border-[#0A0A0A] flex items-center justify-center text-[10px] font-bold ${
                    day.active ? 'bg-[#FF5722] text-[#FDFBF7]' : 'bg-[#FDFBF7] text-[#0A0A0A]'
                  }`}
                  title={`${day.date}: ${day.minutes} minutes`}
                >
                  {day.minutes > 0 ? `${day.minutes}m` : '•'}
                </div>
                <p className="text-[10px] mt-1 text-[#0A0A0A]">{day.label.split(' ')[0]}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
          <div className="lg:col-span-2 card animate-fade-up stagger-9" data-testid="quick-actions-card">
            <h2 className="text-2xl font-black text-[#0A0A0A] mb-6" style={{ fontFamily: 'Outfit, sans-serif' }}>
              Quick Actions
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <Link
                to="/upload"
                className="p-6 bg-[#FDFBF7] rounded-xl border-2 border-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow transition-all"
                data-testid="upload-action-btn"
              >
                <FileText className="w-8 h-8 text-[#FF5722] mb-3" strokeWidth={2.5} />
                <h3 className="font-bold text-[#0A0A0A] mb-1">Upload Material</h3>
                <p className="text-sm text-[#0A0A0A]">Add new study docs</p>
              </Link>

              <Link
                to="/notes"
                className="p-6 bg-[#FDFBF7] rounded-xl border-2 border-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow transition-all"
                data-testid="notes-action-btn"
              >
                <NotebookPen className="w-8 h-8 text-[#FF865E] mb-3" strokeWidth={2.5} />
                <h3 className="font-bold text-[#0A0A0A] mb-1">Take Notes</h3>
                <p className="text-sm text-[#0A0A0A]">Capture your thoughts</p>
              </Link>

              <Link
                to="/tutor"
                className="p-6 bg-[#FDFBF7] rounded-xl border-2 border-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow transition-all"
                data-testid="tutor-action-btn"
              >
                <BookOpen className="w-8 h-8 text-[#A2D2FF] mb-3" strokeWidth={2.5} />
                <h3 className="font-bold text-[#0A0A0A] mb-1">AI Tutor</h3>
                <p className="text-sm text-[#0A0A0A]">Get instant help</p>
              </Link>

              <Link
                to="/quiz"
                className="p-6 bg-[#FDFBF7] rounded-xl border-2 border-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow transition-all"
                data-testid="quiz-action-btn"
              >
                <Brain className="w-8 h-8 text-[#CDB4DB] mb-3" strokeWidth={2.5} />
                <h3 className="font-bold text-[#0A0A0A] mb-1">Take Quiz</h3>
                <p className="text-sm text-[#0A0A0A]">Test your knowledge</p>
              </Link>

              <Link
                to="/flashcards"
                className="p-6 bg-[#FDFBF7] rounded-xl border-2 border-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow transition-all"
                data-testid="flashcards-action-btn"
              >
                <Award className="w-8 h-8 text-[#FFC857] mb-3" strokeWidth={2.5} />
                <h3 className="font-bold text-[#0A0A0A] mb-1">Flashcards</h3>
                <p className="text-sm text-[#0A0A0A]">Review concepts</p>
              </Link>

              <Link
                to="/documents"
                className="p-6 bg-[#FDFBF7] rounded-xl border-2 border-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow transition-all"
                data-testid="documents-action-btn"
              >
                <FileText className="w-8 h-8 text-[#0A0A0A] mb-3" strokeWidth={2.5} />
                <h3 className="font-bold text-[#0A0A0A] mb-1">My Library</h3>
                <p className="text-sm text-[#0A0A0A]">Browse documents</p>
              </Link>
            </div>
          </div>

          <div className="card animate-fade-up stagger-10" data-testid="recent-docs-card">
            <h2 className="text-2xl font-black text-[#0A0A0A] mb-6" style={{ fontFamily: 'Outfit, sans-serif' }}>
              Recent Documents
            </h2>
            <div className="space-y-3">
              {dashboardData?.recent_documents?.length > 0 ? (
                dashboardData.recent_documents.slice(0, 5).map((doc, idx) => (
                  <Link
                    key={doc.id}
                    to={`/documents/${doc.id}`}
                    className="block p-4 bg-[#FDFBF7] rounded-lg border-2 border-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow transition-all"
                    data-testid={`recent-doc-${idx}`}
                  >
                    <p className="font-semibold text-[#0A0A0A] truncate">{doc.original_filename}</p>
                    <p className="text-xs text-[#0A0A0A] mt-1">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                  </Link>
                ))
              ) : (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-[#0A0A0A] mx-auto mb-3 opacity-30" />
                  <p className="text-sm text-[#0A0A0A]">No documents yet</p>
                  <Link to="/upload" className="text-sm font-semibold text-[#FF5722] underline mt-2 inline-block">
                    Upload your first document
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
