import React from 'react';
import { Sparkles, Zap } from "lucide-react";
import { motion } from "framer-motion";

const AIAdvisorCard = ({ report }) => {
  if (!report) return null;

  // Función simple para formatear negritas de markdown (**texto**)
  const formatText = (text) => {
    return text.split('\n').map((line, i) => (
      <p key={i} className="mb-3 last:mb-0 leading-relaxed">
        {line.split('**').map((part, j) => 
          j % 2 === 1 ? <strong key={j} className="font-bold text-white drop-shadow-sm">{part}</strong> : part
        )}
      </p>
    ));
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative overflow-hidden rounded-2xl ai-gradient p-8 card-shadow-lg text-white group hover:shadow-2xl transition-shadow duration-300"
    >
      {/* Efectos de fondo mejorados */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:scale-110 transition-transform duration-700" />
      <div className="absolute bottom-0 left-0 w-64 h-64 bg-white/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2 group-hover:scale-110 transition-transform duration-700" />
      
      {/* Partículas flotantes decorativas */}
      <div className="absolute top-10 left-10 w-2 h-2 bg-white/40 rounded-full animate-ping"></div>
      <div className="absolute bottom-20 right-20 w-2 h-2 bg-white/40 rounded-full animate-ping" style={{animationDelay: '1s'}}></div>
      
      <div className="relative z-10">
        {/* Header mejorado */}
        <div className="flex items-center justify-between mb-6 pb-5 border-b border-white/20">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-yellow-300 rounded-xl blur-md opacity-50 animate-pulse"></div>
              <div className="relative flex items-center justify-center w-12 h-12 bg-white/20 rounded-xl backdrop-blur-sm shadow-lg">
                <Sparkles className="w-6 h-6 text-yellow-200" strokeWidth={2.5} />
              </div>
            </div>
            <div>
              <h2 className="text-xl font-bold text-white drop-shadow-md">AI Smart Advisor</h2>
              <p className="text-xs text-white/80 font-medium flex items-center gap-1.5">
                <Zap size={12} className="text-yellow-300" />
                Análisis generado por GPT-4o
              </p>
            </div>
          </div>
          
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-white/10 rounded-lg backdrop-blur-sm border border-white/20">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-xs font-semibold">Activo</span>
          </div>
        </div>

        {/* Contenido del reporte */}
        <div className="text-sm text-white/95 leading-relaxed space-y-2">
          {formatText(report)}
        </div>
        
        {/* Badge inferior */}
        <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-white/70">
          <span className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 bg-white/60 rounded-full"></div>
            Generado en tiempo real
          </span>
          <span className="font-medium">Confianza: Alta</span>
        </div>
      </div>
    </motion.div>
  );
};

export default AIAdvisorCard;