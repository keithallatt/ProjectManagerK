Back: [[Project Tracking]]
12th June 2022

# Milestones

Milestones are a good way of keeping track of a projects progress at a glance.

## Setting milestones
For each project, a list / data structure keeps track of the different milestones, each milestone ordered based on what they rely on (Topological Ordering).

Each milestone will have
- A milestone name
- Start date (set when undertaking the tasks)
- End date (when milestone completed)
- Predicted end / goal end date
- Requirements
	- Maybe a way of determining which requirements are complete?

## How to determine 'completeness' of a milestone?

- In the list of requirements, each one could have a test suite associated with them, and when they all pass, the requirement is considered 'complete'
- If all requirements are considered 'complete', then the milestone is completed


## Warnings for missed milestones?

- Condition
	- Current Date >= Goal End Date && End Date is None
- Consequences