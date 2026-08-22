import type { ReactElement } from 'react'

export type IconName = 'home' | 'file' | 'chart' | 'brain' | 'folder' | 'search' | 'arrow' | 'arrowLeft' | 'check' | 'alert' | 'info' | 'bank' | 'download' | 'x' | 'user' | 'droplet' | 'zap' | 'calendar' | 'trendUp' | 'trendDown' | 'trendFlat' | 'shield' | 'target' | 'database' | 'pie' | 'building' | 'chartUp' | 'clock' | 'list' | 'bars' | 'clipboard'

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  const shapes: Record<IconName, ReactElement> = {
    home: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    file: <><path d="M6 3h8l4 4v14H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/><path d="M14 3v5h5M8 13h8M8 17h5"/></>,
    chart: <><path d="M4 19V5M4 19h17"/><path d="m7 15 4-4 3 2 5-6"/></>,
    brain: <><path d="M9.6 4.5A3.1 3.1 0 0 0 4.5 7a3.8 3.8 0 0 0 .5 7.1 3.2 3.2 0 0 0 5.2 2.4M14.4 4.5A3.1 3.1 0 0 1 19.5 7a3.8 3.8 0 0 1-.5 7.1 3.2 3.2 0 0 1-5.2 2.4M12 4v16M8 9c1.5 0 2.7.6 4 1.8M16 9c-1.5 0-2.7.6-4 1.8"/></>,
    folder: <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>, search: <><circle cx="11" cy="11" r="6"/><path d="m16 16 4 4"/></>, arrow: <><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></>, check: <path d="m5 12 4.2 4.2L19 6.5"/>, alert: <><path d="M12 3 3 20h18Z"/><path d="M12 9v4M12 17h.01"/></>, bank: <><path d="m3 10 9-6 9 6M5 10v8M9 10v8M15 10v8M19 10v8M3 20h18"/></>, download: <><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></>, x: <path d="M6 6l12 12M18 6L6 18"/>, arrowLeft: <><path d="M19 12H5"/><path d="m11 18-6-6 6-6"/></>, info: <><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.01"/></>, user: <><rect x="4" y="4" width="16" height="16" rx="3"/><circle cx="12" cy="10.5" r="2.5"/><path d="M7 18c1-2.5 2.8-3.5 5-3.5s4 1 5 3.5"/></>,
    droplet: <path d="M12 2c-4.2 5-7 9.2-7 13a7 7 0 0 0 14 0c0-3.8-2.8-8-7-13Z"/>,
    zap: <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/></>,
    trendUp: <><path d="m4 16 6-6 4 4 6-7"/><path d="M15 7h5v5"/></>,
    trendDown: <><path d="m4 8 6 6 4-4 6 7"/><path d="M15 17h5v-5"/></>,
    trendFlat: <path d="M5 12h14"/>,
    shield: <><path d="M12 3 20 6v5c0 5-3.4 8.6-8 10-4.6-1.4-8-5-8-10V6Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></>,
    target: <><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></>,
    database: <><ellipse cx="12" cy="5" rx="7" ry="3"/><path d="M5 5v7c0 1.7 3.1 3 7 3s7-1.3 7-3V5M5 12v7c0 1.7 3.1 3 7 3s7-1.3 7-3v-7"/></>,
    pie: <><path d="M12 3v9h9"/><path d="M20.5 15A8.5 8.5 0 1 1 9 3.5"/></>,
    building: <><rect x="3" y="6" width="8.5" height="15" rx="1.2"/><path d="M11.5 10.5h7.3a1.2 1.2 0 0 1 1.2 1.2V21"/><path d="M6 10h2.5M6 13.5h2.5M6 17h2.5M14.5 14.5h2.5M14.5 18h2.5"/><path d="M2 21h20"/></>,
    chartUp: <><path d="M4 21v-4M10 21v-6.5M16 21v-9"/><path d="m5 9.5 5-4 3 2 6.5-5.5"/><path d="M15 2h4.5v4.5"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7.2V12l3.3 2"/></>,
    list: <><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h.01M8 12h.01M8 16h.01M11.5 8H16M11.5 12H16M11.5 16H16"/></>,
    bars: <><path d="M4 20V13M9.3 20V8M14.7 20v-6M20 20V4"/></>,
    clipboard: <><rect x="4" y="5" width="16" height="16" rx="2"/><path d="M9 5V3.6c0-.3.3-.6.6-.6h4.8c.3 0 .6.3.6.6V5"/><path d="m8.6 13 2.2 2.2 4.6-4.6"/></>,
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{shapes[name]}</svg>
}
