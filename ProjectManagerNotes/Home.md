@@ -1,54 +0,0 @@
12th June 2022

# Project Manager K
Created by: Keith Allatt | https://github.com/keithallatt | June 2022

> Proof that there exists irrational numbers $p$, $q$ exist such that $p^q$ is rational.
> $(\sqrt{2}^{\sqrt{2}} \not\in \mathbb{Q} \implies (\sqrt{2}^{\sqrt{2}})^{\sqrt{2}} \in \mathbb{Q}) \implies (\exists p,q \not \in \mathbb{Q})(p^q \in \mathbb{Q})$


### Goal
The goal of this software is to be able to track a variety of projects and relevant milestones. 

There are a variety of [[Interaction Methods]].

[[Project Tracking]] allows for milestone planning over time; assigning severity to different milestone targets.

[[Project Planning]]

[[Security]]

[[Key Performance Indicators]]

[[Documentation]]

Useful Links
- [Format your notes](https://help.obsidian.md/How+to/Format+your+notes)

### Git Interaction
#Git is very useful for working in teams, and turns a lightweight database API into a verifiable project manager. 

## Project Status
####  *The Good*
- The program has a nice-enough looking GUI that runs at a passable FPS
- The command line tool is steadily gaining functionality
	- `cmd_line_file.py` runs over SSH on the Mac
#### *The Bad*
- Many interactions with the projects database is done through each script, not through the GUI or command line
- Many additions tank the FPS, and many aesthetic features had to be cut

## Checklist
- [x] SSH access from other computers set up
- [x] Static IP Address configured on router
- [x] Add VCS to main project
- [ ] Add Project Updating Functionality to GUI
- [x] Update project board path to this obsidian vault
- [ ] Add command line tool.
- [ ] Add table for schedule or use some other format.
- [ ] Customize colours of prompt in `PyInquirer`
- [ ] Documentation
	- [ ] IO:
	- [ ] Project Tracking:
	- [ ] Git Integration
- [ ] Write Tests
