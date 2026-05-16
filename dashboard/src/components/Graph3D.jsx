import React, { useRef, useEffect, useState, useMemo } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';

const MAX_RENDER_NODES = 2000;
const MAX_RENDER_EDGES = 5000;

export default function Graph3D({ graphData }) {
  const fgRef = useRef();
  const [dimensions, setDimensions] = useState({ width: window.innerWidth, height: window.innerHeight });

  useEffect(() => {
    const handleResize = () => setDimensions({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Safety limits: Prune graph if it exceeds max size
  const prunedData = useMemo(() => {
    let { nodes, links } = graphData;
    if (nodes.length > MAX_RENDER_NODES) {
      nodes = nodes.slice(-MAX_RENDER_NODES);
      const nodeIds = new Set(nodes.map(n => n.id));
      links = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));
    }
    if (links.length > MAX_RENDER_EDGES) {
      links = links.slice(-MAX_RENDER_EDGES);
    }
    return { nodes, links };
  }, [graphData]);

  return (
    <ForceGraph3D
      ref={fgRef}
      width={dimensions.width}
      height={dimensions.height}
      graphData={prunedData}
      nodeRelSize={6}
      nodeColor={node => {
        if (node.type === 'suspicious') return 'red';
        if (node.type === 'mutated') return 'orange';
        if (node.type === 'exported') return '#10b981'; // green
        return '#3b82f6'; // blue
      }}
      nodeResolution={16}
      linkDirectionalParticles={2}
      linkDirectionalParticleSpeed={d => d.weight ? 0.01 * d.weight : 0.01}
      linkDirectionalParticleWidth={1.5}
      linkColor={() => 'rgba(255,255,255,0.2)'}
      backgroundColor="#0f172a"
      enableNodeDrag={false}
      onNodeClick={node => {
        // Aim at node
        const distance = 40;
        const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
        fgRef.current.cameraPosition(
          { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
          node, // lookAt
          3000  // ms transition
        );
      }}
    />
  );
}
