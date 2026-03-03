# Session Context

## User Prompts

### Prompt 1

Implement the following plan:

# Plan: Multi-Agent Flowchart Architecture

## Context

The current flowchart agent is a single `LlmAgent` doing everything — asking questions, validating answers, saving state, handling commands. The user wants to split this into a proper multi-agent hierarchy:

1. **Principal Agent (PA)** — orchestrator managing conversation flow
2. **Question Tracker Agent** — determines and presents the next question
3. **Answer Validator Agent** — validates answers before s...

### Prompt 2

What is your view on :  Multi-Agent Systems in ADK , Are we following same patterns?

### Prompt 3

gemini-2.0-flash , i think this model is outdated, get the lates flash model?

### Prompt 4

If you see I have already answered the question The agent should be able to map if there are questions which are already answered then you should skip asking those questions

### Prompt 5

Hmm just not the next question but for the entirety of the flow chart , because user could update already answerewd question and can answer future questions

### Prompt 6

okay push the changes in , ensure no creds are pushed

### Prompt 7

okay how are we doing session management , I will need some thing where I can clean of the session

### Prompt 8

may be a shelll script that i run to clear of all of it?

### Prompt 9

Can you see the bug , when i changed the answers it should have branched , but it didnt

### Prompt 10

can you add this ./scripts/clear_sessions.sh into read me

### Prompt 11

great , well push this changes then

