# Análise: estilo de arte do Tibia vs. Pixel Master

> Objetivo: entender a diferença entre o que o **Pixel Master** gera hoje e um sistema capaz de criar
> personagens/criaturas **no mesmo estilo do Tibia** — mesma projeção ("inclinação"), mesmo tamanho
> (64×64 px) e mesmo estilo de desenho.

---

## 0. Status da investigação dos "outfits no GitHub"

Procurei os outfits do Tibia nos seus repositórios e **não os encontrei**:

- Repositórios públicos de `berger33` (8): nenhum contém sprites/outfits do Tibia
  (`pixel-master`, `chs-recruta`, `berger33-chs-recruta`, `aurora-document-rag`,
  `indoor-grow-automation`, `leadflow-local-first`, `SimuladorLotofacil`, `berger33`).
- `pixel-master` (branch atual e `main`): só o código do Pixel Master, sem assets de Tibia.
- Gists públicos: vazio (ou sem acesso).
- Busca de código (`search/code`) por "tibia"/"outfit": nada.

⚠️ **Preciso que você me diga onde estão os outfits** (nome do repositório + pasta, link, ou anexe os
arquivos). Se estiverem em um repositório **privado**, eu não consigo acessá-los com o token atual.

A análise abaixo foi feita com as **especificações reais do Tibia**, documentadas pela comunidade
(OTLand, Reddit, renderizadores de outfits). Ela vale mesmo sem os arquivos específicos, mas com os
seus outfits eu consigo refinar as proporções, a paleta e o contorno para o seu material exato.

---

## 1. O que é o "estilo Tibia"

### 1.1 Projeção — a "inclinação" (o ponto mais importante)

O Tibia **não** usa visão frontal/lateral (como o Pixel Master atual) e **não** usa isométrica
pura (2:1 dimétrica). Ele usa uma **projeção oblíqua, do tipo "cabinet" (cavaleira)**, vista de cima
para baixo em ~3/4 ([1](https://www.reddit.com/r/IndieDev/comments/17vxat6/is_tibia_isometric_diametric_or_planometric/)).

- O personagem é visto **de cima e de frente ao mesmo tempo**: a face frontal fica "de frente" para o
  espectador e o corpo/topo **recua** para trás (eixo de profundidade inclinado ~135° entre o eixo Z
  e o eixo X) ([1](https://www.reddit.com/r/IndieDev/comments/17vxat6/is_tibia_isometric_diametric_or_planometric/)).
- É isso que dá o "achatamento" característico: cabeça grande e mais à frente, corpo compacto, pés
  ancorados na parte de baixo do tile.
- Na prática, um sprite de personagem do Tibia tem o **topo/corpo desenhado "de cima"** (dorso,
  ombros) enquanto as **pernas e pés aparecem de frente**, com o personagem levemente "deitado" na
  diagonal da câmera.

### 1.2 Tamanho dos sprites

| Elemento | Tamanho |
|----------|---------|
| Tile de chão / itens / criaturas normais | **32×32** |
| Criaturas grandes (Demon, Cyclops, Hydra) | **64×64** (2×2 tiles, composto de 4 sprites) |
| Outfits modernos (padronizado por renderizadores) | **64×64** |

Fontes: [2](https://www.reddit.com/r/TibiaMMO/comments/va0x95/tibia_pixelart/),
[3](https://otland.net/threads/sprite-question.162389/),
[4](https://github.com/renatorib/tibia-outfitter).

> A biblioteca `tibia-outfitter` inclusive **padroniza tudo para 64×64** (transforma 32×32 → 64×64)
> justamente para ter saída consistente ([4](https://github.com/renatorib/tibia-outfitter)).

### 1.3 Estrutura do outfit (direções + animações)

Um outfit do Tibia não é "uma imagem animada" — é uma **matriz de sprites**:

- **4 direções**: Norte (costas), Sul (frente), Leste/Oeste (laterais) —
  [3](https://otland.net/threads/sprite-question.162389/).
- **Por direção**: 1 frame parado + 2 frames de caminhada (alternância de pernas/pés) +
  opcionalmente ataque/morte/uso de item ([5](https://otland.net/threads/adding-new-outfits-looktypes-detailed-free-samples.84412/)).
  - A regra oficial de montagem: **"Animação 1 é sempre o personagem parado; 2, 3, 4… são os frames
    de movimento"** ([5](https://otland.net/threads/adding-new-outfits-looktypes-detailed-free-samples.84412/)).
- No `.dat`/`.spr`, os eixos de padrão são ([6](https://otland.net/threads/sprite-manipulation.252151/)):
  - **PatternX = direções** (4),
  - **PatternY = addons** (acessórios: capa, capacete…),
  - **PatternZ = montarias** (mount),
  - **Layers = camadas de blending** (para recolorir o outfit).

### 1.4 Sistema de cores (muito diferente de uma paleta comum)

O Tibia tem um sistema de **cores em camadas/template**:

- Paleta global fixa: **133 cores** ([7](https://otland.net/threads/tibia-7-7-map-editor-for-original-cipsoft-sec-files-pyqt5-pre-alpha.303850/)).
- O outfit é desenhado em **camadas tintáveis** por parte do corpo: **cabeça (head), corpo (body),
  pernas (legs) e pés (feet)** ([8](https://github.com/renatorib/tibia-outfitter)).
- Ou seja: o jogador **troca a cor** do outfit **sem trocar o sprite** — só muda o "tint" aplicado à
  camada de sombreamento (template de luz/sombra) de cada parte.

### 1.5 Estilo de desenho

- **Contorno escuro** (borda preta/escura) bem definido em volta da silhueta.
- **Paleta limitada** por sprite, com **sombreamento em rampa** (não dithering pesado).
- **Sem anti-aliasing** — pixels "duros".
- **Foreshortening oblíquo**: cabeça relativamente maior, corpo compacto, pernas encurtadas pela
  perspectiva.
- **Âncora dos pés fixa** no centro-inferior (ou no quadrante inferior-direito, para criaturas 2×2),
  para o personagem "pisar" no tile sem flutuar ([3](https://otland.net/threads/sprite-question.162389/)).

---

## 2. Comparação direta: Pixel Master atual × Tibia

| Aspecto | Pixel Master (hoje) | Tibia | Impacto |
|---------|---------------------|-------|---------|
| **Projeção** | Frontal/lateral plana | Oblíqua top-down 3/4 (cabinet, ~135°) | **A diferença central.** O "look" do Tibia vem daqui. |
| **Direções** | 1 (frontal) | 4 (N/E/S/W) | Personagem não "vira" no jogo. |
| **Tamanho** | 16/32 (exemplos em 16, ampliados 4×) | 32×32 (padrão) / **64×64 (outfits)** | Resolução e nível de detalhe diferentes. |
| **Âncora** | Centro do canvas | Pés no centro-inferior do tile | Sem âncora, o sprite "flutua" no mapa. |
| **Animações** | idle/walk/attack, 1 direção, derivadas por deslocamento | parado + 2 walk × 4 direções | Sem virada de corpo; movimento "flat". |
| **Cores** | Paleta flat por projeto | **Template tintável por partes** (head/body/legs/feet) + paleta 133 cores | Sem recoloração de outfit. |
| **Camadas** | 1 camada | Layers (blending), addons, mounts | Sem acessórios/montarias. |
| **Estilo** | Pixel art genérico | Contorno escuro + foreshortening oblíquo | Aparência "reconhecível" de Tibia ausente. |

**Conclusão:** o Pixel Master atual gera sprites **de plataforma/RPG frontal** (estilo Pokémon/Stardew),
enquanto o Tibia exige sprites **objetos de um mundo oblíquo top-down**, com 4 direções, âncora fixa,
animação por direção e coloração em camadas.

---

## 3. O que precisa mudar para gerar "igual ao Tibia"

### 3.1 Projeção e canvas

- Canvas fixo **64×64** (com opção 32×32 para itens/criaturas pequenas).
- Desenhar em **vista oblíqua top-down**: topo/cabeça vistos de cima, corpo/frente vistos de frente,
  com o eixo de profundidade a ~135°.
- Linha de chão (referência do tile em diamante oblíquo) sobreposta ao editor, para guiar o desenho.

### 3.2 Âncora dos pés

- Ponto de âncora fixo no **centro-inferior** (x=32, y=~60 em 64×64) do canvas.
- Todos os frames/direções **mantêm o mesmo ponto de contato**, garantindo que o personagem não
  "flutue" nem "deslize".

### 3.3 Direções

- Modelar o outfit em **4 direções**. Economia clássica: desenhar **Sul (frente)**, **Norte (costas)** e
  **uma lateral (Leste)**; **Oeste = espelho de Leste** (Tibia faz exatamente isso em muitos outfits).
- Estrutura de dados: `animations[estado][direção][frame]`.

### 3.4 Animações por direção

- **Parado (stand)**: 1 frame.
- **Caminhando (walk)**: 2 frames (alternância de perna/pé), por direção.
- Opcionais: ataque, conjuração, dano, morte.

> Importante sobre "consistência" (o ponto que você levantou na etapa anterior): no Tibia a
> consistência **não vem de derivar frames por deslocamento** — vem de **desenhar cada direção sobre a
> mesma "boneca" (rig)** e manter a mesma paleta, o mesmo contorno e o mesmo ponto de âncora. O
> deslocamento de 1px do Pixel Master não produz um personagem oblíquo de 4 direções.

### 3.5 Sistema de cores em camadas (o "outfit recolorível")

- Desenhar o personagem em **camadas separadas por parte**: `head`, `body`, `legs`, `feet`
  (e opcionalmente `addon`, `mount`).
- Cada camada tem um **template de sombreamento** (tons de cinza/rampa de luz) + um **tint**
  aplicado por cima. Assim, mudar a cor do outfit **não exige redesenhar**.
- Usar a **paleta Tibia (133 cores)** ou um subconjunto curado.

### 3.6 Estilo de desenho

- Contorno escuro em toda a silhueta.
- Sombreamento em 2–4 rampas por material (pele, tecido, metal).
- Sem anti-aliasing.
- Proporções do Tibia: cabeça ~1/3 a 1/2 da altura, corpo compacto, pernas curtas (foreshortening).

---

## 4. Plano de implementação sugerido (fases)

1. **Fase A — Fundação 64×64 + projeção**: novo canvas 64×64, guia de tile oblíquo, âncora de pés.
2. **Fase B — 4 direções + espelhamento E/W**: estrutura `direção × frame`, ferramenta de espelho.
3. **Fase C — Animações por direção**: stand + 2 walk por direção; o "walk" alterna pernas dentro da
   vista oblíqua.
4. **Fase D — Cores em camadas**: head/body/legs/feet tintáveis + paleta Tibia (133 cores).
5. **Fase E — Templates estilo Tibia**: 1–2 personagens de exemplo desenhados no estilo (não só os
   9 atuais, que são de vista frontal).
6. **Fase F — Export compatível**: `.spr`/`.dat` (via ObjectBuilder) ou PNG 64×64 por direção/frame,
   já no layout esperado por OTClient/TFS.

---

## 5. Referências

1. Reddit r/IndieDev — "Tibia uses an oblique projection (cabinet)"; ângulo Z-X de 135°.
2. Reddit r/TibiaMMO — tamanhos: 32×32 itens/personagens, 64×64 criaturas grandes.
3. OTLand — 32×32 padrão; 64×64 = 4 splits; 4 direções parado + 4 direções andando.
4. `renatorib/tibia-outfitter` — padroniza outfits para 64×64.
5. OTLand — "Adicionando outfits/looktypes": PatternX/Y/Z, Animação 1 = parado, 2+ = movimento.
6. OTLand — "Sprite Manipulation": PatternX=direções, Y=addons, Z=mount, Layers=blending.
7. OTLand — Map editor 7.7: paleta Tibia de 133 cores, looktype, direção/animação, tint por partes.
8. `renatorib/tibia-outfitter` — propriedades `head/body/legs/feet` de coloração do outfit.
