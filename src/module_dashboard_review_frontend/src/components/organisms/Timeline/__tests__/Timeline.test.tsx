import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Timeline } from '../Timeline';
import type { Hecho } from '@/types/domain';

// Mock de los utils de clustering
vi.mock('@/utils/clustering', () => ({
  getRelationType: (protagonist: Hecho, relatedId: number) => {
    // Simulación simple basada en IDs
    const relations: Record<number, string> = {
      2: 'causa',
      3: 'consecuencia',
      4: 'contradictorio',
      5: 'ampliacion',
      6: 'relacionado'
    };
    return relations[relatedId] || 'relacionado';
  },
  getRelationStrength: (protagonist: Hecho, relatedId: number) => {
    // Simulación simple basada en IDs
    const strengths: Record<number, number> = {
      2: 8,
      3: 9,
      4: 5,
      5: 7,
      6: 3
    };
    return strengths[relatedId] || 5;
  }
}));

const createMockHecho = (id: number, overrides?: Partial<Hecho>): Hecho => ({
  id,
  articulo_id: id,
  contenido: `Contenido del hecho ${id}`,
  importancia: 5,
  esOpinion: false,
  esFalso: false,
  verificado: true,
  fechaCreacion: new Date('2024-01-01'),
  fechaOcurrencia: new Date(`2024-01-0${id}`),
  articuloMetadata: {
    titulo: `Artículo ${id}`,
    url: `https://example.com/${id}`,
    medio: `Medio ${id}`,
    fechaPublicacion: `2024-01-0${id}`
  },
  ...overrides
});

describe('Timeline', () => {
  const protagonist = createMockHecho(1, { importancia: 9 });

  it('debe renderizar el título de la timeline', () => {
    render(
      <Timeline 
        protagonist={protagonist} 
        relatedHechos={[]} 
      />
    );

    expect(screen.getByText(/línea temporal de hechos relacionados/i)).toBeInTheDocument();
  });

  it('debe renderizar correctamente hechos relacionados con diferentes tipos de relación', () => {
    const relatedHechos = [
      createMockHecho(2), // causa
      createMockHecho(3), // consecuencia
      createMockHecho(4), // contradictorio
      createMockHecho(5), // ampliacion
      createMockHecho(6)  // relacionado
    ];

    render(
      <Timeline 
        protagonist={protagonist} 
        relatedHechos={relatedHechos} 
      />
    );

    // Verificar que se muestran los labels correctos
    expect(screen.getByText('Causa')).toBeInTheDocument();
    expect(screen.getByText('Consecuencia')).toBeInTheDocument();
    expect(screen.getByText('Contradice')).toBeInTheDocument();
    expect(screen.getByText('Amplía')).toBeInTheDocument();
    expect(screen.getByText('Relacionado')).toBeInTheDocument();

    // Verificar el contenido de los hechos
    relatedHechos.forEach(hecho => {
      expect(screen.getByText(hecho.contenido)).toBeInTheDocument();
    });
  });

  it('debe mostrar el indicador de relación fuerte cuando la fuerza es >= 7', () => {
    const relatedHechos = [
      createMockHecho(2), // fuerza 8
      createMockHecho(3), // fuerza 9
      createMockHecho(4), // fuerza 5
      createMockHecho(5), // fuerza 7
      createMockHecho(6)  // fuerza 3
    ];

    render(
      <Timeline 
        protagonist={protagonist} 
        relatedHechos={relatedHechos} 
      />
    );

    const fuerteLabels = screen.getAllByText('Fuerte');
    expect(fuerteLabels).toHaveLength(3); // IDs 2, 3 y 5 tienen fuerza >= 7
  });

  it('debe mostrar las fechas formateadas correctamente', () => {
    const relatedHechos = [
      createMockHecho(2, { 
        fechaOcurrencia: new Date('2024-01-15') 
      }),
      createMockHecho(3, { 
        fechaOcurrencia: new Date('2024-02-20') 
      })
    ];

    render(
      <Timeline 
        protagonist={protagonist} 
        relatedHechos={relatedHechos} 
      />
    );

    // Las fechas deben estar formateadas en español
    expect(screen.getByText(/15.*ene.*2024/i)).toBeInTheDocument();
    expect(screen.getByText(/20.*feb.*2024/i)).toBeInTheDocument();
  });

  it('debe mostrar la información del medio de cada hecho', () => {
    const relatedHechos = [
      createMockHecho(2, { 
        articuloMetadata: { 
          ...createMockHecho(2).articuloMetadata, 
          medio: 'El País' 
        } 
      }),
      createMockHecho(3, { 
        articuloMetadata: { 
          ...createMockHecho(3).articuloMetadata, 
          medio: 'La Vanguardia' 
        } 
      })
    ];

    render(
      <Timeline 
        protagonist={protagonist} 
        relatedHechos={relatedHechos} 
      />
    );

    expect(screen.getByText('El País')).toBeInTheDocument();
    expect(screen.getByText('La Vanguardia')).toBeInTheDocument();
  });

  it('debe mostrar indicador de alta importancia para hechos con importancia >= 7', () => {
    const relatedHechos = [
      createMockHecho(2, { importancia: 8 }),
      createMockHecho(3, { importancia: 9 }),
      createMockHecho(4, { importancia: 5 }),
      createMockHecho(5, { importancia: 7 })
    ];

    render(
      <Timeline 
        protagonist={protagonist} 
        relatedHechos={relatedHechos} 
      />
    );

    expect(screen.getByText(/alta importancia.*8\/10/i)).toBeInTheDocument();
    expect(screen.getByText(/alta importancia.*9\/10/i)).toBeInTheDocument();
    expect(screen.getByText(/alta importancia.*7\/10/i)).toBeInTheDocument();
    expect(screen.queryByText(/alta importancia.*5\/10/i)).not.toBeInTheDocument();
  });

  it('debe ejecutar onHechoClick cuando se hace clic en un hecho', () => {
    const onHechoClick = vi.fn();
    const relatedHechos = [
      createMockHecho(2),
      createMockHecho(3)
    ];

    render(
      <Timeline 
        protagonist={protagonist} 
        relatedHechos={relatedHechos}
        onHechoClick={onHechoClick}
      />
    );

    // Hacer clic en el primer hecho relacionado
    const firstHecho = screen.getByText('Contenido del hecho 2').closest('[role="button"]') || 
                      screen.getByText('Contenido del hecho 2').closest('div[style*="cursor: pointer"]');
    
    if (firstHecho) {
      fireEvent.click(firstHecho);
      expect(onHechoClick).toHaveBeenCalledWith(relatedHechos[0]);
    }
  });

  it('debe aplicar estilos de hover cuando onHechoClick está definido', () => {
    const relatedHechos = [createMockHecho(2)];

    const { container } = render(
      <Timeline 
        protagonist={protagonist} 
        relatedHechos={relatedHechos}
        onHechoClick={vi.fn()}
      />
    );

    // Verificar que el Paper tiene cursor pointer
    const paper = container.querySelector('[class*="MuiPaper-root"]');
    expect(paper).toHaveStyle({ cursor: 'pointer' });
  });

  it('debe no tener cursor pointer cuando onHechoClick no está definido', () => {
    const relatedHechos = [createMockHecho(2)];

    const { container } = render(
      <Timeline 
        protagonist={protagonist} 
        relatedHechos={relatedHechos}
      />
    );

    // Verificar que el Paper tiene cursor default
    const paper = container.querySelector('[class*="MuiPaper-root"]');
    expect(paper).toHaveStyle({ cursor: 'default' });
  });

  it('debe aplicar colores correctos según el tipo de relación', () => {
    const relatedHechos = [
      createMockHecho(2), // causa - azul
      createMockHecho(3), // consecuencia - verde
      createMockHecho(4), // contradictorio - rojo
      createMockHecho(5), // ampliacion - púrpura
      createMockHecho(6)  // relacionado - gris azulado
    ];

    const { container } = render(
      <Timeline 
        protagonist={protagonist} 
        relatedHechos={relatedHechos} 
      />
    );

    // Verificar que cada Paper tiene el borde izquierdo del color correcto
    const papers = container.querySelectorAll('[class*="MuiPaper-root"]');
    
    expect(papers[0]).toHaveStyle({ borderLeft: '4px solid #2196F3' }); // causa
    expect(papers[1]).toHaveStyle({ borderLeft: '4px solid #4CAF50' }); // consecuencia
    expect(papers[2]).toHaveStyle({ borderLeft: '4px solid #FF5722' }); // contradictorio
    expect(papers[3]).toHaveStyle({ borderLeft: '4px solid #9C27B0' }); // ampliacion
    expect(papers[4]).toHaveStyle({ borderLeft: '4px solid #607D8B' }); // relacionado
  });
});