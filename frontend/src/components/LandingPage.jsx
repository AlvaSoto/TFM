import React from 'react';
import { Droplets, Brain, TrendingDown, Shield, Zap, BarChart3, CheckCircle, ArrowRight, Github, Linkedin } from 'lucide-react';
import { motion } from 'framer-motion';

const LandingPage = ({ onEnter }) => {
  const features = [
    {
      icon: Brain,
      title: "Intelligent Leak Detection",
      description: "AI learns your consumption patterns and alerts you instantly when something's wrong",
      color: "from-purple-500 to-purple-600"
    },
    {
      icon: TrendingDown,
      title: "Smart Cost Management",
      description: "Understand your consumption patterns and get predictions of your monthly expenses",
      color: "from-emerald-500 to-emerald-600"
    },
    {
      icon: Shield,
      title: "24/7 Protection",
      description: "Never worry again - continuous monitoring while you sleep, work, or travel",
      color: "from-blue-500 to-blue-600"
    },
    {
      icon: Zap,
      title: "Personalized Advice",
      description: "Get tailored recommendations from AI to optimize your water usage",
      color: "from-amber-500 to-amber-600"
    }
  ];

  const stats = [
    { value: "93.7%", label: "ROC-AUC", description: "Detection Accuracy" },
    { value: "160", label: "Households", description: "Monitored" },
    { value: "180", label: "Days", description: "Continuous Monitoring" },
    { value: "2.7M", label: "Records", description: "Training Dataset" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 text-white overflow-hidden">
      {/* Efectos de fondo animados */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
      </div>

      <div className="relative z-10">
        {/* Header/Nav */}
        <nav className="p-6 flex justify-between items-center max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-blue-500 rounded-2xl blur-md opacity-50"></div>
              <div className="relative bg-gradient-to-br from-blue-500 to-blue-700 p-2.5 rounded-2xl">
                <Droplets size={28} strokeWidth={2.5} />
              </div>
            </div>
            <span className="text-2xl font-bold">Smart Water Monitor</span>
          </div>
          
          <div className="flex gap-4">
            <a href="https://github.com/AlvaSoto/TFM" target="_blank" rel="noopener noreferrer" 
               className="p-2.5 bg-white/10 hover:bg-white/20 rounded-xl transition-colors backdrop-blur-sm">
              <Github size={20} />
            </a>
            <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer"
               className="p-2.5 bg-white/10 hover:bg-white/20 rounded-xl transition-colors backdrop-blur-sm">
              <Linkedin size={20} />
            </a>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="max-w-7xl mx-auto px-6 pt-20 pb-32">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center max-w-4xl mx-auto"
          >
            {/* Main Title */}
            <h1 className="text-6xl md:text-7xl font-black mb-6 leading-tight">
              Intelligent Water Leak
              <span className="block bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
                Detection System
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl md:text-2xl text-slate-300 mb-12 leading-relaxed max-w-3xl mx-auto">
              Real-time monitoring platform powered by Deep Learning to detect anomalies, 
              prevent water waste, and optimize consumption
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
              <button 
                onClick={onEnter}
                className="group relative px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-xl font-bold text-lg transition-all duration-300 shadow-2xl shadow-blue-500/50 hover:shadow-blue-500/70 hover:scale-105 active:scale-95 flex items-center gap-3"
              >
                <span>Access Dashboard</span>
                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
              </button>
              
              <a 
                href="https://github.com/AlvaSoto/TFM" 
                target="_blank" 
                rel="noopener noreferrer"
                className="px-8 py-4 bg-white/10 hover:bg-white/20 backdrop-blur-sm rounded-xl font-bold text-lg transition-all duration-300 border border-white/20 hover:border-white/40"
              >
                View on GitHub
              </a>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
              {stats.map((stat, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + idx * 0.1 }}
                  className="p-6 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 hover:bg-white/10 transition-all"
                >
                  <div className="text-4xl font-black bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent mb-2">
                    {stat.value}
                  </div>
                  <div className="text-lg font-bold mb-1">{stat.label}</div>
                  <div className="text-sm text-slate-400">{stat.description}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </section>

        {/* Features Section */}
        <section className="max-w-7xl mx-auto px-6 pb-32">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold mb-4">
                What This Solution Delivers
              </h2>
              <p className="text-xl text-slate-300 max-w-2xl mx-auto">
                Advanced detection, instant alerts, and actionable insights to protect 
                your water infrastructure and reduce waste
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {features.map((feature, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 + idx * 0.1 }}
                  className="group p-8 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300 hover:scale-105"
                >
                  <div className={`inline-flex p-4 bg-gradient-to-br ${feature.color} rounded-xl mb-4 shadow-lg group-hover:scale-110 transition-transform`}>
                    <feature.icon size={32} strokeWidth={2.5} />
                  </div>
                  <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                  <p className="text-slate-300 leading-relaxed">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </section>

        {/* Tech Stack Section */}
        <section className="max-w-7xl mx-auto px-6 pb-32">
          <div className="bg-white/5 backdrop-blur-sm rounded-3xl border border-white/10 p-12">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold mb-4">Why Choose Smart Water Monitor?</h2>
              <p className="text-slate-300 text-lg">Enterprise-grade technology made simple</p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {/* Backend */}
              <div className="space-y-4">
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <BarChart3 size={24} className="text-blue-400" />
                  Smart Detection
                </h3>
                <div className="space-y-2">
                  {['Learns your patterns', 'Detects anomalies instantly', 'No false alarms', 'Always improving', 'Works automatically', 'Proven accuracy'].map((tech, i) => (
                    <div key={i} className="flex items-center gap-2 text-slate-300">
                      <CheckCircle size={16} className="text-emerald-400" />
                      <span>{tech}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Frontend */}
              <div className="space-y-4">
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <Zap size={24} className="text-purple-400" />
                  Easy to Use
                </h3>
                <div className="space-y-2">
                  {['Beautiful dashboard', 'Works on any device', 'Real-time updates', 'Interactive charts', 'No training needed', 'Instant insights'].map((tech, i) => (
                    <div key={i} className="flex items-center gap-2 text-slate-300">
                      <CheckCircle size={16} className="text-emerald-400" />
                      <span>{tech}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Data */}
              <div className="space-y-4">
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <Shield size={24} className="text-emerald-400" />
                  Peace of Mind
                </h3>
                <div className="space-y-2">
                  {['24/7 monitoring', 'Instant alerts', 'Historical tracking', 'Cost savings', 'Water conservation', 'Zero installation'].map((tech, i) => (
                    <div key={i} className="flex items-center gap-2 text-slate-300">
                      <CheckCircle size={16} className="text-emerald-400" />
                      <span>{tech}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Final */}
        <section className="max-w-7xl mx-auto px-6 pb-20">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-12 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-black/20"></div>
            <div className="relative z-10">
              <h2 className="text-4xl md:text-5xl font-bold mb-6">
                Stop Paying for Water You're Wasting
              </h2>
              <p className="text-xl mb-8 text-white/90 max-w-2xl mx-auto">
                Start saving money today with intelligent leak detection that never sleeps
              </p>
              <button 
                onClick={onEnter}
                className="px-10 py-5 bg-white text-blue-600 hover:bg-slate-100 rounded-xl font-bold text-lg transition-all duration-300 shadow-2xl hover:scale-105 active:scale-95"
              >
                See it in Action
              </button>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/10 py-8">
          <div className="max-w-7xl mx-auto px-6 text-center">
            <p className="text-slate-400">
              © 2026 Smart Water Monitor · Developed by <span className="font-semibold text-white">Álvaro Soto Álvarez</span>
            </p>
            <p className="text-slate-500 text-sm mt-2">
              AI-Powered Water Management Platform
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default LandingPage;
