import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const api = axios.create({
  baseURL: API,
  withCredentials: true,
});

function ensureArray(value, name) {
  if (!Array.isArray(value)) {
    throw new Error(`Unexpected ${name} response: expected array`);
  }
  return value;
}

function ensureQuizShape(obj) {
  if (!obj || typeof obj !== 'object') throw new Error('Unexpected quiz response');
  if (!obj.quiz_data || !Array.isArray(obj.quiz_data.questions)) throw new Error('Quiz response missing questions array');
  return obj;
}

export const documentService = {
  upload: (formData) => api.post('/documents/upload', formData),
  list: async () => {
    const resp = await api.get('/documents');
    ensureArray(resp.data, 'documents');
    return resp;
  },
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
  generateQuiz: async (documentIds, questionTypes, difficulty = 'medium', numQuestions = 10) => {
    const resp = await api.post('/ai/quiz', { document_ids: documentIds, question_types: questionTypes, difficulty, num_questions: numQuestions });
    ensureQuizShape(resp.data);
    return resp;
  },
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
  list: async () => {
    const resp = await api.get('/flashcards');
    ensureArray(resp.data, 'flashcards');
    return resp;
  },
};

export const notesService = {
  list: async () => {
    const resp = await api.get('/notes');
    ensureArray(resp.data, 'notes');
    return resp;
  },
  get: (id) => api.get(`/notes/${id}`),
  create: (note) => api.post('/notes', note),
  update: (id, note) => api.put(`/notes/${id}`, note),
  delete: (id) => api.delete(`/notes/${id}`),
};

export default api;
