import { describe, it, expect } from 'vitest';
import { createClusters, getRelationType, getRelationStrength } from '@/utils/clustering';
import type { Hecho } from '@/types/domain';

// Mock data helper
const createMockHecho = (id: number, overrides?: Partial<Hecho>): Hecho => ({
  id,
  contenido: `Hecho ${id}`,
  importancia: 5,
  fechaOcurrencia: '2024-01-01',
  tipoHecho: 'SUCESO',
  articuloMetadata: {
    titular: 'Artículo de prueba',
    url: 'https://example.com',
    medio: 'Test Media',
    fechaPublicacion: '2024-01-01'
  },
  ...overrides
});

describe('clustering', () => {
  describe('createClusters', () => {
    it('debe crear un cluster por cada hecho sin relaciones', () => {
      const hechos = [
        createMockHecho(1),
        createMockHecho(2),
        createMockHecho(3)
      ];

      const clusters = createClusters(hechos);

      expect(clusters).toHaveLength(3);
      clusters.forEach(cluster => {
        expect(cluster.hechos).toHaveLength(1);
        expect(cluster.totalRelaciones).toBe(0);
      });
    });

    it('debe agrupar hechos relacionados en un mismo cluster', () => {
      const hechos = [
        createMockHecho(1, {
          relaciones: [{
            hecho_relacionado_id: 2,
            tipo_relacion: 'consecuencia',
            fuerza_relacion: 8,
            direccion: 'origen'
          }]
        }),
        createMockHecho(2, {
          relaciones: [{
            hecho_relacionado_id: 1,
            tipo_relacion: 'causa',
            fuerza_relacion: 8,
            direccion: 'destino'
          }]
        }),
        createMockHecho(3)
      ];

      const clusters = createClusters(hechos);

      expect(clusters).toHaveLength(2);
      const relatedCluster = clusters.find(c => c.hechos.length > 1);
      expect(relatedCluster).toBeDefined();
      expect(relatedCluster!.hechos).toHaveLength(2);
      expect(relatedCluster!.totalRelaciones).toBe(1);
    });

    it('debe seleccionar el protagonista con mayor importancia', () => {
      const hechos = [
        createMockHecho(1, {
          importancia: 3,
          relaciones: [{
            hecho_relacionado_id: 2,
            tipo_relacion: 'relacionado',
            fuerza_relacion: 5,
            direccion: 'origen'
          }]
        }),
        createMockHecho(2, {
          importancia: 9,
          relaciones: [{
            hecho_relacionado_id: 1,
            tipo_relacion: 'relacionado',
            fuerza_relacion: 5,
            direccion: 'destino'
          }]
        })
      ];

      const clusters = createClusters(hechos);

      expect(clusters).toHaveLength(1);
      expect(clusters[0].protagonista.id).toBe(2);
      expect(clusters[0].protagonista.importancia).toBe(9);
    });

    it('debe manejar relaciones complejas con múltiples conexiones', () => {
      const hechos = [
        createMockHecho(1, {
          relaciones: [
            { hecho_relacionado_id: 2, tipo_relacion: 'causa', fuerza_relacion: 7, direccion: 'origen' },
            { hecho_relacionado_id: 3, tipo_relacion: 'relacionado', fuerza_relacion: 5, direccion: 'origen' }
          ]
        }),
        createMockHecho(2, {
          relaciones: [
            { hecho_relacionado_id: 1, tipo_relacion: 'consecuencia', fuerza_relacion: 7, direccion: 'destino' },
            { hecho_relacionado_id: 4, tipo_relacion: 'ampliacion', fuerza_relacion: 6, direccion: 'origen' }
          ]
        }),
        createMockHecho(3, {
          relaciones: [
            { hecho_relacionado_id: 1, tipo_relacion: 'relacionado', fuerza_relacion: 5, direccion: 'destino' }
          ]
        }),
        createMockHecho(4, {
          relaciones: [
            { hecho_relacionado_id: 2, tipo_relacion: 'ampliacion', fuerza_relacion: 6, direccion: 'destino' }
          ]
        }),
        createMockHecho(5)
      ];

      const clusters = createClusters(hechos);

      expect(clusters).toHaveLength(2);
      const bigCluster = clusters.find(c => c.hechos.length > 1);
      expect(bigCluster!.hechos).toHaveLength(4);
      expect(bigCluster!.totalRelaciones).toBe(4);
    });

    it('debe garantizar que no haya duplicados en los clusters', () => {
      const hechos = [
        createMockHecho(1, {
          relaciones: [
            { hecho_relacionado_id: 2, tipo_relacion: 'causa', fuerza_relacion: 8, direccion: 'origen' },
            { hecho_relacionado_id: 3, tipo_relacion: 'consecuencia', fuerza_relacion: 7, direccion: 'origen' }
          ]
        }),
        createMockHecho(2, {
          relaciones: [
            { hecho_relacionado_id: 1, tipo_relacion: 'consecuencia', fuerza_relacion: 8, direccion: 'destino' },
            { hecho_relacionado_id: 3, tipo_relacion: 'relacionado', fuerza_relacion: 5, direccion: 'origen' }
          ]
        }),
        createMockHecho(3, {
          relaciones: [
            { hecho_relacionado_id: 1, tipo_relacion: 'causa', fuerza_relacion: 7, direccion: 'destino' },
            { hecho_relacionado_id: 2, tipo_relacion: 'relacionado', fuerza_relacion: 5, direccion: 'destino' }
          ]
        })
      ];

      const clusters = createClusters(hechos);
      const allHechoIds = clusters.flatMap(c => c.hechos.map(h => h.id));
      const uniqueIds = new Set(allHechoIds);

      expect(allHechoIds).toHaveLength(3);
      expect(uniqueIds.size).toBe(3);
    });
  });

  describe('getRelationType', () => {
    it('debe devolver el tipo de relación correcto', () => {
      const hecho = createMockHecho(1, {
        relaciones: [
          { hecho_relacionado_id: 2, tipo_relacion: 'causa', fuerza_relacion: 8, direccion: 'origen' },
          { hecho_relacionado_id: 3, tipo_relacion: 'contradictorio', fuerza_relacion: 6, direccion: 'origen' }
        ]
      });

      expect(getRelationType(hecho, 2)).toBe('causa');
      expect(getRelationType(hecho, 3)).toBe('contradictorio');
      expect(getRelationType(hecho, 4)).toBeUndefined();
    });

    it('debe manejar hechos sin relaciones', () => {
      const hecho = createMockHecho(1);
      expect(getRelationType(hecho, 2)).toBeUndefined();
    });
  });

  describe('getRelationStrength', () => {
    it('debe devolver la fuerza de relación correcta', () => {
      const hecho = createMockHecho(1, {
        relaciones: [
          { hecho_relacionado_id: 2, tipo_relacion: 'causa', fuerza_relacion: 8, direccion: 'origen' },
          { hecho_relacionado_id: 3, tipo_relacion: 'relacionado', fuerza_relacion: 3, direccion: 'origen' }
        ]
      });

      expect(getRelationStrength(hecho, 2)).toBe(8);
      expect(getRelationStrength(hecho, 3)).toBe(3);
      expect(getRelationStrength(hecho, 4)).toBe(0);
    });

    it('debe devolver 0 para hechos sin relaciones', () => {
      const hecho = createMockHecho(1);
      expect(getRelationStrength(hecho, 2)).toBe(0);
    });
  });
});