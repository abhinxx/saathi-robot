# Saathi — pitch script

## Submission description (paste this)

**Saathi** (साथी, Nepali for *companion*) is a small tethered field robot whose only job is to
reach into a void a human body cannot fit through, find a trapped person's hand, hold it, and
talk to them in their own language until the dig reaches them.

People trapped in rubble do not only die of injury. They die of shock, dehydration and giving up,
which is why the first thing a rescue team does before any lifting is get a voice to the person
and keep it there for as many hours as the excavation takes. Today that means a rescuer lying
face down in silt with one arm through a gap. It does not scale, it cannot enter a tunnel a
shoulder will not pass, and it has to stop the moment the barrier lake upstream starts moving.

On 26 August 2026 a glacier collapse in Rasuwa killed at least 669 people and left around 2,900
missing. Fourteen hydropower tunnels are flooded with people unaccounted for inside them. Nepal
has publicly asked for foreign technical help with tunnel rescue specifically. There is no
network in that valley, so Saathi runs its speech on the device.

Built this weekend: a 6-DOF RobStride arm on the LeRobot stack performing a force-limited hold on
a live human hand, with Nepali speech triggered on contact. The enabling detail is that these
actuators already report per-joint torque on every MIT-protocol feedback frame, and the driver
decodes it, but the robot class discards it. We put it back, which is what makes a grip safe
enough to close on a person.

**Track:** 2, Action. Plus the voice challenge.

---

## Round 1 — Pitch (1:30)

> **0:00** Part of my family is from these mountains. That photo is me on a pass up there. So
> understand that I did not go looking for a problem this weekend.
>
> **0:12** Four days ago a piece of a glacier the size of a neighbourhood fell twelve hundred
> metres into a valley in Nepal. Six hundred and sixty-nine people are confirmed dead. Two
> thousand nine hundred are still missing.
>
> **0:18** Everyone who could run, ran. The warning was minutes. Everyone still under that debris
> has been there since Wednesday morning.
>
> **0:30** Here is the thing I did not know before this weekend. People trapped in rubble do not
> mainly die of their injuries. They die of shock, of dehydration, and of giving up. So the first
> thing a rescue team does, before they lift a single slab, is get a voice to that person and
> keep it there. For as long as the dig takes. Six hours, sometimes longer.
>
> **0:50** Right now that means a human being lies face down in wet silt with one arm through a
> gap in the concrete, talking into the dark. It is the most important job on the site. It also
> does not scale, it cannot go into a tunnel a shoulder will not fit through, and it has to stop
> the second the lake above the valley starts to move. And there are two lakes above that valley
> still filling right now.
>
> **1:10** So we built the hand. This is Saathi. Companion, in Nepali. It goes into the gap a
> person cannot, it finds a hand, it holds it, and it talks to them in Nepali with no network,
> because there is no network left in that valley.
>
> **1:25** It does not dig. It does not lift. It stays.

## Demo (2:00)

1. **The grip, on a judge.** Ask one of them to put their hand in. Trigger the hold. Say out loud
   while it closes: *this is not closing to a position, it is closing to a force.* Let them feel
   it and confirm it does not hurt.
2. **Why that matters.** A normal gripper is told where to stop. Give it a hand instead of a box
   and it goes to that position anyway. Saathi is told how hard it may squeeze, and stops wherever
   the resistance crosses the limit.
3. **The voice.** Trigger the Nepali line on contact. State that in production this is generated
   on the device, and why: no signal at the bottom of a collapsed building.
4. **Honest scope, said before they ask.** This is the hand. The tracked body that carries it into
   the rubble is next, and it is on the last slide.

## Q&A — the four questions you will get

**"Why not just extract them?"**
Because extraction needs a crane and hours of engineering, and moving a crush injury too early
kills people. The gap between finding someone and reaching them is the dangerous part, and nothing
currently occupies that gap except a volunteer lying in the dirt.

**"Isn't this just a gripper with a speaker?"**
The gripper is the easy half. The hard half is that it closes on force rather than position, which
required getting torque out of a driver that decodes it and then throws it away, and that is the
only reason it is safe to put a person's hand in it.

**"How is this extreme-condition relevant?"**
It is built for a specific place. No network, no road for forty-two kilometres, no bridges,
fourteen flooded tunnels, and an upstream lake that can force an evacuation mid-rescue. Every
design choice, especially running speech on the device, comes from one of those facts.

**"What is the honest state of it?"**
The hold and the speech are real and you just watched them. The chassis is a render. The weight
of current arms is too high for the real thing and that needs hardware that does not exist yet.

## Final round (3:00) — cut to

Pitch to 1:30 as above. Demo the grip on a judge and the Nepali line, nothing else. Close on:
*the warning is minutes, the rescue is hours, and nobody should spend those hours alone.*
