import axios from 'axios';
import { BACKEND_BASE_URL, BACKEND_URL_ERROR } from '../config/backend';

const API = `${BACKEND_BASE_URL}/api`;

const api = axios.create({
  baseURL: API,
  withCredentials: true,
});

if (BACKEND_URL_ERROR) {
  // Fail fast and loudly: never let a request silently target the user's own machine.
  api.interceptors.request.use(() => Promise.reject(new Error(BACKEND_URL_ERROR)));
}

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

export const authService = {
  requestPasswordReset: (email) => api.post('/auth/password-reset/request', { email }),
  confirmPasswordReset: (email, token, newPassword) => api.post('/auth/password-reset/confirm', {
    email,
    token,
    new_password: newPassword,
  }),
};

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
  generateMockExam: (payload) => api.post('/ai/mock-exam', payload),
  submitMockExam: (payload) => api.post('/mock-exams/submit', payload),
  generateFlashcards: (documentId) => api.post('/ai/flashcards', { document_id: documentId }),
  generateStudyPlan: (payloadOrExamDates, dailyStudyTime) => {
    const payload = Array.isArray(payloadOrExamDates)
      ? { exam_dates: payloadOrExamDates, daily_study_time: dailyStudyTime ?? 60 }
      : (payloadOrExamDates || {});
    return api.post('/ai/study-plan', payload);
  },
};

export const progressService = {
  getStats: () => api.get('/progress/stats'),
  getSummary: () => api.get('/progress/summary'),
  listSessions: () => api.get('/progress/sessions'),
  logActivity: (activityData) => api.post('/progress/log-activity', activityData),
  setDailyGoal: (dailyGoalMinutes) => api.put('/progress/daily-goal', { daily_goal_minutes: dailyGoalMinutes }),
};

export const dashboardService = {
  get: () => api.get('/dashboard'),
  getCurrentStudyPlan: () => api.get('/study-plan/current'),
  getAnalytics: () => api.get('/analytics/overview'),
};

export const knowledgeGraphService = {
  generate: (documentId, subject = '', topic = '') =>
    api.post('/knowledge-graph/generate', { document_id: documentId, subject, topic }),
  list: () => api.get('/knowledge-graph'),
  get: (mapId) => api.get(`/knowledge-graph/${mapId}`),
  saveProgress: (mapId, payload) => api.post(`/knowledge-graph/${mapId}/progress`, payload),
  getProgress: (mapId) => api.get(`/knowledge-graph/${mapId}/progress`),
  assess: (mapId, conceptId, questionType = 'short') =>
    api.post(`/knowledge-graph/${mapId}/assessment`, { concept_id: conceptId, question_type: questionType }),
};

export const flashcardService = {
  list: async () => {
    const resp = await api.get('/flashcards');
    ensureArray(resp.data, 'flashcards');
    return resp;
  },
  get: (id) => api.get(`/flashcards/${id}`),
  create: (payload) => api.post('/flashcards', payload),
  update: (id, payload) => api.put(`/flashcards/${id}`, payload),
  remove: (id) => api.delete(`/flashcards/${id}`),
  addCard: (id, payload) => api.post(`/flashcards/${id}/cards`, payload),
  removeCard: (id, cardIndex) => api.delete(`/flashcards/${id}/cards/${cardIndex}`),
};

export const libraryService = {
  listQualifications: () => api.get('/library/qualifications'),
  getQualification: (slug) => api.get(`/library/qualifications/${slug}`),
  listSubjects: (qualificationSlug) => api.get(`/library/qualifications/${qualificationSlug}/subjects`),
  getSubject: (qualificationSlug, subjectSlug) => api.get(`/library/qualifications/${qualificationSlug}/subjects/${subjectSlug}`),
  getTopic: (qualificationSlug, subjectSlug, topicSlug) => api.get(`/library/qualifications/${qualificationSlug}/subjects/${subjectSlug}/topics/${topicSlug}`),
  getAdminCatalog: () => api.get('/admin/library/catalog'),
  saveQualification: (payload) => api.post('/admin/library/qualifications', payload),
  saveSubject: (payload) => api.post('/admin/library/subjects', payload),
  saveTopic: (payload) => api.post('/admin/library/topics', payload),
  saveResource: (payload) => api.post('/admin/library/resources', payload),
  deleteQualification: (slug) => api.delete(`/admin/library/qualifications/${slug}`),
  deleteSubject: (slug) => api.delete(`/admin/library/subjects/${slug}`),
  deleteTopic: (slug) => api.delete(`/admin/library/topics/${slug}`),
  deleteResource: (slug) => api.delete(`/admin/library/resources/${slug}`),
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
