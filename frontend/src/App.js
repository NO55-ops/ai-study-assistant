import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Toaster } from 'sonner';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import NotesWidget from './components/NotesWidget';
import Login from './pages/Login';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import Planner from './pages/Planner';
import Upload from './pages/Upload';
import Documents from './pages/Documents';
import DocumentView from './pages/DocumentView';
import KnowledgeGraph from './pages/KnowledgeGraph';
import Tutor from './pages/Tutor';
import Quiz from './pages/Quiz';
import Flashcards from './pages/Flashcards';
import Notes from './pages/Notes';
import Settings from './pages/Settings';
import Library from './pages/Library';
import LibraryQualification from './pages/LibraryQualification';
import LibrarySubject from './pages/LibrarySubject';
import LibraryTopic from './pages/LibraryTopic';
import LibraryAdminEditor from './pages/LibraryAdminEditor';
import './App.css';
import { BACKEND_URL_ERROR } from './config/backend';

const BackendConfigNotice = ({ message }) => (
  <div
    className="min-h-screen flex items-center justify-center px-4 noise-overlay"
    style={{ background: 'var(--bg-main)' }}
    data-testid="backend-config-error"
  >
    <div className="w-full max-w-xl bg-white rounded-2xl border-2 border-[#0A0A0A] neo-shadow p-8">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#FF5722]">Configuration error</p>
      <h1
        className="text-3xl font-black text-[#0A0A0A] mt-2 mb-3"
        style={{ fontFamily: 'Outfit, sans-serif' }}
      >
        The app cannot reach the backend
      </h1>
      <p className="text-[#0A0A0A]" style={{ fontFamily: 'DM Sans, sans-serif' }}>
        {message}
      </p>
      <p className="text-sm text-[#0A0A0A]/70 mt-4">
        No API request was made and nothing was saved or lost — this is a build configuration problem,
        not a problem with your account or data.
      </p>
    </div>
  </div>
);

const GlobalNotesWidget = () => {
  const { user } = useAuth();
  if (!user) return null;
  return <NotesWidget />;
};

function App() {
  if (BACKEND_URL_ERROR) {
    return <BackendConfigNotice message={BACKEND_URL_ERROR} />;
  }

  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Toaster position="top-right" richColors />
          <GlobalNotesWidget />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/onboarding"
            element={
              <ProtectedRoute>
                <Onboarding />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Navbar />
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/planner"
            element={
              <ProtectedRoute>
                <Navbar />
                <Planner />
              </ProtectedRoute>
            }
          />
          <Route
            path="/knowledge-graph"
            element={
              <ProtectedRoute>
                <Navbar />
                <KnowledgeGraph />
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <Navbar />
                <Upload />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents"
            element={
              <ProtectedRoute>
                <Navbar />
                <Documents />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents/:id"
            element={
              <ProtectedRoute>
                <Navbar />
                <DocumentView />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tutor"
            element={
              <ProtectedRoute>
                <Navbar />
                <Tutor />
              </ProtectedRoute>
            }
          />
          <Route
            path="/quiz"
            element={
              <ProtectedRoute>
                <Navbar />
                <Quiz />
              </ProtectedRoute>
            }
          />
          <Route
            path="/flashcards"
            element={
              <ProtectedRoute>
                <Navbar />
                <Flashcards />
              </ProtectedRoute>
            }
          />
          <Route
            path="/library"
            element={
              <ProtectedRoute>
                <Navbar />
                <Library />
              </ProtectedRoute>
            }
          />
          <Route
            path="/library/:qualificationSlug"
            element={
              <ProtectedRoute>
                <Navbar />
                <LibraryQualification />
              </ProtectedRoute>
            }
          />
          <Route
            path="/library/:qualificationSlug/:subjectSlug"
            element={
              <ProtectedRoute>
                <Navbar />
                <LibrarySubject />
              </ProtectedRoute>
            }
          />
          <Route
            path="/library/:qualificationSlug/:subjectSlug/:topicSlug"
            element={
              <ProtectedRoute>
                <Navbar />
                <LibraryTopic />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/library-editor"
            element={
              <ProtectedRoute>
                <Navbar />
                <LibraryAdminEditor />
              </ProtectedRoute>
            }
          />
          <Route
            path="/notes"
            element={
              <ProtectedRoute>
                <Navbar />
                <Notes />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Navbar />
                <Settings />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
