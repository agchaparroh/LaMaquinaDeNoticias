/**
 * Clustering algorithm for grouping related hechos
 * 
 * This algorithm creates clusters of connected hechos ensuring:
 * - No hecho appears in more than one cluster
 * - The protagonist (highest importance) leads each cluster
 * - Related hechos are sorted chronologically
 */

import type { Hecho, HechoRelacion, HechoCluster } from '@/types/domain';

export type { HechoCluster };

/**
 * Creates clusters from an array of hechos based on their relationships
 * Ensures no duplicates - each hecho appears exactly once
 */
export function createClusters(hechos: Hecho[]): HechoCluster[] {
  const visited = new Set<number>();
  const clusters: HechoCluster[] = [];
  
  // Create a map for quick hecho lookup
  const hechoMap = new Map<number, Hecho>();
  hechos.forEach(hecho => hechoMap.set(hecho.id, hecho));
  
  // Build bidirectional relation graph
  const graph = buildRelationGraph(hechos);
  
  // Process each hecho
  for (const hecho of hechos) {
    if (visited.has(hecho.id)) continue;
    
    // Find all connected hechos using DFS
    const connectedIds = findConnectedComponent(hecho.id, graph, visited);
    
    // Get actual hecho objects
    const connectedHechos = connectedIds
      .map(id => hechoMap.get(id))
      .filter((h): h is Hecho => h !== undefined);
    
    // Select protagonist (highest importance)
    const protagonist = selectProtagonist(connectedHechos);
    
    // Get related hechos (excluding protagonist)
    const related = connectedHechos
      .filter(h => h.id !== protagonist.id)
      .sort(sortByDate);
    
    // Calculate total importance for sorting clusters
    const totalImportance = connectedHechos.reduce((sum, h) => sum + h.importancia, 0);
    
    clusters.push({
      id: `cluster-${protagonist.id}`,
      protagonista: protagonist,
      hechos: connectedHechos,
      totalRelaciones: countRelations(connectedHechos)
    });
  }
  
  // Sort clusters by total importance of protagonist (descending)
  return clusters.sort((a, b) => b.protagonista.importancia - a.protagonista.importancia);
}

/**
 * Counts the total number of unique relations in a cluster
 */
function countRelations(hechos: Hecho[]): number {
  const relationPairs = new Set<string>();
  
  hechos.forEach(hecho => {
    if (hecho.relaciones) {
      hecho.relaciones.forEach(rel => {
        // Create a unique key for each relation pair to avoid double counting
        const key = [hecho.id, rel.hecho_relacionado_id].sort().join('-');
        relationPairs.add(key);
      });
    }
  });
  
  return relationPairs.size;
}

/**
 * Builds a bidirectional graph of hecho relationships
 */
function buildRelationGraph(hechos: Hecho[]): Map<number, Set<number>> {
  const graph = new Map<number, Set<number>>();
  
  // Initialize graph with all hecho ids
  hechos.forEach(hecho => {
    graph.set(hecho.id, new Set<number>());
  });
  
  // Add edges for all relationships
  hechos.forEach(hecho => {
    if (hecho.relaciones) {
      hecho.relaciones.forEach(relacion => {
        // Add bidirectional edge
        const neighbors = graph.get(hecho.id);
        if (neighbors) {
          neighbors.add(relacion.hecho_relacionado_id);
        }
        
        // Add reverse edge for bidirectional relationship
        const reverseNeighbors = graph.get(relacion.hecho_relacionado_id);
        if (reverseNeighbors) {
          reverseNeighbors.add(hecho.id);
        }
      });
    }
  });
  
  return graph;
}

/**
 * Finds all connected hechos using depth-first search
 */
function findConnectedComponent(
  startId: number, 
  graph: Map<number, Set<number>>, 
  visited: Set<number>
): number[] {
  const component: number[] = [];
  const stack = [startId];
  
  while (stack.length > 0) {
    const currentId = stack.pop()!;
    
    if (visited.has(currentId)) continue;
    
    visited.add(currentId);
    component.push(currentId);
    
    // Add all unvisited neighbors to stack
    const neighbors = graph.get(currentId);
    if (neighbors) {
      neighbors.forEach(neighborId => {
        if (!visited.has(neighborId)) {
          stack.push(neighborId);
        }
      });
    }
  }
  
  return component;
}

/**
 * Selects the protagonist from a group of hechos
 * The protagonist is the hecho with the highest importance
 */
function selectProtagonist(hechos: Hecho[]): Hecho {
  return hechos.reduce((protagonist, current) => 
    current.importancia > protagonist.importancia ? current : protagonist
  );
}

/**
 * Sorts hechos by date (chronological order)
 */
function sortByDate(a: Hecho, b: Hecho): number {
  const dateA = new Date(a.fechaOcurrencia).getTime();
  const dateB = new Date(b.fechaOcurrencia).getTime();
  return dateA - dateB;
}

/**
 * Gets the type of relation between two hechos
 */
export function getRelationType(
  fromHecho: Hecho, 
  toHechoId: number
): HechoRelacion['tipo_relacion'] | null {
  if (!fromHecho.relaciones) return null;
  
  const relation = fromHecho.relaciones.find(
    rel => rel.hecho_relacionado_id === toHechoId
  );
  
  return relation ? relation.tipo_relacion : null;
}

/**
 * Gets the strength of relation between two hechos
 */
export function getRelationStrength(
  fromHecho: Hecho, 
  toHechoId: number
): number {
  if (!fromHecho.relaciones) return 0;
  
  const relation = fromHecho.relaciones.find(
    rel => rel.hecho_relacionado_id === toHechoId
  );
  
  return relation ? relation.fuerza_relacion : 0;
}