// ================================================================================
// ECOMSIMPLY - PREMIUM DATA TABLE AWWWARDS  
// Table élégante avec zebra stripes, sticky headers, hover effects
// ================================================================================

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronUp, ChevronDown, Eye, Edit, Trash2, Download, ExternalLink } from 'lucide-react';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { Skeleton } from './ui/Skeleton';
import { cn } from '../lib/utils';

const PremiumTable = ({ 
  data = [], 
  columns = [], 
  loading = false,
  emptyMessage = "Aucune donnée disponible",
  onRowClick,
  className = ""
}) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedData = React.useMemo(() => {
    if (!sortConfig.key) return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];
      
      if (aVal < bVal) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aVal > bVal) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [data, sortConfig]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      },
    },
  };

  const rowVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        duration: 0.4,
        ease: [0.22, 0.61, 0.36, 1],
      },
    },
  };

  if (loading) {
    return (
      <div className={cn("bg-card rounded-xl border border-border shadow-soft-sm overflow-hidden", className)}>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-8 w-24" />
          </div>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center space-x-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-8 w-20" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <motion.div 
        className={cn("bg-card rounded-xl border border-border shadow-soft-sm p-12 text-center", className)}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="text-6xl mb-4 opacity-20">📊</div>
        <p className="text-muted-foreground text-lg">{emptyMessage}</p>
      </motion.div>
    );
  }

  return (
    <motion.div 
      className={cn("bg-card rounded-xl border border-border shadow-soft-sm overflow-hidden", className)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="overflow-x-auto">
        <table className="w-full">
          {/* Header */}
          <thead className="bg-muted/30 sticky top-0 z-10">
            <tr>
              {columns.map((column, index) => (
                <th
                  key={column.key}
                  className={cn(
                    "px-6 py-4 text-left text-sm font-semibold text-foreground border-b border-border",
                    column.sortable && "cursor-pointer hover:bg-muted/50 transition-colors duration-2",
                    index === 0 && "rounded-tl-xl",
                    index === columns.length - 1 && "rounded-tr-xl"
                  )}
                  onClick={() => column.sortable && handleSort(column.key)}
                >
                  <div className="flex items-center space-x-2">
                    <span>{column.title}</span>
                    {column.sortable && sortConfig.key === column.key && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ duration: 0.2 }}
                      >
                        {sortConfig.direction === 'asc' ? (
                          <ChevronUp className="w-4 h-4 text-primary" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-primary" />
                        )}
                      </motion.div>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          {/* Body */}
          <motion.tbody variants={containerVariants} initial="hidden" animate="visible">
            {sortedData.map((row, rowIndex) => (
              <motion.tr
                key={row.id || rowIndex}
                variants={rowVariants}
                className={cn(
                  "transition-all duration-2 border-b border-border/50 hover:bg-muted/20",
                  rowIndex % 2 === 0 ? "bg-background" : "bg-muted/5",
                  onRowClick && "cursor-pointer"
                )}
                onClick={() => onRowClick && onRowClick(row)}
                whileHover={{ scale: 1.005 }}
              >
                {columns.map((column, colIndex) => (
                  <td 
                    key={column.key}
                    className={cn(
                      "px-6 py-4 text-sm",
                      colIndex === 0 && rowIndex === sortedData.length - 1 && "rounded-bl-xl",
                      colIndex === columns.length - 1 && rowIndex === sortedData.length - 1 && "rounded-br-xl"
                    )}
                  >
                    {column.render ? (
                      column.render(row[column.key], row, rowIndex)
                    ) : (
                      <span className="text-foreground">
                        {row[column.key]}
                      </span>
                    )}
                  </td>
                ))}
              </motion.tr>
            ))}
          </motion.tbody>
        </table>
      </div>
    </motion.div>
  );
};

// Helper component pour les actions de ligne
export const TableActions = ({ onView, onEdit, onDelete, onExport, onPublish, className = "" }) => {
  return (
    <div className={cn("flex items-center space-x-2", className)}>
      {onView && (
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onView(); }}>
          <Eye className="w-4 h-4" />
        </Button>
      )}
      {onEdit && (
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onEdit(); }}>
          <Edit className="w-4 h-4" />
        </Button>
      )}
      {onExport && (
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onExport(); }}>
          <Download className="w-4 h-4" />
        </Button>
      )}
      {onPublish && (
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onPublish(); }}>
          <ExternalLink className="w-4 h-4" />
        </Button>
      )}
      {onDelete && (
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onDelete(); }} className="text-destructive hover:bg-destructive/10">
          <Trash2 className="w-4 h-4" />
        </Button>
      )}
    </div>
  );
};

export default PremiumTable;