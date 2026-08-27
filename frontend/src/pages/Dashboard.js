import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { dashboardService, progressService } from '../services/api';
import { Link } from 'react-router-dom';
import { FileText, BookOpen, Brain, Award, TrendingUp, Calendar, Flame, NotebookPen } from 'lucide-react';
import { toast } from 'sonner';

const Dashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const { data } = await dashboardService.get();
        setDashboardData(data);
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card animate-fade-up stagger-5" data-testid="quick-actions-card">
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

          <div className="card animate-fade-up stagger-6" data-testid="recent-docs-card">
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
