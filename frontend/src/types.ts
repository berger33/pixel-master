export type Direction = 'down' | 'left' | 'right' | 'up';
export type AnimationName = 'idle' | 'walk' | 'death';

export interface StatBlock {
  level: number;
  health: number;
  mana: number;
  attack: number;
  defense: number;
  magic_attack: number;
  magic_defense: number;
  speed: number;
  stamina: number;
  accuracy: number;
  evasion: number;
  experience_reward: number;
  gold_reward: number;
}

export interface AbilitySpec {
  key: string;
  name: string;
  description: string;
  kind: string;
  power: number;
  cooldown: number;
  cost: number;
}

export interface ProceduralBlueprint {
  seed: number;
  species: string;
  archetype: string;
  gender: 'male' | 'female' | 'neutral';
  body_size: number;
  head_size: number;
  limb_thickness: number;
  hair_style: string | null;
  hair_length: number;
  facial_hair: boolean;
  eyes_style: string;
  skin_tone: string | null;
  outfit: string;
  armor_level: number;
  headgear: string | null;
  weapon: string | null;
  offhand: string | null;
  cape: boolean;
  wings: boolean;
  horns: string | null;
  tail: string | null;
  extra_limbs: number;
  spikes: number;
  outline: boolean;
  shading: boolean;
}

export interface CharacterAsset {
  id: string;
  slug: string;
  name: string;
  kind: 'character' | 'creature';
  species: string;
  description: string;
  rarity: string;
  tags: string[];
  origin: 'procedural' | 'image';
  seed: number;
  procedural: ProceduralBlueprint | null;
  image_params: Record<string, unknown> | null;
  source_image_ref: string | null;
  stats: StatBlock;
  abilities: AbilitySpec[];
  frame_width: number;
  frame_height: number;
  created_at: string;
  updated_at: string;
}

export interface PreviewUrls {
  pose: Record<string, string>;
  strip: Record<string, string>;
  sheet: string;
  gif: string;
  manifest: string;
}

export interface GenerateResponse {
  asset: CharacterAsset;
  preview: PreviewUrls;
  frame_count: number;
  color_count: number;
}

export interface ImportInfo {
  detectedView: string;
  sourceSize: number[];
  paletteSize: number;
  backgroundRemoved: boolean;
  warnings: string[];
  directions: string[];
}

export interface ImportResponse {
  asset: CharacterAsset;
  preview: PreviewUrls;
  import_info: ImportInfo;
}

export interface SpeciesInfo {
  key: string;
  name: string;
  kind: string;
  archetype: string;
  rarity: string;
  tags: string[];
  hairStyles: string[];
  outfits: string[];
  weapons: string[];
  headgear: string[];
  horns: string[];
  tails: string[];
  wings: boolean;
}

export interface Meta {
  species: SpeciesInfo[];
  archetypes: string[];
  hair_styles: string[];
  headgear: string[];
  weapons: string[];
  offhands: string[];
  outfits: string[];
  horns: string[];
  tails: string[];
  palettes: Record<string, string[]>;
  rarities: string[];
  directions: string[];
  animations: string[];
  abilities: { key: string; name: string; kind: string; description: string }[];
}

export interface ManifestDirection {
  frames: string[];
  order: number[];
  count: number;
}

export interface ManifestAnimation {
  fps: number;
  loops: boolean;
  pingPong: boolean;
  directions: Record<string, ManifestDirection>;
}

export interface Manifest {
  frameWidth: number;
  frameHeight: number;
  columns: number;
  rows: number;
  frameCount: number;
  anchor: { x: number; y: number };
  animations: Record<string, ManifestAnimation>;
  animationStartIndex: Record<string, Record<string, number>>;
}

export interface AnimationSpec {
  name: AnimationName;
  fps: number;
  loops: boolean;
  directions: string[];
  frames_per_direction: Record<string, number>;
}

export interface ExportBundle {
  asset_id: string;
  filename: string;
  size_bytes: number;
  files: string[];
  sprite_width: number;
  sprite_height: number;
  atlas_width: number;
  atlas_height: number;
  frame_count: number;
  color_count: number;
  animations: AnimationSpec[];
  download_url: string;
}

export interface ExportOptions {
  formats: string[];
  include_sparrow_xml: boolean;
  include_gif_preview: boolean;
  include_individual_frames: boolean;
  include_manifest: boolean;
  include_stats: boolean;
  include_vandoria_card: boolean;
  scale: number;
  transparent_background: boolean;
}
