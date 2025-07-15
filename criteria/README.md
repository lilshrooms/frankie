# Criteria Folder

This folder contains YAML files defining underwriting criteria for each loan type.

## How to Use
- Each loan type (e.g., conventional, FHA, jumbo) should have its own YAML file (e.g., `conventional.yaml`).
- These files are loaded by the application to provide context to the AI model when evaluating loan requests.
- To add or update criteria, edit the relevant YAML file.

## Example Structure
```
loan_type: conventional
min_credit_score: 680
max_dti: 43
required_documents:
  - pay_stubs
  - bank_statements
  - credit_report
notes:
  - No bankruptcies in last 7 years
  - Stable employment history
``` 