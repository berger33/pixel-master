import { useRef, useState } from 'react';
import type { ImportInfo, Meta } from '../types';

interface Props {
  meta: Meta | null;
  busy: boolean;
  lastInfo: ImportInfo | null;
  onImport: (form: FormData) => void;
}

/**
 * Modo "foto de IA": envia um render em alta resolução e o backend o converte
 * em um personagem jogável (recorte, pixelização, 4 direções e animações).
 */
export default function ImportPanel({ meta, busy, lastInfo, onImport }: Props) {
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [fileName, setFileName] = useState('');
  const [name, setName] = useState('');
  const [species, setSpecies] = useState('human');
  const [rarity, setRarity] = useState('common');
  const [level, setLevel] = useState(1);
  const [targetSize, setTargetSize] = useState(52);
  const [paletteSize, setPaletteSize] = useState(16);
  const [tolerance, setTolerance] = useState(38);
  const [squeeze, setSqueeze] = useState(0.74);
  const [background, setBackground] = useState<'auto' | 'alpha' | 'keep'>('auto');
  const [outline, setOutline] = useState(true);

  const pick = (f: File | null) => {
    if (!f) return;
    setFileName(f.name);
    if (!name) setName(f.name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' '));
  };

  const submit = () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    form.append('name', name.trim() || file.name);
    form.append('kind', meta?.species.find((s) => s.key === species)?.kind ?? 'character');
    form.append('rarity', rarity);
    form.append('level', String(level));
    form.append('species', species);
    form.append('description', 'Importado de um render de IA pelo Pixel Master.');
    form.append(
      'params',
      JSON.stringify({
        target_size: targetSize,
        palette_size: paletteSize,
        background_tolerance: tolerance,
        background,
        outline,
        side_squeeze: squeeze,
        synthesize_directions: true,
      }),
    );
    onImport(form);
  };

  return (
    <div className="panel">
      <h2>🖼️ Importar render de IA</h2>
      <p className="hint">
        Envie uma imagem de personagem em alta resolução (fundo simples funciona melhor). O Pixel
        Master recorta, pixeliza, sintetiza as 4 direções e anima (idle / walk / death).
      </p>

      <div
        className="dropzone"
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          pick(e.dataTransfer.files?.[0] ?? null);
        }}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".png,.jpg,.jpeg,.webp,.bmp"
          hidden
          onChange={(e) => pick(e.target.files?.[0] ?? null)}
        />
        {fileName ? `📎 ${fileName}` : 'Clique ou arraste a imagem aqui'}
      </div>

      <div className="grid2">
        <label className="span2">
          Nome
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="ex.: Caçadora Élfica" />
        </label>
        <label>
          Espécie (ficha)
          <select value={species} onChange={(e) => setSpecies(e.target.value)}>
            {meta?.species.map((s) => (
              <option key={s.key} value={s.key}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Raridade
          <select value={rarity} onChange={(e) => setRarity(e.target.value)}>
            {meta?.rarities.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
        <label>
          Nível
          <input type="number" min={1} max={255} value={level} onChange={(e) => setLevel(Number(e.target.value))} />
        </label>
        <label>
          Fundo
          <select value={background} onChange={(e) => setBackground(e.target.value as 'auto' | 'alpha' | 'keep')}>
            <option value="auto">automático</option>
            <option value="alpha">usar alfa</option>
            <option value="keep">manter</option>
          </select>
        </label>
      </div>

      <div className="sliders">
        <Slider label="Altura alvo (px)" value={targetSize} min={24} max={64} step={1} onChange={setTargetSize} fmt={(v) => v.toFixed(0)} />
        <Slider label="Cores da paleta" value={paletteSize} min={4} max={32} step={1} onChange={setPaletteSize} fmt={(v) => v.toFixed(0)} />
        <Slider label="Tolerância de fundo" value={tolerance} min={0} max={120} step={1} onChange={setTolerance} fmt={(v) => v.toFixed(0)} />
        <Slider label="Compressão lateral" value={squeeze} min={0.5} max={1} step={0.02} onChange={setSqueeze} />
      </div>
      <div className="checks">
        <label className="check">
          <input type="checkbox" checked={outline} onChange={(e) => setOutline(e.target.checked)} />
          Contorno
        </label>
      </div>

      <button className="primary big" disabled={busy || !fileName} onClick={submit}>
        {busy ? 'Convertendo…' : '🪄 Transformar em personagem'}
      </button>

      {lastInfo && (
        <div className="info-card">
          <div>
            <b>vista detectada:</b> {lastInfo.detectedView} · <b>fundo removido:</b>{' '}
            {lastInfo.backgroundRemoved ? 'sim' : 'não'}
          </div>
          <div>
            <b>origem:</b> {lastInfo.sourceSize.join('×')} px · <b>paleta:</b> {lastInfo.paletteSize} cores ·{' '}
            <b>direções:</b> {lastInfo.directions.join(', ')}
          </div>
          {lastInfo.warnings.length > 0 && (
            <div className="warn">⚠️ {lastInfo.warnings.join(' · ')}</div>
          )}
        </div>
      )}
    </div>
  );
}

function Slider(props: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
  fmt?: (v: number) => string;
}) {
  const fmt = props.fmt ?? ((v: number) => v.toFixed(2));
  return (
    <label className="slider">
      <span>
        {props.label} <b>{fmt(props.value)}</b>
      </span>
      <input
        type="range"
        min={props.min}
        max={props.max}
        step={props.step}
        value={props.value}
        onChange={(e) => props.onChange(Number(e.target.value))}
      />
    </label>
  );
}
