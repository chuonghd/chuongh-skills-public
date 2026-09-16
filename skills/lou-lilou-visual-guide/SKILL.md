---
name: lou-lilou-visual-guide
description: "Create Lou & Lilou fashion guides by adapting the educational concept of an uploaded source visual, guiding the user through extremely brief copy choices, and generating an original branded visual. Use when a user wants to recreate, adapt, or develop a practical fashion infographic for mid-aged women."
---

# Lou & Lilou Visual Guide

Create practical, polished fashion guides for **Lou & Lilou**, a brand serving mid-aged women. Treat an uploaded visual guide as the source for educational content, not as a layout template. Treat any separately attached avatar or persona images as identity references for that request.

## Adaptation Standard

Preserve the source guide's educational concept and informational relationships while creating an original Lou & Lilou execution. Knowledge structure means the categories, definitions, and mappings—not their original spatial arrangement.

- Design the composition from a blank canvas. Do not trace, closely reproduce, or lightly reskin the source layout.
- Do not reuse another brand's logo, promotional phrasing, or distinctive artwork verbatim. This restriction does not apply to educational terminology or classification labels that must remain accurate.
- If source text is unclear, infer its likely educational intent instead of blocking on unnecessary questions.
- Default to a refined, editorial, feminine, modern aesthetic with crisp typography, clean edges, polished fashion imagery, strong readability, and practical educational value.
- Choose proportions for readability and balance; do not preserve the source aspect ratio by default.
- Keep the voice warm, tasteful, concrete, and confidence-building without patronizing the audience.

## Educational Content Fidelity

Treat the source guide's substantive educational content as locked. Preserve its terminology, classification names, definitions, relationships, sequences, quantities, caveats, and recommendation mappings.

- Keep domain terms and category labels exactly when they are legible. For example, retain **XO legs**, **X legs**, **O legs**, and **I legs** rather than replacing them with numbered or paraphrased category names.
- Preserve definitions accurately. For example, **“knees touch, calves apart”** must not become **“knees closer, calves apart.”**
- Keep every recommendation associated with its original category; do not move, remove, merge, or invent recommendations.
- Filler words, connective phrasing, and explanatory prose may be lightly rewritten only when the educational meaning remains unchanged.
- Brand slogans, promotional copy, and decorative wording should be adapted into original Lou & Lilou language.
- Before generation, extract the educational labels, definitions, and mappings from the source and treat them as required content. If a term is unreadable, infer conservatively from the visual context without renaming clear neighboring categories.

## Visual Direction and Quality Bar

Create a fresh editorial system suited to the content rather than inheriting the source's visual grammar. Reconsider the page flow, grouping, grid, section containers, image treatment, and header/footer composition while keeping educational relationships easy to follow.

- Build a clear reading path with one dominant headline, concise supporting copy, unmistakable category headings, and labels placed close to their visuals.
- Use a disciplined grid, generous whitespace, consistent margins, deliberate alignment, and balanced visual weight. Avoid simply converting the source's rows into similar cards or preserving the same item positions.
- Use elegant editorial typography with restrained font pairing, consistent hierarchy, comfortable line lengths, and strong legibility at social-media viewing sizes.
- Use a cohesive, sophisticated palette with warm neutrals, subtle tonal contrast, and restrained accents. Maintain sufficient text/background contrast.
- Recreate garments, diagrams, and decorative elements as original, stylistically consistent visuals. Do not closely copy the source's exact cutouts, illustrations, crops, or ornaments.
- Keep garments and educational diagrams consistently scaled and visually comparable. Avoid warped anatomy, malformed clothing, uneven baselines, ambiguous labels, and mismatched rendering styles.
- Integrate a selected avatar intentionally into the composition. The portrait should support the hierarchy without crowding the headline or displacing educational content.
- Prefer refinement over decoration. Avoid unnecessary badges, gradients, shadows, borders, flourishes, or filler elements that do not clarify the guide.
- Before presenting the result, inspect it for clipped or misspelled text, missing categories, incorrect mappings, overlaps, awkward crops, inconsistent spacing, and weak contrast. Regenerate when a material defect prevents a high-quality result.

## Copy Workflow

Extreme brevity is mandatory during selection. Use exactly four sequential turns:

1. Tagline/topic
2. Description
3. CTA
4. Header avatar

Selection turns contain choices only. Do not add an introduction, acknowledgement, rationale, recommendation, adaptation commentary, or filler. Never explain the differences unless the user explicitly asks.

### Turn 1: Tagline / Topic

After receiving the source visual, reply in exactly this structure:

```markdown
### 1) Tagline / Topic
A - **[option]**
B - **[option]**
C - **[option]**
D - **[option]**
E - **[option]**

Choose A, B, C, D, or E.
```

Make each option concise and benefit-led.

### Turn 2: Description

After the user selects a tagline/topic, reply in exactly this structure:

```markdown
### 2) Description
A - [option]
B - [option]
C - [option]
D - [option]

Choose A, B, C, or D.
```

Make each option infographic-ready, normally one or two short sentences, and consistent with the selected tagline/topic.

### Turn 3: CTA

After the user selects a description, reply in exactly this structure:

```markdown
### 3) CTA
A - **[option]**
B - **[option]**
C - **[option]**
D - **[option]**

Choose A, B, C, or D.
```

Make each option a brief, open-ended topic question that invites the audience to reflect or respond. Tie it directly to the guide's subject, avoid yes/no questions and command-style CTAs, and use natural prompts such as **“Which skirt suits your legs best?”**

### Turn 4: Header Avatar

After the user selects a CTA, reply in exactly this structure:

```markdown
### 4) Header Avatar
A - **Lou**
B - **Lilou**
C - **None**
D - **Both Lou and Lilou**

Choose A, B, C, or D.
```

This final choice controls which bundled brand avatars appear in the header:

- **Lou:** use [`assets/lou.png`](assets/lou.png).
- **Lilou:** use [`assets/lilou.png`](assets/lilou.png).
- **None:** do not include a brand avatar in the header.
- **Both Lou and Lilou:** use both assets as separate identity references and integrate both avatars naturally into the header.

### Generate After Selection

Once the three copy components and header-avatar choice are approved:

1. Briefly show the approved tagline/topic, description, CTA, and header-avatar choice.
2. Do not ask for confirmation.
3. Immediately use the available image-generation tool to create the high-definition branded guide.
4. Use the approved copy exactly, except for minor punctuation changes needed for clean rendering.
5. Include the extracted educational terminology, definitions, and mappings in the generation prompt as locked content. Require the generated guide to render them accurately and verify the output against the source before presenting it.
6. Include the visual-direction requirements in the generation prompt and explicitly instruct the tool to create a fresh composition rather than reproduce the source's layout or artwork.

When Lou or Lilou is selected, explicitly pass that avatar's bundled asset to the image-generation tool as an image reference. When Both is selected, pass both bundled assets as separate identity references and instruct the tool to preserve each identity distinctly. Also pass the source guide and any applicable user-attached avatar references when supported. Make each reference's separate role explicit in the generation prompt. If None is selected, do not pass Lou or Lilou and do not place a brand avatar in the header. If image generation is unavailable, state that limitation plainly rather than claiming a visual was generated.

## Attachment Roles

Determine image roles from the conversation and visual context:

- **Source guide:** supplies educational content, information structure, and design context.
- **Bundled avatar:** supplies Lou's identity, Lilou's identity, or both identities when selected in Turn 4.
- **Avatar/persona image:** supplies character identity only.

Do not confuse people appearing inside the source guide with bundled or separately attached avatars unless the user explicitly says they are the same person. Do not assume separately attached avatar images exist when none were attached.

### No Avatar Attached

- Do not invent additional recurring brand personas.
- Use only the bundled avatar selected in Turn 4; if None is selected, do not add an avatar portrait to the header.
- Use no persona imagery unless human figures are genuinely required by the educational concept.
- Treat any necessary people as generic illustrative models, never as named or established brand personas.

### One Avatar Attached

- Use the actual attachment as a visual identity reference when the request calls for that person elsewhere in the guide.
- Do not substitute it for the Turn 4 header choice unless the user explicitly overrides that choice.
- Do not invent another avatar for symmetry.

### Two Avatars Attached

- Use both actual attachments as separate visual identity references when the request calls for those people elsewhere in the guide.
- Do not substitute them for the Turn 4 header choice unless the user explicitly overrides that choice.

### Identity Fidelity

For every attached avatar:

- Explicitly provide the actual attachment as an image reference whenever the generation tool supports it.
- Preserve recognizable facial identity and distinguishing appearance.
- Pose, expression, clothing, crop, lighting, and styling may adapt to the new composition.
- Never replace the attachment with an invented lookalike.
- If the tool cannot use the attachment as a reference, say so; do not silently substitute a generated face or claim it represents the avatar.

Apply the same identity-fidelity requirements to each selected bundled asset. The selected assets are generation references, not decorative source material to approximate from memory. When Both is selected, keep Lou and Lilou recognizable as two distinct people rather than blending their features.

## Header Restraint

Do not automatically add avatar names, signatures, labels, mini biographies, slogans, decorative quotes, handwritten notes, speech bubbles, hearts, side captions, invented taglines, or filler microcopy. Avatar portraits generally need no accompanying text.
