# softlendar — Vocabulary Man

This is the shorthand vocabulary for the softlendar landing page.
Kep this man handy so you don't forget!

## Shorthand Reference

| Shorthand | Full Word     |
| --------- | ------------- |
| plese     | please        |
| valid     | validate      |
| mak       | make          |
| erl       | early         |
| brose     | browse        |
| voce      | voice         |
| static    | fun / victory |
| kep       | keep          |
| man       | manual        |
| ed        | edit          |
| msg       | message       |
| col       | column        |
| nw        | now           |
| se        | see           |
| loc       | location      |
| sv        | save          |
| late      | lately        |
| wwt       | wait          |
| sm        | some          |
| latr      | later         |
| evr       | ever          |
| lang      | language      |
| mem       | memory        |
| ne        | new           |

## Notes

- Use these shorthands when writing comments, docs, and msgs.
- If you're erl in the project and need to brose the code, this man will help you valid things.
- Kep it updated if new shorthands are added — it's a static reference!
- Nw you can se the loc of any file using these shorthands.
- Wwt no more — sv this man and ed it anytime!
- Sm shorthands save sm time!
### Total: 21 Shorthands
## technic
***overview** = tak a lok at evryfiles related to current project*
***redo** = cut/rm current project and rebuild it*
## Developing works
***feedyday** = user comment, complain, feedback;*
***logoday** = logo updating*
## Shorthand Rules
- *shh = shorthand*
- **any 4 letter word that has consonent at 1st and 3rd letter and vowel in 2nd and at last an e** — cut e = shh
- **any word that has to vowel in the middle** — cut one vowel from those 2 = shh 
- **any wrd that has two consonent in the 3rd and 4th places and one vowel in the 2nd place and another consonent at the 1st place** — cut vowel = shh
- use **data/import lng**

## Project Rules
- **if developer say no ned then no ned to ask permission** — just do it yourself
- **"succceesss" = stage and generate commit msg** — when user says "succceesss", run git add and stage all modified files then generate a commit message (do NOT commit)
- **in any chats if said listen then listen until said do it** — if user say listen then do not get on it until user say do it or mak it
**when said commited** — know that it is commited
**when said deployed** — know that it's liv and run: fetch softlendar.com
**when said data listen** — listen for detail
## Commit Log

### var:0 — initial commit

- index.html — login modal added, keyboard shortcut button added
- ct.js — Login() updated to use modal instead of prompt(), welcom h1 shows username
- ct.css — login overlay, box, inputs, button, error styles added
- keymap-ct.js — keyboard shortcuts (T, V, 1-4, H, W, N, ?)
- sound-ct.js — playSound() using Web Speech API with voice loading fix
- bootin-ct.js — showAlert1(), showAlert2() keymap help
- act-ct.js — imageUrls object, changeImage()
- deploy.md — deployment platform reference created
- man.md — vocabulary shorthand reference created

### var:1 — power command system

- power-ct.js — time-travel command system created (commit save, commit log, commit now, chnge code to date=, chnge code to var=)
- index.html — added power-ct.js script link, command input box with run button
- ct.css — power command box styles (black background, green terminal text, lawngreen borders)

### var:2 — termirator landing update

- index.html — future project links removed; marquee labels removed (logos only); nav bar added with smooth-scroll anchors; termirator_logo.svg, nametermer_logo.svg, haster_logo.svg, setomoly_logo.svg, brose_logo.svg, serch_logo.svg added to marquee; terminal section added with 3 contexts (softlendar/cyberdyne/termitoria); tab autocomplete; termirator added alongside catlearning.fyi; contact form added with email backend; favicon replaced with softlendar_logo.svg
- landing.css — terminal styles added (dark card, prompt, output, input, scrollbar); badge categories organized; badge-float animation added; contact form styles added (gradient bg, frosted card, animated button with loader); nav bar styles added
- main.py — Flask backend with /, /contact (POST), /api/projects, /api/health, and dynamic project detail routes (/softlendar, /catlearning, /termirator, /brose, /serch, /nametermer, /haster, /setomoly, /redarbot, /dobart, /bylothon)
- project.html — project detail page template with logo, tagline, description, stack, status, and visit button
- 404.html — dark theme 404 page with back link
- .env.example + requirements.txt — email config and Python dependencies
- man.md — commit log updated
- termirator_logo.svg — hex frame T-prompt with blink cursor
- nametermer_logo.svg — wifi mark with orange N
- haster_logo.svg — hex frame H with lightning crossbar and speed dot
- setomoly_logo.svg — atom orbit with nucleus dots and spinning electron
- brose_logo.svg — browser window with globe and traffic dots
- serch_logo.svg — magnifying lens with sparkle dots and scan line
- softlendar_logo.svg — sun with rays, glow ring, S-curve, sparkle dots
