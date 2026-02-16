'use client';

import { useEffect, useState } from 'react';

const STATS_URL = 'https://api.prodway.ai/prodway/stats';

export default function StatsSection() {
  const [stats, setStats] = useState<{ forms_filled: number; sows_sent: number } | null>(null);

  useEffect(() => {
    fetch(STATS_URL)
      .then((res) => res.json())
      .then((data) => setStats({ forms_filled: data.forms_filled ?? 0, sows_sent: data.sows_sent ?? 0 }))
      .catch(() => setStats(null));
  }, []);

  const formsLabel = stats ? (stats.forms_filled > 0 ? stats.forms_filled.toLocaleString() : '—') : '…';
  const sowsLabel = stats ? (stats.sows_sent > 0 ? stats.sows_sent.toLocaleString() : '—') : '…';

  return (
    <section className="py-14 border-y border-[#262626]">
      <div className="max-w-3xl mx-auto px-5">
        <div className="grid grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-3xl md:text-4xl font-bold tracking-tight gradient-text">{formsLabel}</div>
            <div className="text-[13px] font-medium text-[#a3a3a3] mt-1.5">Forms filled</div>
          </div>
          <div>
            <div className="text-3xl md:text-4xl font-bold tracking-tight gradient-text">{sowsLabel}</div>
            <div className="text-[13px] font-medium text-[#a3a3a3] mt-1.5">SOWs sent</div>
          </div>
          <div>
            <div className="text-3xl md:text-4xl font-bold tracking-tight gradient-text">60s</div>
            <div className="text-[13px] font-medium text-[#a3a3a3] mt-1.5">Request to SOW</div>
          </div>
        </div>
      </div>
    </section>
  );
}
