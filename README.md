<!-- markdownlint-disable MD033 MD041 -->
<div align="center">

# GLQS - Girl Life Quick Start

[![Version](https://img.shields.io/github/v/release/xBandaku/GLQS?color=%230567ff&label=Latest%20Release&style=for-the-badge)](https://github.com/xBandaku/GLQS/releases/latest)
![Downloads](https://img.shields.io/github/downloads/xBandaku/GLQS/total?label=Total%20Downloads&style=for-the-badge)
[![License](https://img.shields.io/github/license/xBandaku/GLQS?style=for-the-badge)](LICENSE)

</div>
<!-- markdownlint-enable MD033 MD041 -->

*Girl Life is an 18+ game; this mod and repository are intended for adult audiences.*

GLQS is a quick-setup cheat mod for **Girl Life**. Once installed, you can
open it from your own room, from the game's cheat menu, or from Settings >
Mods. It covers 14 top-level screens - no save editing or outside tools
required.

This guide covers everything a player needs: getting the mod, installing it,
and turning it on in-game. (Developers who want to build GLQS from
source instead of downloading it should see [`CLAUDE.md`](CLAUDE.md) - not
needed for normal play.)

## What's in the Menu

- Clothing & Accessories, Body Mods - every outfit, tattoo, and piercing available at once
- Consumables, Money, Skills & Attributes, Grades & Academics
- Health & Energy, Recurrent Cheats - standing toggles like never needing to eat, sleep, or shave
- Relationships - status overview plus marry/divorce controls
- Fame & Reputation, Jobs & Career, Housing & Property - your homes and your car
- Magic, Lifestyle - casino chips, pain, and fetish preferences

The Consumables screen lists every item Set All touches: stackable items
with their counts, and single items (things you either own or don't) with a
click-to-toggle link. Set All fills stacks to the chosen amount and gives one
of each single item.

## Contents

- [1. How to Get the Mod](#1-how-to-get-the-mod)
- [2. How to Install the Mod](#2-how-to-install-the-mod)
- [3. How to Enable the Mod In-Game](#3-how-to-enable-the-mod-in-game)
- [Troubleshooting / FAQ](#troubleshooting--faq)

## 1. How to Get the Mod

> **Before you download:** GLQS is a mod for **Girl Life - English
> Community Version (ECV)**. Make sure Girl Life (ECV) is already installed
> and working on its own first - GLQS has nothing to load into by
> itself and cannot be played individually.

GLQS is distributed as a single, ready-to-use file, `GLQS.qsp`:

1. Go to the **[GLQS Releases page](https://github.com/xBandaku/GLQS/releases/latest)**.
2. The release at the top is always the newest version.
3. Under **Assets**, download **`GLQS.qsp`**.
   - The page will also list "Source code (zip)" and "Source code (tar.gz)" -
     ignore those. They're just a snapshot of the raw project source for
     developers and won't work as a mod on their own. You only need
     `GLQS.qsp`.
4. Save it somewhere you'll remember (e.g. your Downloads folder) - you'll
   move it in the next step.

There's nothing to unzip, install, or run - `GLQS.qsp` is the finished mod
file itself.

*Prefer to build it yourself from source instead? See the Build section in
[`CLAUDE.md`](CLAUDE.md).*

## 2. How to Install the Mod

1. Find the folder where **Girl Life** itself is installed.
2. Inside that folder, look for a subfolder named exactly `mod` (all
   lowercase, no "s"). If it doesn't exist yet, create it.
3. Move or copy the `GLQS.qsp` file you downloaded into that `mod` folder.
4. Don't rename the file - it must stay exactly `GLQS.qsp`.

You should now have a file at `<your Girl Life folder>/mod/GLQS.qsp`. That's
the entire install - the next section switches it on inside the game.

## 3. How to Enable the Mod In-Game

Putting the file in the `mod` folder makes it available, but Girl Life won't
actually use it until you register it once from inside the game:

1. Open Girl Life and get to the **Mods** screen, either:
   - from the very first title screen (before loading or starting a save),
     click **Manage mods**; or
   - from inside an existing save, open your in-game phone, tap the
     gear/Settings icon, then open the **Mods** tab.
2. Click **Install new mod**.
3. A text box asks you to type a mod name. Type `GLQS` exactly - capital
   letters matter - and confirm.
   - The prompt mentions "the example image above" - that's generic wording
     the game shows for installing any mod, not something specific to GLQS.
     Just type `GLQS`.
4. GLQS now appears in your installed mods list and is active immediately -
   no restart needed.

> **About the version number shown:** the Mods list displays version numbers
> in the base game's own major.minor "fix" patch format - so, for example,
> GLQS version 0.34.4 shows up as **"0.34 fix 4"**. It's the same version,
> not a mismatch.

<!-- -->

> **Using an existing save?** Girl Life tracks installed mods per save file.
> If you have older saves from before you installed GLQS, load each one and
> repeat steps 1-3 once, then save again so it sticks.

### Using the mod

Once installed, a bold **MOD Quick Setup MOD** link automatically appears near
the top of the screen whenever you're in your own room - click it to open
GLQS's own cheat menu. It's on by default, so there's nothing else to turn on.

The link only shows up in your own room: your current home's bedroom, your
uni dorm room, or the therapist's hotel room. It intentionally does not
appear anywhere else, including while your character is still being created
or during the game's own scripted story or sex scenes (even ones set in your
bedroom).

That's expected behavior, not a bug - it just keeps the link out of the way
everywhere except the one place you'd naturally check it.

You can also open GLQS from anywhere, two ways:

- **Settings > Mods tab:** click **Open GLQS** on the GLQS row.
- **The game's own cheat menu:** every tab has an **Open GLQS** link at the
  bottom.

**Return** in GLQS takes you back to whichever of these you came from. The
switch to hide the room link is on the GLQS Index; the other two ways stay
available either way.

## Troubleshooting / FAQ

**I don't see the "Quick Setup" link anywhere.**
First check you're actually in your own room (home bedroom, dorm room, or the
therapist's hotel room) - the link only appears there. If it's still missing
even in one of those rooms, open GLQS from phone Settings > **Mods** tab >
**Open GLQS** and check the room-link switch on its Index.

**I keep seeing a message like "WARNING: mod_GLQS is not found!", or the Quick
Setup link has disappeared after closing and reopening Girl Life.**
Go to phone Settings > **Mods** tab and click **Update all mods**. Confirm
the "are you sure" prompt by typing anything into it. This reloads every
installed mod's code for your current session and should bring GLQS back.

**I got a message like "GLQS.qsp is not a Girl life ECV mod, please contract
its author for help".**
(Yes, "contract" - that's the base game's own wording, not a typo introduced
here.) It means the game couldn't read `GLQS.qsp` as a valid mod. Re-download
the file in case it's corrupted or incomplete, confirm it's named exactly
`GLQS.qsp` inside your `mod` folder, and confirm you're running Girl Life -
English Community Version.

**I got an "ACCESS DENIED... cannot be played individually" message.**
That appears only if `GLQS.qsp` gets opened directly as if it were its own
game, instead of being installed as a mod through the Mods tab. Follow the
installation and enabling steps above instead.

**Where can I see what's new in the latest version?**
Check the [Releases page](https://github.com/xBandaku/GLQS/releases) on
GitHub for the full changelog, or, in-game, click the small info icon next to
GLQS's entry in your installed mods list.

## License

GLQS's own source code is licensed under the [MIT License](LICENSE). This
covers the mod's `.qsps`/`.qsp` files and build tooling only - it has no
bearing on **Girl Life** itself, which remains its own separate, independently
licensed game.
