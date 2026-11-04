# Speaker mounting and protective-case review

11 October 2026. Research and design recommendation; no new enclosure CAD or acoustic performance claim. Existing v1 carriers remain unchanged.

## Evidence

Owner measurements: 98 × 44 × 20 mm body; four approximately 6 mm mounting openings; mounting plane described as about 10 mm from front/back fascia. Hole-centre spacing and exact mounting-plane datum still need confirmation for revised CAD.

The [Waveshare listing](https://www.waveshare.com/product/accessories/8ohm-5w-speaker.htm) gives nominal 100 × 45 × 21 mm, 8 Ω, 5 W. No manufacturer mounting-hardware specification or acoustic driver parameters were found in the material reviewed. The [Francois Stander reference model](https://www.printables.com/model/1274311-waveshare-8o-5w-speaker) depicts a housed assembly. An existing acoustic housing is therefore the working inference; its sealing and any vents need checking on the physical unit. Do not assume both circular features are powered drivers without evidence.

## Mounting recommendation

Approximately 6 mm holes do not imply M6 screws or prove that rubber inserts were intended. For a temporary rigid attachment, retain M3 screws with washers whose outside diameter bridges the opening and seats wholly on the lug. Use a fitted reducing bush if needed to prevent lateral movement; leave assembly clearance and do not force a nominal 6 mm plug into an approximate opening. Use a locking nut or captive nut arrangement that secures the part without crushing the lug. Screw length depends on the measured stack.

For isolation, use a grooved silicone/EPDM grommet selected for actual hole diameter, lug thickness and screw size. A compression-limiting sleeve/shoulder can prevent the screw from flattening the elastomer. Avoid hard contact bypassing the compliant mount. No exact grommet or sleeve dimensions are released because lug thickness and seating have not been measured. Thin foam or silicone seating pads are a simpler anti-rattle option, but are not equivalent to fully isolating the fastener path.

This is a proposed mounting method, not a Waveshare-prescribed installation. [PUI Audio](https://puiaudio.com/news/what-makes-pui-audios-speaker-drivers-unique/) describes rubber/silicone isolation as a means to reduce transmission of vibration into the structure.

## Recommended printed design

One repeatable removable cradle per speaker, preserving its existing housing, is preferable as the first prototype. Capture its rigid rim/lugs rather than loading the diaphragms. Provide compliant seating pads, cable strain relief and a replaceable open honeycomb grille with clearance for all moving surfaces and any vents. Keep the front recess shallow and avoid hard body contact elsewhere that can rattle.

Use a separate panel adapter with two supported M3 attachment points, or one M3 screw and a positive locating feature, to resist rotation. Retain the verified panel-hole coordinates. Existing inlaid M3 mounting positions may require spacers; a new adapter must support its contact faces rather than distort the panel by tightening across a gap. Do not assume the previous standoff/screw length remains correct with a new bracket stack.

A white cradle and contrasting black open grille suit the existing visual direction. The grille is perforated, not a solid translucent lighting diffuser. As a starting target use approximately 50–60% open area over the sound-emitting region and verify clearance through full diaphragm travel. [Same Sky's enclosure guide](https://www2.sameskydevices.com/blog/how-to-design-a-micro-speaker-enclosure) describes the protection/attenuation tradeoff of grille openings and the need to keep a grille clear of moving parts.

## Expected acoustic value and test

The likely benefit is less rattling, secure orientation and protection. A second decorative shell around a closed housing does not automatically add usable rear acoustic volume. Preserve existing vents and radiating surfaces. If the hardware instead proves to be open-backed, a sealed rear chamber becomes a separate design option; it must be sized and tested rather than assigned an arbitrary volume. No bass port or acoustic chamber is specified here.

[Same Sky's mounting guidance](https://www2.sameskydevices.com/blog/speaker-mounting-guidelines-and-best-practices) explains that mounting and cavity design can affect resonance and that rigid, secure mounting can prevent buzzing. It supports testing the complete installation, not promising a tonal improvement from appearance alone.

Test the same speaker and node sequentially on the simple carrier and proposed cradle, at the same location, orientation, gain and listening/microphone position. Use speech, experiment tones and a modest-level sweep; compare rattles, response and the node microphone's pickup. Compare grille on/off. Establish each node's baseline separately before testing multiple simultaneous speakers. Repeated units should use the same construction to keep experimental behaviour comparable.

Decision: recommend a removable protective cradle with optional compliant seating. Full acoustic enclosure redesign is conditional on establishing whether the supplied housing already provides the rear chamber. This review does not authorize an unmeasured hole pattern or establish improved sound quality.
