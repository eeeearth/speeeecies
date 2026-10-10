import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { buildModel, poseModel } from "../../site/js/blockmesh.js";

const bodyPlans = JSON.parse(await readFile(new URL("../../schema/v0.1/body-plans.json", import.meta.url)));
const fox = JSON.parse(await readFile(new URL("../../species/vulpes-vulpes/species.json", import.meta.url)));
// The pre-merge tegu record supplies these geometry inputs. Keep only the
// fields buildQuadrupedLike uses so this renderer test does not depend on PR #103.
const tegu = {
  traits: { length_m: 0.8, shoulder_height_m: 0.2 },
  look: { body_plan: "quadruped", proportions: { leg_length_ratio: 0.4 }, poses: { walk: {}, gallop: {} } },
};

function projectedLegBox(part, angleDeg) {
  const angle = (angleDeg * Math.PI) / 180;
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const offsetX = part.center[0] - part.pivot[0];
  const offsetY = part.center[1] - part.pivot[1];
  return {
    center: [part.pivot[0] + offsetX * cos - offsetY * sin, part.pivot[1] + offsetX * sin + offsetY * cos],
    axes: [[cos, sin], [-sin, cos]],
    half: [part.size[0] / 2, part.size[1] / 2],
  };
}

function boxesIntersect(a, b) {
  const delta = [b.center[0] - a.center[0], b.center[1] - a.center[1]];
  for (const axis of [...a.axes, ...b.axes]) {
    const projection = Math.abs(delta[0] * axis[0] + delta[1] * axis[1]);
    const radius = (box) => box.half.reduce((sum, half, index) => {
      const boxAxis = box.axes[index];
      return sum + half * Math.abs(axis[0] * boxAxis[0] + axis[1] * boxAxis[1]);
    }, 0);
    if (projection >= radius(a) + radius(b) - 1e-9) return false;
  }
  return true;
}

function assertNoSameSideLegIntersection(species, gait, phase) {
  const model = buildModel(species, bodyPlans);
  const transforms = poseModel(model, species, gait, phase);
  for (const side of ["left", "right"]) {
    const front = model.parts.find((part) => part.name === `leg_front_${side}`);
    const rear = model.parts.find((part) => part.name === `leg_rear_${side}`);
    assert.equal(front.pivot[2], rear.pivot[2], `${side} hips should share a lateral plane`);
    const frontBox = projectedLegBox(front, transforms[front.name].rot[2]);
    const rearBox = projectedLegBox(rear, transforms[rear.name].rot[2]);
    assert.equal(
      boxesIntersect(frontBox, rearBox),
      false,
      `${species.slug || "tegu"} ${gait} phase ${phase} ${side} legs intersect in profile`,
    );
  }
}

test("quadruped gait rotates legs in profile and moves feet fore and aft", () => {
  const model = buildModel(fox, bodyPlans);
  for (const [pose, expected] of [["walk", 22], ["gallop", 35]]) {
    const atForwardStride = poseModel(model, fox, pose, 0.25).leg_front_left.rot;
    assert.deepEqual(atForwardStride.slice(0, 2), [0, 0]);
    assert.ok(atForwardStride[2] > 0 && atForwardStride[2] <= expected);

    const leg = model.parts.find((part) => part.name === "leg_front_left");
    const dx = leg.center[0] - leg.pivot[0];
    const dy = leg.center[1] - leg.pivot[1];
    const angle = (atForwardStride[2] * Math.PI) / 180;
    const strideX = dx * Math.cos(angle) - dy * Math.sin(angle) - dx;
    assert.ok(strideX > 0, `${pose} should move the foot forward at phase 0.25`);
    assert.equal(leg.center[2] - leg.pivot[2], 0, "rest-pose leg is in the sagittal plane");

    const atBackStride = poseModel(model, fox, pose, 0.75).leg_front_left.rot;
    assert.ok(atBackStride[2] < 0, `${pose} should swing the foot back at phase 0.75`);
    assert.deepEqual(atBackStride.slice(0, 2), [0, 0], "gait should not rotate the leg sideways");
  }
});

test("walk, trot, and gallop keep same-side mammal legs from intersecting", () => {
  for (const phase of [0.25, 0.75]) {
    for (const gait of ["walk", "trot", "gallop"]) {
      assertNoSameSideLegIntersection(fox, gait, phase);
    }
    for (const gait of ["walk", "gallop"]) assertNoSameSideLegIntersection(tegu, gait, phase);
  }
});

test("geometry limit preserves tegu gallop and relative fox gait sizes", () => {
  const foxModel = buildModel(fox, bodyPlans);
  const teguModel = buildModel(tegu, bodyPlans);
  const foxWalk = poseModel(foxModel, fox, "walk", 0.25).leg_front_left.rot[2];
  const foxTrot = poseModel(foxModel, fox, "trot", 0.25).leg_front_left.rot[2];
  const foxGallop = poseModel(foxModel, fox, "gallop", 0.25).leg_front_left.rot[2];
  const teguGallop = poseModel(teguModel, tegu, "gallop", 0.25).leg_front_left.rot[2];

  assert.ok(foxWalk > 0 && foxWalk < foxTrot && foxTrot < foxGallop && foxGallop < 35);
  assert.equal(teguGallop, 35, "tegu geometry should retain the full gallop swing");
});
