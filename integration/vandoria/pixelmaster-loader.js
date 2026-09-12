/**
 * Pixel Master → Vandoria (Phaser 3)
 * ----------------------------------
 * Helper oficial de integração. Carrega um pacote do Pixel Master direto da
 * API e registra um personagem jogável na cena, com animações de
 * idle / walk / death nas 4 direções.
 *
 * Uso:
 *   import { loadPixelMasterCharacter, spawnCharacter } from './pixelmaster-loader.js';
 *
 *   // no preload/create da cena:
 *   await loadPixelMasterCharacter(this, 'hero', '/api/characters/<id>');
 *   const hero = spawnCharacter(this, 'hero', 400, 300);
 *   hero.walk('left');
 *   hero.die();
 *
 * O loader usa SOMENTE o manifesto de grade uniforme + o atlas PNG, ou seja,
 * o mesmo caminho que qualquer sprite comum do Phaser — sem dependências.
 */

const DIRECTIONS = ['down', 'left', 'right', 'up'];

/**
 * Baixa manifesto + atlas e registra todas as animações do personagem.
 * @param {Phaser.Scene} scene
 * @param {string} key     chave única do sprite na cena
 * @param {string} baseUrl URL base do personagem (ex.: /api/characters/abc123)
 */
export async function loadPixelMasterCharacter(scene, key, baseUrl) {
  const manifestRes = await fetch(`${baseUrl}/manifest.json`);
  if (!manifestRes.ok) throw new Error(`Pixel Master: manifesto indisponível (${manifestRes.status})`);
  const manifest = await manifestRes.json();

  await new Promise((resolve, reject) => {
    scene.load.spritesheet(key, `${baseUrl}/sheet.png?scale=1`, {
      frameWidth: manifest.frameWidth,
      frameHeight: manifest.frameHeight,
    });
    scene.load.once(`filecomplete-spritesheet-${key}`, resolve);
    scene.load.once('loaderror', reject);
    scene.load.start();
  });

  const start = manifest.animationStartIndex;
  const counts = manifest.animationFrameCounts;

  for (const animName of Object.keys(manifest.animations)) {
    const fps = manifest.animations[animName].fps;
    const loops = manifest.animations[animName].loops;
    for (const dir of DIRECTIONS) {
      if (!(dir in start[animName])) continue;
      const from = start[animName][dir];
      const to = from + counts[animName][dir] - 1;
      const animKey = `${key}_${animName}_${dir}`;
      if (scene.anims.exists(animKey)) continue;
      scene.anims.create({
        key: animKey,
        frames: scene.anims.generateFrameNumbers(key, { start: from, end: to }),
        frameRate: fps,
        repeat: loops ? -1 : 0,
      });
    }
  }
  return manifest;
}

/**
 * Cria um sprite controlável do personagem já carregado.
 * @returns sprite com métodos walk(dir), idle(dir), die(), stopMoving()
 */
export function spawnCharacter(scene, key, x, y, direction = 'down') {
  const sprite = scene.add.sprite(x, y, key);
  sprite.setOrigin(0.5, 1.0); // pés no chão
  sprite._pmDirection = direction;
  sprite.play(`${key}_idle_${direction}`);

  sprite.setDirection = (dir) => {
    sprite._pmDirection = dir;
    const current = sprite.anims.currentAnim?.key ?? '';
    if (current.includes('_walk_')) sprite.play(`${key}_walk_${dir}`);
    else sprite.play(`${key}_idle_${dir}`);
    // espelha horizontalmente quando olha para a direita, se só houver left
    return sprite;
  };

  sprite.idle = (dir = sprite._pmDirection) => sprite.play(`${key}_idle_${dir}`, true);
  sprite.walk = (dir = sprite._pmDirection) => sprite.play(`${key}_walk_${dir}`, true);
  sprite.stopMoving = () => sprite.idle();

  sprite.die = () => {
    sprite.play(`${key}_death_${sprite._pmDirection}`, true);
    sprite.once('animationcomplete', () => sprite.setAlpha(0.6));
    return sprite;
  };

  return sprite;
}

/**
 * Atalho: carrega a *ficha funcional* (stats + habilidades) para o backend/combate.
 */
export async function loadCharacterCard(baseUrl) {
  const res = await fetch(`${baseUrl}/card.json`);
  if (!res.ok) throw new Error(`Pixel Master: card indisponível (${res.status})`);
  return res.json();
}

export default { loadPixelMasterCharacter, spawnCharacter, loadCharacterCard };
