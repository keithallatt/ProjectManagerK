12th June 2022

# Project Manager K
Created by: Keith Allatt | https://github.com/keithallatt | June 2022

### Some fun math :)

> Proof that there exists irrational numbers $p$, $q$ exist such that $p^q$ is rational.
> $(\sqrt{2}^{\sqrt{2}} \not\in \mathbb{Q} \implies (\sqrt{2}^{\sqrt{2}})^{\sqrt{2}} \in \mathbb{Q}) \implies (\exists p,q \not \in \mathbb{Q})(p^q \in \mathbb{Q})$
> 
> Proof that $e^x > 0$ for all $x \in \mathbb{R}$. 
$\begin{align*} (\exists k > 0)(e^x = -k) &\implies (\exists k > 0)(\frac{1}{k}e^{x} = -1) \implies \\ (\exists k > 0)(\frac{1}{\sqrt{k}}e^{x/2})^2 = -1) &\implies (\exists y \in \mathbb{R})(y^2 = -1) \implies \perp)\end{align*}$


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

####  The Good
- The program has a nice-enough looking GUI that runs at a passable FPS
- The command line tool is steadily gaining functionality
	- `cmd_line_file.py` runs over SSH on the Mac
#### The Bad
- Many interactions with the projects database is done through each script, not through the GUI or command line
- Many additions tank the FPS, and many aesthetic features had to be cut

## Checklist
- [x] SSH access from other computers set up
- [x] Static IP Address configured on router
- [x] Add VCS to main project
- [ ] Add Project Updating Functionality to GUI
- [x] Update project board path to this obsidian vault
- [x] Add command line tool.
	- [x] Add key functionality
		- [x] Git
			- [x] Pull
			- [x] Push
			- [x] Status
			- [x] Commit
- [ ] Add table for schedule or use some other format.
- [ ] ~~Customise colours of prompt in `PyInquirer`~~ (not possible with current version)
- [ ] Documentation
	- [ ] IO:
	- [ ] Project Tracking:
	- [ ] Git Integration
- [ ] Write Tests

