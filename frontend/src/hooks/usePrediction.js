/**
 * usePrediction — async polling hook for the multi-food inference pipeline.
 *
 * Usage:
 *   const { submit, status, result, error } = usePrediction();
 *   await submit(imageFile);
 */

import { useState, useRef, useCallback } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const POLL_INTERVAL_MS = 1500;
const MAX_POLLS = 40; // 60 seconds max

export function usePrediction() {
  const [status, setStatus] = useState(null); // queued | processing | done | failed
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const pollTimer = useRef(null);
  const pollCount = useRef(0);

  const _stopPolling = () => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current);
      pollTimer.current = null;
    }
  };

  const _poll = useCallback(async (jobId, token) => {
    pollCount.current += 1;
    if (pollCount.current > MAX_POLLS) {
      _stopPolling();
      setStatus("failed");
      setError("Inference timed out. Please try again.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/predict/status/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setStatus(data.status);

      if (data.status === "done") {
        _stopPolling();
        setResult(data.result);
      } else if (data.status === "failed") {
        _stopPolling();
        setError(data.error || "Inference failed.");
      }
    } catch (err) {
      _stopPolling();
      setError(err.message);
      setStatus("failed");
    }
  }, []);

  const submit = useCallback(
    async (imageFile, token) => {
      // Reset state
      setStatus("queued");
      setResult(null);
      setError(null);
      pollCount.current = 0;
      _stopPolling();

      const formData = new FormData();
      formData.append("file", imageFile);

      const res = await fetch(`${API_BASE}/predict/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        const text = await res.text();
        setStatus("failed");
        setError(text);
        return;
      }

      const { job_id } = await res.json();
      // Start polling
      pollTimer.current = setInterval(
        () => _poll(job_id, token),
        POLL_INTERVAL_MS,
      );
    },
    [_poll],
  );

  return { submit, status, result, error };
}
