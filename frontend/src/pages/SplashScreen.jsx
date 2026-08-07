import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./SplashScreen.css";

// Petits ratios financiers qui défilent en fond, pour évoquer l'analyse de
// données en cours pendant que le logo se dessine — purement décoratif,
// aucune valeur réelle n'est calculée ici.
const TICKER_VALUES = [
  "Current Ratio  1.93",
  "Altman Z''  3.73",
  "ROE  10.28%",
  "DSCR  1.17",
  "DSO  542.7j",
  "Autonomie Fin.  34.45%",
  "Marge nette  16.29%",
  "Asset Turnover  0.22",
];

function ParticleField() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let animationFrameId;
    let particles = [];
    let width = 0;
    let height = 0;

    const NUM_PARTICLES = 70;
    const LINK_DISTANCE = 130;

    function resize() {
      width = canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      height = canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    }

    function initParticles() {
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      particles = Array.from({ length: NUM_PARTICLES }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.25,
      }));
    }

    function step() {
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      ctx.clearRect(0, 0, w, h);

      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
      }

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < LINK_DISTANCE) {
            ctx.strokeStyle = `rgba(235, 51, 73, ${0.14 * (1 - dist / LINK_DISTANCE)})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      for (const p of particles) {
        ctx.fillStyle = "rgba(255, 107, 122, 0.6)";
        ctx.beginPath();
        ctx.arc(p.x, p.y, 1.6, 0, Math.PI * 2);
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(step);
    }

    resize();
    initParticles();
    step();

    window.addEventListener("resize", () => {
      resize();
      initParticles();
    });

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={canvasRef} className="splash-canvas" />;
}

export default function SplashScreen() {
  const navigate = useNavigate();
  const [ready, setReady] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [tickerIndex, setTickerIndex] = useState(0);

  useEffect(() => {
    const readyTimer = setTimeout(() => setReady(true), 2600);
    return () => clearTimeout(readyTimer);
  }, []);

  useEffect(() => {
    const tickerTimer = setInterval(() => {
      setTickerIndex((i) => (i + 1) % TICKER_VALUES.length);
    }, 1100);
    return () => clearInterval(tickerTimer);
  }, []);

  function enter() {
    if (leaving) return;
    setLeaving(true);
    setTimeout(() => navigate("/nouvelle-analyse"), 420);
  }

  return (
    <div
      className={`splash ${ready ? "splash--ready" : ""} ${leaving ? "splash--leaving" : ""}`}
      onClick={ready ? enter : undefined}
    >
      <ParticleField />

      <div className="splash-vignette" />

      <div className="splash-content">
        <div className="splash-mark">
          <svg viewBox="0 0 120 120" className="splash-mark__svg">
            <polygon
              points="60,6 108,33 108,87 60,114 12,87 12,33"
              className="splash-mark__hex"
            />
            <path d="M35 62 L52 78 L86 40" className="splash-mark__check" />
          </svg>
          <div className="splash-mark__glow" />
        </div>

        <h1 className="splash-title">
          <span>Credit</span> <span className="splash-title__accent">Risk</span>{" "}
          <span>Intelligence</span>
        </h1>

        <p className="splash-tagline">Analyse financière augmentée par l'IA — de la donnée brute à la décision</p>

        <div className="splash-ticker">
          <span key={tickerIndex} className="splash-ticker__value">
            {TICKER_VALUES[tickerIndex]}
          </span>
        </div>

        <div className="splash-progress">
          <div className="splash-progress__bar" />
        </div>

        <button
          type="button"
          className={`splash-enter ${ready ? "splash-enter--visible" : ""}`}
          onClick={enter}
        >
          Entrer dans la plateforme
          <span className="splash-enter__arrow">→</span>
        </button>

        <p className="splash-brand">Devoteam Africa</p>
      </div>
    </div>
  );
}
