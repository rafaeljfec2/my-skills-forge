## Required Deliverables

For every architectural proposal or evaluation, provide:

### 1. Logical Diagram (Text Format)

Use ASCII art or structured text to represent:

- Components and their relationships
- Data flow
- External dependencies
- Integration points

Example format:

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Client    │──────│   API GW    │──────│   Service   │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │   Database  │
                     └─────────────┘
```

### 2. Technical Justification

Explain:

- Why this architecture fits the requirements
- How it addresses key considerations
- Technology choices and their rationale
- Alignment with business goals

### 3. Points of Attention

Highlight:

- Critical implementation details
- Potential failure points
- Areas requiring careful monitoring
- Compliance or regulatory considerations
- Migration or integration challenges

### 4. Trade-offs

Document:

- What was prioritized and what was deferred
- Cost vs. benefit analysis
- Short-term vs. long-term implications
- Alternative approaches considered and why they were not chosen

## Output Template

Use this structure for architectural proposals:

```markdown
# [Architecture Name / System Design]

## Overview

[Brief description of the system and its purpose]

## Logical Architecture

[Text-based diagram showing components and relationships]

## Technical Justification

### Requirements Addressed

- [Requirement 1]: [How architecture addresses it]
- [Requirement 2]: [How architecture addresses it]

### Technology Choices

- [Technology 1]: [Rationale]
- [Technology 2]: [Rationale]

### Key Considerations

- **Performance**: [Approach]
- **Scalability**: [Approach]
- **Observability**: [Approach]
- **Security**: [Approach]
- **Cost**: [Approach]
- **Maintainability**: [Approach]

## Points of Attention

⚠️ **Critical Areas**:

- [Critical point 1]
- [Critical point 2]

📋 **Implementation Notes**:

- [Implementation detail 1]
- [Implementation detail 2]

🔍 **Monitoring Requirements**:

- [What to monitor]
- [Key metrics]

## Trade-offs

### Prioritized

- [What was prioritized and why]

### Deferred

- [What was deferred and implications]

### Alternatives Considered

- **Alternative 1**: [Why not chosen]
- **Alternative 2**: [Why not chosen]
```
