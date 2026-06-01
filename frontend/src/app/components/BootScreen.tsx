import { motion } from "motion/react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { CinematicBackground } from "./CinematicBackground";
import { CheckCircle2 } from "lucide-react";
import { audioSystem } from "./AudioSystem";

const bootSequence = [
  { text: "Initializing NEXUS AI Core...", delay: 0 },
  { text: "Loading neural network modules", delay: 800 },
  { text: "Connecting to MongoDB Cluster", delay: 1600 },
  { text: "Establishing secure data stream", delay: 2400 },
  { text: "Loading predictive model v3.7.2", delay: 3200 },
  { text: "Streaming telemetry channels", delay: 4000 },
  { text: "Initializing sensor network", delay: 4800 },
  { text: "Calibrating AI inference engine", delay: 5600 },
  { text: "System ready", delay: 6400 },
];

export function BootScreen() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Play initial boot sound
    audioSystem.playSystemEvent();

    bootSequence.forEach((step, index) => {
      setTimeout(() => {
        setCurrentStep(index + 1);
        setProgress(((index + 1) / bootSequence.length) * 100);
        
        // Play sound for each step
        if (index < bootSequence.length - 1) {
          audioSystem.playDataStream();
        } else {
          // Final step - play mode switch sound
          audioSystem.playModeSwitch();
        }
      }, step.delay);
    });

    setTimeout(() => {
      navigate("/dashboard");
    }, 7500);
  }, [navigate]);

  return (
    <div className="relative size-full flex items-center justify-center overflow-hidden">
      <CinematicBackground />

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-3xl mx-4"
      >
        {/* Terminal-style boot screen */}
        <div className="backdrop-blur-xl bg-black/40 border border-cyan-500/30 rounded-2xl p-8 shadow-2xl">
          {/* Header */}
          <div className="mb-8">
            <motion.div
              className="flex items-center gap-3 mb-4"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <div className="w-3 h-3 rounded-full bg-green-400 shadow-lg shadow-green-400/50 animate-pulse" />
              <h2 className="text-2xl font-bold text-white">
                NEXUS AI SYSTEM INITIALIZATION
              </h2>
            </motion.div>
            <div className="h-px bg-gradient-to-r from-cyan-500/50 via-purple-500/50 to-transparent" />
          </div>

          {/* Boot logs */}
          <div className="space-y-3 mb-8 font-mono text-sm min-h-[300px]">
            {bootSequence.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{
                  opacity: index < currentStep ? 1 : 0,
                  x: index < currentStep ? 0 : -10,
                }}
                transition={{ duration: 0.3 }}
                className="flex items-center gap-3"
              >
                {index < currentStep - 1 ? (
                  <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
                ) : index === currentStep - 1 ? (
                  <motion.div
                    className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full flex-shrink-0"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  />
                ) : (
                  <div className="w-4 h-4 flex-shrink-0" />
                )}
                <span
                  className={`${
                    index < currentStep - 1
                      ? "text-green-400"
                      : index === currentStep - 1
                      ? "text-cyan-400"
                      : "text-gray-600"
                  }`}
                >
                  [{new Date().toLocaleTimeString()}] {step.text}
                  {index === currentStep - 1 && (
                    <motion.span
                      animate={{ opacity: [1, 0] }}
                      transition={{ duration: 0.5, repeat: Infinity }}
                    >
                      _
                    </motion.span>
                  )}
                </span>
              </motion.div>
            ))}
          </div>

          {/* Progress bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">System Boot Progress</span>
              <span className="text-cyan-400 font-mono">{Math.round(progress)}%</span>
            </div>
            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/50"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>

          {/* Scanning animation */}
          <motion.div
            className="mt-6 p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg"
            animate={{
              borderColor: [
                "rgba(6, 182, 212, 0.3)",
                "rgba(6, 182, 212, 0.6)",
                "rgba(6, 182, 212, 0.3)",
              ],
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <div className="flex items-center justify-center gap-2 text-cyan-400 text-sm">
              <motion.div
                className="flex gap-1"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                <span className="w-1 h-1 bg-cyan-400 rounded-full" />
                <span className="w-1 h-1 bg-cyan-400 rounded-full" />
                <span className="w-1 h-1 bg-cyan-400 rounded-full" />
              </motion.div>
              <span>Establishing secure connection</span>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}