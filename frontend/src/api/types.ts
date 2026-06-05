export type Role = "educator" | "student" | "admin";

export type OutputFormat =
  | "adhd_gamified"
  | "dyslexia_audio"
  | "asd_structured"
  | "blended";

export type ReviewStatus = "pending" | "approved" | "rejected" | "auto_approved";

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: Role;
  institution_id: string | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface DocumentOut {
  id: string;
  file_name: string;
  file_type: string;
  parse_status: string;
  page_count: number | null;
  created_at: string;
}

export interface DocumentStatus {
  document_id: string;
  parse_status: string;
  parse_error: string | null;
  atom_count: number;
  estimated_transform_minutes: number;
}

export interface ProfileWeights {
  adhd_weight: number;
  dyslexia_weight: number;
  asd_weight: number;
  profile_version: number;
  calibration_source: string;
  last_calibrated_at: string;
}

export interface QuizQuestion {
  id: string;
  text: string;
}

export type QuizAnswer = "never" | "sometimes" | "often" | "always";

export interface TransformedAtom {
  id: string;
  atom_id: string;
  sequence_index: number | null;
  output_format: OutputFormat;
  transformed_text: string;
  audio_script: string | null;
  review_status: ReviewStatus;
}

export interface StudentContent {
  document_id: string;
  student_id: string;
  profile_snapshot: Record<string, number>;
  atoms: TransformedAtom[];
}

export interface ReviewQueueItem {
  transformed_atom_id: string;
  atom_id: string;
  output_format: OutputFormat;
  review_status: ReviewStatus;
  atom_preview: string;
  transform_preview: string;
  file_name: string;
  created_at: string;
}

export interface ReviewQueue {
  items: ReviewQueueItem[];
  total: number;
  page: number;
}

export interface Session {
  id: string;
  document_id: string;
  started_at: string;
  ended_at: string | null;
  total_atoms: number | null;
  atoms_completed: number;
}
