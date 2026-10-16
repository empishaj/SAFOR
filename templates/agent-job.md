# SAFOR Agent Job — {{jobKey}}

> Authoritative contract: `{{jobJsonRef}}`  
> Job ID: `{{jobId}}`

## Job Identity
- Job ID: `{{jobId}}`
- Job Key: `{{jobKey}}`
- Type: {{jobType}}
- Contract Revision: {{contractRevision}}

## Package & Sequence
- Package: `{{packageId}}`
- Work Item: `{{workItemId}}`
- Plan Sequence: {{planSequence}}
- Package Sequence: {{packageSequence}}
- Dispatch Sequence: {{dispatchSequence}}
- Attempt: {{attempt}}
- Rework Cycle: {{reworkCycle}}

## MASTER Provenance
- Created: {{createdAt}}
- Issued: {{issuedAt}}
- MASTER: `{{masterId}}` {{masterVersion}}
- Run: `{{masterRunId}}`
- State Revision: {{masterStateRevision}}

## Assignment
- Agent: `{{agentId}}` — {{agentName}}
- Identity Revision: {{identityRevision}}
- Reason: {{assignmentReason}}

## Role
- Role: `{{roleId}}` — {{roleName}}
- Mission: {{roleMission}}
- Responsibilities: {{roleResponsibilities}}
- Must not act as: {{mustNotActAs}}

## Skills
{{skills}}

## Task
**Objective:** {{objective}}

{{instruction}}

**Expected outcome:** {{expectedOutcome}}

**In scope:** {{inScope}}

**Out of scope:** {{outOfScope}}

## Dependencies & Inputs
{{dependenciesAndInputs}}

## Authorization
{{authorization}}

## Workspace & Git
{{workspaceAndGit}}

## Scheduling
{{scheduling}}

## Expected Outputs & Return Paths
{{outputsAndReturnPaths}}

## Verification & Review
{{verificationAndReview}}

## Constraints & Stop Conditions
{{constraintsAndStops}}

---
This Markdown is a HUMAN-readable projection. The JSON job contract is authoritative.
