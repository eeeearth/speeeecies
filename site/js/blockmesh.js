// blockmesh.js — procedural block-mesh model builder and animator for speeeecies.
//
// No three.js dependency. Exports:
//   buildModel(species, bodyPlans) -> { parts: [{name, parent, center, size, pivot, color}], bodyPlan, bounds }
//   poseModel(model, species, poseName, phase) -> { partName: { rot: [x,y,z] degrees, pos: [x,y,z] } }
//
// Coordinate frame: x forward, y up, z right. Ground is y = 0.
// `center`, `pivot` are in the model's own rest-pose space (absolute, not parent-relative);
// the renderer is expected to build a parent-first hierarchy of groups anchored at each
// part's pivot, and to apply poseModel's rotations about that pivot.

// ---------- small math/utility helpers ----------

function globToRegExp(glob) {
  const escaped = glob.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*");
  return new RegExp(`^${escaped}$`);
}

function matchesGlob(name, glob) {
  if (glob === name) return true;
  if (!glob.includes("*")) return false;
  return globToRegExp(glob).test(name);
}

function mergeProportions(defaults, overrides) {
  const out = Object.assign({}, defaults);
  if (overrides) {
    for (const k of Object.keys(overrides)) {
      if (overrides[k] !== undefined) out[k] = overrides[k];
    }
  }
  return out;
}

function resolvePartSlot(partName, defaultColors, partColorOverrides) {
  let slot = "body";
  // default_colors: exact match wins over glob among defaults, but later declared
  // defaults don't have ordering guarantees, so just do exact-first then glob.
  if (defaultColors) {
    if (defaultColors[partName]) {
      slot = defaultColors[partName];
    } else {
      for (const key of Object.keys(defaultColors)) {
        if (matchesGlob(partName, key)) slot = defaultColors[key];
      }
    }
  }
  // species overrides: globs, later keys win (object key order = declaration order).
  if (partColorOverrides) {
    for (const key of Object.keys(partColorOverrides)) {
      if (matchesGlob(partName, key)) slot = partColorOverrides[key];
    }
  }
  return slot;
}

function resolveSlotColor(slot, palette) {
  palette = palette || {};
  if (palette[slot]) return palette[slot];
  if (slot === "eye") return palette.eye || "#1a1a1a";
  // belly, markings, accent (and any unknown slot) fall back to body.
  return palette.body || "#999999";
}

const DEG = Math.PI / 180;

function addv(a, b) {
  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
}
function scalev(a, s) {
  return [a[0] * s, a[1] * s, a[2] * s];
}

// ---------- buildModel ----------

export function buildModel(species, bodyPlans) {
  const look = species.look;
  if (!look) throw new Error("species.look is missing");
  const planId = look.body_plan;
  const planDef = bodyPlans && bodyPlans.plans && bodyPlans.plans[planId];
  if (!planDef) {
    throw new Error(`Unknown body plan: ${JSON.stringify(planId)}`);
  }
  const proportions = mergeProportions(planDef.defaults || {}, look.proportions || {});
  const traits = species.traits || {};
  const palette = look.palette || { body: "#999999" };
  const defaultColors = planDef.default_colors || {};
  const partColorOverrides = look.part_colors || {};

  const builders = {
    quadruped: buildQuadrupedLike,
    hopper: buildQuadrupedLike,
    anuran: buildAnuran,
    biped_winged: buildBipedWinged,
    serpentine: buildSerpentine,
    hexapod: buildHexapod,
    hexapod_winged: buildHexapod,
  };
  const builder = builders[planId];
  if (!builder) throw new Error(`Unknown body plan: ${JSON.stringify(planId)}`);

  const rawParts = builder(planId, proportions, traits);

  const parts = rawParts.map((p) => {
    const slot = resolvePartSlot(p.name, defaultColors, partColorOverrides);
    return {
      name: p.name,
      parent: p.parent || null,
      center: p.center,
      size: p.size,
      pivot: p.pivot,
      slot,
      color: resolveSlotColor(slot, palette),
    };
  });

  const byName = {};
  for (const p of parts) byName[p.name] = p;

  // extra_parts: offsets/sizes are fractions of the PARENT part's box size.
  for (const extra of look.extra_parts || []) {
    const parent = byName[extra.parent];
    if (!parent) {
      throw new Error(`Unknown part name (extra_part parent): ${JSON.stringify(extra.parent)}`);
    }
    const makeOne = (name, offset) => {
      const center = [
        parent.center[0] + offset[0] * parent.size[0],
        parent.center[1] + offset[1] * parent.size[1],
        parent.center[2] + offset[2] * parent.size[2],
      ];
      const size = [
        extra.size[0] * parent.size[0],
        extra.size[1] * parent.size[1],
        extra.size[2] * parent.size[2],
      ];
      const part = {
        name,
        parent: extra.parent,
        center,
        size,
        pivot: parent.pivot.slice(),
        slot: extra.color,
        color: resolveSlotColor(extra.color, palette),
      };
      parts.push(part);
      byName[name] = part;
    };
    if (extra.mirror) {
      const offR = [extra.offset[0], extra.offset[1], Math.abs(extra.offset[2])];
      const offL = [extra.offset[0], extra.offset[1], -Math.abs(extra.offset[2])];
      makeOne(`${extra.name}_right`, offR);
      makeOne(`${extra.name}_left`, offL);
    } else {
      makeOne(extra.name, extra.offset);
    }
  }

  // bounding box, for the previewer's camera framing.
  let min = [Infinity, Infinity, Infinity];
  let max = [-Infinity, -Infinity, -Infinity];
  for (const p of parts) {
    for (let i = 0; i < 3; i++) {
      const lo = p.center[i] - p.size[i] / 2;
      const hi = p.center[i] + p.size[i] / 2;
      if (lo < min[i]) min[i] = lo;
      if (hi > max[i]) max[i] = hi;
    }
  }
  return { parts, bodyPlan: planId, bounds: { min, max } };
}

// ---------- per-plan geometry builders ----------
// Each returns an array of { name, parent, center, size, pivot } in rest-pose
// absolute model space (x forward, y up, z right; ground at y=0). Parents
// always precede children in the array.

function buildQuadrupedLike(planId, pr, traits) {
  const length = traits.length_m || 0.5;
  const torsoLength = length * 0.42;
  const torsoHeight = torsoLength / (pr.torso_aspect || 2.0);
  const torsoWidth = torsoHeight * (pr.girth_ratio || 0.8);
  const legLength =
    traits.shoulder_height_m != null
      ? Math.max(traits.shoulder_height_m - torsoHeight / 2, torsoHeight * 0.2)
      : torsoLength * (pr.leg_length_ratio || 0.45);
  const headSize = torsoHeight * (pr.head_scale || 0.7);
  const neckLength = torsoLength * 0.32;
  const neckAngle = (pr.neck_angle_deg != null ? pr.neck_angle_deg : 30) * DEG;
  const snoutLength = headSize * (pr.beak_ratio != null ? pr.beak_ratio : 0.5);
  const tailLength = torsoLength * (pr.tail_ratio != null ? pr.tail_ratio : 0.5);
  const earHeight = headSize * (pr.ear_ratio != null ? pr.ear_ratio : 0.3);
  const legThick = torsoWidth * 0.28;

  const torsoY = legLength + torsoHeight / 2;
  const parts = [];

  parts.push({
    name: "body",
    parent: null,
    center: [0, torsoY, 0],
    size: [torsoLength, torsoHeight, torsoWidth],
    pivot: [0, torsoY, 0],
  });

  const neckPivot = [torsoLength / 2, torsoY + torsoHeight * 0.25, 0];
  const neckDir = [Math.cos(neckAngle), Math.sin(neckAngle), 0];
  const neckCenter = addv(neckPivot, scalev(neckDir, neckLength / 2));
  parts.push({
    name: "neck",
    parent: "body",
    center: neckCenter,
    size: [neckLength, headSize * 0.55, headSize * 0.55],
    pivot: neckPivot,
  });

  const headPivot = addv(neckPivot, scalev(neckDir, neckLength));
  const headCenter = addv(headPivot, scalev(neckDir, headSize * 0.5));
  parts.push({
    name: "head",
    parent: "neck",
    center: headCenter,
    size: [headSize, headSize * 0.85, headSize * 0.75],
    pivot: headPivot,
  });

  const snoutPivot = addv(headCenter, [headSize / 2, 0, 0]);
  parts.push({
    name: "snout",
    parent: "head",
    center: addv(snoutPivot, [snoutLength / 2, 0, 0]),
    size: [Math.max(snoutLength, 0.001), headSize * 0.4, headSize * 0.4],
    pivot: snoutPivot,
  });

  const earPivot = [headCenter[0] - headSize * 0.2, headCenter[1] + headSize * 0.35, 0];
  for (const side of [1, -1]) {
    parts.push({
      name: side > 0 ? "ear_right" : "ear_left",
      parent: "head",
      center: [earPivot[0], earPivot[1] + earHeight / 2, side * headSize * 0.3],
      size: [headSize * 0.25, earHeight, headSize * 0.12],
      pivot: [earPivot[0], earPivot[1], side * headSize * 0.3],
    });
  }

  const legX = torsoLength * 0.32;
  const legZ = torsoWidth / 2 * 0.65;
  const legY = torsoY - torsoHeight / 2;
  for (const [nx, xLab] of [
    [legX, "front"],
    [-legX, "rear"],
  ]) {
    for (const side of [1, -1]) {
      const pivot = [nx, legY, side * legZ];
      parts.push({
        name: `leg_${xLab}_${side > 0 ? "right" : "left"}`,
        parent: "body",
        center: [nx, legY - legLength / 2, side * legZ],
        size: [legThick, legLength, legThick],
        pivot,
      });
    }
  }

  const tailPivot = [-torsoLength / 2, torsoY + torsoHeight * 0.1, 0];
  parts.push({
    name: "tail",
    parent: "body",
    center: [tailPivot[0] - tailLength / 2, tailPivot[1], 0],
    size: [Math.max(tailLength, 0.001), headSize * 0.35, headSize * 0.35],
    pivot: tailPivot,
  });

  return parts;
}

function buildAnuran(planId, pr, traits) {
  const length = traits.length_m || 0.08; // snout-vent length
  // `torso_aspect` is length/width (not length/height) for this squat plan;
  // height is then fixed as a fraction of width, not of `girth_ratio` — a
  // frog or toad's body is flat and wide, not a tall box on stilts.
  const torsoAspect = pr.torso_aspect != null ? pr.torso_aspect : 1.3;
  const girth = pr.girth_ratio != null ? pr.girth_ratio : 1.1;
  const torsoLength = length * 0.8;
  const torsoWidth = (torsoLength / torsoAspect) * (girth / 1.1);
  const torsoHeight = torsoWidth * 0.45; // squat and flat
  const legRatio = pr.leg_length_ratio != null ? pr.leg_length_ratio : 0.6;

  const frontLegLength = torsoLength * legRatio * 0.4;
  const thighLength = torsoLength * legRatio * 0.55;
  const shinLength = torsoLength * legRatio * 0.55;
  const headScale = pr.head_scale != null ? pr.head_scale : 0.8;
  const headWidth = torsoWidth * 0.92;
  const headLength = torsoLength * 0.34 * (headScale / 0.8);
  const headHeight = torsoHeight * 0.85;
  const legThick = torsoWidth * 0.12;

  // Belly close to the ground: a small fixed clearance, not the rear leg's
  // full built length (the rear legs are posed folded — see animateAnuran —
  // so their neutral length doesn't set the stance height).
  const groundClearance = torsoHeight * 0.35;
  const torsoY = groundClearance + torsoHeight / 2;
  const parts = [];

  parts.push({
    name: "body",
    parent: null,
    center: [0, torsoY, 0],
    size: [torsoLength, torsoHeight, torsoWidth],
    pivot: [0, torsoY, 0],
  });

  // Head: wide and flat, nearly as wide as the body.
  const headPivot = [torsoLength / 2, torsoY + torsoHeight * 0.08, 0];
  const headCenter = addv(headPivot, [headLength * 0.42, headHeight * 0.05, 0]);
  parts.push({
    name: "head",
    parent: "body",
    center: headCenter,
    size: [headLength, headHeight, headWidth],
    pivot: headPivot,
  });

  // Eyes: small bumps on TOP of the head, at its front corners.
  for (const side of [1, -1]) {
    const eyePivot = [
      headCenter[0] + headLength * 0.28,
      headCenter[1] + headHeight / 2,
      side * headWidth * 0.32,
    ];
    parts.push({
      name: side > 0 ? "eye_right" : "eye_left",
      parent: "head",
      center: [eyePivot[0], eyePivot[1] + headHeight * 0.14, eyePivot[2]],
      size: [headHeight * 0.32, headHeight * 0.3, headHeight * 0.32],
      pivot: eyePivot,
    });
  }

  const legY = torsoY - torsoHeight / 2;

  // Front legs: short single struts near the front corners (angled outward
  // and forward in animateAnuran, not at rest here).
  const frontX = torsoLength * 0.32;
  const frontZ = (torsoWidth / 2) * 0.85;
  for (const side of [1, -1]) {
    const pivot = [frontX, legY, side * frontZ];
    parts.push({
      name: `leg_front_${side > 0 ? "right" : "left"}`,
      parent: "body",
      center: [frontX, legY - frontLegLength / 2, side * frontZ],
      size: [legThick, frontLegLength, legThick],
      pivot,
    });
  }

  // Rear legs: two hinged segments each (thigh, then shin), built pointing
  // straight down from the hip; animateAnuran bends them into a resting "Z"
  // fold (thigh forward, shin back) splayed out beside the hips, or extends
  // them for a hop.
  const rearX = -torsoLength * 0.4;
  const rearZ = (torsoWidth / 2) * 0.85;
  for (const side of [1, -1]) {
    const hipPivot = [rearX, legY, side * rearZ];
    const thighName = `leg_rear_${side > 0 ? "right" : "left"}`;
    parts.push({
      name: thighName,
      parent: "body",
      center: [rearX, legY - thighLength / 2, side * rearZ],
      size: [legThick * 1.15, thighLength, legThick * 1.15],
      pivot: hipPivot,
    });
    const kneePivot = [rearX, legY - thighLength, side * rearZ];
    parts.push({
      name: `${thighName}_lower`,
      parent: thighName,
      center: [rearX, legY - thighLength - shinLength / 2, side * rearZ],
      size: [legThick, shinLength, legThick],
      pivot: kneePivot,
    });
  }

  return parts;
}

function buildBipedWinged(planId, pr, traits) {
  const length = traits.length_m || 0.15;
  const wingspan = traits.wingspan_m || length * 2.2;
  const torsoLength = length * 0.4;
  const torsoHeight = torsoLength / (pr.torso_aspect || 1.8);
  const torsoWidth = torsoHeight * (pr.girth_ratio || 0.9);
  const legLength = torsoLength * (pr.leg_length_ratio != null ? pr.leg_length_ratio : 0.3);
  const headSize = torsoHeight * (pr.head_scale || 0.75);
  const neckAngle = (pr.neck_angle_deg != null ? pr.neck_angle_deg : 20) * DEG;
  const beakLength = headSize * (pr.beak_ratio != null ? pr.beak_ratio : 0.5);
  const tailLength = torsoLength * (pr.tail_ratio != null ? pr.tail_ratio : 0.5);
  const wingAspect = pr.wing_aspect || 3.0;
  const legThick = torsoWidth * 0.22;

  const torsoY = legLength + torsoHeight / 2;
  const parts = [];

  parts.push({
    name: "body",
    parent: null,
    center: [0, torsoY, 0],
    size: [torsoLength, torsoHeight, torsoWidth],
    pivot: [0, torsoY, 0],
  });

  const breastPivot = [torsoLength * 0.15, torsoY - torsoHeight * 0.15, 0];
  parts.push({
    name: "breast",
    parent: "body",
    center: [breastPivot[0] + torsoLength * 0.08, breastPivot[1] - torsoHeight * 0.1, 0],
    size: [torsoLength * 0.55, torsoHeight * 0.7, torsoWidth * 0.85],
    pivot: breastPivot,
  });

  const headPivot = [torsoLength / 2, torsoY + torsoHeight * 0.35, 0];
  const neckDir = [Math.cos(neckAngle), Math.sin(neckAngle), 0];
  const headCenter = addv(headPivot, scalev(neckDir, headSize * 0.45));
  parts.push({
    name: "head",
    parent: "body",
    center: headCenter,
    size: [headSize * 0.85, headSize * 0.8, headSize * 0.75],
    pivot: headPivot,
  });

  const beakPivot = addv(headCenter, scalev(neckDir, headSize * 0.42));
  parts.push({
    name: "beak",
    parent: "head",
    center: addv(beakPivot, scalev(neckDir, beakLength / 2)),
    size: [Math.max(beakLength, 0.001), headSize * 0.25, headSize * 0.22],
    pivot: beakPivot,
  });

  for (const side of [1, -1]) {
    parts.push({
      name: side > 0 ? "eye_right" : "eye_left",
      parent: "head",
      center: [headCenter[0], headCenter[1] + headSize * 0.1, side * headSize * 0.34],
      size: [headSize * 0.14, headSize * 0.14, headSize * 0.14],
      pivot: [headCenter[0], headCenter[1] + headSize * 0.1, side * headSize * 0.34],
    });
  }

  // Each wing is two hinged segments (inner: shoulder to wrist, outer: wrist
  // to tip), each half the span. A single rigid box can't fold shorter than
  // its own length; splitting it lets a folded wing (inner swept back along
  // the flank, outer folded back over the inner — see foldWing/foldOuter in
  // animateBipedWinged) stay within about the torso's own length, instead of
  // the whole half-span sticking out past the tail.
  const halfSpan = Math.max(wingspan / 2 - torsoWidth / 2, torsoWidth);
  const innerLen = halfSpan * 0.5;
  const outerLen = halfSpan * 0.5;
  const wingChord = halfSpan / wingAspect;
  const wingPivotY = torsoY + torsoHeight * 0.25;
  for (const side of [1, -1]) {
    const shoulder = [torsoLength * 0.05, wingPivotY, side * torsoWidth / 2];
    const innerName = side > 0 ? "wing_right" : "wing_left";
    parts.push({
      name: innerName,
      parent: "body",
      center: [shoulder[0], shoulder[1], shoulder[2] + (side * innerLen) / 2],
      size: [wingChord, torsoHeight * 0.12, innerLen],
      pivot: shoulder,
    });
    const wrist = [shoulder[0], shoulder[1], shoulder[2] + side * innerLen];
    parts.push({
      name: `${innerName}_outer`,
      parent: innerName,
      center: [wrist[0], wrist[1], wrist[2] + (side * outerLen) / 2],
      size: [wingChord * 0.82, torsoHeight * 0.1, outerLen],
      pivot: wrist,
    });
  }

  const tailPivot = [-torsoLength / 2, torsoY + torsoHeight * 0.05, 0];
  parts.push({
    name: "tail",
    parent: "body",
    center: [tailPivot[0] - tailLength / 2, tailPivot[1], 0],
    size: [Math.max(tailLength, 0.001), torsoHeight * 0.15, torsoWidth * 0.8],
    pivot: tailPivot,
  });

  const legY = torsoY - torsoHeight / 2;
  const legZ = torsoWidth / 2 * 0.5;
  for (const side of [1, -1]) {
    const pivot = [0, legY, side * legZ];
    parts.push({
      name: side > 0 ? "leg_right" : "leg_left",
      parent: "body",
      center: [0, legY - legLength / 2, side * legZ],
      size: [legThick, Math.max(legLength, 0.001), legThick],
      pivot,
    });
  }

  return parts;
}

function buildSerpentine(planId, pr, traits) {
  const length = traits.length_m || 0.6;
  const segments = Math.max(3, Math.round(pr.segments || 10));
  const girth = pr.girth_ratio != null ? pr.girth_ratio : 1.0;
  const headScale = pr.head_scale != null ? pr.head_scale : 1.3;
  const unit = length / (segments + headScale);
  const thickness = unit * girth * 1.3;
  const headLength = unit * headScale;

  const parts = [];
  const y = thickness / 2;
  const headCenter = [length / 2 - headLength / 2, y, 0];
  const headPivot = [length / 2, y, 0];
  parts.push({
    name: "head",
    parent: null,
    center: headCenter,
    size: [headLength, thickness * 1.05, thickness * 1.1],
    pivot: headPivot,
  });

  let prevPivot = [headCenter[0] - headLength / 2, y, 0];
  let prevName = "head";
  for (let i = 0; i < segments; i++) {
    // taper gently toward the tail.
    const taper = 1 - (i / segments) * 0.5;
    const segLen = unit * taper;
    const segThick = thickness * taper;
    const center = [prevPivot[0] - segLen / 2, y, 0];
    const name = `segment${i}`;
    parts.push({
      name,
      parent: prevName,
      center,
      size: [segLen, segThick, segThick],
      pivot: prevPivot.slice(),
    });
    prevPivot = [prevPivot[0] - segLen, y, 0];
    prevName = name;
  }

  return parts;
}

function buildHexapod(planId, pr, traits) {
  const length = traits.length_m || 0.02;
  const torsoLength = length * 0.4;
  const torsoHeight = torsoLength / (pr.torso_aspect || 2.5);
  const torsoWidth = torsoHeight * (pr.girth_ratio || 0.8);
  const legLength = torsoLength * (pr.leg_length_ratio != null ? pr.leg_length_ratio : 0.6);
  const headSize = torsoHeight * (pr.head_scale || 0.8);
  const abdomenLength = torsoLength * (pr.tail_ratio != null ? pr.tail_ratio : 1.0);
  const legThick = torsoWidth * 0.14;

  const torsoY = legLength + torsoHeight / 2;
  const parts = [];

  parts.push({
    name: "thorax",
    parent: null,
    center: [0, torsoY, 0],
    size: [torsoLength, torsoHeight, torsoWidth],
    pivot: [0, torsoY, 0],
  });

  const headPivot = [torsoLength / 2, torsoY + torsoHeight * 0.1, 0];
  const headCenter = addv(headPivot, [headSize * 0.4, 0, 0]);
  parts.push({
    name: "head",
    parent: "thorax",
    center: headCenter,
    size: [headSize * 0.8, headSize * 0.8, headSize * 0.8],
    pivot: headPivot,
  });

  for (const side of [1, -1]) {
    const pivot = [headCenter[0] + headSize * 0.25, headCenter[1] + headSize * 0.25, side * headSize * 0.2];
    parts.push({
      name: side > 0 ? "antenna_right" : "antenna_left",
      parent: "head",
      center: addv(pivot, [headSize * 0.5, headSize * 0.35, 0]),
      size: [headSize * 1.0, headSize * 0.12, headSize * 0.12],
      pivot,
    });
  }

  const abdomenPivot = [-torsoLength / 2, torsoY, 0];
  parts.push({
    name: "abdomen",
    parent: "thorax",
    center: [abdomenPivot[0] - abdomenLength / 2, torsoY, 0],
    size: [abdomenLength, torsoHeight * 0.9, torsoWidth * 0.9],
    pivot: abdomenPivot,
  });

  const legY = torsoY - torsoHeight / 2;
  const legZ = torsoWidth / 2 * 0.75;
  const xs = [torsoLength * 0.32, 0, -torsoLength * 0.32];
  const labels = ["front", "mid", "rear"];
  for (let i = 0; i < 3; i++) {
    for (const side of [1, -1]) {
      const pivot = [xs[i], legY, side * legZ];
      parts.push({
        name: `leg_${labels[i]}_${side > 0 ? "right" : "left"}`,
        parent: "thorax",
        center: [xs[i], legY - legLength / 2, side * legZ],
        size: [legThick, legLength, legThick],
        pivot,
      });
    }
  }

  if (planId === "hexapod_winged") {
    const wingspan = traits.wingspan_m || length * 4;
    const wingAspect = pr.wing_aspect || 1.6;
    const halfSpan = Math.max(wingspan / 2 - torsoWidth / 2, torsoWidth);
    const wingChord = halfSpan / wingAspect;
    const wingPivotY = torsoY + torsoHeight * 0.35;
    for (const side of [1, -1]) {
      const pivot = [torsoLength * 0.1, wingPivotY, side * torsoWidth * 0.3];
      parts.push({
        name: side > 0 ? "wing_right" : "wing_left",
        parent: "thorax",
        center: [pivot[0], pivot[1], pivot[2] + (side * halfSpan) / 2],
        size: [wingChord, torsoHeight * 0.05, halfSpan],
        pivot,
      });
    }
  }

  return parts;
}

// ---------- poseModel ----------

function sinCycle(phase, offset = 0) {
  return Math.sin(2 * Math.PI * (phase + offset));
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function applyKeyframes(base, keyframes, phase) {
  if (!keyframes || keyframes.length === 0) return;
  const sorted = keyframes.slice().sort((a, b) => a.t - b.t);
  let lo = sorted[sorted.length - 1];
  let hi = sorted[0];
  let loT = lo.t - 1;
  let hiT = hi.t;
  for (let i = 0; i < sorted.length; i++) {
    if (sorted[i].t <= phase) {
      lo = sorted[i];
      loT = sorted[i].t;
    }
  }
  for (let i = 0; i < sorted.length; i++) {
    if (sorted[i].t >= phase) {
      hi = sorted[i];
      hiT = sorted[i].t;
      break;
    }
  }
  const span = hiT - loT;
  const t = span > 0 ? (phase - loT) / span : 0;
  const names = new Set([...Object.keys(lo.parts || {}), ...Object.keys(hi.parts || {})]);
  for (const name of names) {
    const rLo = (lo.parts && lo.parts[name] && lo.parts[name].rot_deg) || [0, 0, 0];
    const rHi = (hi.parts && hi.parts[name] && hi.parts[name].rot_deg) || [0, 0, 0];
    const rot = [lerp(rLo[0], rHi[0], t), lerp(rLo[1], rHi[1], t), lerp(rLo[2], rHi[2], t)];
    ensure(base, name);
    base[name].rot = addv(base[name].rot, rot);
  }
}

function ensure(base, name) {
  if (!base[name]) base[name] = { rot: [0, 0, 0], pos: [0, 0, 0] };
}

function addIdleBob(base, phase, amp = 1) {
  ensure(base, "body");
  base.body.pos = addv(base.body.pos, [0, 0.01 * amp * sinCycle(phase), 0]);
  const headName = base.head ? "head" : null;
  if (headName) {
    base[headName].rot = addv(base[headName].rot, [0, 4 * amp * sinCycle(phase, 0.1), 0]);
  }
}

const animators = {
  quadruped: animateLeggedWalker,
  hopper: animateHopper,
  anuran: animateAnuran,
  biped_winged: animateBipedWinged,
  serpentine: animateSerpentine,
  hexapod: animateHexapod,
  hexapod_winged: animateHexapodWinged,
};

export function poseModel(model, species, poseName, phase) {
  phase = ((phase % 1) + 1) % 1;
  const poseSpec = (species.look && species.look.poses && species.look.poses[poseName]) || {};
  const amplitude = poseSpec.amplitude != null ? poseSpec.amplitude : 1;
  const base = {};
  for (const p of model.parts) ensure(base, p.name);

  const animate = animators[model.bodyPlan] || (() => {});
  animate(base, poseName, phase, amplitude, model);

  applyKeyframes(base, poseSpec.keyframes, phase);
  return base;
}

function legSwing(base, name, angle) {
  ensure(base, name);
  base[name].rot = addv(base[name].rot, [angle, 0, 0]);
}

function animateLeggedWalker(base, poseName, phase, amp) {
  if (poseName === "idle") {
    addIdleBob(base, phase, amp);
    return;
  }
  if (poseName === "rest") {
    ensure(base, "body");
    base.body.pos = addv(base.body.pos, [0, -0.02 * amp, 0]);
    for (const n of ["leg_front_left", "leg_front_right", "leg_rear_left", "leg_rear_right"]) {
      legSwing(base, n, 8);
    }
    return;
  }
  const swingDeg = poseName === "gallop" ? 35 : poseName === "trot" ? 28 : 22;
  const s = swingDeg * amp;
  // diagonal pairs: front-left+rear-right vs front-right+rear-left.
  legSwing(base, "leg_front_left", s * sinCycle(phase));
  legSwing(base, "leg_rear_right", s * sinCycle(phase));
  legSwing(base, "leg_front_right", s * sinCycle(phase, 0.5));
  legSwing(base, "leg_rear_left", s * sinCycle(phase, 0.5));
  if (poseName === "gallop") {
    ensure(base, "body");
    base.body.rot = addv(base.body.rot, [0, 0, 6 * amp * sinCycle(phase, 0.25)]);
    base.body.pos = addv(base.body.pos, [0, 0.015 * amp * Math.abs(sinCycle(phase * 2)), 0]);
    ensure(base, "tail");
    base.tail.rot = addv(base.tail.rot, [0, 10 * amp * sinCycle(phase, 0.25), 0]);
  } else {
    ensure(base, "tail");
    base.tail.rot = addv(base.tail.rot, [0, 6 * amp * sinCycle(phase), 0]);
  }
}

function animateHopper(base, poseName, phase, amp) {
  if (poseName === "idle") {
    addIdleBob(base, phase, amp);
    return;
  }
  if (poseName === "rest") {
    for (const n of ["leg_front_left", "leg_front_right", "leg_rear_left", "leg_rear_right"]) {
      legSwing(base, n, 15);
    }
    return;
  }
  // hop and walk: whole body bounces, rear legs drive the hop.
  const bounce = Math.max(0, sinCycle(phase));
  ensure(base, "body");
  base.body.pos = addv(base.body.pos, [0, 0.04 * amp * bounce, 0]);
  base.body.rot = addv(base.body.rot, [8 * amp * sinCycle(phase, 0.15), 0, 0]);
  legSwing(base, "leg_rear_left", -40 * amp * bounce);
  legSwing(base, "leg_rear_right", -40 * amp * bounce);
  legSwing(base, "leg_front_left", -15 * amp * bounce);
  legSwing(base, "leg_front_right", -15 * amp * bounce);
}

// Front legs are short struts; angle them outward (x, splay) and forward (z,
// lean) — this is the resting stance, applied in every pose.
function tuckFrontLegs(base) {
  for (const side of [1, -1]) {
    const name = `leg_front_${side > 0 ? "right" : "left"}`;
    ensure(base, name);
    base[name].rot = addv(base[name].rot, [side * 25, 0, -18]);
  }
}

// Rear legs, folded in a "Z" beside the hips: the thigh splays outward and
// pulls forward (x = outward splay, z = forward lean), then the shin bends
// hard back at the knee — a large *relative* rotation in the thigh's own
// (already splayed) frame, the same hairpin technique as the wing fold —
// so the foot ends up tucked back near the hip instead of trailing out
// beyond the splayed thigh. `foldAmount` 1 = fully folded (resting), 0 =
// fully extended (mid-hop).
function foldRearLeg(base, side, foldAmount, amp) {
  const thigh = `leg_rear_${side > 0 ? "right" : "left"}`;
  const shin = `${thigh}_lower`;
  ensure(base, thigh);
  ensure(base, shin);
  // foldAmount 1 = resting Z-fold (splayed out, pulled forward, knee bent
  // hard back); foldAmount 0 = kicked out behind for a hop launch (little
  // splay, swung back, nearly straight) — not just "no extra rotation",
  // which would leave the leg at its neutral straight-down build pose.
  const splay = lerp(15, 60, foldAmount) * amp;
  const forwardLean = lerp(45, -30, foldAmount);
  const kneeBend = lerp(15, 130, foldAmount) * amp;
  base[thigh].rot = addv(base[thigh].rot, [side * splay, 0, forwardLean]);
  base[shin].rot = addv(base[shin].rot, [0, 0, kneeBend]);
}

function animateAnuran(base, poseName, phase, amp) {
  ensure(base, "body");
  // Squat posture, common to every pose: nose tilted slightly up.
  base.body.rot = addv(base.body.rot, [0, 0, 6]);
  tuckFrontLegs(base);

  if (poseName === "idle") {
    addIdleBob(base, phase, amp);
    foldRearLeg(base, 1, 1, amp);
    foldRearLeg(base, -1, 1, amp);
    return;
  }
  if (poseName === "rest") {
    foldRearLeg(base, 1, 1, amp);
    foldRearLeg(base, -1, 1, amp);
    base.body.pos = addv(base.body.pos, [0, -0.015 * amp, 0]);
    return;
  }
  if (poseName === "walk") {
    const bounce = Math.max(0, sinCycle(phase));
    base.body.pos = addv(base.body.pos, [0, 0.012 * amp * bounce, 0]);
    foldRearLeg(base, 1, 0.8 - 0.3 * bounce, amp);
    foldRearLeg(base, -1, 0.8 - 0.3 * sinCycle(phase, 0.5), amp);
    return;
  }
  if (poseName === "swim") {
    const kick = Math.abs(sinCycle(phase));
    foldRearLeg(base, 1, 1 - kick, amp);
    foldRearLeg(base, -1, 1 - Math.abs(sinCycle(phase, 0.5)), amp);
    return;
  }
  // hop: rear legs extend backward as the body lifts and pitches up
  // (push-off), then fold again on landing.
  const t = ((phase % 1) + 1) % 1;
  const launch = Math.max(0, Math.sin(Math.PI * t)); // 0 -> 1 -> 0 over the cycle
  foldRearLeg(base, 1, 1 - launch, amp);
  foldRearLeg(base, -1, 1 - launch, amp);
  base.body.pos = addv(base.body.pos, [0, 0.035 * amp * launch, 0]);
  base.body.rot = addv(base.body.rot, [0, 0, 10 * amp * launch]);
}

// Folded wing: the inner segment sweeps backward alongside the flank
// (rotation about the local y axis, since the wing box extends sideways
// along z at rest) plus a small downward hug (rotation about x). The outer
// segment then bends hard back at the wrist — a large *relative* rotation in
// the inner segment's own (already-swept) frame — so it folds back over the
// inner segment instead of continuing to stick straight out. side = +1
// (right) / -1 (left).
function foldWing(base, side, sweepDeg, hugDeg, wristBendDeg) {
  const inner = side > 0 ? "wing_right" : "wing_left";
  const outer = `${inner}_outer`;
  ensure(base, inner);
  ensure(base, outer);
  base[inner].rot = addv(base[inner].rot, [side * hugDeg, -side * sweepDeg, 0]);
  // A ~180 deg relative yaw folds the outer segment back flush against the
  // inner one (a hairpin); a bit short of that leaves it angled off the tail.
  base[outer].rot = addv(base[outer].rot, [0, -side * wristBendDeg, 0]);
}

// Spread wing (fly/glide): both segments stay near their built-in sideways
// extension (rot ~0), with flap as a rotation about the body's long (x)
// axis — the correct axis for flapping a wing that extends along z. Both
// wings move in the same sense (mirrored by `side`) so they flap together.
function spreadWing(base, side, flapDeg, outerExtraDeg) {
  const inner = side > 0 ? "wing_right" : "wing_left";
  const outer = `${inner}_outer`;
  ensure(base, inner);
  ensure(base, outer);
  base[inner].rot = addv(base[inner].rot, [side * flapDeg, 0, 0]);
  base[outer].rot = addv(base[outer].rot, [side * outerExtraDeg, 0, 0]);
}

function tuckLegs(base, tuckDeg) {
  for (const name of ["leg_left", "leg_right"]) {
    ensure(base, name);
    // Rotate the leg (which hangs straight down at rest) up and back against
    // the belly — a rotation about the body's lateral (z) axis.
    base[name].rot = addv(base[name].rot, [0, 0, tuckDeg]);
  }
}

function animateBipedWinged(base, poseName, phase, amp) {
  if (poseName === "idle") {
    addIdleBob(base, phase, amp);
    foldWing(base, 1, 60, 8, 160);
    foldWing(base, -1, 60, 8, 160);
    return;
  }
  if (poseName === "perched") {
    foldWing(base, 1, 62, 8, 165);
    foldWing(base, -1, 62, 8, 165);
    return;
  }
  if (poseName === "rest") {
    foldWing(base, 1, 62, 8, 165);
    foldWing(base, -1, 62, 8, 165);
    ensure(base, "body");
    base.body.pos = addv(base.body.pos, [0, -0.02 * amp, 0]);
    return;
  }
  if (poseName === "glide") {
    spreadWing(base, 1, 0, 0);
    spreadWing(base, -1, 0, 0);
    tuckLegs(base, 150);
    return;
  }
  if (poseName === "fly") {
    // Amplitude ~40 deg around a spread (horizontal, rot ~0) wing; the outer
    // segment adds a little extra flap for a natural whip at the tip.
    const flap = 40 * amp * sinCycle(phase);
    spreadWing(base, 1, flap, flap * 0.4);
    spreadWing(base, -1, flap, flap * 0.4);
    tuckLegs(base, 150);
    ensure(base, "body");
    base.body.rot = addv(base.body.rot, [10, 0, 0]);
    return;
  }
  // walk / hop on the ground: wings folded, legs hop/step.
  foldWing(base, 1, 58, 8, 158);
  foldWing(base, -1, 58, 8, 158);
  const bounce = Math.max(0, sinCycle(phase));
  ensure(base, "body");
  base.body.pos = addv(base.body.pos, [0, 0.02 * amp * bounce, 0]);
  ensure(base, "leg_left");
  ensure(base, "leg_right");
  base.leg_left.rot = addv(base.leg_left.rot, [-30 * amp * bounce, 0, 0]);
  base.leg_right.rot = addv(base.leg_right.rot, [-30 * amp * bounce, 0, 0]);
}

function animateSerpentine(base, poseName, phase, amp, model) {
  const segNames = model.parts.map((p) => p.name).filter((n) => n !== "head");
  if (poseName === "idle") {
    ensure(base, "head");
    base.head.rot = addv(base.head.rot, [0, 6 * amp * sinCycle(phase, 0.1), 0]);
    return;
  }
  if (poseName === "rest") {
    return;
  }
  // travelling yaw wave down the body, slither and swim.
  const amount = poseName === "swim" ? 26 : 22;
  segNames.forEach((name, i) => {
    const wave = amount * amp * sinCycle(phase, -i * 0.12);
    ensure(base, name);
    base[name].rot = addv(base[name].rot, [0, wave, 0]);
  });
  ensure(base, "head");
  base.head.rot = addv(base.head.rot, [0, amount * 0.6 * amp * sinCycle(phase), 0]);
}

function animateHexapod(base, poseName, phase, amp) {
  if (poseName === "idle") {
    addIdleBob(base, phase, amp);
    return;
  }
  if (poseName === "rest") {
    return;
  }
  // tripod gait: front+rear on one side move with mid on the other.
  const s = 30 * amp;
  legSwing(base, "leg_front_left", s * sinCycle(phase));
  legSwing(base, "leg_rear_left", s * sinCycle(phase));
  legSwing(base, "leg_mid_right", s * sinCycle(phase));
  legSwing(base, "leg_front_right", s * sinCycle(phase, 0.5));
  legSwing(base, "leg_rear_right", s * sinCycle(phase, 0.5));
  legSwing(base, "leg_mid_left", s * sinCycle(phase, 0.5));
}

function animateHexapodWinged(base, poseName, phase, amp) {
  ensure(base, "wing_left");
  ensure(base, "wing_right");
  if (poseName === "idle") {
    addIdleBob(base, phase, amp);
    base.wing_left.rot = addv(base.wing_left.rot, [-20, 0, 0]);
    base.wing_right.rot = addv(base.wing_right.rot, [20, 0, 0]);
    return;
  }
  if (poseName === "perched") {
    base.wing_left.rot = addv(base.wing_left.rot, [-80, 0, 0]);
    base.wing_right.rot = addv(base.wing_right.rot, [80, 0, 0]);
    return;
  }
  if (poseName === "rest") {
    base.wing_left.rot = addv(base.wing_left.rot, [-80, 0, 0]);
    base.wing_right.rot = addv(base.wing_right.rot, [80, 0, 0]);
    return;
  }
  if (poseName === "fly") {
    const flap = 65 * amp * sinCycle(phase * 6);
    base.wing_left.rot = addv(base.wing_left.rot, [-10 - flap, 0, 0]);
    base.wing_right.rot = addv(base.wing_right.rot, [10 + flap, 0, 0]);
    return;
  }
  // walk: wings folded, legs step.
  base.wing_left.rot = addv(base.wing_left.rot, [-70, 0, 0]);
  base.wing_right.rot = addv(base.wing_right.rot, [70, 0, 0]);
  const s = 20 * amp;
  legSwing(base, "leg_front_left", s * sinCycle(phase));
  legSwing(base, "leg_rear_left", s * sinCycle(phase));
  legSwing(base, "leg_mid_right", s * sinCycle(phase));
  legSwing(base, "leg_front_right", s * sinCycle(phase, 0.5));
  legSwing(base, "leg_rear_right", s * sinCycle(phase, 0.5));
  legSwing(base, "leg_mid_left", s * sinCycle(phase, 0.5));
}
