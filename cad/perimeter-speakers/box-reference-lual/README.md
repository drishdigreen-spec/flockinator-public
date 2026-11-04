# Candidate enclosed speaker mount: lual speaker box

Source: [Speaker Box for 8Ω 5W Mini Speaker by lual](https://www.printables.com/model/1766846-speaker-box-for-8ohm-5w-mini-speaker/files), updated 28 June 2026; inspected 11 October 2026. Original files are unchanged. License as displayed on the primary page: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Keep this reference separate from the GPL carrier files. Any adaptation of this shell must retain its attribution and applicable license terms. No remix or panel adapter has been generated here.

## Fit and protection

The author specifies a snap-in housing for approximately 99 × 45 × 21 mm speakers. Owner measurements are 98 × 44 × 20 mm. That is a promising nominal match, but snap retention depends on actual lug location, thickness and seating; a smaller body does not establish successful retention.

The 3MF mesh measures **113 × 48 × 23 mm overall**, with one connected watertight solid and consistent winding. It includes a slotted front guard, side walls and internal snap features, with an open rear. At one unobstructed section the cavity is approximately 108 × 45 mm; clips reduce usable space elsewhere. No guarantee of fit is inferred from that section.

The guard addresses the exposed-diaphragm problem. Check that neither moving surface can touch the grille and that the cable exits freely. The reference retains the supplied speaker assembly rather than replacing its existing housing. Its open back means it does not itself provide a new sealed rear acoustic chamber; the author's description provides no measured acoustic improvement. Assess protection, retention and sound on one physical sample first.

## Integration with Flockinator

**The existing twin carrier cannot accept two copies at the current spacing:** centres are 110 mm apart, while each box is 113 mm long, giving 3 mm nominal overlap in a coplanar arrangement. Centres of 115 mm would leave a proposed 2 mm gap. An integrated design may use a shared shell wall instead, but that is a different model to validate.

Do not simply add the shell over the current carrier pads: both designs occupy the mounting-lug region and use different retention approaches. Retain the known panel interface and design a shell-to-adapter connection with two attachment points or a locating feature against rotation. Check the whiteboard plane and full assembly depth again; the previous 3.85 mm reference clearance does not transfer to this shell.

Keep one removable speaker assembly per node. Use the stock 150 mm leads where actual routing permits; extend the central four and any short perimeter routes. Provide strain relief and orient exits toward their ESP32. A removable rear retainer could protect the wiring where needed; it must preserve existing acoustic vents and be evaluated for rattle and clearance. A honeycomb front can replace the slotted guard in a later version if its open area and diaphragm clearance are maintained.

## Printing basis

Use the 3MF as geometry, then slice for the actual Bambu printer and filament; the supplied Prusa settings/G-code are not a Bambu print job. The page's 23 g and 1 h 24 m figures describe the author's PLA/Prusa MK3.9 print and are not estimates for our integrated model. No printer job has been sent.

The archive also includes OBJ and the author's PDF. On the initial OBJ import, face seams produced a non-watertight result; direct inspection of the 3MF gave a connected watertight mesh. `inspection.json` records the results and original file hashes. `box-inspection-preview.png` is our two-view rendering of the original 3MF geometry.

Decision: use this as a concrete candidate for the protected speaker enclosure. A front guard and surrounding shell are part of the required solution; the earlier bare carriers alone are not the completed design. Acoustic benefit remains an A/B test objective, not a claimed property.
