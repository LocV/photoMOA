export interface AnalysisResult {
  success: boolean;
  id: string;
  shot_count: number;
  moa_value: number | null;
  annotated_image: string; // Base64 encoded image
  shots: number[][]; // Array of [x, y] coordinates
  error?: string;
}

export interface HistoryEntry {
  id: string;
  filename: string;
  annotated_filename: string;
  upload_time: string;
  shot_count: number;
  moa_value: number | null;
  shots: number[][];
}

export interface UploadResponse {
  success: boolean;
  id: string;
  shot_count: number;
  moa_value: number | null;
  annotated_image: string;
  shots: number[][];
  error?: string;
}
