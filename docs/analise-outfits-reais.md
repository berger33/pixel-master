# Análise empírica — outfits reais do Tibia (medidos, não estimados)

> Este documento registra medições feitas **diretamente nos sprites reais do Tibia**
> (extraídos do pacote de sprites usado pelo renderizador `tibia-outfitter`, que corresponde
> aos mesmos outfits que você anexou — Ranger, Warrior, Wizard, Retro Warrior, Royal Pumpkin).
>
> ⚠️ **Copyright:** os sprites do Tibia são © CipSoft GmbH. Eles foram usados **apenas para
> medição/estudo** neste sandbox e **não são redistribuídos** neste repositório.

---

## 1. Onde os dados vêm

- Os arquivos que você anexou (`Outfit_Ranger_Male.gif`, etc.) são os **previews animados da
  TibiaWiki**, todos em **64×64** e com ~2s de duração (confirmado via API da wiki).
- Esses GIFs de 64×64 são **previews**: o sprite nativo do jogo é **32×32** (outfits antigos) ou
  **64×64** (outfits novos). O `tibia-outfitter` padroniza tudo para 64×64 (upscale 2×).
- Os sprites nativos têm a seguinte organização de arquivos (cada um é um PNG com transparência):

```
{looktype}/{direcao}_{mount}_{addon}_{frame}.png
ex: 128/3_1_1_1.png   -> looktype 128, direção 3 (frente), sem montaria, sem addon, frame 1
```

---

## 2. Medições concretas

### 2.1 Dimensões

| Medida | Valor medido |
|--------|--------------|
| Sprite nativo (outfits antigos) | **32×32** (looktype 10) |
| Sprite nativo (outfits novos) | **64×64** (looktype 128) |
| GIF de preview (TibiaWiki) | **64×64** (upscale 2× do 32×32, ou nativo 64) |
| Corpo do personagem (32×32, frente) | ~19×12 px (bbox), pés em y≈22 |
| Corpo do personagem (64×64, frente) | ~30×32 px (bbox), pés em y=63 |

> **Conclusão de tamanho:** o "64×64" que você quer é, na prática, um **32×32 desenhado com
> detalhe e depois escalado 2×** (ou um nativo 64×64 nos outfits modernos). O sprite **não** é
> desenhado pixel a pixel em 64 — é desenhado em 32 e o estilo "gordo/achatado" vem da projeção.

### 2.2 Direções (4, com espelhamento parcial)

- **4 direções**: `1 = Norte` (costas), `2 = Leste`, `3 = Sul` (frente), `4 = Oeste`.
- Alguns outfits armazenam as 4; outros armazenam **3 e geram Oeste = espelho de Leste**.
- Medição no looktype 10: **Leste ≠ espelho de Oeste** (apenas 4% dos pixels espelhados batem),
  ou seja, esse outfit desenha as 4 direções **separadamente**.
- **Ponto crítico (a "inclinação"):** o sprite **muda de posição dentro do tile conforme a
  direção** por causa da projeção oblíqua:
  - Frente (Sul): bbox x[6..24], y[11..22] → baixo, centralizado
  - Leste: bbox x[1..11], y[1..15] → deslocado para cima/esquerda
  - Oeste: bbox x[21..31], y[0..14] → deslocado para cima/direita

  Isto é a assinatura da **projeção oblíqua top-down (~135°)**. Não é só "desenhar de lado":
  cada direção tem um **deslocamento/âncora próprio** para os pés caírem no mesmo ponto do chão.

### 2.3 Ciclo de caminhada (4 frames por direção)

Medição das alturas do corpo (looktype 10, frente):

| Frame | Altura (bbox) | Interpretação |
|-------|---------------|---------------|
| 1 | 12 px | **parado** (postura compacta) |
| 2 | 19 px | passo (pernas estendidas) |
| 3 | 11 px | **parado** |
| 4 | 19 px | passo |

> **Conclusão de animação:** o "andar" do Tibia é um ciclo de **4 fases** = parado → passo →
> parado → passo, **por direção**. Ou seja, um outfit completo tem **4 direções × 4 frames = 16
> sprites** (sem contar addons e montarias). Nada disso é "derivado por deslocamento de 1px" —
> cada frame é **desenhado**, mantendo a mesma paleta/contorno/âncora.

### 2.4 Cores — outline escuro + paleta limitada + TINT por partes

- **Contorno**: cor quase-preta — `(22,22,22)` nos 32×32, `(1,1,1)`/`(1,0,0)` nos 64×64.
  Confirmado: todo outfit tem **borda escura bem definida** em volta da silhueta.
- **Paleta limitada**: ~40 cores únicas (32×32) e ~263 (64×64). Sem anti-aliasing.
- **Sistema de cor por camadas (o mais importante que faltava confirmar):**
  cada sprite tem um arquivo gêmeo `_template.png`, que é uma **máscara em cores puras RGB**:

  | Cor da máscara | Parte do corpo | Contagem (px) |
  |----------------|----------------|---------------|
  | `(255,0,0)` vermelho | **cabeça** | 200 |
  | `(255,255,0)` amarelo | **torso/corpo** | 108 |
  | `(0,255,0)` verde | **pernas** | 95 |
  | `(0,0,255)` azul | **pés** | 34 |

  Isso significa que o jogador **troca a cor** do outfit **sem redesenhar nada**: o renderizador
  substitui cada região de cor pura pela cor escolhida. É o mecanismo "head/body/legs/feet" dos
  outfits do Tibia — confirmado por medição.

### 2.5 Addons e montarias

- **Addons**: campo 3 do nome = `1` (base), `2` (addon 1), `3` (addon 2). Acessórios (capas,
  capacetes, asas…) desenhados como **camadas separadas** sobrepostas ao corpo.
- **Montarias**: campo 2 = `1` (sem montaria), `2` (montaria). O sprite da montaria é um looktype
  separado, desenhado **atrás** do personagem.

---

## 3. Comparação final: Pixel Master (atual) × Tibia (medido)

| Dimensão | Pixel Master hoje | Tibia (medido) |
|----------|-------------------|----------------|
| Projeção | Frontal/lateral plana | **Oblíqua top-down ~135°** (deslocamento por direção) |
| Canvas | 16/32/48/64 à escolha, 1 sprite | **32×32 nativo + upscale 64**, 16 sprites por outfit |
| Direções | 1 (frente) | **4** (N/E/S/W), com espelho E↔W opcional |
| Animação | idle/walk/attack, **derivada por deslocamento** | **parado+passo ×4 direções, desenhados** |
| Âncora | centro do canvas | **pés no chão, com offset por direção** |
| Cores | paleta flat por projeto | **outline escuro + máscara de tint por partes (head/body/legs/feet)** |
| Camadas | 1 | corpo + addons + montaria (múltiplas) |
| Contorno | opcional | **obrigatório, preto quase puro** |
| Estilo | RPG genérico (Pokémon/Stardew) | **foreshortening oblíquo, cabeça grande, corpo achatado** |

**Resposta direta à sua pergunta:** o que o sistema atual gera é um sprite **de plataforma/frontal
de 1 direção**, com animação sintética por deslocamento e cor "chapada". Um sistema "igual ao Tibia"
precisa de: **(a)** projeção oblíqua com âncora por direção, **(b)** 4 direções × 4 frames desenhados,
**(c)** contorno escuro, **(d)** coloração por máscara de partes (não por paleta fixa), e
**(e)** export no layout `{direção}_{mount}_{addon}_{frame}`.

---

## 4. O que precisa ser implementado (próximas fases)

1. **Canvas 32×32 com guia oblíqua** + upscale 64×64 na exportação (o "64×64" é preview, não o
   canvas de desenho).
2. **4 direções** com offset/âncora por direção (espelho opcional para Oeste).
3. **Ciclo de 4 frames por direção** (parado → passo → parado → passo), desenhados.
4. **Camadas de cor por partes** (head/body/legs/feet) com máscara de tint — permite recolorir
   sem redesenhar (o coração do sistema de outfits).
5. **Addons e montarias** como camadas separadas.
6. **Export** no padrão `{looktype}/{direcao}_{mount}_{addon}_{frame}.png` + templates de cor,
   compatível com `tibia-outfitter`/OTClient.

---

## 5. Referências

- TibiaWiki (API): `Outfit_*.gif` — todos 64×64, duração 2s.
- `renatorib/tibia-outfitter` (outfits.zip) — sprites nativos 32×32/64×64 + templates de cor.
- OTLand — estrutura `.spr`/`.dat`: PatternX/Y/Z = direções/addons/montarias, Layers = blending.
- Medições deste documento: extraídas com Pillow dos PNGs de `outfits.zip`.
