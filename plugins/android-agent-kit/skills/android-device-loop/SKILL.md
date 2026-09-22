---
name: android-device-loop
description: Drive and read an Android device without screenshots.
version: 1.0.0
license: MIT
---

# Device loop (text-first)

Read and control a real device or emulator through the accessibility tree instead of
screenshots. Works without a vision model, costs a fraction of the tokens an image
would, and gives deterministic element data — exact bounds, ids, and state — that a
screenshot cannot.

## When to Use

- Reproducing a reported bug on a device
- Confirming a UI change actually rendered
- Navigating an app to reach a screen under test
- Extracting what is currently on screen

**Don't use for:** visual-fidelity questions — colour accuracy, shadow softness, overlap
that the tree reports as legal. Those need a screenshot and a vision-capable review.

## Prerequisites

```bash
adb devices -l
```

`device` = ready. `unauthorized` = the USB-debugging prompt on the phone was never
accepted. `offline` = reconnect the cable. Empty list = enable Developer Options →
USB debugging, or boot an emulator.

With more than one device attached, every command below needs `-s <serial>`.

## Read the screen

```bash
adb exec-out uiautomator dump /dev/tty
```

Streams XML to stdout with no `/sdcard` round trip. If it returns nothing usable:

```bash
adb shell uiautomator dump /sdcard/ui.xml && adb shell cat /sdcard/ui.xml
```

Each `<node>` carries what you need to act:

| Attribute | Use |
|---|---|
| `text` | Visible label — the primary way to find an element |
| `content-desc` | Accessibility label; the only handle on icon-only buttons |
| `resource-id` | Stable id, survives copy changes — prefer it when present |
| `bounds="[x0,y0][x1,y1]"` | Tap point is the centre: `((x0+x1)/2, (y0+y1)/2)` |
| `clickable` | `false` means tapping does nothing — find the clickable ancestor |
| `enabled`, `checked`, `focused`, `scrollable` | Current state |

**A dump fails while the screen is animating.** That is not a broken tool — wait a
second and dump again. Retry up to three times before concluding something is wrong.
Secure windows (payment sheets, DRM video) legitimately refuse to dump.

## Act on what you found

Compute the centre of the target's `bounds`, then:

```bash
adb shell input tap <x> <y>
adb shell input swipe <x1> <y1> <x2> <y2> 300      # last arg = duration ms
adb shell input keyevent KEYCODE_BACK              # also HOME, ENTER, TAB, DEL
```

Text entry needs escaping — `input text` treats spaces and shell metacharacters as
syntax. Replace every space with `%s`:

```bash
adb shell input text "hello%sworld"
```

Tap the field first to focus it, then type. Verify by re-dumping and confirming the
field's `text` attribute changed — never assume typing landed.

## Scrolling to reach off-screen content

An element absent from the dump may exist below the fold. Scroll and re-dump:

```bash
adb shell wm size                                   # e.g. 1080x2340
adb shell input swipe 540 1600 540 700 400          # scroll down one screen
```

Stop when two consecutive dumps are identical — that means the list has bottomed out.
Cap the attempts; an infinite list will never converge.

## App control

```bash
adb shell monkey -p <package> -c android.intent.category.LAUNCHER 1   # launch
adb shell am start -n <package>/<.MainActivity>                       # launch a specific activity
adb shell am force-stop <package>
adb shell pm clear <package>                                          # wipe data, fresh-install state
adb shell pm list packages -3                                         # third-party packages only
adb shell dumpsys window | grep mCurrentFocus                         # what is actually in front
```

## Device facts that change your advice

```bash
adb shell getprop ro.build.version.sdk      # API level
adb shell wm size                           # resolution in px
adb shell wm density                        # dpi
```

The tree reports **pixels**; Material's rules are in **dp**. Convert before judging any
size: `dp = px / (density / 160)`. On a 480dpi device the ratio is 3, so a 48dp minimum
touch target is 144px. Skipping this conversion produces confidently wrong verdicts.

## Pitfalls

1. **Tapping coordinates from an old dump.** The screen moves. Dump, act, re-dump.
2. **Matching on `text` for icon buttons.** They have none — use `content-desc`.
3. **Tapping a non-clickable node.** `TextView` inside a clickable row does nothing;
   walk up to the smallest ancestor with `clickable="true"`.
4. **Forgetting `-s` with multiple devices.** adb errors out rather than picking one.
5. **Treating a dump failure as app breakage.** Animation and secure windows both block
   dumping while the app is perfectly healthy.

## Verification

- Element located by `resource-id` or `content-desc` where available, not raw coordinates
- Each action confirmed by a follow-up dump showing the expected change
- px→dp conversion applied before any size judgement
