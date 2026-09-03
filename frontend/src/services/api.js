import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const api = axios.create({
  baseURL: API,
  withCredentials: true,
});

export const documentService = {
  upload: (formData) => api.post('/documents/upload', formData),
  list: () => api.get('/documents'),
  get: (id) => api.get(`/documents/${id}`),
  getFile: (id) => api.get(`/documents/${id}/file`, { responseType: 'blob' }),
  delete: (id) => api.delete(`/documents/${id}`),
};

export const aiService = {
  generateSummary: (documentId, summaryType = 'detailed') =>
    api.post('/ai/summary', { document_id: documentId, summary_type: summaryType }),
  askTutor: (documentId, question, difficultyMode = 'intermediate', sessionId = null) =>
    api.post('/ai/tutor', { document_id: documentId, question, difficulty_mode: difficultyMode, session_id: sessionId }, {
      responseType: 'text',
    }),
  generateQuiz: (documentIds, questionTypes, difficulty = 'medium', numQuestions = 10) =>
    api.post('/ai/quiz', { document_ids: documentIds, question_types: questionTypes, difficulty, num_questions: numQuestions }),
  generateFlashcards: (documentId) => api.post('/ai/flashcards', { document_id: documentId }),
  generateStudyPlan: (examDates, dailyStudyTime) =>
    api.post('/ai/study-plan', { exam_dates: examDates, daily_study_time: dailyStudyTime }),
};

export const progressService = {
  getStats: () => api.get('/progress/stats'),
  logActivity: (activityData) => api.post('/progress/log-activity', activityData),
};

export const dashboardService = {
  get: () => api.get('/dashboard'),
  getCurrentStudyPlan: () => api.get('/study-plan/current'),
};

export const flashcardService = {
  list: () => api.get('/flashcards'),
};

export const notesService = {
  list: () => api.get('/notes'),
  get: (id) => api.get(`/notes/${id}`),
  create: (note) => api.post('/notes', note),
  update: (id, note) => api.put(`/notes/${id}`, note),
  delete: (id) => api.delete(`/notes/${id}`),
};

export default api;
