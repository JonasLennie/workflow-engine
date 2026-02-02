import { useState, useEffect } from "react";

export default function usePolling(url, intervalMs = 2000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!url) {
      setData(null);
      return;
    }

    let active = true;

    const poll = () => {
      fetch(url)
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .then((d) => active && setData(d))
        .catch((e) => active && setError(e.message));
    };

    poll();
    const id = setInterval(poll, intervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [url, intervalMs]);

  return { data, error };
}
