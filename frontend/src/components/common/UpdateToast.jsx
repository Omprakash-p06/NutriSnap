import React, { useState, useEffect } from "react";
import { useRegisterSW } from "virtual:pwa-register/react";
import { RefreshCw, WifiOff, X } from "lucide-react";

export const UpdateToast = () => {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(r) {
      // Check for updates periodically
      if (r) {
        setInterval(
          () => {
            r.update();
          },
          60 * 60 * 1000,
        ); // 1 hour
      }
    },
    onRegisterError(error) {
      console.error("SW registration error", error);
    },
  });

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return (
    <div className="fixed bottom-4 left-0 right-0 z-50 flex flex-col items-center gap-2 px-4 pointer-events-none">
      {/* Offline Banner */}
      {isOffline && (
        <div className="bg-amber-100 text-amber-800 px-4 py-2 rounded-full shadow-lg flex items-center gap-2 text-sm font-medium border border-amber-200 pointer-events-auto">
          <WifiOff size={16} />
          <span>You are offline. Some features may be limited.</span>
        </div>
      )}

      {/* Update Prompt */}
      {needRefresh && (
        <div className="bg-white px-4 py-3 rounded-xl shadow-xl border border-gray-200 flex items-center gap-4 pointer-events-auto max-w-sm w-full">
          <div className="bg-indigo-100 text-indigo-600 p-2 rounded-full">
            <RefreshCw size={20} />
          </div>
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-gray-900">
              Update available
            </h4>
            <p className="text-xs text-gray-500">
              A new version of NutriSnap is ready.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => updateServiceWorker(true)}
              className="text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 px-3 py-1.5 rounded-lg transition-colors"
            >
              Update
            </button>
            <button
              onClick={() => setNeedRefresh(false)}
              className="text-gray-400 hover:text-gray-600 p-1"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
