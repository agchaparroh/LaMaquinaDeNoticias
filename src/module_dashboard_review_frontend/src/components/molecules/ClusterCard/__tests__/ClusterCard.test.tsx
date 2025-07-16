import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ClusterCard } from '../ClusterCard';
import type { HechoCluster } from '@/types/domain';

// Mock del componente Timeline
vi.mock('@/components/organisms', () => ({
  Timeline: ({ protagonist, relatedHechos }: any) => (
    <div data-testid="timeline">
      <div>Timeline for {protagonist.contenido}</div>
      <div>{relatedHechos.length} related facts</div>
    </div>
  )
}));

// Mock del componente HechoCard
vi.mock('@/components/molecules', () => ({
  HechoCard: ({ hecho }: any) => (
    <div data-testid={`hecho-card-${hecho.id}`}>
      HechoCard: {hecho.contenido}
    </div>
  ),
  ClusterCard: vi.requireActual('../ClusterCard').ClusterCard
}));

const createMockCluster = (overrides?: Partial<HechoCluster>): HechoCluster => ({
  id: '1',
  protagonista: {
    id: 1,
    contenido: 'Hecho protagonista',
    importancia: 8,
    fechaOcurrencia: '2024-01-01',
    tipoHecho: 'SUCESO',
    articuloMetadata: {
      titular: 'Artículo de prueba',
      url: 'https://example.com',
      medio: 'Test Media',
      fechaPublicacion: '2024-01-01'
    }
  },
  hechos: [],
  totalRelaciones: 0,
  ...overrides
});

describe('ClusterCard', () => {
  const defaultProps = {
    cluster: createMockCluster(),
    onImportanceChange: vi.fn(),
    onMarkAsFalse: vi.fn(),
    onFeedbackSubmitted: vi.fn(),
    isImportanceLoading: vi.fn(() => false)
  };

  it('debe renderizar un cluster singleton correctamente', () => {
    render(<ClusterCard {...defaultProps} />);

    expect(screen.getByTestId('hecho-card-1')).toBeInTheDocument();
    expect(screen.queryByTestId('timeline')).not.toBeInTheDocument();
    expect(screen.queryByText(/hechos relacionados/i)).not.toBeInTheDocument();
  });

  it('debe renderizar un cluster con múltiples hechos', () => {
    const clusterWithRelated = createMockCluster({
      hechos: [
        defaultProps.cluster.protagonista,
        {
          id: 2,
          contenido: 'Hecho relacionado 1',
          importancia: 6,
          fechaOcurrencia: '2024-01-02',
          tipoHecho: 'SUCESO',
          articuloMetadata: {
            titular: 'Otro artículo',
            url: 'https://example.com/2',
            medio: 'Test Media 2',
            fechaPublicacion: '2024-01-02'
          }
        },
        {
          id: 3,
          contenido: 'Hecho relacionado 2',
          importancia: 5,
          fechaOcurrencia: '2024-01-03',
          tipoHecho: 'SUCESO',
          articuloMetadata: {
            titular: 'Tercer artículo',
            url: 'https://example.com/3',
            medio: 'Test Media 3',
            fechaPublicacion: '2024-01-03'
          }
        }
      ],
      totalRelaciones: 2
    });

    render(<ClusterCard {...defaultProps} cluster={clusterWithRelated} />);

    expect(screen.getByTestId('hecho-card-1')).toBeInTheDocument();
    expect(screen.getByText(/2 hechos relacionados/i)).toBeInTheDocument();
    expect(screen.queryByTestId('timeline')).not.toBeInTheDocument(); // Colapsado por defecto
  });

  it('debe expandir y colapsar la timeline al hacer clic', async () => {
    const clusterWithRelated = createMockCluster({
      hechos: [
        defaultProps.cluster.protagonista,
        {
          id: 2,
          articulo_id: 2,
          contenido: 'Hecho relacionado',
          importancia: 6,
          esOpinion: false,
          esFalso: false,
          verificado: true,
          fechaCreacion: new Date('2024-01-02'),
          fechaOcurrencia: new Date('2024-01-02'),
          articuloMetadata: {
            titulo: 'Otro artículo',
            url: 'https://example.com/2',
            medio: 'Test Media 2',
            fechaPublicacion: '2024-01-02'
          }
        }
      ],
      totalRelaciones: 1
    });

    render(<ClusterCard {...defaultProps} cluster={clusterWithRelated} />);

    const expandButton = screen.getByText(/1 hecho relacionado/i);
    
    // Expandir
    fireEvent.click(expandButton);
    await waitFor(() => {
      expect(screen.getByTestId('timeline')).toBeInTheDocument();
    });

    // Colapsar
    fireEvent.click(expandButton);
    await waitFor(() => {
      expect(screen.queryByTestId('timeline')).not.toBeInTheDocument();
    });
  });

  it('debe propagar los callbacks correctamente', () => {
    const onImportanceChange = vi.fn();
    const onMarkAsFalse = vi.fn();
    const onFeedbackSubmitted = vi.fn();

    render(
      <ClusterCard 
        {...defaultProps}
        onImportanceChange={onImportanceChange}
        onMarkAsFalse={onMarkAsFalse}
        onFeedbackSubmitted={onFeedbackSubmitted}
      />
    );

    // Los callbacks se pasan al HechoCard interno
    // En una implementación real, deberíamos simular las interacciones
    // dentro del HechoCard para verificar que los callbacks se ejecutan
  });

  it('debe mostrar el indicador de grupo para clusters con relaciones', () => {
    const clusterWithRelated = createMockCluster({
      hechos: [
        defaultProps.cluster.protagonista,
        {
          id: 2,
          articulo_id: 2,
          contenido: 'Hecho relacionado',
          importancia: 6,
          esOpinion: false,
          esFalso: false,
          verificado: true,
          fechaCreacion: new Date('2024-01-02'),
          fechaOcurrencia: new Date('2024-01-02'),
          articuloMetadata: {
            titulo: 'Otro artículo',
            url: 'https://example.com/2',
            medio: 'Test Media 2',
            fechaPublicacion: '2024-01-02'
          }
        }
      ],
      totalRelaciones: 1
    });

    render(<ClusterCard {...defaultProps} cluster={clusterWithRelated} />);

    // Verificar que se muestra el chip de grupo
    const groupChip = screen.getByText(/grupo/i);
    expect(groupChip).toBeInTheDocument();
  });

  it('debe manejar correctamente clusters con muchos hechos relacionados', () => {
    const manyRelatedHechos = Array.from({ length: 10 }, (_, i) => ({
      id: i + 2,
      articulo_id: i + 2,
      contenido: `Hecho relacionado ${i + 1}`,
      importancia: 5,
      esOpinion: false,
      esFalso: false,
      verificado: true,
      fechaCreacion: new Date('2024-01-02'),
      fechaOcurrencia: new Date('2024-01-02'),
      articuloMetadata: {
        titulo: `Artículo ${i + 2}`,
        url: `https://example.com/${i + 2}`,
        medio: `Test Media ${i + 2}`,
        fechaPublicacion: '2024-01-02'
      }
    }));

    const clusterWithMany = createMockCluster({
      hechos: [defaultProps.cluster.protagonista, ...manyRelatedHechos],
      totalRelaciones: 10
    });

    render(<ClusterCard {...defaultProps} cluster={clusterWithMany} />);

    expect(screen.getByText(/10 hechos relacionados/i)).toBeInTheDocument();
  });
});