# FusionGears — user guide

**English** · [Русский](USER_GUIDE.ru.md) · [← back to the overview](../README.md)

The dialogs follow Fusion's interface language: Russian in a Russian Fusion, English in any other. To switch, change Fusion's language (Preferences → General → Language) and restart Fusion.

## 1. Installation

1. Download the repository (**Code → Download ZIP**) and unpack it. Rename the folder `FusionGears-main` to **`FusionGears`**: the folder name must match `FusionGears.py`, otherwise Fusion will not run it.
2. In Fusion press **Shift+S** (or **Utilities → Add-Ins → Scripts and Add-Ins**). This is not the *Fusion Extensions* store.
3. **Add-Ins** tab → **+** → select the `FusionGears` folder.
4. Turn on the switch in the FusionGears row. **Run on Startup** loads the add-in every time Fusion starts.

Three buttons appear:

| Button | Where |
|---|---|
| Herringbone / helical gear | Solid → Create |
| Bevel gear | Solid → Create |
| Gear train check | Solid → Inspect |

**Updating.** Replace the files in the folder and restart the add-in: switch it off and on again (or Stop → Run).

## 2. Quick start

1. Open a new design.
2. **Solid → Create → Herringbone / helical gear**.
3. In **Typical set** pick, for example, "Herringbone 1:2, 3D printing (m2, 20/40)".
4. Press **OK**. You get the pinion, the gear, a grounded frame, two revolute joints and a motion link.
5. **Assemble → Animate Joint Relationships** turns the pair. Dragging a gear with the mouse works too.

## 3. Cylindrical gear (herringbone, helical, spur)

| Field | Meaning |
|---|---|
| Typical set | fills the dialog with a ready set; *Custom* changes nothing |
| Tooth type | Herringbone / Helical / Spur |
| Normal module | module in the normal section of the tooth, mm |
| Number of teeth | teeth of this gear |
| Helix angle | helix angle at the pitch cylinder; 25–35° is usual for herringbone |
| Hand | Right / Left; the mating gear gets the opposite hand |
| Pressure angle | usually 20° |
| Face width | full width; each herringbone half is width/2 |
| Bore diameter | 0 — no bore |
| Backlash | normal backlash of the pair; each gear is thinned by half. 0.1–0.2 mm for FDM printing |
| Create mating gear | builds the second gear in mesh at the centre distance |
| Teeth of gear 2, Bore of gear 2 | the second gear |
| Joints and motion link | frame, revolute joints and motion link for the pair |
| Calculation | diameters, transverse module, centre distance; error messages also show here |

Herringbone gears print without supports and produce no axial force; a helical pair does, so plan the bearings for it.

## 4. Bevel gear

| Field | Meaning |
|---|---|
| Tooth line | Straight / Skew (tangential) / Spiral (logarithmic) / Circular arc (Gleason) |
| Outer transverse module | module at the large end, mm |
| Number of teeth / Teeth of the mating gear | both are needed: the ratio sets the cone angle |
| Shaft angle | angle between the shafts, usually 90° |
| Spiral angle (mid-face) | for skew, spiral and Gleason teeth, usually 25–35° |
| Hand | the mating gear gets the opposite hand |
| Cutter radius (0 = auto) | Gleason teeth only: radius of the cutter head; 0 takes the mean cone distance Rm |
| Face width | tooth length along the cone; the dialog warns above Re/3 |
| Back thickness | thickness of the disc behind the teeth |
| Sections along the tooth | accuracy of curved teeth (more is finer and slower) |
| Create mating gear | builds the mate with a common cone apex |

**Calculation** shows the pitch cone angle δ, the outer pitch diameter, the cone distance Re and the virtual number of teeth; for curved teeth also the spiral angle at the toe, mid-face and heel, and for Gleason teeth the cutter radius.

### Which tooth line to choose

| Tooth line | Tooth trace on the crown gear | Spiral angle along the tooth |
|---|---|---|
| Straight | radial line through the apex | 0 |
| Skew (tangential) | straight line tangent to a circle around the apex | grows towards the toe |
| Spiral (logarithmic) | logarithmic spiral | constant |
| Circular arc (Gleason) | arc of the cutter head circle | grows towards the heel, as on Gleason face-milled gears |

The Gleason tooth is the usual choice for curved-tooth bevel gears. A smaller cutter radius gives a more curved tooth and a larger change of the spiral angle; with a cutter radius equal to Rm and β = 35° the angle runs from about 30° at the toe to 40° at the heel. If the cutter is too small for the face, the dialog says so and suggests a value.

## 5. Mechanism: joints and motion link

**Joints and motion link** (on by default when a pair is built) creates:

- a grounded component **Gear frame**;
- a **revolute joint** for each gear about its axis, taken from a hidden "rotation axis" sketch inside the gear's component;
- a **motion link** "Gear ratio z1:z2". Its direction is tested: the pinion is turned by a quarter of its pitch and the teeth must not intersect.

To turn the gears:

- **Assemble → Animate Joint Relationships** follows motion links;
- dragging a gear with the mouse follows them too;
- **Animate Joint** (right-click a joint) turns **one** joint only, so the other gear stays still. That is how Fusion works, not a fault in the gear train.

Joints need an Assembly or Hybrid design. In a Part design the gears are built and a message says no joints were made.

## 6. Gear train check

**Inspect → Gear train check** analyses every revolute joint and motion link of the design, including ones you made by hand:

| Message | Meaning and fix |
|---|---|
| … the links make it turn in opposite directions / at different speeds | chains of links contradict each other, for example three gears meshing in a triangle cannot turn together. Remove a gear or a link |
| … the teeth of … collide when turning | the link has the wrong direction or ratio. Edit it and toggle Reverse, or fix the angles |
| … intersect in the current position | gears sit inside each other, often a new pair built at the origin over an old one. Move it |
| … are in mesh but have no motion link | one gear would turn and its neighbour would stay still. Add a motion link (Assemble → Motion Link) |
| Link … does not transmit rotation | the link is broken (see its state in the browser) or the gear cannot turn, for example it is grounded. Suppressed links are skipped |

How it works: for each link the check turns one of its joints by 3° with all other links suppressed and measures how the other joint moves. It then looks for contradictions across all chains and checks the bodies for intersections. Joint positions and link states are restored afterwards.

After a pair with joints is built, the check runs by itself and shows a window only when it finds a problem.

## 7. Demo set

The `demo/FusionGearsDemo` script shows the check at work:

1. Shift+S → **Scripts** tab → **+** → the `demo/FusionGearsDemo` folder → run it.
2. Two documents open:
   - **a correct gear train**: a z15 → z30 → z20 chain at an angle and a 15:30 bevel pair; the check finds no problems;
   - **a faulty gear train**: a reversed link, a z18 gear in mesh without a link and three z21 gears in a triangle; the check finds all three.
3. At the end the script shows what the check found. Run the check yourself in each document.

## 8. Typical sets

| Cylindrical | Bevel (shafts at 90°) |
|---|---|
| Herringbone 1:2, 3D printing — m2, 20/40, β30°, backlash 0.15 | Bevel 1:1, straight — m2, 20/20 |
| Herringbone 1:3, NEMA17 gearbox — m1.5, 15/45, 5 mm shaft | Bevel 1:2, straight — m1.5, 15/30 |
| Herringbone 1:3, large — m3, 18/54 | Bevel 1:1, spiral 35° — m2, 20/20 |
| Helical 1:2 — m1, 20/40, β20° | Bevel 1:2, skew 25° — m2, 16/32 |
| Spur 1:2 — m1, 17/34 | Bevel 1:3, spiral 35° — m1.5, 14/42 |
| Spur 1:4 — m0.5, 15/60 | Bevel 1:2, Gleason circular 35° — m2, 16/32 |

Add your own sets to `presets.py`: names in both languages, lengths in millimetres, angles in degrees, list items by their key (`herringbone`, `gleason`, `right`, …).

## 9. 3D printing tips

- Backlash 0.1–0.2 mm for FDM, 0.05 mm or less for resin.
- Keep at least 14–15 teeth: without profile shift, small gears are undercut.
- Module 1 mm or more for a 0.4 mm FDM nozzle; module 0.5 is at the limit.
- Herringbone gears print better than helical ones: no overhangs, no axial force.

## 10. Troubleshooting

| Symptom | Cause |
|---|---|
| No buttons | the add-in is not running, or its folder is not named `FusionGears` |
| Pointed tooth / teeth overlap at the root | too few teeth or too large an angle — add teeth |
| Face width exceeds … | reduce the bevel face width (≤ Re/3 is recommended) |
| The cutter radius … is too small | increase the Gleason cutter radius or set 0 |
| The other gear does not turn | Animate Joint was used; use Animate Joint Relationships |
| Gears turn the same way | the link is reversed — run the gear train check, it names the link |
| Dialogs in the wrong language | they follow Fusion's language; change it in Preferences and restart Fusion |
| "a command definition with that id already exists" | the add-in was restarted many times in one session; restart Fusion |
