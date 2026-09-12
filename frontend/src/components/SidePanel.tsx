import { useState } from 'react';
import { thumbUrl } from '../api';
import type { BatchExportResult, CharacterAsset, ExportBundle, ExportOptions } from '../types';

interface Props {
  asset: CharacterAsset | null;
  library: CharacterAsset[];
  bundle: ExportBundle | null;
  batch: BatchExportResult | null;
  exporting: boolean;
  exportingBatch: boolean;
  onExport: (options: ExportOptions) => void;
  onExportBatch: (options: ExportOptions) => void;
  onLoad: (id: string) => void;
  onDelete: (id: string) => void;
}

const FORMATS: { id: string; label: string }[] = [
  { id: 'phaser_hash', label: 'Phaser JSON Hash' },
  { id: 'uniform_grid', label: 'Grade uniforme + manifesto' },
  { id: 'phaser_array', label: 'Phaser JSON Array' },
  { id: 'aseprite_sheet', label: 'Aseprite (tags)' },
];

export default function SidePanel({
  asset,
  library,
  bundle,
  batch,
  exporting,
  exportingBatch,
  onExport,
  onExportBatch,
  onLoad,
  onDelete,
}: Props) {
  const [formats, setFormats] = useState<string[]>(['phaser_hash', 'uniform_grid']);
  const [scale, setScale] = useState(1);
  const [gif, setGif] = useState(true);
  const [frames, setFrames] = useState(false);
  const [card, setCard] = useState(true);

  const toggle = (id: string) =>
    setFormats((f) => (f.includes(id) ? f.filter((x) => x !== id) : [...f, id]));

  const stats = asset?.stats;

  return (
    <div className="side">
      {/* ------------------------------------------------------------ ficha */}
      <section className="panel">
        <h2>📜 Ficha funcional</h2>
        {!asset ? (
          <p className="hint">Gere ou importe um personagem para ver a ficha.</p>
        ) : (
          <>
            <div className="asset-head">
              <img src={thumbUrl(asset.id, 'down', 3)} alt={asset.name} className="thumb" />
              <div>
                <b>{asset.name}</b>
                <div className="muted">
                  {asset.species} · {asset.rarity} · nv {stats?.level} · {asset.origin === 'image' ? 'foto de IA' : 'procedural'}
                </div>
                <div className="muted">seed {asset.seed}</div>
              </div>
            </div>
            {stats && (
              <table className="stats">
                <tbody>
                  <Row k="Vida" v={stats.health} />
                  <Row k="Mana" v={stats.mana} />
                  <Row k="Ataque" v={stats.attack} />
                  <Row k="Defesa" v={stats.defense} />
                  <Row k="Atq. mágico" v={stats.magic_attack} />
                  <Row k="Def. mágica" v={stats.magic_defense} />
                  <Row k="Velocidade" v={stats.speed} />
                  <Row k="Vigor" v={stats.stamina} />
                  <Row k="Precisão" v={`${stats.accuracy}%`} />
                  <Row k="Evasão" v={`${stats.evasion}%`} />
                  <Row k="XP (recompensa)" v={stats.experience_reward} />
                  <Row k="Ouro (recompensa)" v={stats.gold_reward} />
                </tbody>
              </table>
            )}
            {asset.abilities.length > 0 && (
              <ul className="abilities">
                {asset.abilities.map((a) => (
                  <li key={a.key} title={a.description}>
                    <span className={`tag tag-${a.kind}`}>{a.kind}</span> {a.name}
                    {a.power > 0 ? ` (${a.power})` : ''}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </section>

      {/* --------------------------------------------------------- exportar */}
      <section className="panel">
        <h2>📦 Exportar para o Vandoria</h2>
        <div className="checks col">
          {FORMATS.map((f) => (
            <label key={f.id} className="check">
              <input type="checkbox" checked={formats.includes(f.id)} onChange={() => toggle(f.id)} />
              {f.label}
            </label>
          ))}
          <label className="check">
            <input type="checkbox" checked={gif} onChange={(e) => setGif(e.target.checked)} /> preview.gif
          </label>
          <label className="check">
            <input type="checkbox" checked={frames} onChange={(e) => setFrames(e.target.checked)} /> quadros individuais
          </label>
          <label className="check">
            <input type="checkbox" checked={card} onChange={(e) => setCard(e.target.checked)} /> card.json (stats p/ backend)
          </label>
        </div>
        <label className="slider">
          <span>
            Escala do PNG <b>{scale}×</b>
          </span>
          <input type="range" min={1} max={8} step={1} value={scale} onChange={(e) => setScale(Number(e.target.value))} />
        </label>
        <button
          className="primary big"
          disabled={!asset || exporting}
          onClick={() =>
            onExport({
              formats,
              include_sparrow_xml: false,
              include_gif_preview: gif,
              include_individual_frames: frames,
              include_manifest: true,
              include_stats: card,
              include_vandoria_card: card,
              scale,
              transparent_background: true,
            })
          }
        >
          {exporting ? 'Empacotando…' : '⬇️ Baixar pacote (.zip)'}
        </button>
        {bundle && (
          <div className="info-card">
            <div>
              <b>{bundle.filename}</b> · {(bundle.size_bytes / 1024).toFixed(1)} KB
            </div>
            <div>
              atlas {bundle.atlas_width}×{bundle.atlas_height} · {bundle.frame_count} quadros ·{' '}
              {bundle.color_count} cores
            </div>
            <div className="muted">{bundle.files.length} arquivos no pacote</div>
            <a className="linklike" href={bundle.download_url} download={bundle.filename}>
              baixar novamente ↗
            </a>
          </div>
        )}
      </section>

      {/* -------------------------------------------------------- biblioteca */}
      <section className="panel">
        <h2>🗄️ Biblioteca ({library.length})</h2>
        <button
          className="primary"
          style={{ width: '100%', marginBottom: 10 }}
          disabled={library.length === 0 || exportingBatch}
          onClick={() =>
            onExportBatch({
              formats,
              include_sparrow_xml: false,
              include_gif_preview: gif,
              include_individual_frames: false,
              include_manifest: true,
              include_stats: card,
              include_vandoria_card: card,
              scale: 1,
              transparent_background: true,
            })
          }
        >
          {exportingBatch ? 'Empacotando bestiário…' : `📚 Exportar bestiário completo (${library.length})`}
        </button>
        {batch && (
          <div className="info-card">
            <div>
              <b>{batch.filename}</b> · {(batch.size_bytes / 1024).toFixed(1)} KB
            </div>
            <div className="muted">
              {batch.character_count} personagens · {batch.files.length} arquivos · inclui bestiary.json +
              contact_sheet.png
            </div>
            <a className="linklike" href={batch.download_url} download={batch.filename}>
              baixar novamente ↗
            </a>
          </div>
        )}
        {library.length === 0 ? (
          <p className="hint">Nenhum personagem salvo ainda.</p>
        ) : (
          <ul className="library">
            {library.map((a) => (
              <li key={a.id} className={asset?.id === a.id ? 'active' : ''}>
                <img src={thumbUrl(a.id, 'down', 2)} alt={a.name} loading="lazy" />
                <div className="lib-meta">
                  <b>{a.name}</b>
                  <span className="muted">
                    {a.species} · {a.rarity}
                  </span>
                </div>
                <div className="lib-actions">
                  <button title="carregar" onClick={() => onLoad(a.id)}>
                    abrir
                  </button>
                  <button title="excluir" className="danger" onClick={() => onDelete(a.id)}>
                    ✕
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function Row({ k, v }: { k: string; v: number | string }) {
  return (
    <tr>
      <td>{k}</td>
      <td className="num">{v}</td>
    </tr>
  );
}
