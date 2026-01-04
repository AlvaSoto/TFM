import React from 'react';
import { Sparkles } from "lucide-react";
import { motion } from "framer-motion";

const AIAdvisorCard = ({ report }) => {
  if (!report) return null;

  // Función simple para formatear negritas de markdown (**texto**)
  const formatText = (text) => {
    return text.split('\n').map((line, i) => (
      <p key={i} className="mb-2 last:mb-0">
        {line.split('**').map((part, j) => 
          j % 2 === 1 ? <strong key={j} className="font-semibold text-white">{part}</strong> : part
        )}
      </p>
    ));
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative overflow-hidden rounded-2xl ai-gradient p-6 shadow-xl text-white"
    >
      {/* Efectos de fondo */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/10 rounded-full blur-2xl translate-y-1/2 -translate-x-1/2" />
      
      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-4 border-b border-white/20 pb-4">
          <div className="flex items-center justify-center w-10 h-10 bg-white/20 rounded-lg backdrop-blur-sm shadow-inner">
            <Sparkles className="w-5 h-5 text-yellow-300" />
          </div>
          <div>
            <h2 className="text-lg font-bold">AI Smart Advisor</h2>
            <p className="text-xs text-white/80">Análisis generado por GPT-4o</p>
          </div>
        </div>

        <div className="text-sm text-white/90 leading-relaxed font-light">
          {formatText(report)}
        </div>
      </div>
    </motion.div>
  );
};

export default AIAdvisorCard;