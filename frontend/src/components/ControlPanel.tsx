import { useEffect, useMemo, useState } from 'react';
import type { Meta } from '../types';

export interface ProcForm {
  name: string;
  rarity: string;
  level: number;
  seed: number;
  species: string;
  gender: 'male' | 'female' | 'neutral';
  body_size: number;
  head_size: number;
  limb_thickness: number;
  hair_style: string;
  hair_length: number;
  facial_hair: boolean;
  outfit: string;
  armor_level: number;
  headgear: string;
  weapon: string;
  offhand: string;
  horns: string;
  tail: string;
  cape: boolean;
  wings: boolean;
  outline: boolean;
  shading: boolean;
}

const NONE = '—';

const defaultForm = (): ProcForm => ({
  name: '',
  rarity: 'common',
  level: 1,
  seed: 1234,
  species: 'human',
  gender: 'neutral',
  body_size: 1,
  head_size: 1,
  limb_thickness: 1,
  hair_style: '',
  hair_length: 0.5,
  facial_hair: false,
  outfit: 'adventurer',
  armor_level: 1,
  headgear: '',
  weapon: '',
  offhand: '',
  horns: '',
  tail: '',
  cape: false,
  wings: false,
  outline: true,
  shading: true,
});

interface Props {
  meta: Meta | null;
  busy: boolean;
  onGenerate: (payload: Record<string, unknown>) => void;
}

export default function ControlPanel({ meta, busy, onGenerate }: Props) {
  const [form, setForm] = useState<ProcForm>(defaultForm);

  const species = useMemo(
    () => meta?.species.find((s) => s.key === form.species) ?? null,
    [meta, form.species],
  );

  // ao trocar de espécie, adota os padrões dela
  useEffect(() => {
    if (!species) return;
    setForm((f) => ({
      ...f,
      outfit: species.outfits.includes(f.outfit) ? f.outfit : species.outfits[0] ?? 'adventurer',
      weapon: species.weapons.includes(f.weapon) ? f.weapon : species.weapons[0] ?? '',
      hair_style: species.hairStyles.includes(f.hair_style) ? f.hair_style : species.hairStyles[0] ?? '',
      headgear: '',
      horns: species.horns[0] ?? '',
      tail: species.tails[0] ?? '',
      wings: species.wings,
    }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.species]);

  const set = <K extends keyof ProcForm>(key: K, value: ProcForm[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const submit = () => {
    const kind = species?.kind ?? 'character';
    const name = form.name.trim() || `${species?.name ?? 'Personagem'} #${form.seed}`;
    onGenerate({
      name,
      kind,
      rarity: form.rarity,
      level: form.level,
      tags: species?.tags ?? [],
      description: `Gerado proceduralmente pelo Pixel Master (seed ${form.seed}).`,
      seed: form.seed,
      blueprint: {
        seed: form.seed,
        species: form.species,
        gender: form.gender,
        body_size: form.body_size,
        head_size: form.head_size,
        limb_thickness: form.limb_thickness,
        hair_style: form.hair_style || null,
        hair_length: form.hair_length,
        facial_hair: form.facial_hair,
        eyes_style: 'normal',
        outfit: form.outfit,
        armor_level: form.armor_level,
        headgear: form.headgear || null,
        weapon: form.weapon || null,
        offhand: form.offhand || null,
        horns: form.horns || null,
        tail: form.tail || null,
        cape: form.cape,
        wings: form.wings,
        outline: form.outline,
        shading: form.shading,
      },
    });
  };

  const opt = (v: string) => (v === '' ? NONE : v);

  return (
    <div className="panel">
      <h2>⚙️ Geração procedural</h2>
      <div className="grid2">
        <label className="span2">
          Nome
          <input value={form.name} placeholder="ex.: Cavaleiro de Vandoria" onChange={(e) => set('name', e.target.value)} />
        </label>
        <label>
          Espécie
          <select value={form.species} onChange={(e) => set('species', e.target.value)}>
            {meta?.species.map((s) => (
              <option key={s.key} value={s.key}>
                {s.name} ({s.kind})
              </option>
            ))}
          </select>
        </label>
        <label>
          Raridade
          <select value={form.rarity} onChange={(e) => set('rarity', e.target.value)}>
            {meta?.rarities.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
        <label>
          Nível
          <input type="number" min={1} max={255} value={form.level} onChange={(e) => set('level', Number(e.target.value))} />
        </label>
        <label>
          Seed
          <div className="row">
            <input type="number" value={form.seed} onChange={(e) => set('seed', Number(e.target.value))} />
            <button
              type="button"
              title="seed aleatório"
              onClick={() => set('seed', Math.floor(Math.random() * 1_000_000))}
            >
              🎲
            </button>
          </div>
        </label>
        <label>
          Vestuário
          <select value={form.outfit} onChange={(e) => set('outfit', e.target.value)}>
            {meta?.outfits.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </label>
        <label>
          Cabelo
          <select value={opt(form.hair_style)} onChange={(e) => set('hair_style', e.target.value === NONE ? '' : e.target.value)}>
            <option value={NONE}>automático</option>
            {meta?.hair_styles.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
          </select>
        </label>
        <label>
          Arma
          <select value={opt(form.weapon)} onChange={(e) => set('weapon', e.target.value === NONE ? '' : e.target.value)}>
            <option value={NONE}>nenhuma</option>
            {meta?.weapons.map((w) => (
              <option key={w} value={w}>
                {w}
              </option>
            ))}
          </select>
        </label>
        <label>
          Mão secundária
          <select value={opt(form.offhand)} onChange={(e) => set('offhand', e.target.value === NONE ? '' : e.target.value)}>
            <option value={NONE}>nenhuma</option>
            {meta?.offhands.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </label>
        <label>
          Cobertura de cabeça
          <select value={opt(form.headgear)} onChange={(e) => set('headgear', e.target.value === NONE ? '' : e.target.value)}>
            <option value={NONE}>nenhuma</option>
            {meta?.headgear.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
          </select>
        </label>
        <label>
          Chifres
          <select value={opt(form.horns)} onChange={(e) => set('horns', e.target.value === NONE ? '' : e.target.value)}>
            <option value={NONE}>nenhum</option>
            {meta?.horns.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
          </select>
        </label>
        <label>
          Cauda
          <select value={opt(form.tail)} onChange={(e) => set('tail', e.target.value === NONE ? '' : e.target.value)}>
            <option value={NONE}>nenhuma</option>
            {meta?.tails.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="sliders">
        <Slider label="Corpo" value={form.body_size} min={0.6} max={1.5} step={0.05} onChange={(v) => set('body_size', v)} />
        <Slider label="Cabeça" value={form.head_size} min={0.6} max={1.6} step={0.05} onChange={(v) => set('head_size', v)} />
        <Slider label="Membros" value={form.limb_thickness} min={0.6} max={1.6} step={0.05} onChange={(v) => set('limb_thickness', v)} />
        <Slider label="Comp. cabelo" value={form.hair_length} min={0} max={1} step={0.05} onChange={(v) => set('hair_length', v)} />
        <Slider label="Armadura" value={form.armor_level} min={0} max={4} step={1} onChange={(v) => set('armor_level', v)} />
      </div>

      <div className="checks">
        <Check label="Capa" value={form.cape} onChange={(v) => set('cape', v)} />
        <Check label="Asas" value={form.wings} onChange={(v) => set('wings', v)} />
        <Check label="Barba" value={form.facial_hair} onChange={(v) => set('facial_hair', v)} />
        <Check label="Contorno" value={form.outline} onChange={(v) => set('outline', v)} />
        <Check label="Sombreamento" value={form.shading} onChange={(v) => set('shading', v)} />
      </div>

      <button className="primary big" disabled={busy} onClick={submit}>
        {busy ? 'Gerando…' : '✨ Gerar personagem'}
      </button>
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
}) {
  return (
    <label className="slider">
      <span>
        {props.label} <b>{props.value.toFixed(2)}</b>
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

function Check(props: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="check">
      <input type="checkbox" checked={props.value} onChange={(e) => props.onChange(e.target.checked)} />
      {props.label}
    </label>
  );
}
