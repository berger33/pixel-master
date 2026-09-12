import { useCallback, useEffect, useState } from 'react';
import { api, manifestUrl, sheetUrl } from './api';
import ControlPanel from './components/ControlPanel';
import ImportPanel from './components/ImportPanel';
import SidePanel from './components/SidePanel';
import SpritePreview from './components/SpritePreview';
import type {
  AnimationName,
  BatchExportResult,
  CharacterAsset,
  Direction,
  ExportBundle,
  ExportOptions,
  ImportInfo,
  Manifest,
  Meta,
} from './types';

const DIRECTIONS: Direction[] = ['down', 'left', 'right', 'up'];
const ANIMATIONS: AnimationName[] = ['idle', 'walk', 'death'];

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [mode, setMode] = useState<'procedural' | 'import'>('procedural');

  const [asset, setAsset] = useState<CharacterAsset | null>(null);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [library, setLibrary] = useState<CharacterAsset[]>([]);
  const [bundle, setBundle] = useState<ExportBundle | null>(null);
  const [importInfo, setImportInfo] = useState<ImportInfo | null>(null);

  const [direction, setDirection] = useState<Direction>('down');
  const [animation, setAnimation] = useState<AnimationName>('idle');
  const [zoom, setZoom] = useState(5);
  const [playing, setPlaying] = useState(true);

  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportingBatch, setExportingBatch] = useState(false);
  const [batch, setBatch] = useState<BatchExportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshLibrary = useCallback(async () => {
    try {
      setLibrary(await api.list());
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    api
      .meta()
      .then(setMeta)
      .catch((e) => setError(String(e)));
    refreshLibrary();
  }, [refreshLibrary]);

  const adopt = useCallback(async (next: CharacterAsset) => {
    setAsset(next);
    setBundle(null);
    setError(null);
    try {
      const m = await api.manifest(next.id);
      setManifest(m);
      // escolhe uma animação/direção válidas para o asset
      if (!m.animations[animation]) setAnimation('idle');
      if (!m.animations[animation]?.directions[direction]) setDirection('down');
    } catch (e) {
      setError(String(e));
    }
    refreshLibrary();
  }, [animation, direction, refreshLibrary]);

  const onGenerate = useCallback(
    async (payload: Record<string, unknown>) => {
      setBusy(true);
      setError(null);
      try {
        const res = await api.generate(payload);
        await adopt(res.asset);
      } catch (e) {
        setError(String(e));
      } finally {
        setBusy(false);
      }
    },
    [adopt],
  );

  const onImport = useCallback(
    async (form: FormData) => {
      setBusy(true);
      setError(null);
      try {
        const res = await api.importImage(form);
        setImportInfo(res.import_info);
        await adopt(res.asset);
      } catch (e) {
        setError(String(e));
      } finally {
        setBusy(false);
      }
    },
    [adopt],
  );

  const onLoad = useCallback(
    async (id: string) => {
      setError(null);
      try {
        const a = await api.get(id);
        await adopt(a);
      } catch (e) {
        setError(String(e));
      }
    },
    [adopt],
  );

  const onDelete = useCallback(
    async (id: string) => {
      try {
        await api.remove(id);
        if (asset?.id === id) {
          setAsset(null);
          setManifest(null);
        }
        refreshLibrary();
      } catch (e) {
        setError(String(e));
      }
    },
    [asset, refreshLibrary],
  );

  const onExport = useCallback(
    async (options: ExportOptions) => {
      if (!asset) return;
      setExporting(true);
      setError(null);
      try {
        const b = await api.export(asset.id, options);
        setBundle(b);
        const a = document.createElement('a');
        a.href = b.download_url;
        a.download = b.filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
      } catch (e) {
        setError(String(e));
      } finally {
        setExporting(false);
      }
    },
    [asset],
  );

  const onExportBatch = useCallback(async (options: ExportOptions) => {
    setExportingBatch(true);
    setError(null);
    try {
      const b = await api.exportBatch({ ids: null, options });
      setBatch(b);
      const a = document.createElement('a');
      a.href = b.download_url;
      a.download = b.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      setError(String(e));
    } finally {
      setExportingBatch(false);
    }
  }, []);

  const availableAnims = manifest ? ANIMATIONS.filter((a) => manifest.animations[a]) : ANIMATIONS;
  const availableDirs =
    manifest && animation ? DIRECTIONS.filter((d) => manifest.animations[animation]?.directions[d]) : DIRECTIONS;

  return (
    <div className="app">
      <header>
        <div className="brand">
          <span className="logo">🎮</span>
          <div>
            <h1>Pixel Master</h1>
            <span className="muted">forjador de personagens &amp; criaturas de Vandoria</span>
          </div>
        </div>
        <nav className="tabs">
          <button className={mode === 'procedural' ? 'active' : ''} onClick={() => setMode('procedural')}>
            ⚙️ Procedural
          </button>
          <button className={mode === 'import' ? 'active' : ''} onClick={() => setMode('import')}>
            🖼️ Foto de IA
          </button>
        </nav>
      </header>

      {error && <div className="error">❌ {error}</div>}

      <main>
        <div className="left">
          {mode === 'procedural' ? (
            <ControlPanel meta={meta} busy={busy} onGenerate={onGenerate} />
          ) : (
            <ImportPanel meta={meta} busy={busy} lastInfo={importInfo} onImport={onImport} />
          )}
        </div>

        <div className="center">
          <section className="panel preview-panel">
            <div className="preview-controls">
              <div className="seg">
                {availableDirs.map((d) => (
                  <button key={d} className={direction === d ? 'active' : ''} onClick={() => setDirection(d)}>
                    {d}
                  </button>
                ))}
              </div>
              <div className="seg">
                {availableAnims.map((a) => (
                  <button key={a} className={animation === a ? 'active' : ''} onClick={() => setAnimation(a)}>
                    {a}
                  </button>
                ))}
              </div>
              <button className="ghost" onClick={() => setPlaying((p) => !p)}>
                {playing ? '⏸ pausar' : '▶ reproduzir'}
              </button>
              <label className="slider inline">
                zoom <b>{zoom}×</b>
                <input type="range" min={2} max={10} step={1} value={zoom} onChange={(e) => setZoom(Number(e.target.value))} />
              </label>
            </div>
            <SpritePreview
              sheetSrc={asset ? sheetUrl(asset.id, 1) : null}
              manifest={manifest}
              direction={direction}
              animation={animation}
              zoom={zoom}
              playing={playing}
            />
            {!asset && <p className="hint center-hint">Gere um personagem ou importe uma foto de IA para ver a pré-visualização animada.</p>}
          </section>
        </div>

        <SidePanel
          asset={asset}
          library={library}
          bundle={bundle}
          batch={batch}
          exporting={exporting}
          exportingBatch={exportingBatch}
          onExport={onExport}
          onExportBatch={onExportBatch}
          onLoad={onLoad}
          onDelete={onDelete}
        />
      </main>
    </div>
  );
}
