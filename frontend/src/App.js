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
import Upload from './pages/Upload';
import Documents from './pages/Documents';
import DocumentView from './pages/DocumentView';
import Tutor from './pages/Tutor';
import Quiz from './pages/Quiz';
import Flashcards from './pages/Flashcards';
import Notes from './pages/Notes';
import Settings from './pages/Settings';
import Library from './pages/Library';
import LibraryQualification from './pages/LibraryQualification';
import LibrarySubject from './pages/LibrarySubject';
import LibraryTopic from './pages/LibraryTopic';
import './App.css';

const GlobalNotesWidget = () => {
  const { user } = useAuth();
  if (!user) return null;
  return <NotesWidget />;
};

function App() {
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
