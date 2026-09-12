# Integração Pixel Master ⇄ Vandoria

Este diretório contém o helper oficial de integração para **Phaser 3**
(`pixelmaster-loader.js`) e a documentação do contrato de exportação.

## Arquivos de um pacote exportado

| Arquivo | Para que serve |
|---|---|
| `spritesheet.png` | Atlas de grade uniforme (todos os quadros de todas as animações/direções) |
| `manifest.json` | Índices de animação por direção + fps + âncora — o "mapa" do atlas |
| `atlas_phaser.json` / `atlas_phaser_array.json` | Formatos TexturePacker (Phaser/PixiJS) |
| `atlas_sparrow.xml` | Formato Sparrow/Starling (outros motores 2D) |
| `atlas_aseprite.json` | Tags para reimportar no Aseprite |
| `preview.gif` | Pré-visualização animada (idle → walk → death) |
| `frames/*.png` | Quadros individuais (opcional) |
| `card.json` | **Ficha funcional**: stats, habilidades, recompensas — para o backend de combate |
| `README.txt` | Instruções rápidas geradas por personagem |

## Convenção de grade

* Quadro fixo de `frameWidth × frameHeight` (padrão 64×64).
* Cada **linha** = um par `(animação, direção)`, na ordem `idle, walk, death` ×
  `down, left, right, up`.
* Cada **coluna** = um quadro da sequência.
* O sprite é alinhado pela **base** (os pés encostam no fundo da célula), então
  `origin (0.5, 1.0)` posiciona corretamente no chão do mapa.

## Uso em Phaser 3

```js
import { loadPixelMasterCharacter, spawnCharacter, loadCharacterCard } from './pixelmaster-loader.js';

class CenaVandoria extends Phaser.Scene {
  async create() {
    const baseUrl = '/api/characters/' + this.personagemId;
    await loadPixelMasterCharacter(this, 'hero', baseUrl);

    this.hero = spawnCharacter(this, 'hero', 400, 300);
    this.card = await loadCharacterCard(baseUrl);   // stats p/ combate

    this.input.keyboard.on('keydown-LEFT',  () => { this.hero.setDirection('left');  this.hero.walk(); });
    this.input.keyboard.on('keydown-RIGHT', () => { this.hero.setDirection('right'); this.hero.walk(); });
    this.input.keyboard.on('keydown-UP',    () => { this.hero.setDirection('up');    this.hero.walk(); });
    this.input.keyboard.on('keydown-DOWN',  () => { this.hero.setDirection('down');  this.hero.walk(); });
    this.input.keyboard.on('keyup',         () => this.hero.idle());
  }
}
```

## Uso da ficha funcional no backend de combate

`card.json` traz exatamente o que um sistema de combate precisa:

```jsonc
{
  "id": "...", "slug": "cacadora-elfica", "name": "Caçadora Élfica",
  "species": "elf", "rarity": "epic",
  "stats": { "level": 12, "health": 214, "mana": 66, "attack": 27,
             "defense": 18, "speed": 11, "experience_reward": 96, "gold_reward": 65 },
  "powerRating": 318,
  "abilities": [ { "key": "flecha_arcana", "name": "Flecha Arcana",
                   "kind": "attack", "power": 18, "cooldown": 7.0, "cost": 10 } ],
  "sprite": { "atlas": "spritesheet.png", "frameWidth": 64, "frameHeight": 64,
              "anchor": { "x": 0.5, "y": 1.0 } },
  "animations": { "walk": { "fps": 8, "loops": true, "directions": { ... } } }
}
```
