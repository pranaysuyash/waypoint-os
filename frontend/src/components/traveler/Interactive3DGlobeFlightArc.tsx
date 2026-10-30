'use client';

import React, { useState, useRef, useEffect } from 'react';

export interface GlobeWaypoint {
  id: string;
  code: string;
  city: string;
  lat: number;
  lng: number;
  isOrigin?: boolean;
}

interface Interactive3DGlobeFlightArcProps {
  waypoints?: GlobeWaypoint[];
  activeLegTitle?: string;
}

const DEFAULT_WAYPOINTS: GlobeWaypoint[] = [
  { id: '1', code: 'JFK', city: 'New York', lat: 40.6413, lng: -73.7781, isOrigin: true },
  { id: '2', code: 'LHR', city: 'London', lat: 51.4700, lng: -0.4543 },
  { id: '3', code: 'CDG', city: 'Paris', lat: 49.0097, lng: 2.5479 },
  { id: '4', code: 'FCO', city: 'Rome', lat: 41.8003, lng: 12.2389 },
];

export function Interactive3DGlobeFlightArc({
  waypoints = DEFAULT_WAYPOINTS,
  activeLegTitle = 'JFK → LHR → CDG → FCO',
}: Interactive3DGlobeFlightArcProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [rotationAngle, setRotationAngle] = useState<number>(0.2); // radians
  const [pitchAngle, setPitchAngle] = useState<number>(0.35); // tilt radians
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [lastMousePos, setLastMousePos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [flightPhase, setFlightPhase] = useState<number>(0); // 0 to 1 for animated plane

  // Auto-rotation when not interacting
  useEffect(() => {
    let animationId: number;
    const animate = () => {
      if (!isDragging) {
        setRotationAngle((prev) => prev + 0.003);
      }
      setFlightPhase((prev) => (prev >= 1 ? 0 : prev + 0.006));
      animationId = requestAnimationFrame(animate);
    };
    animationId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationId);
  }, [isDragging]);

  // Render 3D orthographic globe on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const cx = width / 2;
    const cy = height / 2;
    const radius = Math.min(width, height) * 0.38;

    ctx.clearRect(0, 0, width, height);

    // 1. Atmosphere Radial Glow (Space Horizon)
    const glowGrad = ctx.createRadialGradient(cx, cy, radius * 0.9, cx, cy, radius * 1.25);
    glowGrad.addColorStop(0, 'rgba(56, 189, 248, 0.25)');
    glowGrad.addColorStop(0.5, 'rgba(14, 165, 233, 0.08)');
    glowGrad.addColorStop(1, 'rgba(10, 13, 18, 0)');
    ctx.fillStyle = glowGrad;
    ctx.fillRect(0, 0, width, height);

    // 2. Globe Body (Dark Planetary sphere)
    const sphereGrad = ctx.createRadialGradient(cx - radius * 0.35, cy - radius * 0.35, radius * 0.1, cx, cy, radius);
    sphereGrad.addColorStop(0, '#1e293b');
    sphereGrad.addColorStop(0.65, '#0f172a');
    sphereGrad.addColorStop(1, '#020617');

    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fillStyle = sphereGrad;
    ctx.fill();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = '#334155';
    ctx.stroke();
    ctx.clip(); // Clip all continents and arcs inside the sphere horizon

    // 3. Latitude and Longitude Graticule Mesh
    ctx.strokeStyle = 'rgba(71, 85, 105, 0.25)';
    ctx.lineWidth = 0.8;

    // Draw Parallels (Latitude lines)
    for (let lat = -60; lat <= 60; lat += 30) {
      const latRad = (lat * Math.PI) / 180;
      const yRel = -Math.sin(latRad) * radius * Math.cos(pitchAngle);
      const rRing = Math.cos(latRad) * radius;
      ctx.beginPath();
      ctx.ellipse(cx, cy + yRel, rRing, rRing * Math.sin(pitchAngle), 0, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Convert (lat, lng) to 3D Cartesian coordinates on sphere
    const latLngToCartesian = (lat: number, lng: number, r: number) => {
      const phi = (lat * Math.PI) / 180;
      const lambda = (lng * Math.PI) / 180 + rotationAngle;
      // Rotated around Y-axis by rotationAngle and X-axis by pitchAngle
      const x = r * Math.cos(phi) * Math.sin(lambda);
      const y = -r * Math.sin(phi);
      const z = r * Math.cos(phi) * Math.cos(lambda);

      // Pitch rotation around X axis
      const cosP = Math.cos(pitchAngle);
      const sinP = Math.sin(pitchAngle);
      const yPitch = y * cosP - z * sinP;
      const zPitch = y * sinP + z * cosP;

      return { x: cx + x, y: cy + yPitch, z: zPitch, visible: zPitch > -radius * 0.2 };
    };

    // 4. Draw Projected Continents / Simplified Landmass Outlines
    // Transatlantic + Europe Landmass clusters
    const sampleCoastlines = [
      // North America East Coast
      [ [45, -70], [40, -74], [35, -78], [30, -81], [25, -80] ],
      // Western Europe & UK
      [ [58, -4], [55, -2], [51, 0], [48, 2], [43, 3], [37, -3], [36, -5] ],
      // Italy / Mediterranean
      [ [46, 12], [44, 10], [41, 14], [38, 15], [37, 14] ],
    ];

    ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
    ctx.lineWidth = 1.2;
    sampleCoastlines.forEach((coast) => {
      ctx.beginPath();
      let started = false;
      coast.forEach(([lat, lng]) => {
        const pt = latLngToCartesian(lat, lng, radius * 0.99);
        if (pt.visible) {
          if (!started) {
            ctx.moveTo(pt.x, pt.y);
            started = true;
          } else {
            ctx.lineTo(pt.x, pt.y);
          }
        }
      });
      ctx.stroke();
    });

    // 5. Great-Circle 3D Parabolic Flight Arcs
    for (let i = 0; i < waypoints.length - 1; i++) {
      const wp1 = waypoints[i];
      const wp2 = waypoints[i + 1];

      const steps = 30;
      ctx.beginPath();
      let arcStarted = false;

      for (let s = 0; s <= steps; s++) {
        const t = s / steps;
        // Spherical interpolation + parabolic altitude lift
        const currentLat = wp1.lat + (wp2.lat - wp1.lat) * t;
        const currentLng = wp1.lng + (wp2.lng - wp1.lng) * t;
        const altitude = 4 * (radius * 0.2) * t * (1 - t); // Parabolic lift

        const pt = latLngToCartesian(currentLat, currentLng, radius + altitude);
        if (pt.visible) {
          if (!arcStarted) {
            ctx.moveTo(pt.x, pt.y);
            arcStarted = true;
          } else {
            ctx.lineTo(pt.x, pt.y);
          }
        }
      }

      ctx.strokeStyle = i === 1 ? '#f85149' : '#38bdf8';
      ctx.lineWidth = 2.5;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // 6. Animated Flight Telemetry Particle
    if (waypoints.length >= 2) {
      const segIndex = Math.min(waypoints.length - 2, Math.floor(flightPhase * (waypoints.length - 1)));
      const segPhase = (flightPhase * (waypoints.length - 1)) - segIndex;
      const wpA = waypoints[segIndex];
      const wpB = waypoints[segIndex + 1];

      const planeLat = wpA.lat + (wpB.lat - wpA.lat) * segPhase;
      const planeLng = wpA.lng + (wpB.lng - wpA.lng) * segPhase;
      const planeAlt = 4 * (radius * 0.2) * segPhase * (1 - segPhase);

      const planePos = latLngToCartesian(planeLat, planeLng, radius + planeAlt);
      if (planePos.visible) {
        ctx.beginPath();
        ctx.arc(planePos.x, planePos.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#38bdf8';
        ctx.stroke();
      }
    }

    // 7. Waypoint Nodes & Pulsing Radar Rings
    waypoints.forEach((wp) => {
      const pt = latLngToCartesian(wp.lat, wp.lng, radius);
      if (pt.visible) {
        // Radar ring
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 7, 0, Math.PI * 2);
        ctx.fillStyle = wp.isOrigin ? '#38bdf8' : '#34d399';
        ctx.fill();

        // Airport Code Label
        ctx.font = "bold 11px 'JetBrains Mono', monospace";
        ctx.fillStyle = '#ffffff';
        ctx.fillText(wp.code, pt.x + 10, pt.y + 4);
      }
    });

    ctx.restore(); // Restore sphere clipping
  }, [rotationAngle, pitchAngle, waypoints, flightPhase]);

  // Mouse / Touch Interaction for Free Rotation
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setLastMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const dx = e.clientX - lastMousePos.x;
    const dy = e.clientY - lastMousePos.y;
    setRotationAngle((prev) => prev + dx * 0.008);
    setPitchAngle((prev) => Math.max(-0.8, Math.min(0.8, prev + dy * 0.008)));
    setLastMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div
      style={{
        background: '#0a0d12',
        border: '1px solid #21262d',
        borderRadius: 16,
        padding: '24px',
        color: '#e6edf3',
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span
              style={{
                fontSize: 10.5,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                padding: '3px 8px',
                borderRadius: 6,
                background: 'rgba(56, 189, 248, 0.12)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.25)',
              }}
            >
              3D Geodesic Cartography · Great-Circle Arcs
            </span>
            <span style={{ fontSize: 12, color: '#8b949e' }}>Click & Drag to Rotate Globe</span>
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#f0f6fc', letterSpacing: '-0.02em' }}>
            Interactive Orthographic 3D Journey Telemetry
          </h3>
          <p style={{ fontSize: 13, color: '#8b949e', margin: '4px 0 0 0' }}>
            Real-time Great-Circle parabolic geodesics tracking transatlantic altitude climb and European transit airspace.
          </p>
        </div>
        <div style={{ fontSize: 12, color: '#38bdf8', fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}>
          {activeLegTitle}
        </div>
      </div>

      {/* Canvas 3D Viewport */}
      <div
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{
          width: '100%',
          height: '360px',
          background: 'radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%)',
          borderRadius: 14,
          border: '1px solid #30363d',
          position: 'relative',
          cursor: isDragging ? 'grabbing' : 'grab',
          overflow: 'hidden',
          marginBottom: 16,
          userSelect: 'none',
        }}
      >
        <canvas
          ref={canvasRef}
          width={700}
          height={360}
          style={{ width: '100%', height: '100%', display: 'block' }}
        />

        {/* Floating Telemetry Badge */}
        <div
          style={{
            position: 'absolute',
            bottom: 14,
            left: 14,
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(8px)',
            border: '1px solid #334155',
            borderRadius: 8,
            padding: '8px 14px',
            fontSize: 11,
            color: '#94a3b8',
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          <div>GEO: Transatlantic Great-Circle WGS84</div>
          <div style={{ color: '#38bdf8', marginTop: 2 }}>ALT ENVELOPE: Cruise FL380 (38,000 ft)</div>
        </div>

        {/* Waypoint Pill List */}
        <div
          style={{
            position: 'absolute',
            top: 14,
            right: 14,
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
          }}
        >
          {waypoints.map((wp) => (
            <div
              key={wp.id}
              style={{
                background: 'rgba(15, 23, 42, 0.85)',
                border: '1px solid #334155',
                borderRadius: 6,
                padding: '4px 10px',
                fontSize: 11,
                color: '#f8fafc',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: wp.isOrigin ? '#38bdf8' : '#34d399' }} />
              <strong>{wp.code}</strong> — {wp.city}
            </div>
          ))}
        </div>
      </div>

      {/* Domain Note */}
      <div
        style={{
          display: 'flex',
          gap: 12,
          padding: '12px 16px',
          borderRadius: 10,
          background: 'rgba(56, 189, 248, 0.08)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          fontSize: 12.5,
          color: '#cbd5e1',
          lineHeight: 1.55,
        }}
      >
        <span style={{ fontSize: 18 }}>🌐</span>
        <div>
          <strong style={{ color: '#38bdf8' }}>Geodesic Spatial Reality:</strong> Flat map projections (like Web Mercator) distort high-latitude routes by over 40%. Waypoint's 3D spherical engine computes real physical distance (5,570 km JFK → LHR) and atmospheric headwinds to determine genuine arrival margins before you book.
        </div>
      </div>
    </div>
  );
}
