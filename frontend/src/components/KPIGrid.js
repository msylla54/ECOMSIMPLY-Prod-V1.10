// ================================================================================
// ECOMSIMPLY - PREMIUM KPI CARDS AWWWARDS
// Cards KPI avec hiérarchie claire et micro-animations
// ================================================================================

import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Activity, Eye, Zap, Star } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { cn } from '../lib/utils';

const KPICard = ({ 
  title, 
  value, 
  trend, 
  trendValue, 
  icon: Icon, 
  description,
  gradient = "from-blue-500 to-cyan-500",
  delay = 0
}) => {
  const isPositiveTrend = trend === 'up' || (typeof trendValue === 'number' && trendValue > 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay, ease: [0.22, 0.61, 0.36, 1] }}
      whileHover={{ y: -2, scale: 1.02 }}
      className="group"
    >
      <Card className="relative overflow-hidden border-border/50 hover:border-border transition-all duration-3 hover:shadow-soft-lg bg-card/80 backdrop-blur-sm">
        {/* Background Gradient */}
        <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-3`} />
        
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient} shadow-soft-sm group-hover:scale-110 transition-transform duration-3`}>
              <Icon className="w-6 h-6 text-white" />
            </div>
            
            {trend && (
              <Badge 
                variant="secondary"
                className={cn(
                  "text-xs font-medium",
                  isPositiveTrend 
                    ? "bg-green-100 text-green-700 hover:bg-green-200" 
                    : "bg-red-100 text-red-700 hover:bg-red-200"
                )}
              >
                <div className="flex items-center gap-1">
                  {isPositiveTrend ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  {trendValue && `${Math.abs(trendValue)}%`}
                </div>
              </Badge>
            )}
          </div>
          
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
        </CardHeader>

        <CardContent className="pt-0">
          {/* Value */}
          <motion.div 
            className="text-3xl font-bold text-foreground mb-1"
            initial={{ scale: 1 }}
            whileHover={{ scale: 1.05 }}
            transition={{ duration: 0.2 }}
          >
            {value}
          </motion.div>
          
          {/* Description */}
          {description && (
            <p className="text-sm text-muted-foreground leading-relaxed">
              {description}
            </p>
          )}

          {/* Progress indicator */}
          <div className="mt-4">
            <div className="w-full h-1 bg-muted rounded-full overflow-hidden">
              <motion.div 
                className={`h-full bg-gradient-to-r ${gradient} rounded-full`}
                initial={{ width: '0%' }}
                animate={{ width: '75%' }}
                transition={{ duration: 1.5, delay: delay + 0.5, ease: 'easeOut' }}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

const KPIGrid = ({ stats }) => {
  const kpiData = [
    {
      title: "Fiches Générées",
      value: stats?.sheets_count || "0",
      trend: "up",
      trendValue: 12,
      icon: Activity,
      description: "Ce mois",
      gradient: "from-purple-500 to-pink-500",
      delay: 0
    },
    {
      title: "Score SEO Moyen",
      value: stats?.avg_seo_score ? `${stats.avg_seo_score}/100` : "98/100",
      trend: "up", 
      trendValue: 5,
      icon: Zap,
      description: "Optimisation continue",
      gradient: "from-green-400 to-emerald-500",
      delay: 0.1
    },
    {
      title: "Vues Totales",
      value: stats?.total_views || "2,847",
      trend: "up",
      trendValue: 18,
      icon: Eye,
      description: "Engagement produit",
      gradient: "from-blue-500 to-cyan-500",
      delay: 0.2
    },
    {
      title: "Satisfaction",
      value: "98%",
      trend: "up",
      trendValue: 2,
      icon: Star,
      description: "Retours clients",
      gradient: "from-yellow-400 to-orange-500",
      delay: 0.3
    }
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  return (
    <motion.div 
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {kpiData.map((kpi, index) => (
        <KPICard key={index} {...kpi} />
      ))}
    </motion.div>
  );
};

export default KPIGrid;