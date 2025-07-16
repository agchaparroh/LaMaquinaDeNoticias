import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useClusters } from '@/hooks/useClusters';
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

describe('useClusters', () => {
  it('debe devolver clusters vacíos cuando no hay hechos', () => {
    const { result } = renderHook(() => useClusters([]));

    expect(result.current.clusters).toEqual([]);
    expect(result.current.stats).toEqual({
      totalClusters: 0,
      singletonClusters: 0,
      averageClusterSize: 0,
      maxClusterSize: 0
    });
  });

  it('debe crear clusters con hechos individuales', () => {
    const hechos = [
      createMockHecho(1),
      createMockHecho(2),
      createMockHecho(3)
    ];

    const { result } = renderHook(() => useClusters(hechos));

    expect(result.current.clusters).toHaveLength(3);
    expect(result.current.stats.totalClusters).toBe(3);
    expect(result.current.stats.singletonClusters).toBe(3);
    expect(result.current.stats.averageClusterSize).toBe(1);
    expect(result.current.stats.maxClusterSize).toBe(1);
  });

  it('debe agrupar hechos relacionados y calcular estadísticas', () => {
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
      createMockHecho(3),
      createMockHecho(4)
    ];

    const { result } = renderHook(() => useClusters(hechos));

    expect(result.current.clusters).toHaveLength(3);
    expect(result.current.stats.totalClusters).toBe(3);
    expect(result.current.stats.singletonClusters).toBe(2);
    expect(result.current.stats.averageClusterSize).toBeCloseTo(1.33, 2);
    expect(result.current.stats.maxClusterSize).toBe(2);
  });

  it('debe memoizar los resultados cuando los hechos no cambian', () => {
    const hechos = [
      createMockHecho(1),
      createMockHecho(2)
    ];

    const { result, rerender } = renderHook(() => useClusters(hechos));
    
    const firstClusters = result.current.clusters;
    const firstStats = result.current.stats;

    // Re-render con los mismos hechos
    rerender();

    expect(result.current.clusters).toBe(firstClusters);
    expect(result.current.stats).toBe(firstStats);
  });

  it('debe recalcular cuando los hechos cambian', () => {
    const initialHechos = [
      createMockHecho(1),
      createMockHecho(2)
    ];

    const { result, rerender } = renderHook(
      ({ hechos }) => useClusters(hechos),
      { initialProps: { hechos: initialHechos } }
    );

    expect(result.current.clusters).toHaveLength(2);

    // Añadir relación entre los hechos
    const updatedHechos = [
      createMockHecho(1, {
        relaciones: [{
          hecho_relacionado_id: 2,
          tipo_relacion: 'relacionado',
          fuerza_relacion: 5,
          direccion: 'origen'
        }]
      }),
      createMockHecho(2, {
        relaciones: [{
          hecho_relacionado_id: 1,
          tipo_relacion: 'relacionado',
          fuerza_relacion: 5,
          direccion: 'destino'
        }]
      })
    ];

    rerender({ hechos: updatedHechos });

    expect(result.current.clusters).toHaveLength(1);
    expect(result.current.clusters[0].hechos).toHaveLength(2);
  });

  it('debe manejar clusters complejos con múltiples relaciones', () => {
    const hechos = [
      createMockHecho(1, {
        importancia: 9,
        relaciones: [
          { hecho_relacionado_id: 2, tipo_relacion: 'causa', fuerza_relacion: 8, direccion: 'origen' },
          { hecho_relacionado_id: 3, tipo_relacion: 'consecuencia', fuerza_relacion: 7, direccion: 'origen' },
          { hecho_relacionado_id: 4, tipo_relacion: 'ampliacion', fuerza_relacion: 6, direccion: 'origen' }
        ]
      }),
      createMockHecho(2, {
        importancia: 7,
        relaciones: [
          { hecho_relacionado_id: 1, tipo_relacion: 'consecuencia', fuerza_relacion: 8, direccion: 'destino' }
        ]
      }),
      createMockHecho(3, {
        importancia: 5,
        relaciones: [
          { hecho_relacionado_id: 1, tipo_relacion: 'causa', fuerza_relacion: 7, direccion: 'destino' }
        ]
      }),
      createMockHecho(4, {
        importancia: 3,
        relaciones: [
          { hecho_relacionado_id: 1, tipo_relacion: 'ampliacion', fuerza_relacion: 6, direccion: 'destino' }
        ]
      }),
      createMockHecho(5, { importancia: 10 })
    ];

    const { result } = renderHook(() => useClusters(hechos));

    expect(result.current.clusters).toHaveLength(2);
    
    const bigCluster = result.current.clusters.find(c => c.hechos.length > 1);
    expect(bigCluster).toBeDefined();
    expect(bigCluster!.hechos).toHaveLength(4);
    expect(bigCluster!.protagonista.id).toBe(1); // Mayor importancia
    expect(bigCluster!.totalRelaciones).toBe(4);

    expect(result.current.stats.maxClusterSize).toBe(4);
    expect(result.current.stats.averageClusterSize).toBe(2.5);
  });
});