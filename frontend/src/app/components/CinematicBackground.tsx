import { motion } from "motion/react";
import { useEffect, useState } from "react";

export function CinematicBackground() {
  const [mousePos, setMousePos] = useState({ x: 0.5, y: 0.5 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({
        x: e.clientX / window.innerWidth,
        y: e.clientY / window.innerHeight,
      });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  return (
    <div className="fixed inset-0 overflow-hidden -z-10">
      {/* Deep space base */}
      <div 
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse at center, #0a0f1a 0%, #000000 100%)',
        }}
      />

      {/* Massive animated light beams from edges */}
      <motion.div
        className="absolute inset-0"
        style={{
          background: `conic-gradient(from ${mousePos.x * 360}deg at 50% 50%, 
            transparent 0deg,
            rgba(6, 182, 212, 0.15) 60deg,
            rgba(59, 130, 246, 0.2) 120deg,
            transparent 180deg,
            rgba(147, 51, 234, 0.15) 240deg,
            rgba(168, 85, 247, 0.2) 300deg,
            transparent 360deg)`,
        }}
        animate={{
          rotate: [0, 360],
        }}
        transition={{
          duration: 60,
          repeat: Infinity,
          ease: "linear",
        }}
      />

      {/* Giant pulsing energy rings */}
      {[...Array(5)].map((_, i) => (
        <motion.div
          key={`ring-${i}`}
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full"
          style={{
            width: `${200 + i * 300}px`,
            height: `${200 + i * 300}px`,
            border: '1px solid',
            borderColor: i % 2 === 0 ? 'rgba(6, 182, 212, 0.1)' : 'rgba(168, 85, 247, 0.1)',
            boxShadow: i % 2 === 0 
              ? '0 0 30px rgba(6, 182, 212, 0.2)' 
              : '0 0 30px rgba(168, 85, 247, 0.2)',
          }}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.2, 0.5, 0.2],
            rotate: i % 2 === 0 ? [0, 360] : [360, 0],
          }}
          transition={{
            duration: 15 + i * 3,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 0.5,
          }}
        />
      ))}

      {/* Floating holographic particles - increased count */}
      {[...Array(100)].map((_, i) => {
        const size = Math.random() * 3 + 1;
        const color = i % 3 === 0 
          ? 'rgba(6, 182, 212, 0.8)' 
          : i % 3 === 1 
          ? 'rgba(168, 85, 247, 0.8)'
          : 'rgba(59, 130, 246, 0.8)';
        
        return (
          <motion.div
            key={`particle-${i}`}
            className="absolute rounded-full"
            style={{
              width: `${size}px`,
              height: `${size}px`,
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              background: color,
              boxShadow: `0 0 ${size * 4}px ${color}`,
            }}
            animate={{
              x: [0, (Math.random() - 0.5) * 100],
              y: [0, (Math.random() - 0.5) * 100],
              opacity: [0, 1, 0],
              scale: [0, 1.5, 0],
            }}
            transition={{
              duration: 5 + Math.random() * 10,
              repeat: Infinity,
              delay: Math.random() * 5,
              ease: "easeInOut",
            }}
          />
        );
      })}

      {/* Volumetric light rays */}
      {[...Array(12)].map((_, i) => (
        <motion.div
          key={`ray-${i}`}
          className="absolute left-1/2 top-1/2 origin-left"
          style={{
            width: '150vh',
            height: '2px',
            background: `linear-gradient(90deg, 
              ${i % 2 === 0 ? 'rgba(6, 182, 212, 0.3)' : 'rgba(168, 85, 247, 0.3)'} 0%, 
              transparent 100%)`,
            transform: `rotate(${(360 / 12) * i}deg)`,
            filter: 'blur(2px)',
          }}
          animate={{
            opacity: [0.2, 0.6, 0.2],
            scaleX: [0.8, 1.2, 0.8],
          }}
          transition={{
            duration: 4 + i * 0.3,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 0.2,
          }}
        />
      ))}

      {/* Energy plasma clouds */}
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            'radial-gradient(circle at 20% 30%, rgba(6, 182, 212, 0.2) 0%, transparent 40%)',
            'radial-gradient(circle at 80% 70%, rgba(168, 85, 247, 0.2) 0%, transparent 40%)',
            'radial-gradient(circle at 40% 60%, rgba(59, 130, 246, 0.2) 0%, transparent 40%)',
            'radial-gradient(circle at 20% 30%, rgba(6, 182, 212, 0.2) 0%, transparent 40%)',
          ],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Scanning arc effect */}
      <motion.div
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[1200px] h-[1200px]"
        style={{
          background: 'conic-gradient(from 0deg, transparent 0deg, rgba(6, 182, 212, 0.3) 30deg, transparent 60deg)',
          borderRadius: '50%',
          filter: 'blur(20px)',
        }}
        animate={{
          rotate: [0, 360],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "linear",
        }}
      />

      {/* Holographic grid lines - radial */}
      <svg className="absolute inset-0 w-full h-full opacity-20" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="radial-grid" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
            <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(6, 182, 212, 0.3)" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#radial-grid)" />
        {/* Radial lines */}
        {[...Array(24)].map((_, i) => {
          const angle = (360 / 24) * i;
          const rad = (angle * Math.PI) / 180;
          const x2 = 50 + Math.cos(rad) * 200;
          const y2 = 50 + Math.sin(rad) * 200;
          return (
            <line
              key={i}
              x1="50%"
              y1="50%"
              x2={`${x2}%`}
              y2={`${y2}%`}
              stroke="rgba(6, 182, 212, 0.1)"
              strokeWidth="0.5"
            />
          );
        })}
        {/* Concentric circles */}
        {[...Array(8)].map((_, i) => (
          <circle
            key={i}
            cx="50%"
            cy="50%"
            r={`${10 + i * 8}%`}
            fill="none"
            stroke="rgba(168, 85, 247, 0.1)"
            strokeWidth="0.5"
          />
        ))}
      </svg>

      {/* Nebula effect */}
      <motion.div
        className="absolute inset-0 opacity-30"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(6, 182, 212, 0.1) 0%, rgba(168, 85, 247, 0.1) 50%, transparent 100%)',
          filter: 'blur(60px)',
        }}
        animate={{
          scale: [1, 1.3, 1],
          rotate: [0, 180, 360],
        }}
        transition={{
          duration: 40,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Data stream particles */}
      {[...Array(30)].map((_, i) => (
        <motion.div
          key={`stream-${i}`}
          className="absolute w-20 h-0.5"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            background: 'linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.8), transparent)',
          }}
          animate={{
            x: [(Math.random() - 0.5) * 400, (Math.random() - 0.5) * -400],
            y: [(Math.random() - 0.5) * 400, (Math.random() - 0.5) * -400],
            opacity: [0, 1, 0],
            rotate: [Math.random() * 360, Math.random() * 360 + 180],
          }}
          transition={{
            duration: 3 + Math.random() * 2,
            repeat: Infinity,
            delay: Math.random() * 3,
            ease: "easeInOut",
          }}
        />
      ))}

      {/* Lens flare effect */}
      <motion.div
        className="absolute w-96 h-96 rounded-full"
        style={{
          left: `${mousePos.x * 100}%`,
          top: `${mousePos.y * 100}%`,
          transform: 'translate(-50%, -50%)',
          background: 'radial-gradient(circle, rgba(6, 182, 212, 0.2) 0%, transparent 70%)',
          filter: 'blur(40px)',
          pointerEvents: 'none',
        }}
        animate={{
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Edge glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0" style={{
          boxShadow: 'inset 0 0 200px rgba(6, 182, 212, 0.1), inset 0 0 100px rgba(168, 85, 247, 0.1)',
        }} />
      </div>
    </div>
  );
}
