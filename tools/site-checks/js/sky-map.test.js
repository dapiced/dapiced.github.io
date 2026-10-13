const test = require("node:test");
const assert = require("node:assert/strict");

const { siderealDegrees, horizontal, project, compass } = require("../../../assets/js/sky-map.js");

const LAT = 45.5019;
const LON = -73.5674;

test("polaris_altitude_is_close_to_the_latitude", () => {
  // Polaris: RA 37.95°, Dec +89.26°. Its altitude stays within ~1° of the latitude.
  for (const hour of [0, 6, 12, 18]) {
    const lst = siderealDegrees(new Date(Date.UTC(2026, 9, 13, hour)), LON);
    const { alt } = horizontal(37.95, 89.26, lst, LAT);
    assert.ok(Math.abs(alt - LAT) < 1, `alt ${alt} at ${hour}h UTC`);
  }
});

test("a_star_on_the_meridian_culminates_due_south", () => {
  const lst = 120;
  const { alt, az } = horizontal(lst, 0, lst, LAT);
  assert.ok(Math.abs(alt - (90 - LAT)) < 1e-9);
  assert.ok(Math.abs(az - 180) < 1e-9);
});

test("vincenzo_star_never_goes_far_below_montreal_horizon", () => {
  // ν Andromedae (Dec +41.08°): lowest altitude = 41.08 + 45.50 - 90 ≈ -3.4°.
  let lowest = 90;
  for (let minute = 0; minute < 24 * 60; minute += 10) {
    const lst = siderealDegrees(new Date(Date.UTC(2026, 9, 13, 0, minute)), LON);
    lowest = Math.min(lowest, horizontal(12.45, 41.08, lst, LAT).alt);
  }
  assert.ok(lowest > -4 && lowest < -3, `lowest ${lowest}`);
});

test("projection_puts_zenith_in_the_centre_and_horizon_on_the_unit_circle", () => {
  const zenith = project(90, 0);
  assert.ok(Math.abs(zenith.x) < 1e-12 && Math.abs(zenith.y) < 1e-12);
  const north = project(0, 0);
  assert.ok(Math.abs(north.y + 1) < 1e-12, "north on top");
  const east = project(0, 90);
  assert.ok(Math.abs(east.x + 1) < 1e-12, "east on the left, as seen looking up");
});

test("compass_rounds_to_the_nearest_of_eight_directions", () => {
  const names = "N,NE,E,SE,S,SW,W,NW".split(",");
  assert.equal(compass(10, names), "N");
  assert.equal(compass(350, names), "N");
  assert.equal(compass(225, names), "SW");
});
