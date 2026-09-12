import { useEffect, useRef, useState } from 'react';
import type { AnimationName, Direction, Manifest } from '../types';

interface Props {
  sheetSrc: string | null;
  manifest: Manifest | null;
  direction: Direction;
  animation: AnimationName;
  zoom: number;
  playing: boolean;
  showGrid?: boolean;
}

/**
 * Renderiza o sprite exatamente como o jogo faria: carrega o atlas de grade
 * uniforme + o manifesto e desenha quadro a quadro num <canvas> com
 * imageSmoothing desligado (pixel-perfect).
 */
export default function SpritePreview({
  sheetSrc,
  manifest,
  direction,
  animation,
  zoom,
  playing,
  showGrid = true,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const [imageOk, setImageOk] = useState(false);
  const [frameIndex, setFrameIndex] = useState(0);

  // carrega a imagem do atlas
  useEffect(() => {
    setImageOk(false);
    if (!sheetSrc) return;
    const img = new Image();
    img.onload = () => {
      imageRef.current = img;
      setImageOk(true);
    };
    img.src = sheetSrc;
  }, [sheetSrc]);

  const anim = manifest?.animations[animation];
  const dirInfo = anim?.directions[direction];
  const startIndex = manifest?.animationStartIndex?.[animation]?.[direction] ?? 0;
  const order = dirInfo?.order ?? [0];
  const fps = anim?.fps ?? 8;
  const columns = manifest?.columns ?? 1;
  const fw = manifest?.frameWidth ?? 64;
  const fh = manifest?.frameHeight ?? 64;

  // loop de animação
  useEffect(() => {
    if (!playing || order.length <= 1) return;
    let raf = 0;
    let last = performance.now();
    let acc = 0;
    let idx = 0;
    const step = (now: number) => {
      acc += now - last;
      last = now;
      const interval = 1000 / fps;
      if (acc >= interval) {
        acc = 0;
        idx = (idx + 1) % order.length;
        setFrameIndex(idx);
      }
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [playing, fps, order.length, animation, direction]);

  useEffect(() => {
    setFrameIndex(0);
  }, [animation, direction, sheetSrc]);

  // desenho
  useEffect(() => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img || !manifest) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // fundo xadrez sutil para evidenciar transparência
    if (showGrid) {
      const cell = 8 * zoom;
      for (let y = 0; y < canvas.height / cell; y++) {
        for (let x = 0; x < canvas.width / cell; x++) {
          ctx.fillStyle = (x + y) % 2 === 0 ? '#232634' : '#2a2e3e';
          ctx.fillRect(x * cell, y * cell, cell, cell);
        }
      }
    }

    const local = order[Math.min(frameIndex, order.length - 1)] ?? 0;
    const atlasIndex = startIndex + local;
    const sx = (atlasIndex % columns) * fw;
    const sy = Math.floor(atlasIndex / columns) * fh;
    ctx.drawImage(img, sx, sy, fw, fh, 0, 0, fw * zoom, fh * zoom);
  }, [imageOk, manifest, frameIndex, zoom, startIndex, order, columns, fw, fh, showGrid]);

  const size = fw * zoom;

  return (
    <div className="preview-box">
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        style={{ width: size, height: size, imageRendering: 'pixelated' }}
      />
      <div className="preview-meta">
        <span>
          {animation} · {direction} · quadro {Math.min(frameIndex, order.length - 1) + 1}/
          {order.length} · {fps} fps
        </span>
        <span>
          atlas {manifest ? `${manifest.columns}×${manifest.rows}` : '—'} · frame {fw}×{fh}
        </span>
      </div>
    </div>
  );
}
