/**
 * Hook for clustering hechos based on their relationships
 * 
 * This hook:
 * - Groups related hechos into clusters
 * - Ensures no duplicates (each hecho appears only once)
 * - Memoizes results for performance
 * - Handles filtering correctly
 */

import { useMemo } from 'react';
import type { Hecho, HechoCluster } from '@/types/domain';
import { createClusters } from '@/utils/clustering';

interface UseClusterResult {
  clusters: HechoCluster[];
  stats: {
    totalClusters: number;
    singletonClusters: number;
    averageClusterSize: number;
    maxClusterSize: number;
  };
}

/**
 * Custom hook that creates clusters from hechos
 * @param hechos - Array of hechos to cluster
 * @returns Object with clusters and statistics
 */
export function useClusters(hechos: Hecho[]): UseClusterResult {
  // Memoize clustering to avoid recalculation on every render
  const result = useMemo(() => {
    if (!hechos || hechos.length === 0) {
      return {
        clusters: [],
        stats: {
          totalClusters: 0,
          singletonClusters: 0,
          averageClusterSize: 0,
          maxClusterSize: 0
        }
      };
    }
    
    // Create clusters ensuring no duplicates
    const clusters = createClusters(hechos);
    
    // Calculate statistics
    const stats = {
      totalClusters: clusters.length,
      singletonClusters: clusters.filter(c => c.hechos.length === 1).length,
      averageClusterSize: clusters.length > 0 
        ? clusters.reduce((sum, c) => sum + c.hechos.length, 0) / clusters.length 
        : 0,
      maxClusterSize: Math.max(...clusters.map(c => c.hechos.length), 0)
    };
    
    return { clusters, stats };
  }, [hechos]);
  
  return result;
}

