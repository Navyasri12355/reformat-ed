import { apiClient } from "./client";
import type {
  DocumentOut,
  DocumentStatus,
  ProfileWeights,
  QuizAnswer,
  QuizQuestion,
  ReviewQueue,
  Session,
  StudentContent,
  TokenPair,
  User,
} from "./types";

export const authApi = {
  async register(body: {
    email: string;
    password: string;
    display_name: string;
    role: "educator" | "student";
  }): Promise<TokenPair> {
    return (await apiClient.post("/auth/register", body)).data;
  },
  async login(email: string, password: string): Promise<TokenPair> {
    return (await apiClient.post("/auth/login", { email, password })).data;
  },
  async me(): Promise<User> {
    return (await apiClient.get("/auth/me")).data;
  },
};

export const documentsApi = {
  async list(): Promise<DocumentOut[]> {
    return (await apiClient.get("/documents")).data;
  },
  async upload(file: File, subject?: string, gradeLevel?: string) {
    const form = new FormData();
    form.append("file", file);
    if (subject) form.append("subject", subject);
    if (gradeLevel) form.append("grade_level", gradeLevel);
    return (await apiClient.post("/documents", form)).data as {
      document_id: string;
      task_id: string;
      poll_url: string;
    };
  },
  async status(documentId: string): Promise<DocumentStatus> {
    return (await apiClient.get(`/documents/${documentId}/status`)).data;
  },
};

export const profilesApi = {
  async quizQuestions(): Promise<QuizQuestion[]> {
    return (await apiClient.get("/profiles/quiz")).data;
  },
  async submitQuiz(studentId: string, answers: Record<string, QuizAnswer>): Promise<ProfileWeights> {
    return (await apiClient.post(`/profiles/${studentId}/quiz`, { answers })).data;
  },
  async get(studentId: string): Promise<ProfileWeights> {
    return (await apiClient.get(`/profiles/${studentId}`)).data;
  },
  async update(studentId: string, weights: { adhd_weight: number; dyslexia_weight: number; asd_weight: number; snapshot_reason?: string }): Promise<ProfileWeights> {
    return (await apiClient.put(`/profiles/${studentId}`, { ...weights, calibration_source: "educator" })).data;
  },
};

export const transformsApi = {
  async request(documentId: string, studentId?: string) {
    return (await apiClient.post("/transforms", { document_id: documentId, student_id: studentId }))
      .data;
  },
  async studentContent(documentId: string, studentId?: string): Promise<StudentContent> {
    const params = new URLSearchParams({ document_id: documentId });
    if (studentId) params.set("student_id", studentId);
    return (await apiClient.get(`/transforms?${params.toString()}`)).data;
  },
  async reviewQueue(page = 1): Promise<ReviewQueue> {
    return (await apiClient.get(`/transforms/review-queue?page=${page}`)).data;
  },
  async review(transformedAtomId: string, action: "approve" | "reject", editedText?: string, rejectionNote?: string) {
    return (
      await apiClient.post(`/transforms/${transformedAtomId}/review`, {
        action,
        edited_text: editedText,
        rejection_note: rejectionNote,
      })
    ).data;
  },
};

export const sessionsApi = {
  async start(documentId: string): Promise<Session> {
    return (await apiClient.post("/sessions", { document_id: documentId })).data;
  },
  async event(
    sessionId: string,
    body: {
      atom_id: string;
      transformed_atom_id?: string;
      event_type: string;
      time_on_atom_ms?: number;
      retry_count?: number;
      payload?: Record<string, unknown>;
    },
  ): Promise<void> {
    await apiClient.post(`/sessions/${sessionId}/events`, body);
  },
  async end(sessionId: string): Promise<Session> {
    return (await apiClient.post(`/sessions/${sessionId}/end`)).data;
  },
  async recalibrate(): Promise<{ recalibrated: boolean }> {
    return (await apiClient.post("/sessions/recalibrate")).data;
  },
};
